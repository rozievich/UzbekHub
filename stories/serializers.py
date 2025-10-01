from rest_framework import serializers

from accounts.serializers import CustomUserMyProfileSerializer
from .models import Story, StoryViewed, StoryReaction


class StoryViewedModelSerializer(serializers.ModelSerializer):
    viewer = CustomUserMyProfileSerializer(read_only=True)
    viewer = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = StoryViewed
        fields = "__all__"
        read_only_fields = ['viewer']


class StoryReactionModelSerializer(serializers.ModelSerializer):
    user = CustomUserMyProfileSerializer(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = StoryReaction
        fields = "__all__"


class StoryModelSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    viewers = StoryViewedModelSerializer(read_only=True, many=True)
    reactions = StoryReactionModelSerializer(read_only=True, many=True)

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_at", "updated_at"]
        extra_kwargs = {
            'marked': {'required': False}
        }

    def validate_audience(self, value):
        if not value and value not in ["public", "contact", "marked"]:
            raise serializers.ValidationError("The audience field must not be empty and only accepts public, contact, and marked fields.")
        return value
