import uuid
import hashlib
from django.db import models
from django.conf import settings
from rest_framework.validators import ValidationError


class PrivateRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="private_rooms_as_user1")
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="private_rooms_as_user2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user1", "user2")
    
    def save(self, *args, **kwargs):
        if self.user1 == self.user2:
            raise ValidationError("user1 va user2 bir xil bo'lishi mumkin emas.")
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"PrivateRoom between {self.user1} and {self.user2}"


class GroupRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=32, unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    profile_pic = models.FileField(upload_to="group_pictures/", blank=True, null=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="GroupRoomMember",
        related_name="group_rooms"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class GroupRoomMember(models.Model):
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"

    ROLES = [
        (MEMBER, "Member"),
        (ADMIN, "Admin"),
        (OWNER, "Owner"),
    ]

    room = models.ForeignKey(GroupRoom, on_delete=models.CASCADE, related_name="group_room_members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("room", "user")

    def __str__(self):
        return f"{self.user} in {self.room} ({self.role})"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    private_room = models.ForeignKey(PrivateRoom, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    group_room = models.ForeignKey(GroupRoom, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
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


class File(models.Model):
    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("voice", "Voice"),
        ("document", "Document"),
        ("other", "Other"),
    ]

    unique_id = models.CharField(max_length=64, unique=True, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="chat_files/")
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="other")
    size = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            hasher = hashlib.sha256()
            self.file.open("rb")
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.unique_id = hasher.hexdigest()
            self.file.close()
        super().save(*args, **kwargs)

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
