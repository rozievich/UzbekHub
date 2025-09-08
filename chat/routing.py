from django.urls import re_path
from .consumers import MultiRoomChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/$", MultiRoomChatConsumer.as_asgi()),
]
