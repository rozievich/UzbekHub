from django.db import models
from uuid import uuid4

from accounts.models import CustomUser


# Post model
class Post(models.Model):
    id = models.CharField(max_length=128, default=uuid4, unique=True, primary_key=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.id

    @property
    def like_count(self):
        return self.post_likes.count()
    
    @property
    def comment_count(self):
        return self.post_comments.count()
    
    @property
    def view_count(self):
        return self.post_views.count()


# Post Image model
class PostImages(models.Model):
    id = models.CharField(max_length=128, default=uuid4, unique=True, primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images")
    image = models.FileField(upload_to="posts/images/")
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id


# Post Views model
class PostViews(models.Model):
    id = models.CharField(max_length=128, default=uuid4, unique=True, primary_key=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_views")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_views")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'owner')
        indexes = [
            models.Index(fields=['post', 'owner']),
        ]

    def __str__(self):
        return self.id


# Post Likes model
class PostLikes(models.Model):
    id = models.CharField(max_length=128, default=uuid4, unique=True, primary_key=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'owner')
        indexes = [
            models.Index(fields=['post', 'owner']),
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self):
        return self.id


# Post Comment model
class PostComment(models.Model):
    id = models.CharField(max_length=128, default=uuid4, unique=True, primary_key=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_comments")
    comment = models.CharField(max_length=600)
    reply_to = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="post_replies")
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['owner', '-created_at']),
        ]

    def __str__(self):
        return self.id

