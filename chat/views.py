from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ChatRoom, RoomMember, Message, File, MessageStatus
from .serializers import (
    ChatRoomSerializer,
    RoomMemberSerializer,
    MessageSerializer,
    FileSerializer,
    MessageStatusSerializer,
)

class ChatRoomViewSet(viewsets.ModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

class RoomMemberViewSet(viewsets.ModelViewSet):
    queryset = RoomMember.objects.all()
    serializer_class = RoomMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

class MessageStatusViewSet(viewsets.ModelViewSet):
    queryset = MessageStatus.objects.all()
    serializer_class = MessageStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
