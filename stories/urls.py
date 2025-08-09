from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StoriesModelViewSet,
    ArchiveStoriesListAPIView,
    ArchiveStoryGetDeleteAPIView,
    UserPublicStoriesAPIView
)

router = DefaultRouter()
router.register('active', StoriesModelViewSet, basename="stories_viewset")


urlpatterns = [
    path('', include(router.urls)),
    path('active/<int:user_id>/stories/', UserPublicStoriesAPIView.as_view(), name="user_stories"),
    path('archive/', ArchiveStoriesListAPIView.as_view(), name="stories_list_delete"),
    path('archive/<int:pk>/', ArchiveStoryGetDeleteAPIView.as_view(), name="stories_detail"),
]
