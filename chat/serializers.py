from rest_framework import serializers

from accounts.models import CustomUser
from .models import ChatRoom, RoomMember, Message, File, MessageStatus
from django.conf import settings


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    attachments = FileSerializer(many=True, read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Message
        fields = "__all__"

    def validate(self, attrs):
        text = attrs.get('text')
        if not text and not self.instance:
            raise serializers.ValidationError("Message must have either text or file!")
        return attrs


class RoomMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())

    class Meta:
        model = RoomMember
        fields = "__all__"


class ChatRoomSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True)
    room_members = RoomMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = "__all__"


class MessageStatusSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all())

    class Meta:
        model = MessageStatus
        fields = "__all__"
