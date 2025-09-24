from rest_framework import serializers

from accounts.models import CustomUser
from .models import ChatRoom, RoomMember, Message, File, MessageStatus, MessageAction
from .validators import validate_user_storage


# MessageAction serializer
class MessageActionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all())

    class Meta:
        model = MessageAction
        fields = "__all__"


# MessageStatus serializer
class MessageStatusSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    message = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all())

    class Meta:
        model = MessageStatus
        fields = "__all__"


# File serializer
class FileSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = File
        fields = "__all__"

    def validate_file(self, value):
        user = self.context["request"].user
        validate_user_storage(user, value)
        return value


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    attachments = FileSerializer(many=True, read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), required=False, allow_null=True)
    statuses = MessageStatusSerializer(many=True, read_only=True)
    actions = MessageActionSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = "__all__"

    def validate(self, attrs):
        text = attrs.get('text')
        if not text and not self.instance:
            raise serializers.ValidationError("Message must have either text or file!")
        return attrs


# RoomMember serializer
class RoomMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all(), write_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = RoomMember
        fields = ["id", "room", "user", "role", "joined_at"]
        read_only_fields = ["id", "role", "joined_at"]

    def validate(self, attrs):
        room = attrs.get("room")
        user = attrs.get("user")

        if RoomMember.objects.filter(room=room, user=user).exists():
            raise serializers.ValidationError("This user already exists in this room.")

        if room.room_type == ChatRoom.PRIVATE:
            count = RoomMember.objects.filter(room=room).count()
            if count >= 2:
                raise serializers.ValidationError("There can only be 2 members in a private chat.")

        return attrs


class ChatRoomSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, write_only=True, required=False)
    room_members = RoomMemberSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = "__all__"

    def validate(self, attrs):
        request_user = self.context['request'].user
        members = attrs.get('members', [])
        room_type = attrs.get('room_type')
        username = attrs.get('username')
        name = attrs.get('name')
        description = attrs.get('description')

        if not room_type:
            raise serializers.ValidationError("Room type required.")

        if request_user not in members:
            members.append(request_user)

        if len(members) != len(set(members)):
            raise serializers.ValidationError("Members must be unique.")

        if room_type == ChatRoom.PRIVATE:
            if len(members) != 2:
                raise serializers.ValidationError("Private rooms must have exactly 2 members.")

            if username or name or description:
                raise serializers.ValidationError("Private chats do not have username, name, or description fields.")
            
            qs = ChatRoom.objects.filter(room_type=ChatRoom.PRIVATE)
            for member in members:
                qs = qs.filter(members=member)
            if qs.exists():
                raise serializers.ValidationError("A private room with these members already exists.")
            
        if room_type == ChatRoom.GROUP:
            if not username or not name:
                raise serializers.ValidationError("Username and name fields are mandatory in group chats")

        attrs['members'] = members
        return attrs

    def create(self, validated_data):
        members = validated_data.pop('members', [])
        request_user = self.context['request'].user

        room = ChatRoom.objects.create(**validated_data)

        if room.room_type == ChatRoom.PRIVATE:
            for user in members:
                RoomMember.objects.create(room=room, user=user, role=RoomMember.MEMBER)

        elif room.room_type == ChatRoom.GROUP:
            for user in members:
                role = RoomMember.OWNER if user == request_user else RoomMember.MEMBER
                RoomMember.objects.create(room=room, user=user, role=role)

        return room
