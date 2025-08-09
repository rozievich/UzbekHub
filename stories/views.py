from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import StoryModelSerializer
from .permissions import IsOwnerPermission
from .models import Story



# Active Stories view
class StoriesModelViewSet(ModelViewSet):
    queryset = Story.objects.filter(is_active=True)
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)
    parser_classes = (FormParser, MultiPartParser)

    def list(self, request, *args, **kwargs):
        user_stories = self.queryset.filter(owner=request.user)
        serializer = self.serializer_class(user_stories, many=True)
        return Response(data=serializer.data, status=200)


# Archive Stories Views
class ArchiveStoriesListAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, )
    parser_classes = (FormParser, MultiPartParser)

    def get(self, request, *args, **kwargs):
        user_stories = Story.objects.filter(owner=request.user, is_active=False)
        serializer = self.serializer_class(user_stories, many=True)
        return Response(serializer.data, status=200)


class ArchiveStoryGetDeleteAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)
    parser_classes = (FormParser, MultiPartParser)

    def get(self, request, pk):
        user_story = get_object_or_404(Story, pk=pk, is_active=False)
        self.check_object_permissions(request, user_story)
        serializer = self.serializer_class(user_story)
        return Response(data=serializer.data, status=200)

    def delete(self, request, pk):
        story = get_object_or_404(Story, pk=pk, is_active=False)
        self.check_object_permissions(request, story)
        story.delete()
        return Response(status=204)


# User Public Stories View
class UserPublicStoriesAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, user_id, *args, **kwargs):
        user_stories = Story.objects.filter(owner_id=user_id, is_active=True, is_private=False)
        serializer = self.serializer_class(user_stories, many=True)
        return Response(data=serializer.data, status=200)
