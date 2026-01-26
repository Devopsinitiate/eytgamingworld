"""
Tests for user report functionality.

This module tests the user report view and form validation.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from dashboard.models import UserReport
from dashboard.forms import UserReportForm

User = get_user_model()


class UserReportViewTest(TestCase):
    """Test user report view functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users with proper password hashing
        self.reporter = User.objects.create_user(
            username='reporter',
            email='reporter@test.com',
            password='testpass123',
            first_name='Reporter',
            last_name='User'
        )
        self.reporter.is_verified = True
        self.reporter.save()
        
        self.reported_user = User.objects.create_user(
            username='reported',
            email='reported@test.com',
            password='testpass123',
            first_name='Reported',
            last_name='User'
        )
        self.reported_user.is_verified = True
        self.reported_user.save()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.is_verified = True
        self.admin_user.save()
    
    def test_user_report_view_requires_login(self):
        """Test that user report view requires authentication"""
        url = reverse('dashboard:user_report', kwargs={'username': self.reported_user.username})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_user_report_view_get(self):
        """Test GET request to user report view"""
        # Force login the user
        self.client.force_login(self.reporter)
        
        url = reverse('dashboard:user_report', kwargs={'username': self.reported_user.username})
        response = self.client.get(url, follow=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/user_report.html')
        self.assertIn('report_form', response.context)
        self.assertIn('reported_user', response.context)
        self.assertEqual(response.context['reported_user'], self.reported_user)
    
    def test_user_cannot_report_themselves(self):
        """Test that users cannot report themselves"""
        # Force login the user
        self.client.force_login(self.reporter)
        
        url = reverse('dashboard:user_report', kwargs={'username': self.reporter.username})
        response = self.client.get(url, follow=True)
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 200)  # After following redirect
        messages = [str(m) for m in response.context['messages']]
        self.assertTrue(any('cannot report yourself' in m.lower() for m in messages))
    
    def test_user_report_submission_valid(self):
        """Test valid user report submission"""
        # Force login the user
        self.client.force_login(self.reporter)
        
        url = reverse('dashboard:user_report', kwargs={'username': self.reported_user.username})
        
        data = {
            'category': 'harassment',
            'description': 'This user has been harassing me with inappropriate messages.'
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Should redirect to profile view
        self.assertEqual(response.status_code, 200)  # After following redirect
        
        # Check that report was created
        report = UserReport.objects.filter(
            reporter=self.reporter,
            reported_user=self.reported_user
        ).first()
        
        self.assertIsNotNone(report)
        self.assertEqual(report.category, 'harassment')
        self.assertEqual(report.status, 'pending')
        self.assertIn('harassing', report.description)
    
    def test_user_report_submission_invalid_empty_description(self):
        """Test user report submission with empty description"""
        # Force login the user
        self.client.force_login(self.reporter)
        
        url = reverse('dashboard:user_report', kwargs={'username': self.reported_user.username})
        
        data = {
            'category': 'spam',
            'description': ''
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Should not redirect (form invalid) - stays on same page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/user_report.html')
        
        # Check that no report was created
        report_count = UserReport.objects.filter(
            reporter=self.reporter,
            reported_user=self.reported_user
        ).count()
        
        self.assertEqual(report_count, 0)
    
    def test_user_report_404_for_nonexistent_user(self):
        """Test that reporting nonexistent user returns 404"""
        # Force login the user
        self.client.force_login(self.reporter)
        
        url = reverse('dashboard:user_report', kwargs={'username': 'nonexistent'})
        response = self.client.get(url, follow=True)
        
        # get_object_or_404 should raise 404 before any redirect
        self.assertEqual(response.status_code, 404)


class UserReportFormTest(TestCase):
    """Test user report form validation"""
    
    def test_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'category': 'harassment',
            'description': 'This is a valid description of the issue.'
        }
        form = UserReportForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_empty_description(self):
        """Test form with empty description"""
        form_data = {
            'category': 'spam',
            'description': ''
        }
        form = UserReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)
    
    def test_form_whitespace_only_description(self):
        """Test form with whitespace-only description"""
        form_data = {
            'category': 'spam',
            'description': '   '
        }
        form = UserReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)
    
    def test_form_description_too_long(self):
        """Test form with description exceeding max length"""
        form_data = {
            'category': 'other',
            'description': 'x' * 1001  # Exceeds 1000 character limit
        }
        form = UserReportForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)
    
    def test_form_valid_categories(self):
        """Test form accepts all valid categories"""
        valid_categories = [
            'inappropriate_content',
            'harassment',
            'spam',
            'cheating',
            'other'
        ]
        
        for category in valid_categories:
            form_data = {
                'category': category,
                'description': 'Valid description for testing.'
            }
            form = UserReportForm(data=form_data)
            self.assertTrue(form.is_valid(), f"Category {category} should be valid")
