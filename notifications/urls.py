from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, FCMDeviceViewSet, SystemNotificationView

router = DefaultRouter()
router.register(r'devices', FCMDeviceViewSet, basename='fcmdevice')
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('system/', SystemNotificationView.as_view(), name='system-notification'),
    path('', include(router.urls)),
]
