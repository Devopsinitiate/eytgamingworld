"""
Tests for dashboard settings views.

This module tests the settings views including profile, privacy,
notifications, security, connected accounts, and account deletion.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from notifications.models import NotificationPreference
from security.models import AuditLog

User = get_user_model()


class SettingsProfileViewTests(TestCase):
    """Test settings profile view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_settings_profile_requires_login(self):
        """Test settings profile page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:settings_profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_profile_get_renders(self):
        """Test settings profile page renders"""
        response = self.client.get(reverse('dashboard:settings_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/profile.html')
    
    def test_settings_profile_update(self):
        """Test updating profile settings"""
        response = self.client.post(reverse('dashboard:settings_profile'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'display_name': 'JohnD',
            'bio': 'Test bio',
        })
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')


class SettingsPrivacyViewTests(TestCase):
    """Test settings privacy view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_settings_privacy_requires_login(self):
        """Test settings privacy page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:settings_privacy'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_privacy_get_renders(self):
        """Test settings privacy page renders"""
        response = self.client.get(reverse('dashboard:settings_privacy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/privacy.html')
    
    def test_settings_privacy_update(self):
        """Test updating privacy settings"""
        response = self.client.post(reverse('dashboard:settings_privacy'), {
            'online_status_visible': 'on',
            'activity_visible': '',  # Unchecked
            'statistics_visible': 'on',
        })
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.online_status_visible)
        self.assertFalse(self.user.activity_visible)
        self.assertTrue(self.user.statistics_visible)


class SettingsNotificationsViewTests(TestCase):
    """Test settings notifications view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_settings_notifications_requires_login(self):
        """Test settings notifications page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:settings_notifications'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_notifications_get_renders(self):
        """Test settings notifications page renders"""
        response = self.client.get(reverse('dashboard:settings_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/notifications.html')
    
    def test_settings_notifications_creates_preferences(self):
        """Test notification preferences are created if they don't exist"""
        self.assertFalse(NotificationPreference.objects.filter(user=self.user).exists())
        
        response = self.client.get(reverse('dashboard:settings_notifications'))
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue(NotificationPreference.objects.filter(user=self.user).exists())
    
    def test_settings_notifications_update(self):
        """Test updating notification preferences"""
        response = self.client.post(reverse('dashboard:settings_notifications'), {
            'in_app_enabled': 'on',
            'email_enabled': 'on',
            'email_tournament_updates': 'on',
        })
        
        prefs = NotificationPreference.objects.get(user=self.user)
        self.assertTrue(prefs.in_app_enabled)
        self.assertTrue(prefs.email_enabled)
        self.assertTrue(prefs.email_tournament_updates)


class SettingsSecurityViewTests(TestCase):
    """Test settings security view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_settings_security_requires_login(self):
        """Test settings security page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:settings_security'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_security_get_renders(self):
        """Test settings security page renders"""
        response = self.client.get(reverse('dashboard:settings_security'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/security.html')
    
    def test_settings_security_password_change(self):
        """Test changing password"""
        response = self.client.post(reverse('dashboard:settings_security'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass456!',
            'new_password2': 'newpass456!',
        })
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456!'))
    
    def test_settings_security_password_change_requires_current(self):
        """Test password change requires current password"""
        response = self.client.post(reverse('dashboard:settings_security'), {
            'old_password': 'wrongpass',
            'new_password1': 'newpass456!',
            'new_password2': 'newpass456!',
        })
        
        self.user.refresh_from_db()
        # Password should not have changed
        self.assertTrue(self.user.check_password('testpass123'))


class SettingsConnectedAccountsViewTests(TestCase):
    """Test settings connected accounts view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_settings_connected_accounts_requires_login(self):
        """Test settings connected accounts page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:settings_accounts'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_connected_accounts_get_renders(self):
        """Test settings connected accounts page renders"""
        response = self.client.get(reverse('dashboard:settings_accounts'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/connected_accounts.html')
    
    def test_settings_connected_accounts_shows_connections(self):
        """Test connected accounts displays connection status"""
        self.user.steam_id = '12345'
        self.user.discord_username = 'testuser#1234'
        self.user.save()
        
        response = self.client.get(reverse('dashboard:settings_accounts'))
        self.assertEqual(response.status_code, 200)
        
        # Check that connected accounts are in context
        self.assertIn('connected_accounts', response.context)
        self.assertTrue(response.context['connected_accounts']['steam']['connected'])
        self.assertTrue(response.context['connected_accounts']['discord']['connected'])
        self.assertFalse(response.context['connected_accounts']['twitch']['connected'])


class AccountDeleteViewTests(TestCase):
    """Test account deletion view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.force_login(self.user)
    
    def test_account_delete_requires_login(self):
        """Test account delete page requires login"""
        self.client.logout()
        response = self.client.get(reverse('dashboard:account_delete'))
        self.assertEqual(response.status_code, 302)
    
    def test_account_delete_get_renders(self):
        """Test account delete page renders"""
        response = self.client.get(reverse('dashboard:account_delete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/settings/delete_account.html')
    
    def test_account_delete_requires_password(self):
        """Test account deletion requires password"""
        response = self.client.post(reverse('dashboard:account_delete'), {
            'password': 'wrongpass',
            'confirm_text': 'DELETE',
        })
        
        self.user.refresh_from_db()
        # User should still be active
        self.assertTrue(self.user.is_active)
    
    def test_account_delete_requires_confirmation_text(self):
        """Test account deletion requires confirmation text"""
        response = self.client.post(reverse('dashboard:account_delete'), {
            'password': 'testpass123',
            'confirm_text': 'delete',  # Wrong case
        })
        
        self.user.refresh_from_db()
        # User should still be active
        self.assertTrue(self.user.is_active)
    
    def test_account_delete_anonymizes_data(self):
        """Test account deletion anonymizes user data"""
        user_id = self.user.id
        
        response = self.client.post(reverse('dashboard:account_delete'), {
            'password': 'testpass123',
            'confirm_text': 'DELETE',
        })
        
        # Refresh user from database
        user = User.objects.get(id=user_id)
        
        # Check that data is anonymized
        self.assertEqual(user.first_name, '[DELETED]')
        self.assertEqual(user.last_name, '[DELETED]')
        self.assertEqual(user.display_name, '[DELETED USER]')
        self.assertIn('deleted_', user.email)
        self.assertFalse(user.is_active)
    
    def test_account_delete_creates_audit_log(self):
        """Test account deletion creates audit log entry"""
        initial_count = AuditLog.objects.count()
        
        response = self.client.post(reverse('dashboard:account_delete'), {
            'password': 'testpass123',
            'confirm_text': 'DELETE',
        })
        
        # Check that audit log was created
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        # Check audit log details
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'delete')
        self.assertEqual(log.model_name, 'User')
        self.assertEqual(log.severity, 'high')
