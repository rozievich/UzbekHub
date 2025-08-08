from rest_framework import serializers

from .models import Story


class StoryModelSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(serializers.CurrentUserDefault())

    class Meta:
        model = Story
        fields = "__all__"
        read_only_fields = ["story_id", "is_active", "created_at", "updated_at"]
    
