import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Story


def delete_file(path):
    if path and os.path.isfile(path):
        os.remove(path)


@receiver(post_delete, sender=Story)
def auto_delete_profile_picture_on_delete(sender, instance, **kwargs):
    if instance.media:
        delete_file(instance.media.path)


@receiver(pre_save, sender=Story)
def auto_delete_old_profile_picture_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = Story.objects.get(pk=instance.pk).media
    except Story.DoesNotExist:
        return

    new_file = instance.media
    if old_file and old_file != new_file:
        delete_file(old_file.path)
