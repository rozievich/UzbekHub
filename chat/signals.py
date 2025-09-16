import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import File


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
