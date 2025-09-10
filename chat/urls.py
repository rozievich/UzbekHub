from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatRoomViewSet,
    RoomMemberViewSet
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'members', RoomMemberViewSet, basename="room_members")

urlpatterns = [
    path('', include(router.urls)),
]
