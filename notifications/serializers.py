from rest_framework import serializers
from django.utils import timezone
from django.utils.timesince import timesince
from .models import Notification, FCMDevice
from accounts.models import CustomUser


NOTIFICATION_ICONS = {
    'like': '❤️',
    'comment': '💬',
    'message': '✉️',
    'system': '📢',
}

NOTIFICATION_COLORS = {
    'like': '#FF3B5C',
    'comment': '#4A90D9',
    'message': '#00C853',
    'system': '#FF9800',
}


class SenderSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'profile_picture')

    def get_full_name(self, obj):
        name = obj.get_full_name()
        return name if name else obj.username or obj.email


class NotificationSerializer(serializers.ModelSerializer):
    sender = SenderSerializer(read_only=True)
    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type',
            'title', 'body', 'data',
            'icon', 'color', 'time_ago',
            'is_read', 'created_at'
        ]
        read_only_fields = fields

    def get_icon(self, obj):
        return NOTIFICATION_ICONS.get(obj.notification_type, '🔔')

    def get_color(self, obj):
        return NOTIFICATION_COLORS.get(obj.notification_type, '#607D8B')

    def get_time_ago(self, obj):
        now = timezone.now()
        diff = now - obj.created_at
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Hozirgina"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} daqiqa oldin"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} soat oldin"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} kun oldin"
        elif seconds < 2592000:
            weeks = int(seconds // 604800)
            return f"{weeks} hafta oldin"
        else:
            months = int(seconds // 2592000)
            return f"{months} oy oldin"


class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['id', 'registration_token', 'device_type', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        # Token unikal bo'lishi kerak, mavjud bo'lsa yangilaymiz
        token = validated_data.get('registration_token')
        device, created = FCMDevice.objects.update_or_create(
            registration_token=token,
            defaults={
                'user': user,
                'device_type': validated_data.get('device_type', 'web')
            }
        )
        return device


class SystemNotificationSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Tanlangan userlar IDlari. Bo'sh bo'lsa hamma userga yuboriladi."
    )
