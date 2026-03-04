from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import CustomUser
from utils.pagination import StandardResultsSetPagination
from .models import Notification, FCMDevice
from .serializers import NotificationSerializer, FCMDeviceSerializer, SystemNotificationSerializer
from .utils import send_fcm_notification


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('sender')

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'notification marked as read'})

    @action(detail=False, methods=['post'])
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class FCMDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = FCMDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return FCMDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SystemNotificationView(APIView):
    """
    Admin uchun system notification yaratish API.
    POST: barcha yoki tanlangan userlarga notification yuboradi.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': "Sizda bu amalni bajarish uchun ruxsat yo'q."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = SystemNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data['title']
        body = serializer.validated_data['body']
        user_ids = serializer.validated_data.get('user_ids', [])

        if user_ids:
            recipients = CustomUser.objects.filter(id__in=user_ids, is_active=True)
        else:
            recipients = CustomUser.objects.filter(is_active=True)

        sent_count = 0
        for user in recipients:
            send_fcm_notification(
                user=user,
                title=title,
                body=body,
                notification_type='system',
                sender=request.user,
                data={'type': 'system'}
            )
            sent_count += 1

        return Response({
            'status': 'success',
            'sent_count': sent_count,
            'title': title,
        }, status=status.HTTP_201_CREATED)
