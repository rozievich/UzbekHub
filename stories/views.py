from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from .serializers import StoryModelSerializer
from .models import Story


class StoryModelViewSet(ModelViewSet):
    queryset = Story.objects.filter(is_active=True)
    serializer_class = StoryModelSerializer
    permission_classes = (IsAuthenticated, )

