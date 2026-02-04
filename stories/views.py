from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from accounts.models import CustomUser
from .models import Story, StoryViewed, StoryReaction
from .permissions import IsOwnerPermission
from .serializers import (
    StoryModelSerializer,
    StoryViewedModelSerializer,
    StoryReactionModelSerializer
)



# Active Stories view
class StoriesModelViewSet(ModelViewSet):
    queryset = Story.objects.filter(is_active=True)
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)
    parser_classes = (FormParser, MultiPartParser)

    def list(self, request, *args, **kwargs):
        user_stories = self.queryset.filter(owner=request.user)
        serializer = self.serializer_class(user_stories, many=True, context={"request": request})
        return Response(data=serializer.data, status=200)

    def retrieve(self, request, *args, **kwargs):
        story = get_object_or_404(Story, pk=kwargs.get("pk"), is_active=True)

        audience_checks = {
            "contact": lambda: request.user in story.owner.contact_lists.all(),
            "mention": lambda: request.user in story.mentions.all(),
        }

        check = audience_checks.get(story.audience)
        if check and not check() and request.user != story.owner:
            return Response(
                {"detail": "You do not have permission to view this story."},
                status=403
            )

        serializer = self.serializer_class(story, context={"request": request})
        return Response(data=serializer.data, status=200)


# User stories views
class UserStoriesAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, )

    def get(self, request, user_id=None, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=user_id)

        visible_q = (
            Q(owner=user) &
            Q(is_active=True) &
            (
                Q(audience='public') |
                (Q(audience='contact') & Q(owner__contact_lists__contact=request.user)) |
                (Q(audience='marked') & Q(marked=request.user))
            )
        )

        stories_qs = (
            Story.objects
            .filter(visible_q)
            .select_related('owner')
            .prefetch_related('marked', 'viewers', 'reactions')
            .distinct()
        )
        serializer = self.serializer_class(stories_qs, many=True, context={'request': request})
        return Response(serializer.data, status=200)



# Archive Stories Views
class ArchiveStoriesListAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, )
    parser_classes = (FormParser, MultiPartParser)

    def get(self, request, *args, **kwargs):
        user_stories = Story.objects.filter(owner=request.user, is_active=False)
        serializer = self.serializer_class(user_stories, many=True, context={"request": request})
        return Response(serializer.data, status=200)


class ArchiveStoryGetDeleteAPIView(APIView):
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, IsOwnerPermission)
    parser_classes = (FormParser, MultiPartParser)

    def get(self, request, pk):
        user_story = get_object_or_404(Story, pk=pk, is_active=False)
        self.check_object_permissions(request, user_story)
        serializer = self.serializer_class(user_story, context={"request": request})
        return Response(data=serializer.data, status=200)

    def delete(self, request, pk):
        story = get_object_or_404(Story, pk=pk, is_active=False)
        self.check_object_permissions(request, story)
        story.delete()
        return Response(status=204)


# Story Reactions viewset
class StoryReactionViewSet(ModelViewSet):
    queryset = StoryReaction.objects.all()
    serializer_class = StoryReactionModelSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['post', 'patch', 'delete']


# Story Viwed viewset
class StoryViewedModelViewSet(ModelViewSet):
    queryset = StoryViewed.objects.all()
    serializer_class = StoryViewedModelSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['post']
