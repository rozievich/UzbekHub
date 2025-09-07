from django.db import models
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import PrivateRoom, GroupRoomMember, Message, File, MessageStatus
from .serializers import (
    PrivateRoomSerializer,
    GroupRoomMemberSerializer,
    MessageSerializer,
    FileSerializer,
    MessageStatusSerializer,
)


# PrivateRoom model viewset
class PrivateRoomAPIView(APIView):
    queryset = PrivateRoom.objects.all()
    serializer_class = PrivateRoomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None, *args, **kwargs):
        rooms = self.queryset.filter(models.Q(user1=request.user) | models.Q(user2=request.user))
        serializer = self.serializer_class(rooms, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=PrivateRoomSerializer)
    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            private_room = serializer.save()
            return Response(self.serializer_class(private_room).data, status=201)
        return Response(serializer.errors, status=400)


# PrivateRoom detail view
class PrivateRoomDetailAPIView(APIView):
    queryset = PrivateRoom.objects.all()
    serializer_class = PrivateRoomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, id, format=None, *args, **kwargs):
        try:
            room = self.queryset.get(id=id)
            if room.user1 != request.user and room.user2 != request.user:
                return Response({"detail": "You do not have permission to view this room."}, status=403)
            serializer = self.serializer_class(room)
            return Response(serializer.data, status=200)
        except PrivateRoom.DoesNotExist:
            return Response({"detail": "Room not found."}, status=404)
    
    def delete(self, request, id, format=None, *args, **kwargs):
        try:
            room = self.queryset.get(id=id)
            if room.user1 != request.user and room.user2 != request.user:
                return Response({"detail": "You do not have permission to delete this room."}, status=403)
            room.delete()
            return Response(status=204)
        except PrivateRoom.DoesNotExist:
            return Response({"detail": "Room not found."}, status=404)
    

# GroupRoom api view
class GroupRoomAPIView(APIView):
    queryset = GroupRoomMember.objects.all()
    serializer_class = GroupRoomMemberSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None, *args, **kwargs):
        memberships = self.queryset.filter(user=request.user)
        serializer = self.serializer_class(memberships, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=GroupRoomMemberSerializer)
    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            membership = serializer.save()
            return Response(self.serializer_class(membership).data, status=201)
        return Response(serializer.errors, status=400)


# GroupRoom detail view\
class GroupRoomDetailAPIView(APIView):
    queryset = GroupRoomMember.objects.all()
    serializer_class = GroupRoomMemberSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, id, format=None, *args, **kwargs):
        try:
            membership = self.queryset.get(id=id, user=request.user)
            serializer = self.serializer_class(membership)
            return Response(serializer.data, status=200)
        except GroupRoomMember.DoesNotExist:
            return Response({"detail": "Membership not found."}, status=404)
    
    def delete(self, request, id, format=None, *args, **kwargs):
        try:
            membership = self.queryset.get(id=id, user=request.user)
            membership.delete()
            return Response(status=204)
        except GroupRoomMember.DoesNotExist:
            return Response({"detail": "Membership not found."}, status=404)


# class ChatRoomViewSet(viewsets.ModelViewSet):
#     queryset = ChatRoom.objects.all()
#     serializer_class = ChatRoomSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         return super().create(request, *args, **kwargs)

# class RoomMemberViewSet(viewsets.ModelViewSet):
#     queryset = RoomMember.objects.all()
#     serializer_class = RoomMemberSerializer
#     permission_classes = [permissions.IsAuthenticated]


# class MessageViewSet(viewsets.ModelViewSet):
#     queryset = Message.objects.all()
#     serializer_class = MessageSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]


# class FileViewSet(viewsets.ModelViewSet):
#     queryset = File.objects.all()
#     serializer_class = FileSerializer
#     permission_classes = [permissions.IsAuthenticated]
#     parser_classes = [MultiPartParser, FormParser]


# class MessageStatusViewSet(viewsets.ModelViewSet):
#     queryset = MessageStatus.objects.all()
#     serializer_class = MessageStatusSerializer
#     permission_classes = [permissions.IsAuthenticated]
