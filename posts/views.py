from rest_framework.response import Response
from rest_framework import viewsets, status, permissions, views, generics

from .permissions import IsOwnerOrReadOnly
from .models import (
    Post,
    PostLikes,
    PostComment,
    PostViews
)
from .serializers import (
    PostSerializer,
    PostLikeSerializer,
    PostCommentSerializer,
    PostViewSerializer
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


# Post Likes Get API View
class PostLikesGetAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        likes = PostLikes.objects.filter(post__id=post_id)
        serializer = PostLikeSerializer(likes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# Post Comment ViewSet
class PostCommentViewSet(viewsets.ModelViewSet):
    queryset = PostComment.objects.all()
    serializer_class = PostCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['post', 'patch', 'delete', 'head', 'options']


class PostCommentGetAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        comments = PostComment.objects.filter(post__id=post_id)
        serializer = PostCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# Post View CreateAPIView
class PostViewCreateAPIView(generics.CreateAPIView):
    queryset = PostViews.objects.all()
    serializer_class = PostViewSerializer
    permission_classes = [permissions.IsAuthenticated]


class PostViewGetAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        views = PostViews.objects.filter(post__id=post_id)
        serializer = PostViewSerializer(views, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
