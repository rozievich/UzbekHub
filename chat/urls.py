from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatRoomViewSet,
    RoomMemberViewSet,
    MessageViewSet,
    FileViewSet,
    MessageStatusViewSet,
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'room-members', RoomMemberViewSet, basename='roommember')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'files', FileViewSet, basename='file')
router.register(r'message-status', MessageStatusViewSet, basename='messagestatus')

urlpatterns = [
    path('', include(router.urls)),
]
