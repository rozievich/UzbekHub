import hashlib
from django.db import models
from rest_framework.validators import ValidationError
from accounts.models import CustomUser


class ChatMessage(models.Model):
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="send_messages")
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="received_messages")
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="private_files/", blank=True, null=True)
    reaction = models.CharField(max_length=128, blank=True, null=True)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="replies")
    is_delivery = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        ordering = ["-created_at"]
    
    def clean(self):
        if not self.message and not self.file:
            raise ValidationError("Sending a message or file is mandatory!")

    def __str__(self):
        return self.message[:30] if self.message else "No message"

class File(models.Model):
    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("voice", "Voice"),
        ("document", "Document"),
        ("other", "Other"),
    ]

    unique_id = models.CharField(max_length=64, unique=True, editable=False)  # 🔑
    file = models.FileField(upload_to="files/")
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
        return f"{self.file_type}: {self.unique_id}"


class ChatGroup(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=32, unique=True)
    tags = models.CharField(max_length=32, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    profile_pic = models.FileField(upload_to="group_picture/")
    members = models.ManyToManyField(CustomUser, related_name="chat_groups")
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Chat Group"
        verbose_name_plural = "Chat Groups"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username


class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="group_files/", blank=True, null=True)
    is_delivery = models.ManyToManyField(CustomUser, related_name="delivery_messages", blank=True)
    is_read = models.ManyToManyField(CustomUser, related_name="read_messages", blank=True)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, blank=True, null=True, related_name="group_replies")
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Group Message"
        verbose_name_plural = "Group Messages"
        ordering = ["-created_at"]
    
    def clean(self):
        if not self.message and not self.file:
            raise ValidationError("Sending a message or file is mandatory!")

    def __str__(self):
        return self.message[:30] if self.message else "No Message"
