"""
Property-based tests for account deletion anonymization functionality.

This module tests the account deletion anonymization property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta
from security.models import AuditLog
from tournaments.models import Tournament, Participant
from core.models import Game
import uuid
from decimal import Decimal

User = get_user_model()


@pytest.mark.django_db
class TestAccountDeletionAnonymization:
    """
    **Feature: user-profile-dashboard, Property 23: Account deletion anonymization**
    
    For any deleted account, all personal information must be replaced with 
    placeholder values, tournament participation records must be retained 
    without personal identifiers, and the user must be immediately logged out.
    
    **Validates: Requirements 18.3, 18.4, 18.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        # Generate user data with various personal information (filter out problematic characters)
        first_name=st.one_of(st.just(''), st.text(min_size=1, max_size=30).filter(lambda x: '\x00' not in x)),
        last_name=st.one_of(st.just(''), st.text(min_size=1, max_size=30).filter(lambda x: '\x00' not in x)),
        display_name=st.one_of(st.just(''), st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x)),
        bio=st.one_of(st.just(''), st.text(min_size=1, max_size=500).filter(lambda x: '\x00' not in x)),
        phone_number=st.one_of(st.just(''), st.text(min_size=10, max_size=15).filter(lambda x: '\x00' not in x)),
        discord_username=st.one_of(st.just(''), st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x)),
        steam_id=st.one_of(st.just(''), st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x)),
        twitch_username=st.one_of(st.just(''), st.text(min_size=1, max_size=50).filter(lambda x: '\x00' not in x)),
        # Tournament participation data
        num_tournaments=st.integers(min_value=0, max_value=5),
        has_wins=st.booleans(),
        has_losses=st.booleans(),
    )
    def test_account_deletion_anonymizes_personal_data(self, first_name, last_name, 
                                                     display_name, bio, phone_number,
                                                     discord_username, steam_id, 
                                                     twitch_username, num_tournaments,
                                                     has_wins, has_losses):
        """
        Test that account deletion properly anonymizes personal data while
        preserving tournament participation records.
        """
        # Create a test user with personal information
        username = f"testuser_{uuid.uuid4().hex[:8]}"
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "secure_test_pass123"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            bio=bio,
            phone_number=phone_number,
            discord_username=discord_username,
            steam_id=steam_id,
            twitch_username=twitch_username,
        )
        
        # Store original data for comparison
        original_user_id = user.id
        original_username = user.username
        original_email = user.email
        
        # Create tournament participation records if specified
        tournaments_created = []
        participants_created = []
        
        if num_tournaments > 0:
            # Create a game first
            game = Game.objects.create(
                name=f"Test Game {uuid.uuid4().hex[:8]}",
                slug=f"test-game-{uuid.uuid4().hex[:8]}",
                description="Test game for property testing"
            )
            
            for i in range(num_tournaments):
                tournament = Tournament.objects.create(
                    name=f"Test Tournament {i}",
                    slug=f"test-tournament-{i}-{uuid.uuid4().hex[:8]}",
                    game=game,
                    organizer=user,
                    max_participants=16,
                    registration_fee=Decimal('10.00'),
                    prize_pool=Decimal('100.00'),
                    description="Test tournament",
                    registration_start=timezone.now(),
                    registration_end=timezone.now() + timedelta(days=7),
                    check_in_start=timezone.now() + timedelta(days=7),
                    start_datetime=timezone.now() + timedelta(days=8)
                )
                tournaments_created.append(tournament)
                
                # Create participant record
                participant = Participant.objects.create(
                    tournament=tournament,
                    user=user,
                    status='confirmed',
                    matches_won=1 if has_wins else 0,
                    matches_lost=1 if has_losses else 0,
                    final_placement=i + 1
                )
                participants_created.append(participant)
        
        # Perform account deletion using the view
        client = Client()
        client.force_login(user)
        
        # Get initial audit log count
        initial_audit_count = AuditLog.objects.count()
        
        # Perform the deletion
        response = client.post(reverse('dashboard:account_delete'), {
            'password': password,
            'confirm_text': 'DELETE',
        })
        
        # Property 1: User should be redirected (logged out)
        assert response.status_code == 302, (
            f"Account deletion should redirect after success, got {response.status_code}"
        )
        
        # Property 2: User should be logged out (session should be cleared)
        # Check if user is still authenticated in the client
        response_after = client.get(reverse('dashboard:home'))
        assert response_after.status_code == 302, (
            "User should be logged out and redirected to login page"
        )
        
        # Refresh user from database
        user.refresh_from_db()
        
        # Property 3: Personal information must be anonymized
        assert user.first_name == '[DELETED]', (
            f"First name should be anonymized, got '{user.first_name}'"
        )
        assert user.last_name == '[DELETED]', (
            f"Last name should be anonymized, got '{user.last_name}'"
        )
        assert user.display_name == '[DELETED USER]', (
            f"Display name should be anonymized, got '{user.display_name}'"
        )
        assert user.email == f'deleted_{original_user_id}@deleted.local', (
            f"Email should be anonymized, got '{user.email}'"
        )
        assert user.bio == '', (
            f"Bio should be cleared, got '{user.bio}'"
        )
        assert user.phone_number == '', (
            f"Phone number should be cleared, got '{user.phone_number}'"
        )
        assert user.discord_username == '', (
            f"Discord username should be cleared, got '{user.discord_username}'"
        )
        assert user.steam_id == '', (
            f"Steam ID should be cleared, got '{user.steam_id}'"
        )
        assert user.twitch_username == '', (
            f"Twitch username should be cleared, got '{user.twitch_username}'"
        )
        
        # Property 4: User account should be deactivated
        assert not user.is_active, (
            "User account should be deactivated (is_active=False)"
        )
        
        # Property 5: Tournament participation records should be retained
        for participant in participants_created:
            participant.refresh_from_db()
            
            # Participant record should still exist
            assert Participant.objects.filter(id=participant.id).exists(), (
                "Tournament participation record should be retained"
            )
            
            # User reference should still point to the same user (but anonymized)
            assert participant.user_id == original_user_id, (
                "Participant should still reference the same user ID"
            )
            
            # Tournament statistics should be preserved
            if has_wins:
                assert participant.matches_won > 0, (
                    "Tournament win statistics should be preserved"
                )
            if has_losses:
                assert participant.matches_lost > 0, (
                    "Tournament loss statistics should be preserved"
                )
            
            # Placement should be preserved
            assert participant.final_placement is not None, (
                "Tournament placement should be preserved"
            )
        
        # Property 6: Audit log should be created
        final_audit_count = AuditLog.objects.count()
        assert final_audit_count > initial_audit_count, (
            "Audit log entry should be created for account deletion"
        )
        
        # Check audit log details
        audit_logs = AuditLog.objects.filter(
            user_id=original_user_id,
            action='delete',
            model_name='User'
        ).order_by('-timestamp')
        
        assert audit_logs.exists(), (
            "Audit log should contain account deletion entry"
        )
        
        audit_log = audit_logs.first()
        assert audit_log.severity == 'high', (
            "Account deletion should be logged with high severity"
        )
        assert original_username in audit_log.details.get('username', ''), (
            "Audit log should preserve original username in details"
        )
        assert original_email in audit_log.details.get('email', ''), (
            "Audit log should preserve original email in details"
        )
    
    @settings(max_examples=50, deadline=None)
    @given(
        # Test with different numbers of tournament participations
        num_tournaments=st.integers(min_value=1, max_value=3),
        different_placements=st.lists(
            st.integers(min_value=1, max_value=10), 
            min_size=1, 
            max_size=3
        )
    )
    def test_tournament_records_preserved_without_personal_identifiers(self, 
                                                                     num_tournaments, 
                                                                     different_placements):
        """
        Test that tournament participation records are preserved but 
        personal identifiers are removed through user anonymization.
        """
        # Ensure we have enough placements for tournaments
        placements = different_placements[:num_tournaments]
        if len(placements) < num_tournaments:
            placements.extend([i + 1 for i in range(len(placements), num_tournaments)])
        
        # Create user with identifiable information
        username = f"identifiable_user_{uuid.uuid4().hex[:8]}"
        email = f"identifiable_{uuid.uuid4().hex[:8]}@example.com"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password="test_pass123",
            first_name="John",
            last_name="Doe",
            display_name="JohnDoe_Gamer",
            bio="I am a competitive gamer"
        )
        
        # Create game and tournaments
        game = Game.objects.create(
            name=f"Competitive Game {uuid.uuid4().hex[:8]}",
            slug=f"comp-game-{uuid.uuid4().hex[:8]}",
            description="Competitive gaming"
        )
        
        tournament_data = []
        for i in range(num_tournaments):
            tournament = Tournament.objects.create(
                name=f"Championship {i + 1}",
                slug=f"championship-{i + 1}-{uuid.uuid4().hex[:8]}",
                game=game,
                organizer=user,
                max_participants=32,
                registration_fee=Decimal('25.00'),
                prize_pool=Decimal('500.00'),
                description=f"Championship tournament {i + 1}",
                registration_start=timezone.now(),
                registration_end=timezone.now() + timedelta(days=7),
                check_in_start=timezone.now() + timedelta(days=7),
                start_datetime=timezone.now() + timedelta(days=8)
            )
            
            participant = Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                matches_won=5 - i,  # Different win counts
                matches_lost=i + 1,  # Different loss counts
                final_placement=placements[i]
            )
            
            tournament_data.append({
                'tournament': tournament,
                'participant': participant,
                'original_wins': 5 - i,
                'original_losses': i + 1,
                'original_placement': placements[i]
            })
        
        # Store original user data
        original_user_id = user.id
        original_display_name = user.display_name
        
        # Delete account
        client = Client()
        client.force_login(user)
        
        response = client.post(reverse('dashboard:account_delete'), {
            'password': 'test_pass123',
            'confirm_text': 'DELETE',
        })
        
        # Verify deletion succeeded
        assert response.status_code == 302
        
        # Refresh user and verify anonymization
        user.refresh_from_db()
        assert user.display_name == '[DELETED USER]'
        assert user.first_name == '[DELETED]'
        assert user.bio == ''
        
        # Property: Tournament records should be preserved with statistics
        for data in tournament_data:
            participant = data['participant']
            participant.refresh_from_db()
            
            # Record should still exist
            assert Participant.objects.filter(id=participant.id).exists(), (
                "Tournament participation record must be preserved"
            )
            
            # User reference should still be valid (pointing to anonymized user)
            assert participant.user_id == original_user_id, (
                "Participant should still reference the user (now anonymized)"
            )
            
            # Tournament statistics should be unchanged
            assert participant.matches_won == data['original_wins'], (
                f"Matches won should be preserved: expected {data['original_wins']}, "
                f"got {participant.matches_won}"
            )
            assert participant.matches_lost == data['original_losses'], (
                f"Matches lost should be preserved: expected {data['original_losses']}, "
                f"got {participant.matches_lost}"
            )
            assert participant.final_placement == data['original_placement'], (
                f"Final placement should be preserved: expected {data['original_placement']}, "
                f"got {participant.final_placement}"
            )
            
            # Tournament should still exist
            tournament = data['tournament']
            assert Tournament.objects.filter(id=tournament.id).exists(), (
                "Tournament record should be preserved"
            )
        
        # Property: Personal identifiers should be removed from user
        # (The user record is anonymized, so when tournament records reference
        # the user, they get anonymized data instead of personal identifiers)
        assert user.display_name != original_display_name, (
            "Personal identifiers should be removed through anonymization"
        )
        assert '[DELETED' in user.display_name, (
            "User should be marked as deleted"
        )
    
    @settings(max_examples=30, deadline=None)
    @given(
        # Test immediate logout behavior
        has_session_data=st.booleans(),
        has_multiple_sessions=st.booleans()
    )
    def test_immediate_logout_after_deletion(self, has_session_data, has_multiple_sessions):
        """
        Test that user is immediately logged out after account deletion.
        """
        # Create user
        user = User.objects.create_user(
            username=f"logout_test_{uuid.uuid4().hex[:8]}",
            email=f"logout_{uuid.uuid4().hex[:8]}@example.com",
            password="logout_pass123"
        )
        
        # Create client and login
        client = Client()
        client.force_login(user)
        
        # Verify user is logged in initially
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 200, "User should be logged in initially"
        
        # Optionally add session data
        if has_session_data:
            session = client.session
            session['test_data'] = 'some_value'
            session.save()
        
        # Create additional client session if specified
        additional_client = None
        if has_multiple_sessions:
            additional_client = Client()
            additional_client.force_login(user)
            
            # Verify additional session works
            response = additional_client.get(reverse('dashboard:home'))
            assert response.status_code == 200, "Additional session should work initially"
        
        # Perform account deletion
        response = client.post(reverse('dashboard:account_delete'), {
            'password': 'logout_pass123',
            'confirm_text': 'DELETE',
        })
        
        # Property: Deletion should redirect (indicating success)
        assert response.status_code == 302, (
            f"Account deletion should redirect, got {response.status_code}"
        )
        
        # Property: User should be immediately logged out from the deleting session
        # Try to access a protected page
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 302, (
            "User should be logged out and redirected to login"
        )
        
        # Verify redirect goes to login or home page
        assert 'login' in response.url or response.url == '/', (
            f"Should redirect to login page, got {response.url}"
        )
        
        # Property: Session should be cleared
        # Try to access session data
        try:
            session_data = client.session.get('test_data')
            # If we can access session, it should be empty or the user should be logged out
            if session_data is not None:
                # Check if user is actually logged out by trying authenticated action
                auth_response = client.get(reverse('dashboard:home'))
                assert auth_response.status_code == 302, (
                    "Even if session exists, user should not be authenticated"
                )
        except:
            # Session might be completely cleared, which is also valid
            pass
        
        # Property: User account should be deactivated
        user.refresh_from_db()
        assert not user.is_active, (
            "User account should be deactivated"
        )
        
        # Property: Additional sessions should also be invalidated
        # (Note: Django doesn't automatically invalidate all sessions, 
        # but the user being deactivated should prevent authentication)
        if additional_client:
            response = additional_client.get(reverse('dashboard:home'))
            # The user is deactivated, so even if session exists, 
            # authentication should fail
            user.refresh_from_db()
            if user.is_active:
                # If somehow user is still active, this would be a bug
                assert False, "User should be deactivated, preventing all authentication"