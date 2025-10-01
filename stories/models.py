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
    audience = models.CharField(max_length=10, choices=select_action, default='pubic')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class StoryViewed(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='viewers')
    viewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.viewer.id)


class StoryReaction(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10)
    reacted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'user')

    def __str__(self):
        return f"{self.user.id} - {self.reaction}"
