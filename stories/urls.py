from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StoryModelViewSet
)

router = DefaultRouter()
router.register("story", StoryModelViewSet, basename="stories")

urlpatterns = [
    path('', include(router.urls))
]
