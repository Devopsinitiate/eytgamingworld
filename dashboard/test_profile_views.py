"""
Tests for profile views.

This module tests the profile viewing, editing, and export functionality.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import json

User = get_user_model()


class ProfileViewTests(TestCase):
    """Tests for profile_view"""
    
    def setUp(self):
        """Set up test users"""
        self.client = Client()
        
        # Create test users
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            username='user1',
            password='testpass123'
        )
        self.user1.display_name = 'User One'
        self.user1.bio = 'Test bio for user 1'
        self.user1.statistics_visible = True
        self.user1.activity_visible = True
        self.user1.save()
        
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            username='user2',
            password='testpass123'
        )
        self.user2.display_name = 'User Two'
        self.user2.statistics_visible = False  # Private profile
        self.user2.activity_visible = False
        self.user2.save()
    
    def test_view_own_profile(self):
        """Test viewing own profile"""
        self.client.login(email='user1@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_view', kwargs={'username': 'user1'}))
        
        assert response.status_code == 200
        assert response.context['is_own_profile'] == True
        assert response.context['profile_owner'] == self.user1
        assert response.context['can_view_statistics'] == True
        assert response.context['can_view_activity'] == True
    
    def test_view_public_profile(self):
        """Test viewing another user's public profile"""
        self.client.login(email='user2@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_view', kwargs={'username': 'user1'}))
        
        assert response.status_code == 200
        assert response.context['is_own_profile'] == False
        assert response.context['profile_owner'] == self.user1
        assert response.context['can_view_statistics'] == True
        assert response.context['can_view_activity'] == True
    
    def test_view_private_profile(self):
        """Test viewing another user's private profile"""
        self.client.login(email='user1@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_view', kwargs={'username': 'user2'}))
        
        assert response.status_code == 200
        assert response.context['is_own_profile'] == False
        assert response.context['profile_owner'] == self.user2
        # Private profile should not show statistics/activity to non-friends
        assert response.context['can_view_statistics'] == False
        assert response.context['can_view_activity'] == False
    
    def test_profile_not_found(self):
        """Test viewing non-existent profile"""
        self.client.login(email='user1@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_view', kwargs={'username': 'nonexistent'}))
        
        assert response.status_code == 404


class ProfileEditTests(TestCase):
    """Tests for profile_edit"""
    
    def setUp(self):
        """Set up test user"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_get_profile_edit(self):
        """Test GET request to profile edit page"""
        self.client.login(email='test@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_edit'))
        
        assert response.status_code == 200
        assert 'profile_form' in response.context
        assert 'avatar_form' in response.context
        assert 'banner_form' in response.context
    
    def test_update_profile_info(self):
        """Test updating profile information"""
        self.client.login(email='test@test.com', password='testpass123')
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'display_name': 'JohnD',
            'bio': 'Updated bio',
            'country': 'USA',
            'city': 'New York',
        }
        
        response = self.client.post(reverse('dashboard:profile_edit'), data)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Verify user was updated
        self.user.refresh_from_db()
        assert self.user.first_name == 'John'
        assert self.user.last_name == 'Doe'
        assert self.user.display_name == 'JohnD'
        assert self.user.bio == 'Updated bio'
    
    def test_avatar_upload(self):
        """Test avatar upload with image processing"""
        self.client.login(email='test@test.com', password='testpass123')
        
        # Create a test image
        image = Image.new('RGB', (800, 800), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        
        avatar_file = SimpleUploadedFile(
            'test_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'avatar': avatar_file}
        )
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Verify avatar was saved
        self.user.refresh_from_db()
        assert self.user.avatar is not None
    
    def test_avatar_too_large(self):
        """Test avatar upload with file too large"""
        self.client.login(email='test@test.com', password='testpass123')
        
        # Create a large image (> 2MB)
        image = Image.new('RGB', (4000, 4000), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG', quality=100)
        image_io.seek(0)
        
        avatar_file = SimpleUploadedFile(
            'large_avatar.jpg',
            image_io.read(),
            content_type='image/jpeg'
        )
        
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            {'avatar': avatar_file}
        )
        
        # Should show error message
        messages = list(response.wsgi_request._messages)
        assert any('under 2MB' in str(m) for m in messages)


class ProfileExportTests(TestCase):
    """Tests for profile_export"""
    
    def setUp(self):
        """Set up test user"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            username='testuser',
            password='testpass123'
        )
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.bio = 'Test bio'
        self.user.save()
    
    def test_export_profile(self):
        """Test exporting profile data"""
        self.client.login(email='test@test.com', password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_export'))
        
        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        assert 'attachment' in response['Content-Disposition']
        assert 'testuser_profile_' in response['Content-Disposition']
        
        # Parse JSON response
        data = json.loads(response.content)
        
        # Verify export structure
        assert 'export_metadata' in data
        assert 'profile' in data
        assert 'game_profiles' in data
        assert 'tournament_history' in data
        assert 'team_memberships' in data
        assert 'payment_history' in data
        assert 'activity_history' in data
        assert 'achievements' in data
        
        # Verify profile data
        assert data['profile']['username'] == 'testuser'
        assert data['profile']['first_name'] == 'John'
        assert data['profile']['last_name'] == 'Doe'
        assert data['profile']['bio'] == 'Test bio'
        
        # Verify sensitive data is excluded
        assert 'password' not in str(data)
    
    def test_export_requires_login(self):
        """Test that export requires authentication"""
        response = self.client.get(reverse('dashboard:profile_export'))
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/accounts/login/' in response.url
