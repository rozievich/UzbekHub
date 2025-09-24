from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .consumers import redis_client
from .models import ChatRoom, Message, File, RoomMember
from .serializers import (
    ChatRoomSerializer,
    MessageSerializer,
    FileSerializer,
    RoomMemberSerializer
)


# Chat Room ViewSet
class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ChatRoom.objects.none()
        return ChatRoom.objects.filter(members=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()

        channel_layer = get_channel_layer()
        
        for member in room.members.all():
            channels = redis_client.smembers(f"user_channels:{member.id}")
            for ch in channels:
                if redis_client.exists(f"channel:{ch}"):
                    async_to_sync(channel_layer.group_add)(
                        f"chat.{room.id}", ch
                    )
                else:
                    redis_client.srem(f"user_channels:{member.id}", ch)
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        room = self.get_object()

        if room.room_type == ChatRoom.GROUP:
            member = RoomMember.objects.filter(room=room, user=request.user).first()
            if not member or member.role not in [RoomMember.OWNER, RoomMember.ADMIN]:
                return Response({"detail": "Only the owner or admin group can change the room."}, status=403)
            return super().update(request, *args, **kwargs)

        if room.room_type == ChatRoom.PRIVATE:
            return Response({"detail": "It is not possible to change the private chat."}, status=403)

        return Response({"detail": "The room type was incorrectly specified."}, status=403)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()

        if room.room_type == ChatRoom.GROUP:
            member = RoomMember.objects.filter(room=room, user=request.user).first()
            if not member or member.role != RoomMember.OWNER:
                return Response({"detail": "Only the owner group can delete a room."}, status=403)
            return super().destroy(request, *args, **kwargs)

        if room.room_type == ChatRoom.PRIVATE:
            if not RoomMember.objects.filter(room=room, user=request.user).exists():
                return Response({"detail": "You are not a member of this private chat."}, status=403)
            return super().destroy(request, *args, **kwargs)
        return Response({"detail": "The room type was incorrectly specified."}, status=403)

    @action(detail=True, methods=["delete"], url_path="clear_messages")
    def clear_messages(self, request, pk=None):
        room = self.get_object()

        member = RoomMember.objects.filter(room=room, user=request.user).first()
        if not member:
            return Response({"detail": "You are not a member of this chat."}, status=403)

        if room.room_type == ChatRoom.GROUP and member.role not in [RoomMember.OWNER, RoomMember.ADMIN]:
            return Response({"detail": "In group chats, only the owner or admin can clear messages."}, status=403)

        room.messages.all().delete()

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat.{room.id}",
            {
                "type": "chat.cleared",
                "room_id": str(room.id),
                "cleared_by": request.user.id
            }
        )
        return Response(status=204)


# Room Members ViewSet
class RoomMemberViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    def get_room(self, room_id):
        return get_object_or_404(ChatRoom, id=room_id)

    def get_member(self, room, user):
        return RoomMember.objects.filter(room=room, user=user).first()

    def check_membership(self, room):
        member = self.get_member(room, self.request.user)
        if not member:
            return None, Response({"detail": "You are not a member of this chat."}, status=status.HTTP_403_FORBIDDEN)
        return member, None

    @action(detail=False, methods=["get"], url_path=r'(?P<room_id>[^/.]+)/members')
    def list_members(self, request, room_id=None):
        room = self.get_room(room_id)
        member, error = self.check_membership(room)
        if error:
            return error
        serializer = RoomMemberSerializer(room.room_members.all(), many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/join')
    def join(self, request, room_id=None):
        room = self.get_room(room_id)
        if room.room_type != ChatRoom.GROUP:
            return Response({"detail": "You can only join group chats."}, status=400)

        member = self.get_member(room, request.user)
        if member:
            return Response({"detail": "You are already a member."}, status=200)

        RoomMember.objects.create(room=room, user=request.user, role=RoomMember.MEMBER)
        return Response({"detail": "You have joined the group."}, status=201)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/leave')
    def leave(self, request, room_id=None):
        room = self.get_room(room_id)
        member = self.get_member(room, request.user)
        if not member:
            return Response({"detail": "You are not a member."}, status=400)
        if member.role == RoomMember.OWNER:
            return Response({"detail": "Owner cannot be removed, transfer ownership to another user first."}, status=400)
        member.delete()
        return Response({"detail": "You have left the group."}, status=200)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/set_admin')
    def set_admin(self, request, room_id=None):
        room = self.get_room(room_id)
        actor, error = self.check_membership(room)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "User not found."}, status=404)
        if error:
            return error
        if actor.role != RoomMember.OWNER:
            return Response({"detail": "Only the owner can appoint an admin."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id).first()
        if not member:
            return Response({"detail": "User not found in the group."}, status=404)
        member.role = RoomMember.ADMIN
        member.save()
        return Response({"detail": f"{member.user} has been appointed as admin."}, status=200)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/remove_admin')
    def remove_admin(self, request, room_id=None):
        room = self.get_room(room_id)
        actor, error = self.check_membership(room)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "User not found."}, status=404)
        if error:
            return error
        if actor.role != RoomMember.OWNER:
            return Response({"detail": "Only the owner can remove an admin."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id, role=RoomMember.ADMIN).first()
        if not member:
            return Response({"detail": "User is not an admin or not found."}, status=404)
        member.role = RoomMember.MEMBER
        member.save()
        return Response({"detail": f"{member.user} has been demoted to member."}, status=200)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/transfer_owner')
    def transfer_owner(self, request, room_id=None):
        room = self.get_room(room_id)
        actor, error = self.check_membership(room)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "User not found."}, status=404)
        if error:
            return error
        if actor.role != RoomMember.OWNER:
            return Response({"detail": "Only the owner can transfer ownership."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id).first()
        if not member:
            return Response({"detail": "User not found in the group."}, status=404)
        actor.role = RoomMember.MEMBER
        actor.save()
        member.role = RoomMember.OWNER
        member.save()
        return Response({"detail": f"Ownership has been transferred to {member.user}."}, status=200)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/add_member')
    def add_member(self, request, room_id=None):
        room = self.get_room(room_id)
        actor, error = self.check_membership(room)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "User not found."}, status=404)
        if error:
            return error
        if actor.role not in [RoomMember.OWNER, RoomMember.ADMIN]:
            return Response({"detail": "Only an admin or owner can add a member."}, status=403)
        if RoomMember.objects.filter(room=room, user_id=user_id).exists():
            return Response({"detail": "User already a member."}, status=400)
        RoomMember.objects.create(room=room, user_id=user_id, role=RoomMember.MEMBER)
        return Response({"detail": "User has been added to the group."})

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/remove_member')
    def remove_member(self, request, room_id=None):
        room = self.get_room(room_id)
        actor, error = self.check_membership(room)
        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "User not found."}, status=404)
        if error:
            return error
        if actor.role not in [RoomMember.OWNER, RoomMember.ADMIN]:
            return Response({"detail": "Only admin or owner user can issue it."}, status=403)
        deleted, _ = RoomMember.objects.filter(room=room, user_id=user_id).delete()
        if deleted:
            return Response({"detail": "User removed from group."}, status=200)
        return Response({"detail": "User not found."}, status=404)


# Message ViewSet
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()

        qs = Message.objects.filter(room__members=self.request.user).select_related("sender", "room")

        room_id = self.request.query_params.get("room_id")
        if room_id:
            qs = qs.filter(room_id=room_id)

        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        room = serializer.validated_data.get("room")
        if not room.members.filter(id=self.request.user.id).exists():
            raise ValidationError({"detail": "You are not a member of this room."})
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user:
            return Response(
                {"detail": "You can only edit your own message."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user:
            return Response(
                {"detail": "You can only delete your own message."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path=r'room/(?P<room_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')
    def list_by_room(self, request, room_id=None):
        qs = Message.objects.filter(room_id=room_id).order_by("-created_at")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=200)


# File ViewSet
class FileViewSet(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return File.objects.none()
        return File.objects.filter(message__room__members=self.request.user).select_related("message", "message__sender")
