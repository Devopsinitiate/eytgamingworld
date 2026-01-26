"""
Tests for game profile management views.

This module tests the game profile CRUD operations including:
- Listing game profiles
- Creating new game profiles
- Editing existing game profiles
- Deleting game profiles (with tournament history protection)
- Setting main game
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Game, UserGameProfile
from tournaments.models import Tournament, Participant
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


@pytest.mark.django_db
class TestGameProfileViews(TestCase):
    """Test game profile management views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Create test games
        self.game1 = Game.objects.create(
            name='Test Game 1',
            slug='test-game-1',
            genre='fps',
            is_active=True
        )
        
        self.game2 = Game.objects.create(
            name='Test Game 2',
            slug='test-game-2',
            genre='moba',
            is_active=True
        )
        
        # Login user
        self.client.login(email='testuser@example.com', password='testpass123')
    
    def test_game_profile_list_view(self):
        """Test that game profile list view displays user's profiles"""
        # Create game profiles
        profile1 = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500,
            is_main_game=True
        )
        
        profile2 = UserGameProfile.objects.create(
            user=self.user,
            game=self.game2,
            in_game_name='Player2',
            skill_rating=1200,
            is_main_game=False
        )
        
        # Access list view
        response = self.client.get(reverse('dashboard:game_profile_list'))
        
        # Check response
        assert response.status_code == 200
        assert profile1 in response.context['game_profiles']
        assert profile2 in response.context['game_profiles']
        
        # Check ordering (main game first, then by skill rating)
        profiles = list(response.context['game_profiles'])
        assert profiles[0] == profile1  # Main game first
        assert profiles[1] == profile2
    
    def test_game_profile_create_view_get(self):
        """Test that game profile create view displays form"""
        response = self.client.get(reverse('dashboard:game_profile_create'))
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['action'] == 'Create'
    
    def test_game_profile_create_view_post_success(self):
        """Test creating a new game profile"""
        data = {
            'game': self.game1.id,
            'in_game_name': 'NewPlayer',
            'skill_rating': 1000,
            'rank': 'Gold',
            'preferred_role': 'Support',
            'is_main_game': True
        }
        
        response = self.client.post(reverse('dashboard:game_profile_create'), data)
        
        # Check redirect
        assert response.status_code == 302
        assert response.url == reverse('dashboard:game_profile_list')
        
        # Check profile was created
        profile = UserGameProfile.objects.get(user=self.user, game=self.game1)
        assert profile.in_game_name == 'NewPlayer'
        assert profile.skill_rating == 1000
        assert profile.is_main_game == True
    
    def test_game_profile_create_duplicate_game(self):
        """Test that creating duplicate game profile is prevented"""
        # Create existing profile
        UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Existing',
            skill_rating=1000
        )
        
        # Try to create duplicate
        data = {
            'game': self.game1.id,
            'in_game_name': 'Duplicate',
            'skill_rating': 1500,
        }
        
        response = self.client.post(reverse('dashboard:game_profile_create'), data)
        
        # Check that form has errors
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors
    
    def test_game_profile_edit_view_get(self):
        """Test that game profile edit view displays form with existing data"""
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500
        )
        
        response = self.client.get(
            reverse('dashboard:game_profile_edit', kwargs={'profile_id': profile.id})
        )
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['game_profile'] == profile
        assert response.context['action'] == 'Edit'
    
    def test_game_profile_edit_view_post_success(self):
        """Test editing an existing game profile"""
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='OldName',
            skill_rating=1000
        )
        
        data = {
            'game': self.game1.id,
            'in_game_name': 'NewName',
            'skill_rating': 1500,
            'rank': 'Platinum',
            'preferred_role': 'DPS',
            'is_main_game': True
        }
        
        response = self.client.post(
            reverse('dashboard:game_profile_edit', kwargs={'profile_id': profile.id}),
            data
        )
        
        # Check redirect
        assert response.status_code == 302
        
        # Check profile was updated
        profile.refresh_from_db()
        assert profile.in_game_name == 'NewName'
        assert profile.skill_rating == 1500
        assert profile.rank == 'Platinum'
    
    def test_game_profile_edit_ownership_check(self):
        """Test that users can only edit their own profiles"""
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123'
        )
        
        # Create profile for other user
        profile = UserGameProfile.objects.create(
            user=other_user,
            game=self.game1,
            in_game_name='OtherPlayer',
            skill_rating=1000
        )
        
        # Try to edit other user's profile
        response = self.client.get(
            reverse('dashboard:game_profile_edit', kwargs={'profile_id': profile.id})
        )
        
        # Should get 404 (not found due to ownership check)
        assert response.status_code == 404
    
    def test_game_profile_delete_view_get(self):
        """Test that game profile delete view displays confirmation"""
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500
        )
        
        response = self.client.get(
            reverse('dashboard:game_profile_delete', kwargs={'profile_id': profile.id})
        )
        
        assert response.status_code == 200
        assert 'game_profile' in response.context
        assert response.context['game_profile'] == profile
    
    def test_game_profile_delete_success(self):
        """Test deleting a game profile without tournament history"""
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500
        )
        
        profile_id = profile.id
        
        response = self.client.post(
            reverse('dashboard:game_profile_delete', kwargs={'profile_id': profile.id})
        )
        
        # Check redirect
        assert response.status_code == 302
        
        # Check profile was deleted
        assert not UserGameProfile.objects.filter(id=profile_id).exists()
    
    def test_game_profile_delete_with_tournament_history(self):
        """Test that deletion is prevented when user has tournament history"""
        profile = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500
        )
        
        # Create tournament with this game
        organizer = User.objects.create_user(
            email='organizer@example.com',
            username='organizer',
            password='testpass123'
        )
        
        tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            description='Test',
            game=self.game1,
            organizer=organizer,
            format='single_elim',
            registration_start=timezone.now(),
            registration_end=timezone.now() + timedelta(days=7),
            check_in_start=timezone.now() + timedelta(days=7),
            start_datetime=timezone.now() + timedelta(days=8),
        )
        
        # Create participation record
        Participant.objects.create(
            tournament=tournament,
            user=self.user,
            status='confirmed'
        )
        
        # Try to delete profile
        response = self.client.post(
            reverse('dashboard:game_profile_delete', kwargs={'profile_id': profile.id})
        )
        
        # Check redirect
        assert response.status_code == 302
        
        # Check profile still exists
        assert UserGameProfile.objects.filter(id=profile.id).exists()
    
    def test_game_profile_set_main(self):
        """Test setting a game profile as main game"""
        # Create two profiles
        profile1 = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500,
            is_main_game=True
        )
        
        profile2 = UserGameProfile.objects.create(
            user=self.user,
            game=self.game2,
            in_game_name='Player2',
            skill_rating=1200,
            is_main_game=False
        )
        
        # Set profile2 as main
        response = self.client.get(
            reverse('dashboard:game_profile_set_main', kwargs={'profile_id': profile2.id})
        )
        
        # Check redirect
        assert response.status_code == 302
        
        # Check that profile2 is now main and profile1 is not
        profile1.refresh_from_db()
        profile2.refresh_from_db()
        
        assert profile1.is_main_game == False
        assert profile2.is_main_game == True
    
    def test_game_profile_main_game_uniqueness(self):
        """Test that only one game can be main at a time"""
        # Create profile and set as main
        profile1 = UserGameProfile.objects.create(
            user=self.user,
            game=self.game1,
            in_game_name='Player1',
            skill_rating=1500,
            is_main_game=True
        )
        
        # Create another profile and set as main
        data = {
            'game': self.game2.id,
            'in_game_name': 'Player2',
            'skill_rating': 1200,
            'is_main_game': True
        }
        
        response = self.client.post(reverse('dashboard:game_profile_create'), data)
        
        # Check that profile1 is no longer main
        profile1.refresh_from_db()
        assert profile1.is_main_game == False
        
        # Check that new profile is main
        profile2 = UserGameProfile.objects.get(user=self.user, game=self.game2)
        assert profile2.is_main_game == True
    
    def test_game_profile_requires_login(self):
        """Test that all game profile views require authentication"""
        # Logout
        self.client.logout()
        
        # Test list view
        response = self.client.get(reverse('dashboard:game_profile_list'))
        assert response.status_code == 302  # Redirect to login
        
        # Test create view
        response = self.client.get(reverse('dashboard:game_profile_create'))
        assert response.status_code == 302  # Redirect to login
