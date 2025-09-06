
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PrivateRoomAPIView,
    PrivateRoomDetailAPIView,
)

# router = DefaultRouter()
# router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
# router.register(r'room-members', RoomMemberViewSet, basename='roommember')
# router.register(r'messages', MessageViewSet, basename='message')
# router.register(r'files', FileViewSet, basename='file')
# router.register(r'message-status', MessageStatusViewSet, basename='messagestatus')

urlpatterns = [
    path('private/', PrivateRoomAPIView.as_view(), name='private-room-list-create'),
    path('private/<uuid:id>/', PrivateRoomDetailAPIView.as_view(), name='private-room-detail'),
    # path('', include(router.urls)),
]
