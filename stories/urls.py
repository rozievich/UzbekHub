from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    StoriesModelViewSet,
    ArchiveStoriesListAPIView,
    ArchiveStoryGetDeleteAPIView,
    UserPublicStoriesAPIView,
    StoryReactionViewSet,
    StoryViewedModelViewSet
)

router = DefaultRouter()
router.register('active', StoriesModelViewSet, basename="stories_viewset")
router.register('reaction', StoryReactionViewSet, basename="stories_reaction")
router.register('viewed', StoryViewedModelViewSet, basename="stories_viewed")

urlpatterns = [
    path('', include(router.urls)),
    path('active/<int:user_id>/stories/', UserPublicStoriesAPIView.as_view(), name="user_stories"),
    path('archive/', ArchiveStoriesListAPIView.as_view(), name="stories_list_delete"),
    path('archive/<int:pk>/', ArchiveStoryGetDeleteAPIView.as_view(), name="stories_detail"),
]
