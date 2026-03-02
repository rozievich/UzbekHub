import os
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from .models import FCMDevice, Notification

logger = logging.getLogger(__name__)

# Firebase initialization
firebase_creds_path = os.path.join(settings.BASE_DIR, 'config', 'ws-notification-4dcca-firebase-adminsdk-fbsvc-9b52b22c40.json')

def initialize_firebase():
    if not firebase_admin._apps:
        if os.path.exists(firebase_creds_path):
            try:
                creds = credentials.Certificate(firebase_creds_path)
                firebase_admin.initialize_app(creds)
                logger.info("Firebase initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Firebase: {e}")
        else:
            logger.warning(f"Firebase service account file not found at {firebase_creds_path}. FCM will not work.")

# Initialize at module level
initialize_firebase()

def send_fcm_notification(user, title, body, notification_type, sender=None, data=None):
    """
    Sends a push notification to all devices registered for a user and saves to Notification history.
    """
    # 1. Save to database history
    Notification.objects.create(
        recipient=user,
        sender=sender,
        notification_type=notification_type,
        title=title,
        body=body,
        data=data or {}
    )

    # 2. Check if Firebase is initialized
    if not firebase_admin._apps:
        logger.warning("Firebase not initialized. Skipping push notification.")
        return

    # 3. Get devices
    devices = FCMDevice.objects.filter(user=user)
    if not devices.exists():
        return

    tokens = list(devices.values_list('registration_token', flat=True))
    
    # 4. Prepare message
    message_data = {
        'type': notification_type,
    }
    if data:
        for k, v in data.items():
            message_data[k] = str(v)

    # 5. Send multicast message
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=message_data,
        tokens=tokens,
    )

    try:
        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent {response.success_count} notifications for user {user.id}")
        
        # Cleanup invalid tokens
        if response.failure_count > 0:
            invalid_tokens = []
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    # Token no longer valid
                    invalid_tokens.append(tokens[idx])
            
            if invalid_tokens:
                FCMDevice.objects.filter(registration_token__in=invalid_tokens).delete()
                logger.info(f"Deleted {len(invalid_tokens)} invalid tokens")
                
    except Exception as e:
        logger.error(f"Error sending multicast message: {e}")
