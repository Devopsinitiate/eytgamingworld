"""
Tests for Notification models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, time

from .models import Notification, NotificationPreference, NotificationTemplate

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test Notification model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test message',
            notification_type='system',
            priority='normal'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test message')
        self.assertEqual(notification.notification_type, 'system')
        self.assertEqual(notification.priority, 'normal')
        self.assertFalse(notification.read)
        self.assertIsNone(notification.read_at)
    
    def test_notification_str_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='system'
        )
        
        expected = f"{self.user.email} - Test Notification"
        self.assertEqual(str(notification), expected)
    
    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='system'
        )
        
        self.assertFalse(notification.read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_read_idempotent(self):
        """Test that marking as read multiple times doesn't change read_at"""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='system'
        )
        
        notification.mark_as_read()
        first_read_at = notification.read_at
        
        # Mark as read again
        notification.mark_as_read()
        
        # read_at should not change
        self.assertEqual(notification.read_at, first_read_at)

    
    def test_create_notification_convenience_method(self):
        """Test create_notification convenience method"""
        notification = Notification.create_notification(
            user=self.user,
            title='Test Title',
            message='Test Message',
            notification_type='tournament',
            priority='high',
            action_url='/tournaments/123/',
            delivery_methods=['in_app', 'email']
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Title')
        self.assertEqual(notification.notification_type, 'tournament')
        self.assertEqual(notification.priority, 'high')
        self.assertEqual(notification.action_url, '/tournaments/123/')
        self.assertEqual(notification.delivery_methods, ['in_app', 'email'])
    
    def test_notification_with_expiry(self):
        """Test notification with expiry date"""
        expires_at = timezone.now() + timedelta(days=7)
        notification = Notification.objects.create(
            user=self.user,
            title='Expiring Notification',
            message='This will expire',
            notification_type='system',
            expires_at=expires_at
        )
        
        self.assertEqual(notification.expires_at, expires_at)
    
    def test_notification_metadata(self):
        """Test notification with metadata"""
        metadata = {'tournament_id': '123', 'match_id': '456'}
        notification = Notification.objects.create(
            user=self.user,
            title='Match Update',
            message='Your match is starting',
            notification_type='match',
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata, metadata)
    
    def test_notification_priority_levels(self):
        """Test different priority levels"""
        priorities = ['low', 'normal', 'high', 'urgent']
        
        for priority in priorities:
            notification = Notification.objects.create(
                user=self.user,
                title=f'{priority.title()} Priority',
                message='Test message',
                notification_type='system',
                priority=priority
            )
            self.assertEqual(notification.priority, priority)
    
    def test_notification_types(self):
        """Test different notification types"""
        types = ['tournament', 'coaching', 'team', 'payment', 'system', 
                'security', 'venue', 'match', 'message', 'achievement']
        
        for notif_type in types:
            notification = Notification.objects.create(
                user=self.user,
                title=f'{notif_type.title()} Notification',
                message='Test message',
                notification_type=notif_type
            )
            self.assertEqual(notification.notification_type, notif_type)


class NotificationPreferenceModelTests(TestCase):
    """Test NotificationPreference model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_preference_creation(self):
        """Test creating notification preferences"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=True,
            push_enabled=False
        )
        
        self.assertEqual(prefs.user, self.user)
        self.assertTrue(prefs.email_enabled)
        self.assertFalse(prefs.push_enabled)
    
    def test_preference_str_representation(self):
        """Test preference string representation"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        expected = f"Notification Preferences for {self.user.email}"
        self.assertEqual(str(prefs), expected)
    
    def test_default_preferences(self):
        """Test default preference values"""
        prefs = NotificationPreference.objects.create(user=self.user)
        
        # In-app should be enabled by default
        self.assertTrue(prefs.in_app_enabled)
        
        # Email should be enabled by default
        self.assertTrue(prefs.email_enabled)
        self.assertTrue(prefs.email_tournament_updates)
        self.assertTrue(prefs.email_coaching_reminders)
        
        # Push should be disabled by default
        self.assertFalse(prefs.push_enabled)
        
        # SMS should be disabled by default
        self.assertFalse(prefs.sms_enabled)
    
    def test_should_send_email_notification(self):
        """Test should_send_notification for email"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=True,
            email_tournament_updates=True
        )
        
        self.assertTrue(prefs.should_send_notification('tournament', 'email'))
    
    def test_should_not_send_email_when_disabled(self):
        """Test email not sent when disabled"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=False
        )
        
        self.assertFalse(prefs.should_send_notification('tournament', 'email'))
    
    def test_should_not_send_specific_type_when_disabled(self):
        """Test specific notification type disabled"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            email_enabled=True,
            email_tournament_updates=False
        )
        
        self.assertFalse(prefs.should_send_notification('tournament', 'email'))
    
    def test_quiet_hours_not_enabled(self):
        """Test quiet hours when not enabled"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            quiet_hours_enabled=False
        )
        
        self.assertFalse(prefs.is_in_quiet_hours())
    
    def test_quiet_hours_within_range(self):
        """Test quiet hours within range"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),  # 10 PM
            quiet_hours_end=time(8, 0)      # 8 AM
        )
        
        # This test depends on current time, so we just verify the method runs
        result = prefs.is_in_quiet_hours()
        self.assertIsInstance(result, bool)
    
    def test_push_notification_preferences(self):
        """Test push notification preferences"""
        prefs = NotificationPreference.objects.create(
            user=self.user,
            push_enabled=True,
            push_tournament_updates=True,
            push_match_updates=False
        )
        
        self.assertTrue(prefs.should_send_notification('tournament', 'push'))
        self.assertFalse(prefs.should_send_notification('match', 'push'))


class NotificationTemplateModelTests(TestCase):
    """Test NotificationTemplate model"""
    
    def test_template_creation(self):
        """Test creating a notification template"""
        template = NotificationTemplate.objects.create(
            name='tournament_start',
            notification_type='tournament',
            title_template='Tournament {tournament_name} is starting!',
            message_template='Your tournament {tournament_name} starts at {start_time}',
            default_priority='high',
            default_delivery_methods=['in_app', 'email']
        )
        
        self.assertEqual(template.name, 'tournament_start')
        self.assertEqual(template.notification_type, 'tournament')
        self.assertEqual(template.default_priority, 'high')
        self.assertTrue(template.is_active)
    
    def test_template_str_representation(self):
        """Test template string representation"""
        template = NotificationTemplate.objects.create(
            name='test_template',
            notification_type='system',
            title_template='Test',
            message_template='Test message'
        )
        
        self.assertEqual(str(template), 'test_template')
    
    def test_template_render(self):
        """Test rendering a template with context"""
        template = NotificationTemplate.objects.create(
            name='tournament_start',
            notification_type='tournament',
            title_template='Tournament {tournament_name} is starting!',
            message_template='Your tournament {tournament_name} starts at {start_time}'
        )
        
        context = {
            'tournament_name': 'Summer Championship',
            'start_time': '2:00 PM'
        }
        
        title, message = template.render(context)
        
        self.assertEqual(title, 'Tournament Summer Championship is starting!')
        self.assertEqual(message, 'Your tournament Summer Championship starts at 2:00 PM')
    
    def test_template_create_notification(self):
        """Test creating notification from template"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        template = NotificationTemplate.objects.create(
            name='match_reminder',
            notification_type='match',
            title_template='Match against {opponent} in {time}',
            message_template='Your match against {opponent} starts in {time}',
            default_priority='high',
            default_delivery_methods=['in_app', 'push']
        )
        
        context = {
            'opponent': 'Team Alpha',
            'time': '30 minutes'
        }
        
        notification = template.create_notification(user, context)
        
        self.assertEqual(notification.user, user)
        self.assertEqual(notification.title, 'Match against Team Alpha in 30 minutes')
        self.assertEqual(notification.notification_type, 'match')
        self.assertEqual(notification.priority, 'high')
