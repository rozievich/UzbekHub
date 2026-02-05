from django.db import models

from accounts.models import CustomUser


# Create your models here.
class Story(models.Model):
    select_action = (
        ('public', 'Public'),
        ('contact', 'Contacts'),
        ('marked', 'Marked'),
    )
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    media = models.FileField(upload_to="stories/")
    caption = models.CharField(max_length=500, blank=True, null=True)
    marked = models.ManyToManyField(CustomUser, related_name="marked_users", blank=True)
    is_active = models.BooleanField(default=True)
    audience = models.CharField(max_length=10, choices=select_action, default='public')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['owner', 'is_active', '-created_at']),
            models.Index(fields=['audience', 'is_active']),
        ]

    def __str__(self):
        return str(self.id)


class StoryViewed(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='viewers')
    viewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]
        unique_together = ('story', 'viewer')
        indexes = [
            models.Index(fields=['story', 'viewer']),
            models.Index(fields=['viewer', '-viewed_at']),
        ]

    def __str__(self):
        return str(self.viewer.id)


class StoryReaction(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10)
    reacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reacted_at"]
        unique_together = ('story', 'user')
        indexes = [
            models.Index(fields=['story', '-reacted_at']),
        ]

    def __str__(self):
        return f"{self.user.id} - {self.reaction}"

