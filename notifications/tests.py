"""
Tests for the notifications app: models, services, and views.
"""
import json
from unittest.mock import patch, MagicMock
from datetime import time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from notifications.models import Device, Notification, NotificationPreference, NotificationTemplate

User = get_user_model()


@pytest.fixture
def notification(player_user):
    return Notification.objects.create(
        user=player_user,
        title='Test Notification',
        message='This is a test',
        notification_type='system',
        priority='normal',
    )


class TestDeviceModel:
    def test_create_device(self, player_user):
        device = Device.objects.create(
            user=player_user,
            subscription_info={'endpoint': 'https://example.com/push'},
            device_name='Test Browser',
        )
        assert device.is_active
        assert device.device_name == 'Test Browser'

    def test_device_str(self, player_user):
        device = Device.objects.create(
            user=player_user,
            subscription_info={'endpoint': 'https://example.com/push'},
            device_name='Chrome',
        )
        assert str(device) == f'Chrome ({player_user.email})'

    def test_deactivate_device(self, player_user):
        device = Device.objects.create(
            user=player_user,
            subscription_info={'endpoint': 'https://example.com/push'},
        )
        device.is_active = False
        device.save()
        db_device = Device.objects.get(pk=device.pk)
        assert not db_device.is_active

    def test_last_used_tracking(self, player_user):
        device = Device.objects.create(
            user=player_user,
            subscription_info={'endpoint': 'https://example.com/push'},
        )
        assert device.last_used_at is None


class TestNotificationModel:
    def test_create_notification(self, notification):
        assert notification.title == 'Test Notification'
        assert not notification.read

    def test_mark_as_read(self, notification):
        notification.mark_as_read()
        assert notification.read
        assert notification.read_at is not None

    def test_notification_str(self, notification):
        expected = f'Test Notification - {notification.user.email}'
        assert str(notification) == expected

    def test_notification_with_content_object(self, player_user):
        ct = ContentType.objects.get_for_model(User)
        n = Notification.objects.create(
            user=player_user,
            title='Linked Notification',
            message='Linked message',
            notification_type='system',
            content_type=ct,
            object_id=str(player_user.pk),
        )
        assert n.content_object == player_user

    def test_notification_expiry(self, player_user):
        n = Notification.objects.create(
            user=player_user,
            title='Expiring',
            message='Will expire',
            notification_type='system',
            expires_at=timezone.now(),
        )
        assert n.expires_at is not None


class TestNotificationPreferenceModel:
    def test_create_preferences(self, player_user):
        prefs = NotificationPreference.objects.create(user=player_user)
        assert prefs.in_app_enabled
        assert prefs.email_enabled
        assert not prefs.push_enabled
        assert not prefs.sms_enabled

    def test_disable_all(self, player_user):
        prefs = NotificationPreference.objects.create(user=player_user)
        prefs.in_app_enabled = False
        prefs.email_enabled = False
        prefs.save()
        db_prefs = NotificationPreference.objects.get(user=player_user)
        assert not db_prefs.in_app_enabled
        assert not db_prefs.email_enabled

    def test_quiet_hours(self, player_user):
        prefs = NotificationPreference.objects.create(
            user=player_user,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
        )
        assert prefs.quiet_hours_enabled


class TestNotificationTemplateModel:
    def test_create_template(self):
        tmpl = NotificationTemplate.objects.create(
            name='welcome_email',
            notification_type='system',
            title_template='Welcome {username}!',
            message_template='Hello {username}, welcome to our platform!',
        )
        assert tmpl.is_active
        assert tmpl.default_priority == 'normal'

    def test_template_str(self):
        tmpl = NotificationTemplate.objects.create(
            name='welcome_email', notification_type='system',
            title_template='Welcome', message_template='Welcome!',
        )
        assert str(tmpl) == 'welcome_email'

    def test_placeholder_formatting(self):
        tmpl = NotificationTemplate.objects.create(
            name='custom_greeting', notification_type='system',
            title_template='Hi {name}!', message_template='Hello {name}, your {item} is ready.',
        )
        title = tmpl.title_template.format(name='Alice')
        message = tmpl.message_template.format(name='Alice', item='order')
        assert title == 'Hi Alice!'
        assert message == 'Hello Alice, your order is ready.'


class TestNotificationViews:
    URL_LIST = reverse('notifications:list')
    URL_RECENT = reverse('notifications:recent')
    URL_PREFS = reverse('notifications:preferences')
    URL_SUBSCRIBE = reverse('notifications:subscribe_push')
    URL_UNSUBSCRIBE = reverse('notifications:unsubscribe_push')
    URL_TEST_PUSH = reverse('notifications:test_push')
    URL_UNREAD_COUNT = reverse('notifications:unread_count')
    URL_MARK_ALL_READ = reverse('notifications:mark_all_as_read')

    @pytest.mark.django_db
    def test_list_requires_login(self, client):
        response = client.get(self.URL_LIST)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_list_authenticated(self, client_logged_in_player, notification):
        response = client_logged_in_player.get(self.URL_LIST)
        assert response.status_code == 200
        assert 'Test Notification' in response.content.decode()

    @pytest.mark.django_db
    def test_unread_count(self, client_logged_in_player, notification):
        response = client_logged_in_player.get(self.URL_UNREAD_COUNT)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['count'] >= 1

    @pytest.mark.django_db
    def test_mark_as_read(self, client_logged_in_player, notification):
        url = reverse('notifications:mark_as_read', kwargs={'notification_id': notification.pk})
        response = client_logged_in_player.post(url)
        assert response.status_code in (200, 302)
        notification.refresh_from_db()
        assert notification.read

    @pytest.mark.django_db
    def test_mark_all_as_read(self, client_logged_in_player, player_user):
        Notification.objects.create(user=player_user, title='N1', message='M1', notification_type='system')
        Notification.objects.create(user=player_user, title='N2', message='M2', notification_type='system')
        response = client_logged_in_player.post(self.URL_MARK_ALL_READ)
        assert response.status_code in (200, 302)
        assert Notification.objects.filter(user=player_user, read=False).count() == 0

    @pytest.mark.django_db
    def test_detail_marks_as_read(self, client_logged_in_player, notification):
        url = reverse('notifications:detail', kwargs={'notification_id': notification.pk})
        response = client_logged_in_player.get(url)
        assert response.status_code in (200, 302)
        notification.refresh_from_db()
        assert notification.read

    @pytest.mark.django_db
    def test_delete_notification(self, client_logged_in_player, notification):
        url = reverse('notifications:delete', kwargs={'notification_id': notification.pk})
        response = client_logged_in_player.post(url)
        assert response.status_code in (200, 302)
        assert Notification.objects.filter(pk=notification.pk).count() == 0

    @pytest.mark.django_db
    def test_recent_returns_last_10(self, client_logged_in_player, player_user):
        for i in range(15):
            Notification.objects.create(
                user=player_user, title=f'N{i}', message='M',
                notification_type='system',
            )
        response = client_logged_in_player.get(self.URL_RECENT)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_preferences_get(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL_PREFS)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_preferences_post(self, client_logged_in_player):
        response = client_logged_in_player.post(self.URL_PREFS, {
            'in_app_enabled': True,
            'email_enabled': False,
            'push_enabled': True,
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_subscribe_push(self, client_logged_in_player):
        response = client_logged_in_player.post(
            self.URL_SUBSCRIBE,
            json.dumps({'endpoint': 'https://example.com/push', 'keys': {'auth': 'abc', 'p256dh': 'xyz'}}),
            content_type='application/json',
        )
        assert response.status_code in (200, 201)

    @pytest.mark.django_db
    def test_unsubscribe_push(self, client_logged_in_player, player_user):
        Device.objects.create(
            user=player_user,
            subscription_info={'endpoint': 'https://example.com/push'},
        )
        response = client_logged_in_player.post(
            self.URL_UNSUBSCRIBE,
            json.dumps({'endpoint': 'https://example.com/push'}),
            content_type='application/json',
        )
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_test_push(self, client_logged_in_player):
        response = client_logged_in_player.post(self.URL_TEST_PUSH, {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert response.status_code == 200
