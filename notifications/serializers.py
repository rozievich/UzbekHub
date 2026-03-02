from rest_framework import serializers
from .models import Notification, FCMDevice
from accounts.models import CustomUser

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'profile_picture')

class NotificationSerializer(serializers.ModelSerializer):
    sender = UserShortSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type', 
            'title', 'body', 'data', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'notification_type', 'title', 'body', 'data', 'created_at']

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
