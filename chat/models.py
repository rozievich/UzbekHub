import uuid
import hashlib
from django.db import models
from django.conf import settings
from rest_framework.validators import ValidationError


class ChatRoom(models.Model):
    PRIVATE = "private"
    GROUP = "group"

    ROOM_TYPES = [
        (PRIVATE, "Private"),
        (GROUP, "Group"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default=PRIVATE)
    name = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=32, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    profile_pic = models.FileField(upload_to="room_pictures/", blank=True, null=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="RoomMember",
        related_name="rooms"
    )

    created_at = models.DateTimeField(auto_now_add=True)


    def clean(self):
        if self.room_type == self.PRIVATE:
            if self.name or self.username or self.description or self.profile_pic:
                raise ValidationError("For private chat, name, username, description, profile_pic must be empty.")
        if self.room_type == self.GROUP:
            if not self.name:
                raise ValidationError("Name is required for group chat.")

    def __str__(self):
        return f"{self.room_type}: {self.name or self.id}"


class RoomMember(models.Model):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"

    ROLES = [
        (MEMBER, "Member"),
        (ADMIN, "Admin"),
        (OWNER, "Owner"),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="room_members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")

    def __str__(self):
        return f"{self.user} in {self.room} ({self.role})"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField(blank=True, null=True)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies")
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.text and not self.attachments.exists():
            raise ValidationError("Message must have either text or file!")

    def __str__(self):
        return self.text[:30] if self.text else "No text"


# File model with custom manager
class FileManager(models.Manager):
    def get_or_create_with_owner(self, uploaded_file, owner, file_type="other"):
        hasher = hashlib.sha256()
        uploaded_file.open("rb")
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        uploaded_file.seek(0)

        file, created = self.get_or_create(
            unique_id=file_hash,
            defaults={
                "file": uploaded_file,
                "file_type": file_type,
                "file_size": uploaded_file.size,
            },
        )

        already_owned = file.owners.filter(id=owner.id).exists()
        if not already_owned:
            file.owners.add(owner)

        return file, created


# File model
class File(models.Model):
    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("voice", "Voice"),
        ("document", "Document"),
        ("other", "Other"),
    ]

    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="files")
    unique_id = models.CharField(max_length=64, unique=True, editable=False)
    messages = models.ManyToManyField(Message, related_name="attachments", blank=True)
    file = models.FileField(upload_to="chat_files/")
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="other")
    file_size = models.BigIntegerField(editable=False, default=0)
    is_temporary = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    objects = FileManager()
    
    def __str__(self):
        return f"{self.file_type} - {self.unique_id[:10]}"


class MessageAction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="actions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user", "value")

    def __str__(self):
        return f"{self.user} {self.value} on {self.message.id}"


class MessageStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="statuses")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "user")

    def __str__(self):
        return f"{self.user} - {self.message.id} (Read: {self.is_read})"
