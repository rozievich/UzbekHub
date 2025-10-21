from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import(
  PostLikeViewSet,
  PostViewSet
)

router = DefaultRouter()
router.register(r'post', PostViewSet, basename='post')
router.register(r'post-like', PostLikeViewSet, basename='post-like')


urlpatterns = [
    path('', include(router.urls)),
]
