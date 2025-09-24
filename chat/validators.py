from django.db.models import Sum
from django.core.exceptions import ValidationError

from .models import File

def get_user_storage_usage(user) -> int:
    return File.objects.filter(owner=user).aggregate(
        total_size=Sum("file_size")
    )["total_size"] or 0


def validate_user_storage(user, new_file):
    MAX_STORAGE = 200 * 1024 * 1024
    used = get_user_storage_usage(user)
    new_file_size = getattr(new_file, "size", 0)
    if used + new_file_size > MAX_STORAGE:
        raise ValidationError("Storage limit reached! Delete old files to upload new ones.")
