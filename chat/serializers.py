import re
from rest_framework.serializers import ModelSerializer, HiddenField, \
    CurrentUserDefault, PrimaryKeyRelatedField, StringRelatedField
from rest_framework.exceptions import ValidationError

from .models import ChatMessage, ChatGroup, GroupMessage
from .utils import decrypt_message_and_file
from accounts.models import CustomUser

class ChatMessageModelSerializer(ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"

    def validate(self, attrs):
        message = attrs.get('message')
        file = attrs.get('file')

        if not message and not file:
            raise ValidationError("Sending a message or file is mandatory!")
        return attrs

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['message'] = decrypt_message_and_file(representation['message'])
        return representation


class ChatGroupModelSerializer(ModelSerializer):
    owner = HiddenField(default=CurrentUserDefault())
    members = PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True)

    class Meta:
        model = ChatGroup
        fields = "id", "name", "username", "owner", "created_at", "members"

    def validate_username(self, username):
        if not re.match(r"^[a-z0-9_]+$", username) or not (5 <= len(username) <= 32):
            raise ValidationError({"message": "The username must be at least 5 characters and at most 32 characters long and can contain letters, numbers, and _."})
        return username


class ChatGroupMessageModelSerializer(ModelSerializer):
    is_delivery = StringRelatedField(many=True)

    class Meta:
        model = GroupMessage
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['message'] = decrypt_message_and_file(representation['message'])
        return representation
