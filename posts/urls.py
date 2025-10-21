from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import(
  PostLikeViewSet,
  PostViewSet,
  PostCommentViewSet,
  PostLikesGetAPIView,
  PostCommentGetAPIView
)

router = DefaultRouter()
router.register(r'post', PostViewSet, basename='post')
router.register(r'like', PostLikeViewSet, basename='post_like')
router.register(r'comment', PostCommentViewSet, basename='post_comment')


urlpatterns = [
    path('', include(router.urls)),
    path('<str:post_id>/likes/', PostLikesGetAPIView.as_view(), name='post-likes-get'),
    path('<str:post_id>/comments/', PostCommentGetAPIView.as_view(), name='post-comments-get'),
]
