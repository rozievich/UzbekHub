import json
import redis
import threading
import time
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone
from .models import ChatRoom, Message, File, MessageAction, MessageStatus

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
HEARTBEAT_INTERVAL = 30
HEARTBEAT_TTL = 60

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
        self._set_online()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        self._send_undelivered_messages()

    def disconnect(self, code):
        if hasattr(self, "room_id"):
            async_to_sync(self.channel_layer.group_discard)(f"chat_{self.room_id}", self.channel_name)
        redis_client.delete(f"online_user:{self.user.id}")
        try:
            self.user.last_online = timezone.now()
            self.user.save(update_fields=["last_online"])
        except Exception:
            pass
        self.close(code=code)

    def _set_online(self):
        redis_client.setex(f"online_user:{self.user.id}", HEARTBEAT_TTL, "1")

    def _heartbeat_loop(self):
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            try:
                self._set_online()
            except Exception:
                break

    def receive(self, text_data=None):
        data = json.loads(text_data)
        if data.get("type") == "ping":
            self._set_online()
            self.send(text_data=json.dumps({"type": "pong"}))
            return
        if data.get("type") == "read":
            self._handle_read(data)
            return
        if data.get("type") == "action":
            self._handle_action(data)
            return
        if data.get("type") == "message":
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

        for member in self.room.members.all():
            MessageStatus.objects.create(
                message=message,
                user=member,
                is_delivered=self._is_online(member.id),
                delivered_at=timezone.now() if self._is_online(member.id) else None,
                is_read=(member == self.user),
                read_at=timezone.now() if member == self.user else None
            )

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
        value = data.get("value")
        message = Message.objects.filter(id=message_id).first()
        if not message:
            return
        action, created = MessageAction.objects.get_or_create(
            message=message,
            user=self.user,
            value=value
        )
        async_to_sync(self.channel_layer.group_send)(
            f"chat_{self.room_id}",
            {
                "type": "chat.action",
                "message_id": str(message.id),
                "value": value,
                "user": self.user.id,
                "created_at": str(action.created_at)
            }
        )

    def _handle_read(self, data):
        message_id = data.get("message_id")
        message = Message.objects.filter(id=message_id).first()
        if not message:
            return
        status = MessageStatus.objects.filter(message=message, user=self.user).first()
        if status and not status.is_read:
            status.is_read = True
            status.read_at = timezone.now()
            status.save()
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.room_id}",
                {
                    "type": "chat.read",
                    "message_id": str(message.id),
                    "user": self.user.username,
                    "read_at": str(status.read_at)
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
            "value": event["value"],
            "user": event["user"],
            "created_at": event["created_at"]
        }))

    def chat_read(self, event):
        self.send(text_data=json.dumps({
            "type": "read",
            "message_id": event["message_id"],
            "user": event["user"],
            "read_at": event["read_at"]
        }))

    def _is_online(self, user_id):
        return redis_client.get(f"online_user:{user_id}") == "1"

    def _send_undelivered_messages(self):
        undelivered = MessageStatus.objects.filter(
            user=self.user, is_delivered=False
        ).select_related("message")
        for status in undelivered:
            msg = status.message
            self.send(text_data=json.dumps({
                "type": "message",
                "message_id": str(msg.id),
                "text": msg.text,
                "sender": msg.sender.username,
                "reply_to": msg.reply_to.id if msg.reply_to else None,
                "file_id": None,
                "created_at": str(msg.created_at)
            }))
            status.is_delivered = True
            status.delivered_at = timezone.now()
            status.save()
