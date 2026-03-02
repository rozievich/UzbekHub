from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PostLikes, PostComment
from notifications.utils import send_fcm_notification
from notifications.constants import LIKE_TITLE, LIKE_BODY, COMMENT_TITLE, COMMENT_BODY, REPLY_TITLE, REPLY_BODY

@receiver(post_save, sender=PostLikes)
def notify_post_like(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        recipient = post.owner
        sender_user = instance.owner
        
        # Don't notify if user likes their own post
        if recipient != sender_user:
            title = LIKE_TITLE
            body = LIKE_BODY.format(user=sender_user.username or sender_user.email)
            
            send_fcm_notification(
                user=recipient,
                title=title,
                body=body,
                notification_type='like',
                sender=sender_user,
                data={'post_id': str(post.id)}
            )

@receiver(post_save, sender=PostComment)
def notify_post_comment(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        recipient = post.owner
        sender_user = instance.owner
        
        # 1. Notify post owner (if not the same person)
        if recipient != sender_user:
            title = COMMENT_TITLE
            body = COMMENT_BODY.format(user=sender_user.username or sender_user.email)
            
            send_fcm_notification(
                user=recipient,
                title=title,
                body=body,
                notification_type='comment',
                sender=sender_user,
                data={'post_id': str(post.id), 'comment_id': str(instance.id)}
            )
            
        # 2. Notify parent comment owner if it's a reply (if not the same person)
        if instance.reply_to and instance.reply_to.owner != sender_user:
            # Don't send double notification to post owner if they are also the parent comment owner
            if instance.reply_to.owner != recipient:
                title = REPLY_TITLE
                body = REPLY_BODY.format(user=sender_user.username or sender_user.email)
                
                send_fcm_notification(
                    user=instance.reply_to.owner,
                    title=title,
                    body=body,
                    notification_type='comment',
                    sender=sender_user,
                    data={'post_id': str(post.id), 'comment_id': str(instance.id)}
                )
