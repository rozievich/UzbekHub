import os
import redis
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import File, Message, MessageStatus
from notifications.utils import send_fcm_notification
from notifications.constants import MESSAGE_TITLE, MESSAGE_BODY

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

@receiver(post_delete, sender=File)
def delete_file_from_disk(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


@receiver(pre_save, sender=File)
def delete_old_file_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = File.objects.get(pk=instance.pk).file
    except File.DoesNotExist:
        return False

    new_file = instance.file
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    if created:
        room = instance.room
        sender_user = instance.sender
        
        # Get all members except sender
        recipients = room.members.exclude(id=sender_user.id)
        
        for recipient in recipients:
            # Check if user is online in Redis
            is_online = redis_client.get(f"online_user:{recipient.id}") == "1"
            
            if not is_online:
                title = MESSAGE_TITLE
                body = MESSAGE_BODY.format(
                    user=sender_user.username or sender_user.email,
                    text=instance.text[:50] + "..." if instance.text and len(instance.text) > 50 else instance.text or "Fayl yuborildi"
                )
                
                send_fcm_notification(
                    user=recipient,
                    title=title,
                    body=body,
                    notification_type='message',
                    sender=sender_user,
                    data={'room_id': str(room.id), 'message_id': str(instance.id)}
                )
