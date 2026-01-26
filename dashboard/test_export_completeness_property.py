"""
Property-based tests for profile export data completeness.

This module tests the export data completeness property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from core.models import User, UserGameProfile
from tournaments.models import Tournament, Participant, Game
from teams.models import Team, TeamMember
from payments.models import Payment
from dashboard.models import Activity, Achievement, UserAchievement
from dashboard.services import ProfileExportService
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


@pytest.mark.django_db
class TestExportDataCompleteness:
    """
    **Feature: user-profile-dashboard, Property 21: Export data completeness**
    
    For any user data export, the JSON must include all required sections (profile, 
    game profiles, tournament history, team memberships, payment history) and must 
    exclude sensitive data (password hash, payment method details).
    
    **Validates: Requirements 17.1, 17.2, 17.5**
    """
    
    def test_export_includes_all_required_sections(self):
        """Property: Export always includes all required top-level sections"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify all required sections are present
        required_sections = [
            'export_metadata',
            'profile',
            'game_profiles',
            'tournament_history',
            'team_memberships',
            'payment_history',
            'activity_history',
            'achievements'
        ]
        
        for section in required_sections:
            assert section in export_data, \
                f"Export must include '{section}' section"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_game_profiles=st.integers(min_value=0, max_value=5)
    )
    def test_export_includes_all_game_profiles(self, num_game_profiles):
        """Property: Export includes all user's game profiles"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create game profiles (each with unique game to avoid constraint violation)
        games = []
        for i in range(num_game_profiles):
            game = Game.objects.create(
                name=f'Test Game {unique_id}_{i}',
                slug=f'test-game-{unique_id}-{i}'
            )
            games.append(game)
            
            UserGameProfile.objects.create(
                user=user,
                game=game,
                in_game_name=f'Player{i}',
                skill_rating=1000 + i * 100
            )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify game profiles count matches
        assert len(export_data['game_profiles']) == num_game_profiles, \
            f"Export should include {num_game_profiles} game profiles, found {len(export_data['game_profiles'])}"
        
        # Cleanup
        UserGameProfile.objects.filter(user=user).delete()
        for game in games:
            game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_payments=st.integers(min_value=0, max_value=10)
    )
    def test_export_includes_all_payments(self, num_payments):
        """Property: Export includes all user's payments"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payments
        for i in range(num_payments):
            Payment.objects.create(
                user=user,
                amount=Decimal('25.00'),
                currency='USD',
                payment_type='tournament_fee',
                status='succeeded'
            )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify payments count matches
        assert len(export_data['payment_history']['payments']) == num_payments, \
            f"Export should include {num_payments} payments, found {len(export_data['payment_history']['payments'])}"
        
        # Cleanup
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    def test_export_excludes_password_hash(self):
        """Property: Export never includes password hash"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with password
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Convert export to string to search for password-related fields
        export_str = str(export_data)
        
        # Verify password hash is not in export
        assert 'password' not in export_data.get('profile', {}), \
            "Export must not include password field in profile"
        
        # Verify no password-related keys anywhere in export
        password_keys = ['password', 'password_hash', 'hashed_password']
        for key in password_keys:
            assert key not in export_str.lower(), \
                f"Export must not include '{key}' anywhere"
        
        # Cleanup
        user.delete()
    
    def test_export_excludes_payment_method_details(self):
        """Property: Export excludes sensitive payment method details"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payment
        Payment.objects.create(
            user=user,
            amount=Decimal('50.00'),
            currency='USD',
            payment_type='tournament_fee',
            status='succeeded',
            stripe_payment_intent_id='pi_test123'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify sensitive payment fields are not in export
        export_str = str(export_data)
        
        sensitive_fields = [
            'card_number',
            'card_last4',
            'stripe_payment_method_id',
            'cvv',
            'card_cvv'
        ]
        
        for field in sensitive_fields:
            assert field not in export_str.lower(), \
                f"Export must not include sensitive field '{field}'"
        
        # Cleanup
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    def test_export_includes_profile_metadata(self):
        """Property: Export always includes metadata section with required fields"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify metadata section exists
        assert 'export_metadata' in export_data, \
            "Export must include export_metadata section"
        
        metadata = export_data['export_metadata']
        
        # Verify required metadata fields
        required_metadata_fields = [
            'generated_at',
            'user_id',
            'username',
            'export_version'
        ]
        
        for field in required_metadata_fields:
            assert field in metadata, \
                f"Export metadata must include '{field}' field"
        
        # Verify user_id matches
        assert metadata['user_id'] == str(user.id), \
            "Export metadata user_id must match actual user ID"
        
        # Verify username matches
        assert metadata['username'] == user.username, \
            "Export metadata username must match actual username"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        has_first_name=st.booleans(),
        has_last_name=st.booleans(),
        has_bio=st.booleans(),
        has_country=st.booleans()
    )
    def test_export_profile_includes_all_profile_fields(
        self, 
        has_first_name, 
        has_last_name, 
        has_bio, 
        has_country
    ):
        """Property: Export profile section includes all profile fields (even if empty)"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with optional fields
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123',
            first_name='John' if has_first_name else '',
            last_name='Doe' if has_last_name else '',
            bio='Test bio' if has_bio else '',
            country='US' if has_country else ''
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify profile section exists
        assert 'profile' in export_data, \
            "Export must include profile section"
        
        profile = export_data['profile']
        
        # Verify all expected profile fields are present (even if None/empty)
        expected_profile_fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'display_name',
            'bio',
            'date_of_birth',
            'country',
            'city',
            'timezone',
            'phone_number',
            'role',
            'skill_level',
            'date_joined',
            'is_verified',
            'total_points',
            'level',
            'connected_accounts',
            'privacy_settings',
            'notification_preferences'
        ]
        
        for field in expected_profile_fields:
            assert field in profile, \
                f"Export profile must include '{field}' field"
        
        # Verify values match
        if has_first_name:
            assert profile['first_name'] == 'John'
        if has_last_name:
            assert profile['last_name'] == 'Doe'
        if has_bio:
            assert profile['bio'] == 'Test bio'
        if has_country:
            assert profile['country'] == 'US'
        
        # Cleanup
        user.delete()
    
    def test_export_team_memberships_includes_current_and_past(self):
        """Property: Export team memberships includes both current and past teams"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create game
        game = Game.objects.create(
            name=f'Test Game {unique_id}',
            slug=f'test-game-{unique_id}'
        )
        
        # Create teams
        current_team = Team.objects.create(
            name=f'Current Team {unique_id}',
            slug=f'current-team-{unique_id}',
            game=game,
            captain=user
        )
        
        past_team = Team.objects.create(
            name=f'Past Team {unique_id}',
            slug=f'past-team-{unique_id}',
            game=game,
            captain=user
        )
        
        # Create memberships
        TeamMember.objects.create(
            team=current_team,
            user=user,
            role='captain',
            status='active'
        )
        
        TeamMember.objects.create(
            team=past_team,
            user=user,
            role='member',
            status='left',
            left_at=timezone.now()
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify team memberships structure
        assert 'team_memberships' in export_data, \
            "Export must include team_memberships section"
        
        team_data = export_data['team_memberships']
        
        # Verify required fields
        assert 'current_teams' in team_data, \
            "Team memberships must include current_teams"
        assert 'past_teams' in team_data, \
            "Team memberships must include past_teams"
        assert 'total_teams_joined' in team_data, \
            "Team memberships must include total_teams_joined"
        
        # Verify counts
        assert len(team_data['current_teams']) == 1, \
            "Should have 1 current team"
        assert len(team_data['past_teams']) == 1, \
            "Should have 1 past team"
        assert team_data['total_teams_joined'] == 2, \
            "Total teams joined should be 2"
        
        # Cleanup
        TeamMember.objects.filter(user=user).delete()
        current_team.delete()
        past_team.delete()
        game.delete()
        user.delete()
    
    def test_export_payment_history_includes_summary(self):
        """Property: Export payment history includes summary statistics"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create payments with different statuses
        Payment.objects.create(
            user=user,
            amount=Decimal('25.00'),
            currency='USD',
            payment_type='tournament_fee',
            status='succeeded'
        )
        
        Payment.objects.create(
            user=user,
            amount=Decimal('30.00'),
            currency='USD',
            payment_type='tournament_fee',
            status='failed'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify payment history structure
        assert 'payment_history' in export_data, \
            "Export must include payment_history section"
        
        payment_data = export_data['payment_history']
        
        # Verify required fields
        assert 'payments' in payment_data, \
            "Payment history must include payments list"
        assert 'summary' in payment_data, \
            "Payment history must include summary"
        
        summary = payment_data['summary']
        
        # Verify summary fields
        required_summary_fields = [
            'total_payments',
            'total_spent',
            'successful_payments',
            'failed_payments'
        ]
        
        for field in required_summary_fields:
            assert field in summary, \
                f"Payment summary must include '{field}' field"
        
        # Verify summary values
        assert summary['total_payments'] == 2
        assert summary['successful_payments'] == 1
        assert summary['failed_payments'] == 1
        assert Decimal(summary['total_spent']) == Decimal('25.00')
        
        # Cleanup
        Payment.objects.filter(user=user).delete()
        user.delete()
    
    def test_export_achievements_includes_summary(self):
        """Property: Export achievements includes summary statistics"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create achievement
        achievement = Achievement.objects.create(
            name=f'Test Achievement {unique_id}',
            slug=f'test-achievement-{unique_id}',
            description='Test description',
            achievement_type='tournament',
            points_reward=50
        )
        
        # Award achievement to user
        UserAchievement.objects.create(
            user=user,
            achievement=achievement,
            is_completed=True,
            earned_at=timezone.now(),
            in_showcase=True
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify achievements structure
        assert 'achievements' in export_data, \
            "Export must include achievements section"
        
        achievements_data = export_data['achievements']
        
        # Verify required fields
        assert 'achievements' in achievements_data, \
            "Achievements must include achievements list"
        assert 'summary' in achievements_data, \
            "Achievements must include summary"
        
        summary = achievements_data['summary']
        
        # Verify summary fields
        required_summary_fields = [
            'total_achievements_earned',
            'total_points_from_achievements',
            'achievements_in_showcase'
        ]
        
        for field in required_summary_fields:
            assert field in summary, \
                f"Achievements summary must include '{field}' field"
        
        # Verify summary values
        assert summary['total_achievements_earned'] == 1
        assert summary['total_points_from_achievements'] == 50
        assert summary['achievements_in_showcase'] == 1
        
        # Cleanup
        UserAchievement.objects.filter(user=user).delete()
        achievement.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_activities=st.integers(min_value=0, max_value=20)
    )
    def test_export_includes_activity_history(self, num_activities):
        """Property: Export includes user's activity history"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create activities
        for i in range(num_activities):
            Activity.objects.create(
                user=user,
                activity_type='profile_updated',
                data={'field': f'field_{i}'}
            )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify activity history is included
        assert 'activity_history' in export_data, \
            "Export must include activity_history section"
        
        # Verify activities count (limited to 500 in implementation)
        expected_count = min(num_activities, 500)
        assert len(export_data['activity_history']) == expected_count, \
            f"Export should include {expected_count} activities, found {len(export_data['activity_history'])}"
        
        # Cleanup
        Activity.objects.filter(user=user).delete()
        user.delete()
    
    def test_export_is_json_serializable(self):
        """Property: Export data is JSON serializable"""
        import json
        
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify export can be serialized to JSON
        try:
            json_str = json.dumps(export_data)
            assert len(json_str) > 0, "JSON serialization should produce non-empty string"
            
            # Verify it can be deserialized back
            deserialized = json.loads(json_str)
            assert isinstance(deserialized, dict), "Deserialized data should be a dictionary"
            
        except (TypeError, ValueError) as e:
            pytest.fail(f"Export data must be JSON serializable, got error: {e}")
        
        # Cleanup
        user.delete()
    
    def test_export_connected_accounts_structure(self):
        """Property: Export includes connected accounts in correct structure"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with connected accounts
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123',
            discord_username='testuser#1234',
            steam_id='76561198000000000',
            twitch_username='testuser_twitch'
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify connected accounts structure
        profile = export_data['profile']
        assert 'connected_accounts' in profile, \
            "Profile must include connected_accounts"
        
        connected_accounts = profile['connected_accounts']
        
        # Verify all account types are present
        account_types = ['discord', 'steam', 'twitch']
        for account_type in account_types:
            assert account_type in connected_accounts, \
                f"Connected accounts must include '{account_type}'"
        
        # Verify values match
        assert connected_accounts['discord'] == 'testuser#1234'
        assert connected_accounts['steam'] == '76561198000000000'
        assert connected_accounts['twitch'] == 'testuser_twitch'
        
        # Cleanup
        user.delete()
    
    def test_export_privacy_settings_structure(self):
        """Property: Export includes privacy settings in correct structure"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with privacy settings
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123',
            online_status_visible=False,
            activity_visible=True,
            statistics_visible=False
        )
        
        # Generate export
        export_data = ProfileExportService.generate_export(user.id)
        
        # Verify privacy settings structure
        profile = export_data['profile']
        assert 'privacy_settings' in profile, \
            "Profile must include privacy_settings"
        
        privacy_settings = profile['privacy_settings']
        
        # Verify all privacy settings are present
        privacy_fields = [
            'online_status_visible',
            'activity_visible',
            'statistics_visible'
        ]
        
        for field in privacy_fields:
            assert field in privacy_settings, \
                f"Privacy settings must include '{field}'"
        
        # Verify values match
        assert privacy_settings['online_status_visible'] == False
        assert privacy_settings['activity_visible'] == True
        assert privacy_settings['statistics_visible'] == False
        
        # Cleanup
        user.delete()
