from rest_framework import serializers

from accounts.models import CustomUser
from accounts.serializers import CustomUserMyProfileSerializer
from .models import PrivateRoom, GroupRoom, GroupRoomMember, Message, File, MessageStatus


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


class GroupRoomMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    room = serializers.PrimaryKeyRelatedField(queryset=GroupRoom.objects.all())

    class Meta:
        model = GroupRoomMember
        fields = "__all__"
    


class MessageStatusSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all())

    class Meta:
        model = MessageStatus
        fields = "__all__"


# PrivateRoom model serializer
class PrivateRoomSerializer(serializers.ModelSerializer):
    user1 = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user2 = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())

    class Meta:
        model = PrivateRoom
        fields = "__all__"

    def validate(self, attrs):
        user1 = attrs.get('user1')
        user2 = attrs.get('user2')
        if user1 == user2:
            raise serializers.ValidationError("Cannot create a private room with yourself.")
        if PrivateRoom.objects.filter(user1=user1, user2=user2).exists() or \
           PrivateRoom.objects.filter(user1=user2, user2=user1).exists():
            raise serializers.ValidationError("Private room between these users already exists.")
        return attrs
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user1'] = CustomUserMyProfileSerializer(instance.user1).data
        data['user2'] = CustomUserMyProfileSerializer(instance.user2).data
        return data


# GroupRoom model serializer
class GroupRoomSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = GroupRoom
        fields = "__all__"
