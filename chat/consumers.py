import json
import redis
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone
from .models import ChatRoom, Message, File, MessageAction, MessageStatus

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
HEARTBEAT_TTL = 60


class MultiRoomChatConsumer(WebsocketConsumer):
    def connect(self):
        self.joined_rooms = set()
        user = self.scope["user"]
        if not user.is_authenticated:
            self.close()
            return
        self.user = user

        redis_client.sadd(f"user_channels:{self.user.id}", self.channel_name)
        redis_client.setex(f"channel:{self.channel_name}", HEARTBEAT_TTL, self.user.id)

        self.accept()
        self._set_online()


    def disconnect(self, code):
        for rid in list(self.joined_rooms):
            async_to_sync(self.channel_layer.group_discard)(f"chat.{rid}", self.channel_name)
        redis_client.srem(f"user_channels:{self.user.id}", self.channel_name)
        redis_client.delete(f"channel:{self.channel_name}")
        redis_client.delete(f"online_user:{self.user.id}")
        try:
            self.user.last_online = timezone.now()
            self.user.save(update_fields=["last_online"])
        except Exception:
            pass

    # --- helpers ---
    def _set_online(self):
        redis_client.expire(f"channel:{self.channel_name}", HEARTBEAT_TTL)
        redis_client.expire(f"user_channels:{self.user.id}", 60)

    def _is_online(self, user_id):
        return redis_client.get(f"online_user:{user_id}") == "1"

    # --- receive router ---
    def receive(self, text_data=None):
        data = json.loads(text_data)

        t = data.get("type")
        if t == "ping":
            self._set_online()
            self.send(text_data=json.dumps({"type": "pong"}))
            return

        if t == "join_rooms":
            self._handle_join_rooms(data)
            return

        if t == "message":
            self._handle_message(data)
            return
        
        if t == "edit_message":
            self._handle_edit_message(data)
            return
        
        if t == "delete_message":
            self._handle_delete_message(data)
            return

        if t == "read":
            self._handle_read(data)
            return

        if t == "action":
            self._handle_action(data)
            return
        
        if t == "typing":
            self._handle_typing(data)
            return

    # --- handlers ---
    def _handle_join_rooms(self, data):
        room_ids = data.get("rooms", [])
        qs = ChatRoom.objects.filter(id__in=room_ids, members__id=self.user.id).values_list("id", flat=True)
        for rid in qs:
            async_to_sync(self.channel_layer.group_add)(f"chat.{rid}", self.channel_name)
            self.joined_rooms.add(str(rid))
        self.send_json({
            "action": "join_rooms",
            "status": "ok",
            "joined_rooms": list(self.joined_rooms),
        })
        self._send_undelivered_messages()

    def _handle_message(self, data):
        room_id = str(data.get("room_id"))
        if room_id not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "message", "type": "error", "message": "Not joined to the room"}))
            return
        room = ChatRoom.objects.filter(id=room_id, members__id=self.user.id).first()
        if not room:
            self.send(text_data=json.dumps({"event": "message", "type": "error", "message": "Not joined to the room"}))
            return
        text = data.get("text")
        reply_to_id = data.get("reply_to")
        file_id = data.get("file_id")

        reply_to = Message.objects.filter(id=reply_to_id, room_id=room_id).first() if reply_to_id else None
        file = File.objects.filter(id=file_id).first() if file_id else None

        message = Message.objects.create(room=room, sender=self.user, text=text, reply_to=reply_to)
        if file:
            file.message = message
            file.save(update_fields=["message"])

        # MessageStatus ni tezroq qilish uchun tayyorlab, bulk_create qilamiz
        statuses = []
        now = timezone.now()
        online_cache = {}
        for member_id, in room.members.values_list("id"):
            if member_id not in online_cache:
                online_cache[member_id] = self._is_online(member_id)
            is_me = (member_id == self.user.id)
            statuses.append(MessageStatus(
                message=message,
                user_id=member_id,
                is_delivered=online_cache[member_id],
                delivered_at=now if online_cache[member_id] else None,
                is_read=is_me,
                read_at=now if is_me else None
            ))
        MessageStatus.objects.bulk_create(statuses, batch_size=200)

        async_to_sync(self.channel_layer.group_send)(
            f"chat.{room_id}",
            {
                "type": "chat.message",
                "room_id": room_id,
                "message_id": str(message.id),
                "text": message.text,
                "sender": self.user.username,
                "reply_to": str(reply_to_id),
                "file_id": str(file_id),
                "created_at": message.created_at.isoformat()
            }
        )

    def _handle_edit_message(self, data):
        message_id = data.get("message_id")
        text = data.get("text")
        message = Message.objects.select_related("room").filter(id=message_id, sender=self.user).first()
        if not message or str(message.room_id) not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "edit_message", "type": "error", "message": "Message not found or not authorized"}))
            return
        
        message.text = text
        message.is_edited = True
        message.save(update_fields=["text", "is_edited", "update_at"])
        async_to_sync(self.channel_layer.group_send)(
            f"chat.{message.room_id}",
            {
                "type": "chat.edit_message",
                "message_id": str(message.id),
                "text": message.text,
                "created_at": message.created_at.isoformat(),
                "updated_at": message.update_at.isoformat()
            }
        )

    def _handle_delete_message(self, data):
        message_id = data.get("message_id")
        message = Message.objects.select_related("room").filter(id=message_id).first()
        if not message or str(message.room_id) not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "delete_message", "type": "error", "message": "Message not found or not authorized"}))
            return
        
        message.delete()
        async_to_sync(self.channel_layer.group_send)(
            f"chat.{message.room_id}",
            {
                "type": "chat.delete_message",
                "message_id": message_id
            }
        )

    def _handle_action(self, data):
        message_id = data.get("message_id")
        value = data.get("value")
        message = Message.objects.select_related("room").filter(id=message_id).first()
        if not message or str(message.room_id) not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "action", "type": "error", "message": "Message not found or not authorized"}))
            return

        action, _ = MessageAction.objects.update_or_create(message=message, user=self.user, defaults={"value": value})
        async_to_sync(self.channel_layer.group_send)(
            f"chat.{message.room_id}",
            {
                "type": "chat.action",
                "message_id": str(message.id),
                "value": value,
                "user": self.user.id,
                "created_at": action.created_at.isoformat() if action.created_at else None
            }
        )

    def _handle_read(self, data):
        message_id = data.get("message_id")
        message = Message.objects.select_related("room").filter(id=message_id).first()
        if not message or str(message.room_id) not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "read", "type": "error", "message": "Message not found or not authorized"}))
            return

        status = MessageStatus.objects.filter(message=message, user=self.user).first()
        if status and not status.is_read:
            status.is_read = True
            status.read_at = timezone.now()
            status.save(update_fields=["is_read", "read_at"])
            async_to_sync(self.channel_layer.group_send)(
                f"chat.{message.room_id}",
                {
                    "type": "chat.read",
                    "message_id": str(message.id),
                    "user": self.user.username,
                    "read_at": status.read_at.isoformat()
                }
            )
    
    def _handle_typing(self, data):
        room_id = str(data.get("room_id"))
        is_typing = data.get("is_typing", False)

        if room_id not in self.joined_rooms:
            self.send(text_data=json.dumps({"event": "typing", "type": "error", "message": "Not joined to the room"}))
            return
        room = ChatRoom.objects.filter(id=room_id, members__id=self.user.id).first()
        if not room:
            self.send(text_data=json.dumps({"event": "typing", "type": "error", "message": "Not joined to the room"}))
            return
        
        async_to_sync(self.channel_layer.group_send)(
            f"chat.{room_id}",
            {
                "type": "chat.typing",
                "user": self.user.id,
                "is_typing": is_typing
            }
        )

    # --- edit message event handlers ---
    def chat_edit_message(self, event):
        self.send(text_data=json.dumps(
            {
                "type": "edit_message",
                "message_id": event["message_id"],
                "text": event["text"],
                "created_at": event["created_at"],
                "updated_at": event["updated_at"]
            }
        ))
    
    # --- delete message event handlers ---
    def chat_delete_message(self, event):
        self.send(text_data=json.dumps(
            {
                "type": "delete_message",
                "message_id": event["message_id"]
            }
        ))

    # --- group event handlers ---
    def chat_message(self, event):
        self.send(text_data=json.dumps({
            "type": "message",
            "room_id": event["room_id"],
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

    def chat_typing(self, event):
        self.send(text_data=json.dumps({
            "type": "typing",
            "user": event["user"],
            "is_typing": event["is_typing"]
        }))

    def chat_cleared(self, event):
        self.send(text_data=json.dumps({
            "type": "cleared",
            "room_id": event["room_id"],
            "cleared_by": event["cleared_by"]
        }))

    # --- undelivered ---
    def _send_undelivered_messages(self):
        if not self.joined_rooms:
            self.send(text_data=json.dumps({"event": "undelivered_messages", "type": "error", "message": "Not joined to any room"}))
            return
        qs = (MessageStatus.objects
              .filter(user=self.user, is_delivered=False, message__room_id__in=self.joined_rooms)
              .select_related("message", "message__sender")
              .order_by("message__created_at"))

        now = timezone.now()
        for st in qs:
            msg = st.message
            self.send(text_data=json.dumps({
                "type": "message",
                "room_id": str(msg.room_id),
                "message_id": str(msg.id),
                "text": msg.text,
                "sender": msg.sender.id,
                "reply_to": str(msg.reply_to_id),
                "file_id": getattr(getattr(msg, "file", None), "id", None),
                "created_at": msg.created_at.isoformat()
            }))
            st.is_delivered = True
            st.delivered_at = now
        MessageStatus.objects.bulk_update(qs, ["is_delivered", "delivered_at"], batch_size=200)
