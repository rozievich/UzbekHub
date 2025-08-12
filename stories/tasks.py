from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Story


@shared_task
def check_story_time():
    cutoff_time = timezone.now()-timedelta(hours=24)
    expired_stories = Story.objects.filter(
        created_at__lt=cutoff_time,
        is_active=True
    )
    expired_stories.update(is_active=False)
