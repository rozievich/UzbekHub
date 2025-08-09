from rest_framework import serializers

from .models import Story


class StoryModelSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["is_active", "created_at", "updated_at"]
        extra_kwargs = {
            'marked': {'required': False}
        }
