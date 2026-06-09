"""
Web Push notification service for EYTGaming.
Uses the Web Push API standard to deliver notifications to browsers.
"""
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_web_push_notification(subscription_info, title, body, url='', notification_id=''):
    """
    Send a push notification to a single device via the Web Push API.

    Args:
        subscription_info: Dict with 'endpoint', 'keys' (p256dh, auth) from browser
        title: Notification title
        body: Notification body text
        url: URL to open when notification is clicked
        notification_id: UUID string for the notification

    Returns:
        bool: True if sent successfully, False otherwise
    """
    vapid_private_key = settings.VAPID_PRIVATE_KEY
    vapid_claim_email = settings.VAPID_CLAIM_EMAIL

    if not vapid_private_key:
        logger.warning('VAPID_PRIVATE_KEY not configured. Push notification not sent.')
        return False

    try:
        from pywebpush import webpush, WebPushException

        payload = json.dumps({
            'title': title,
            'body': body,
            'icon': '/static/images/EYTLOGO.jpg',
            'badge': '/static/images/favicon.ico',
            'data': {
                'url': url,
                'notification_id': notification_id,
            },
        })

        response = webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={
                'sub': f'mailto:{vapid_claim_email}',
            },
        )

        if response and response.status_code == 201:
            logger.info(f'Push notification sent to device (notif_id={notification_id})')
            return True

        logger.warning(
            f'Push notification returned {response.status_code if response else "None"} '
            f'(notif_id={notification_id})'
        )
        return False

    except WebPushException as e:
        if e.response and e.response.status_code == 410:
            logger.info(f'Push subscription expired, device should be deactivated (notif_id={notification_id})')
        else:
            logger.error(f'Web push failed: {e} (notif_id={notification_id})')
        return False
    except Exception as e:
        logger.error(f'Unexpected error sending push notification: {e}')
        return False
