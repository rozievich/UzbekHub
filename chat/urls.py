from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatMessageListAPIView,
    ChatMessageRetrieveAPIView,
    ChatGroupModelViewSet,
    ChatGroupMessageListAPIView,
    ChatGroupMessageRetrieveUpdateDestroyAPIView,
    GroupMemberDestroyAPIView,
    GroupMemberAPIView,
    UploadFileAPIView,
    ChatUserMessageAPIView
)

router = DefaultRouter()

router.register("groups", ChatGroupModelViewSet, basename="groups")

urlpatterns = [
    path('file/upload/', UploadFileAPIView.as_view(), name="chat_file_upload"),
    path('group-member/', GroupMemberAPIView.as_view(), name="group_member_create"),
    path('group-member/<int:group_id>/', GroupMemberDestroyAPIView.as_view(), name="group_member_delete"),
    path('group-messages/', ChatGroupMessageListAPIView.as_view(), name="get_group_messages"),
    path('group-messages/<int:pk>/', ChatGroupMessageRetrieveUpdateDestroyAPIView.as_view(), name="group_messages"),
    path('messages/', ChatMessageListAPIView.as_view(), name="all_messages"),
    path('messages/user/<int:user_id>/', ChatUserMessageAPIView.as_view(), name="user_messages"),
    path('messages/<int:pk>/', ChatMessageRetrieveAPIView.as_view(), name="get_message"),
    path('', include(router.urls)),
]
