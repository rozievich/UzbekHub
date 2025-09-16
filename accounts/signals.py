import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import CustomUser


def delete_file(path):
    if path and os.path.isfile(path):
        os.remove(path)


@receiver(post_delete, sender=CustomUser)
def auto_delete_profile_picture_on_delete(sender, instance, **kwargs):
    if instance.profile_picture:
        delete_file(instance.profile_picture.path)


@receiver(pre_save, sender=CustomUser)
def auto_delete_old_profile_picture_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = CustomUser.objects.get(pk=instance.pk).profile_picture
    except CustomUser.DoesNotExist:
        return

    new_file = instance.profile_picture
    if old_file and old_file != new_file:
        delete_file(old_file.path)
