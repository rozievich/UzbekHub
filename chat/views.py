from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError

from .models import ChatRoom, Message, File, RoomMember
from .serializers import (
    ChatRoomSerializer,
    MessageSerializer,
    FileSerializer,
    RoomMemberSerializer
)


# =======================
# Chat Room ViewSet
# =======================
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
        serializer.save()
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


# =======================
# Room Members ViewSet
# =======================
class RoomMemberViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated, )

    def get_room(self, room_id):
        return get_object_or_404(ChatRoom, id=room_id)

    def get_member(self, room, user):
        return RoomMember.objects.filter(room=room, user=user).first()

    def check_membership(self, room):
        member = self.get_member(room, self.request.user)
        if not member:
            return None, Response({"detail": "Siz ushbu chatning a’zosi emassiz."}, status=status.HTTP_403_FORBIDDEN)
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
            return Response({"detail": "Faqat group chatlarga qo‘shilish mumkin."}, status=400)

        member = self.get_member(room, request.user)
        if member:
            return Response({"detail": "Siz allaqachon a’zosisiz."}, status=200)

        RoomMember.objects.create(room=room, user=request.user, role=RoomMember.MEMBER)
        return Response({"detail": "Guruhga qo‘shildingiz."}, status=201)

    @action(detail=False, methods=["post"], url_path=r'(?P<room_id>[^/.]+)/leave')
    def leave(self, request, room_id=None):
        room = self.get_room(room_id)
        member = self.get_member(room, request.user)
        if not member:
            return Response({"detail": "Siz a’zo emassiz."}, status=400)
        if member.role == RoomMember.OWNER:
            return Response({"detail": "Owner chiqishi mumkin emas, avval ownerlikni boshqa userga o‘tkazing."}, status=400)
        member.delete()
        return Response({"detail": "Guruhdan chiqdingiz."})

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
            return Response({"detail": "Faqat owner admin tayinlay oladi."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id).first()
        if not member:
            return Response({"detail": "User groupda topilmadi."}, status=404)
        member.role = RoomMember.ADMIN
        member.save()
        return Response({"detail": f"{member.user} admin qilindi."})

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
            return Response({"detail": "Faqat owner adminlikni olib tashlay oladi."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id, role=RoomMember.ADMIN).first()
        if not member:
            return Response({"detail": "User admin emas yoki topilmadi."}, status=404)
        member.role = RoomMember.MEMBER
        member.save()
        return Response({"detail": f"{member.user} endi oddiy member."})

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
            return Response({"detail": "Faqat owner ownerlikni o‘tkaza oladi."}, status=403)
        member = RoomMember.objects.filter(room=room, user_id=user_id).first()
        if not member:
            return Response({"detail": "User groupda topilmadi."}, status=404)
        actor.role = RoomMember.MEMBER
        actor.save()
        member.role = RoomMember.OWNER
        member.save()
        return Response({"detail": f"Ownerlik {member.user} ga o‘tkazildi."})

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
            return Response({"detail": "Faqat admin yoki owner member qo‘shishi mumkin."}, status=403)
        if RoomMember.objects.filter(room=room, user_id=user_id).exists():
            return Response({"detail": "User allaqachon a’zo."}, status=400)
        RoomMember.objects.create(room=room, user_id=user_id, role=RoomMember.MEMBER)
        return Response({"detail": "User groupga qo‘shildi."})

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
            return Response({"detail": "Faqat admin yoki owner user chiqarishi mumkin."}, status=403)
        deleted, _ = RoomMember.objects.filter(room=room, user_id=user_id).delete()
        if deleted:
            return Response({"detail": "User groupdan chiqarildi."})
        return Response({"detail": "User topilmadi."}, status=404)


# =======================
# Message ViewSet
# =======================
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

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
            raise ValidationError({"detail": "Siz bu xonaga a'zo emassiz."})
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user:
            return Response(
                {"detail": "Siz faqat o'z xabaringizni tahrirlashingiz mumkin."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user:
            return Response(
                {"detail": "Siz faqat o'z xabaringizni o'chirishingiz mumkin."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path=r'room/(?P<room_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')
    def list_by_room(self, request, room_id=None):
        qs = Message.objects.filter(room_id=room_id).order_by("-created_at")
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data, status=200)


# =======================
# File ViewSet
# =======================
class FileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return File.objects.none()
        return File.objects.filter(message__room__members=self.request.user).select_related("message", "message__sender")
