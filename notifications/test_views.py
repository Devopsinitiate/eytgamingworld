"""
Tests for Notification views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import time
import json

from .models import Notification, NotificationPreference

User = get_user_model()


class NotificationListViewTests(TestCase):
    """Test notification list view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_notification_list_requires_login(self):
        """Test that notification list requires login"""
        self.client.logout()
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_notification_list_renders(self):
        """Test notification list page renders"""
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/list.html')
    
    def test_notification_list_shows_user_notifications(self):
        """Test list shows only user's notifications"""
        # Create notification for current user
        notif1 = Notification.objects.create(
            user=self.user,
            title='User Notification',
            message='Test message',
            notification_type='system'
        )
        
        # Create notification for another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        notif2 = Notification.objects.create(
            user=other_user,
            title='Other User Notification',
            message='Other message',
            notification_type='system'
        )
        
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Notification')
        self.assertNotContains(response, 'Other User Notification')
    
    def test_notification_list_filter_unread(self):
        """Test filtering by unread notifications"""
        Notification.objects.create(
            user=self.user,
            title='Unread Notification',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Read Notification',
            message='Test',
            notification_type='system',
            read=True
        )
        
        response = self.client.get(reverse('notifications:list') + '?filter=unread')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unread Notification')
    
    def test_notification_list_filter_by_type(self):
        """Test filtering by notification type"""
        Notification.objects.create(
            user=self.user,
            title='Tournament Notification',
            message='Test',
            notification_type='tournament'
        )
        Notification.objects.create(
            user=self.user,
            title='Team Notification',
            message='Test',
            notification_type='team'
        )
        
        response = self.client.get(reverse('notifications:list') + '?type=tournament')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tournament Notification')
    
    def test_notification_list_unread_count(self):
        """Test unread count in context"""
        Notification.objects.create(
            user=self.user,
            title='Unread 1',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Unread 2',
            message='Test',
            notification_type='system',
            read=False
        )
        
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unread_count'], 2)


class NotificationDetailViewTests(TestCase):
    """Test notification detail view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_notification_detail_requires_login(self):
        """Test that notification detail requires login"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        self.client.logout()
        response = self.client.get(reverse('notifications:detail', args=[notification.id]))
        self.assertEqual(response.status_code, 302)
    
    def test_notification_detail_marks_as_read(self):
        """Test that viewing detail marks notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='system',
            read=False
        )
        
        self.assertFalse(notification.read)
        
        response = self.client.get(reverse('notifications:detail', args=[notification.id]))
        
        notification.refresh_from_db()
        self.assertTrue(notification.read)
        self.assertIsNotNone(notification.read_at)
    
    def test_notification_detail_redirects_with_action_url(self):
        """Test redirect to action URL if provided"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='tournament',
            action_url='/tournaments/123/'
        )
        
        response = self.client.get(reverse('notifications:detail', args=[notification.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/tournaments/123/')
    
    def test_notification_detail_only_shows_own_notification(self):
        """Test user can only view their own notifications"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        notification = Notification.objects.create(
            user=other_user,
            title='Other User Notification',
            message='Test',
            notification_type='system'
        )
        
        response = self.client.get(reverse('notifications:detail', args=[notification.id]))
        self.assertEqual(response.status_code, 404)


class MarkAsReadViewTests(TestCase):
    """Test mark as read endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_mark_as_read_requires_post(self):
        """Test mark as read requires POST"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        response = self.client.get(reverse('notifications:mark_as_read', args=[notification.id]))
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_mark_as_read_success(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='system',
            read=False
        )
        
        response = self.client.post(reverse('notifications:mark_as_read', args=[notification.id]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        notification.refresh_from_db()
        self.assertTrue(notification.read)
    
    def test_mark_as_read_only_own_notification(self):
        """Test can only mark own notifications as read"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        notification = Notification.objects.create(
            user=other_user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        response = self.client.post(reverse('notifications:mark_as_read', args=[notification.id]))
        self.assertEqual(response.status_code, 404)


class MarkAllAsReadViewTests(TestCase):
    """Test mark all as read endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_mark_all_as_read_requires_post(self):
        """Test mark all as read requires POST"""
        response = self.client.get(reverse('notifications:mark_all_as_read'))
        self.assertEqual(response.status_code, 405)
    
    def test_mark_all_as_read_success(self):
        """Test marking all notifications as read"""
        Notification.objects.create(
            user=self.user,
            title='Unread 1',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Unread 2',
            message='Test',
            notification_type='system',
            read=False
        )
        
        response = self.client.post(reverse('notifications:mark_all_as_read'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify all are marked as read
        unread_count = Notification.objects.filter(user=self.user, read=False).count()
        self.assertEqual(unread_count, 0)
    
    def test_mark_all_as_read_only_user_notifications(self):
        """Test only marks current user's notifications"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_notif = Notification.objects.create(
            user=other_user,
            title='Other User',
            message='Test',
            notification_type='system',
            read=False
        )
        
        response = self.client.post(reverse('notifications:mark_all_as_read'))
        self.assertEqual(response.status_code, 200)
        
        # Other user's notification should still be unread
        other_notif.refresh_from_db()
        self.assertFalse(other_notif.read)


class DeleteNotificationViewTests(TestCase):
    """Test delete notification endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_delete_notification_requires_post(self):
        """Test delete requires POST"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        response = self.client.get(reverse('notifications:delete', args=[notification.id]))
        self.assertEqual(response.status_code, 405)
    
    def test_delete_notification_success(self):
        """Test deleting a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        notification_id = notification.id
        
        response = self.client.post(reverse('notifications:delete', args=[notification_id]))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify notification is deleted
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())
    
    def test_delete_only_own_notification(self):
        """Test can only delete own notifications"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        notification = Notification.objects.create(
            user=other_user,
            title='Test',
            message='Test',
            notification_type='system'
        )
        
        response = self.client.post(reverse('notifications:delete', args=[notification.id]))
        self.assertEqual(response.status_code, 404)
        
        # Notification should still exist
        self.assertTrue(Notification.objects.filter(id=notification.id).exists())


class UnreadCountViewTests(TestCase):
    """Test unread count endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_unread_count_requires_login(self):
        """Test unread count requires login"""
        self.client.logout()
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 302)
    
    def test_unread_count_returns_correct_count(self):
        """Test unread count returns correct number"""
        Notification.objects.create(
            user=self.user,
            title='Unread 1',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Unread 2',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Read',
            message='Test',
            notification_type='system',
            read=True
        )
        
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['count'], 2)
    
    def test_unread_count_zero_when_none(self):
        """Test unread count is zero when no unread notifications"""
        response = self.client.get(reverse('notifications:unread_count'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)



class NotificationPreferencesViewTests(TestCase):
    """Test notification preferences view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_preferences_requires_login(self):
        """Test preferences page requires login"""
        self.client.logout()
        response = self.client.get(reverse('notifications:preferences'))
        self.assertEqual(response.status_code, 302)
    
    def test_preferences_get_renders(self):
        """Test preferences page renders"""
        response = self.client.get(reverse('notifications:preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/preferences.html')
    
    def test_preferences_creates_if_not_exists(self):
        """Test preferences are created if they don't exist"""
        self.assertFalse(NotificationPreference.objects.filter(user=self.user).exists())
        
        response = self.client.get(reverse('notifications:preferences'))
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(NotificationPreference.objects.filter(user=self.user).exists())
    
    def test_preferences_update_email_settings(self):
        """Test updating email preferences"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        response = self.client.post(reverse('notifications:preferences'), {
            'email_enabled': 'on',
            'email_tournament_updates': 'on',
            'email_team_activity': 'on',
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        prefs.refresh_from_db()
        self.assertTrue(prefs.email_enabled)
        self.assertTrue(prefs.email_tournament_updates)
        self.assertTrue(prefs.email_team_activity)
    
    def test_preferences_update_push_settings(self):
        """Test updating push preferences"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        response = self.client.post(reverse('notifications:preferences'), {
            'push_enabled': 'on',
            'push_tournament_updates': 'on',
        })
        
        self.assertEqual(response.status_code, 200)
        
        prefs.refresh_from_db()
        self.assertTrue(prefs.push_enabled)
        self.assertTrue(prefs.push_tournament_updates)
    
    def test_preferences_update_quiet_hours(self):
        """Test updating quiet hours"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        response = self.client.post(reverse('notifications:preferences'), {
            'quiet_hours_enabled': 'on',
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '08:00',
        })
        
        self.assertEqual(response.status_code, 200)
        
        prefs.refresh_from_db()
        self.assertTrue(prefs.quiet_hours_enabled)
        self.assertEqual(prefs.quiet_hours_start, time(22, 0))
        self.assertEqual(prefs.quiet_hours_end, time(8, 0))
    
    def test_preferences_update_discord_webhook(self):
        """Test updating Discord webhook URL"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        response = self.client.post(reverse('notifications:preferences'), {
            'discord_enabled': 'on',
            'discord_webhook_url': 'https://discord.com/api/webhooks/123/abc',
        })
        
        self.assertEqual(response.status_code, 200)
        
        prefs.refresh_from_db()
        self.assertTrue(prefs.discord_enabled)
        self.assertEqual(prefs.discord_webhook_url, 'https://discord.com/api/webhooks/123/abc')
    
    def test_preferences_disable_all(self):
        """Test disabling all preferences"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=True,
            push_enabled=True
        )
        
        # POST with no checkboxes (all disabled)
        response = self.client.post(reverse('notifications:preferences'), {})
        
        self.assertEqual(response.status_code, 200)
        
        prefs.refresh_from_db()
        self.assertFalse(prefs.email_enabled)
        self.assertFalse(prefs.push_enabled)


class RecentNotificationsViewTests(TestCase):
    """Test recent notifications endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_recent_notifications_requires_login(self):
        """Test recent notifications requires login"""
        self.client.logout()
        response = self.client.get(reverse('notifications:recent'))
        self.assertEqual(response.status_code, 302)
    
    def test_recent_notifications_ajax_returns_json(self):
        """Test AJAX request returns JSON"""
        Notification.objects.create(
            user=self.user,
            title='Recent Notification',
            message='Test message',
            notification_type='system'
        )
        
        response = self.client.get(
            reverse('notifications:recent'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('notifications', data)
        self.assertIn('unread_count', data)
        self.assertEqual(len(data['notifications']), 1)
    
    def test_recent_notifications_limits_to_10(self):
        """Test recent notifications limits to 10 items"""
        # Create 15 notifications
        for i in range(15):
            Notification.objects.create(
                user=self.user,
                title=f'Notification {i}',
                message='Test',
                notification_type='system'
            )
        
        response = self.client.get(
            reverse('notifications:recent'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['notifications']), 10)
    
    def test_recent_notifications_html_renders(self):
        """Test non-AJAX request renders HTML"""
        response = self.client.get(reverse('notifications:recent'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notifications/recent.html')
    
    def test_recent_notifications_includes_unread_count(self):
        """Test response includes unread count"""
        Notification.objects.create(
            user=self.user,
            title='Unread',
            message='Test',
            notification_type='system',
            read=False
        )
        Notification.objects.create(
            user=self.user,
            title='Read',
            message='Test',
            notification_type='system',
            read=True
        )
        
        response = self.client.get(
            reverse('notifications:recent'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['unread_count'], 1)
    
    def test_recent_notifications_json_structure(self):
        """Test JSON response has correct structure"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='tournament',
            priority='high',
            action_url='/tournaments/123/'
        )
        
        response = self.client.get(
            reverse('notifications:recent'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        notif_data = data['notifications'][0]
        
        self.assertEqual(notif_data['title'], 'Test Notification')
        self.assertEqual(notif_data['message'], 'Test message')
        self.assertEqual(notif_data['type'], 'tournament')
        self.assertEqual(notif_data['priority'], 'high')
        self.assertEqual(notif_data['action_url'], '/tournaments/123/')
        self.assertIn('id', notif_data)
        self.assertIn('created_at', notif_data)
        self.assertIn('read', notif_data)
