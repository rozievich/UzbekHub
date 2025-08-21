
# ...existing imports...
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.utils import timezone
from .models import ChatRoom, RoomMember, Message, File, MessageStatus, MessageAction

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            self.close()
            return
        self.user = user
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room = ChatRoom.objects.filter(id=self.room_id).first()
        if not self.room or not self.room.members.filter(id=user.id).exists():
            self.close()
            return
        async_to_sync(self.channel_layer.group_add)(f"chat_{self.room_id}", self.channel_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(f"chat_{self.room_id}", self.channel_name)
        self.close(code=code)

    def receive(self, text_data=None):
        data = json.loads(text_data)
        if data.get("action_type"):
            self._handle_action(data)
        else:
            self._handle_message(data)

    def _handle_message(self, data):
        text = data.get("text")
        reply_to_id = data.get("reply_to")
        file_id = data.get("file_id")
        reply_to = Message.objects.filter(id=reply_to_id).first() if reply_to_id else None
        file = File.objects.filter(id=file_id).first() if file_id else None

        message = Message.objects.create(
            room=self.room,
            sender=self.user,
            text=text,
            reply_to=reply_to
        )
        if file:
            file.message = message
            file.save()

        async_to_sync(self.channel_layer.group_send)(
            f"chat_{self.room_id}",
            {
                "type": "chat.message",
                "message_id": str(message.id),
                "text": message.text,
                "sender": self.user.username,
                "reply_to": reply_to_id,
                "file_id": file_id,
                "created_at": str(message.created_at)
            }
        )

    def _handle_action(self, data):
        message_id = data.get("message_id")
        action_type = data.get("action_type")
        value = data.get("value")
        message = Message.objects.filter(id=message_id).first()
        if not message:
            return
        action, created = MessageAction.objects.get_or_create(
            message=message,
            user=self.user,
            action_type=action_type,
            value=value
        )
        async_to_sync(self.channel_layer.group_send)(
            f"chat_{self.room_id}",
            {
                "type": "chat.action",
                "message_id": str(message.id),
                "action_type": action_type,
                "value": value,
                "user": self.user.username,
                "created_at": str(action.created_at)
            }
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            "type": "message",
            "message_id": event["message_id"],
            "text": event["text"],
            "sender": event["sender"],
            "reply_to": event["reply_to"],
            "file_id": event["file_id"],
            "created_at": event["created_at"]
        }))

    def chat_action(self, event):
        self.send(text_data=json.dumps({
            "type": "action",
            "message_id": event["message_id"],
            "action_type": event["action_type"],
            "value": event["value"],
            "user": event["user"],
            "created_at": event["created_at"]
        }))
