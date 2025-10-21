from rest_framework.response import Response
from rest_framework import viewsets, status, permissions

from .permissions import IsOwnerOrReadOnly
from .models import (
    Post,
    PostLikes,
    PostComment,
    PostViews
)
from .serializers import (
    PostSerializer,
    PostLikeSerializer
)

# Post ViewSet
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


# Post like ViewSet
class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = PostLikes.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['post', 'delete', 'head', 'options']
