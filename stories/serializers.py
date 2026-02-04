from rest_framework import serializers

from accounts.serializers import UserMiniSerializer
from .models import Story, StoryViewed, StoryReaction


class StoryViewedModelSerializer(serializers.ModelSerializer):
    viewer = UserMiniSerializer(read_only=True)

    class Meta:
        model = StoryViewed
        fields = "__all__"
        read_only_fields = ['viewer']

    def create(self, validated_data):
        request = self.context['request']
        story_view = StoryViewed.objects.create(viewer=request.user, **validated_data)
        return story_view


class StoryReactionModelSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = StoryReaction
        fields = "__all__"

    def create(self, validated_data):
        request = self.context['request']
        story_reaction = StoryReaction.objects.create(user=request.user, **validated_data)
        return story_reaction


class StoryModelSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    viewers = StoryViewedModelSerializer(read_only=True, many=True)
    reactions = StoryReactionModelSerializer(read_only=True, many=True)

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_at", "updated_at"]
        extra_kwargs = {
            'marked': {'required': False}
        }

    def create(self, validated_data):
        request = self.context['request']
        story = Story.objects.create(owner=request.user, **validated_data)
        return story
