from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.core.files.storage import default_storage

from .serializers import ChatMessageModelSerializer, ChatGroupModelSerializer, ChatGroupMessageModelSerializer
from .models import ChatMessage, ChatGroup, GroupMessage
from .permissions import OwnerBasePermission, GroupOwnerPermission



class ChatMessageListAPIView(ListAPIView):
    serializer_class = ChatMessageModelSerializer
    queryset = ChatMessage.objects.all()
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        user_id = self.request.user.id
        return ChatMessage.objects.filter(Q(from_user__id=user_id) | Q(to_user__id=user_id))


class ChatUserMessageAPIView(ListAPIView):
    serializer_class = ChatMessageModelSerializer
    queryset = ChatMessage.objects.filter()
    permission_classes = (IsAuthenticated, )
    
    def get_queryset(self):
        user = self.request.user
        user_id = self.kwargs.get("user_id")
        return ChatMessage.objects.filter(Q(from_user__id=user_id, to_user__id=user.id) | Q(from_user__id=user.id, to_user__id=user_id))


class ChatMessageRetrieveAPIView(RetrieveAPIView):
    serializer_class = ChatMessageModelSerializer
    queryset = ChatMessage.objects.all()
    permission_classes = (IsAuthenticated, OwnerBasePermission)


class ChatGroupModelViewSet(ModelViewSet):
    serializer_class = ChatGroupModelSerializer
    queryset = ChatGroup.objects.all()
    permission_classes = (IsAuthenticated, GroupOwnerPermission)
    parser_classes = (MultiPartParser, FormParser)


class ChatGroupMessageListAPIView(ListAPIView):
    serializer_class = ChatGroupMessageModelSerializer
    queryset = GroupMessage.objects.all()
    permission_classes = (IsAuthenticated, )


class ChatGroupMessageRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ChatGroupMessageModelSerializer
    queryset = GroupMessage.objects.all()
    permission_classes = (IsAuthenticated, )


class GroupMemberAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "group_id": openapi.Schema(type=openapi.TYPE_INTEGER)
            },
            required=['group_id']
        )
    )

    def post(self, request, *args, **kwargs):
        group_id = request.data.get("group_id")
        
        group_info = ChatGroup.objects.filter(pk=group_id).first()
        if not group_info:
            return Response({"message": "Group not found!"}, status=status.HTTP_404_NOT_FOUND)
        
        if group_info.members.filter(id=request.user.id).exists():
            return Response({"message": "The user is already subscribed to this group!"}, status=status.HTTP_409_CONFLICT)
        
        group_info.members.add(request.user)
        return Response({"message": "You have successfully subscribed to the group!"}, status=status.HTTP_200_OK)


class GroupMemberDestroyAPIView(DestroyAPIView):
    serializer_class = ChatGroupModelSerializer
    queryset = ChatGroup.objects.all()
    permission_classes = (IsAuthenticated, )

    def delete(self, request, *args, **kwargs):
        group_id = kwargs.get('group_id')
        group_info = ChatGroup.objects.filter(pk=group_id).first()

        if not group_info:
            return Response({"message": "Group not found!"}, status=status.HTTP_404_NOT_FOUND)

        if not group_info.members.filter(id=request.user.id).exists():
            return Response({"message": "The user is not subscribed to this group!"}, status=status.HTTP_404_NOT_FOUND)
        
        group_info.members.remove(request.user)
        return Response({"message": "You have successfully left the group."}, status=status.HTTP_204_NO_CONTENT)


class UploadFileAPIView(APIView):
    parser_classes = (FormParser, MultiPartParser)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "file",
                openapi.IN_FORM,
                description="Downloadable file",
                type=openapi.TYPE_FILE,
                required=True
            ),
            openapi.Parameter(
                "chat_type",
                openapi.IN_FORM,
                description="Chat type: 'private' or 'group'",
                type=openapi.TYPE_STRING,
                enum=["private", "group"],
                required=True
            )
        ]
    )

    def post(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        chat_type = request.data.get("chat_type")

        if not file:
            return Response({'error': 'No file uploaded'}, status=400)
        
        if chat_type not in ["private", "group"]:
            return Response({"error": "The chat_type field must be 'private' or 'group'!"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = default_storage.save(f"{chat_type}_files/{file.name}", file)
        return Response({"file_url": file_path}, status=status.HTTP_201_CREATED)
