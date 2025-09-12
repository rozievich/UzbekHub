from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatRoomViewSet,
    RoomMemberViewSet,
    MessageViewSet
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'members', RoomMemberViewSet, basename="room_members")
router.register(r'message', MessageViewSet, basename="messages")

urlpatterns = [
    path('', include(router.urls)),
]
