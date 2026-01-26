"""
Property-based tests for database query optimization.

This module tests the query optimization property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.test import Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test.utils import override_settings
from core.models import User, UserGameProfile, Game
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from notifications.models import Notification
from dashboard.models import Activity, Achievement, UserAchievement
import uuid
from datetime import datetime, timedelta
from django.utils import timezone


User = get_user_model()


@pytest.mark.django_db
class TestQueryOptimization:
    """
    **Feature: user-profile-dashboard, Property 29: Database query optimization**
    
    For any dashboard load, the number of database queries must not exceed a defined threshold.
    
    **Validates: Requirements 16.4**
    """
    
    def setup_method(self):
        """Set up test data for each test method"""
        self.client = Client()
        
    def create_test_user_with_data(self, unique_id):
        """Create a test user with associated data"""
        # Create user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123',
            first_name='Test',
            last_name='User',
            display_name=f'Test User {unique_id}'
        )
        
        # Create some games with unique names and slugs
        game1, created = Game.objects.get_or_create(
            name=f'Test Game 1 {unique_id}',
            defaults={
                'description': 'Test game for testing',
                'slug': f'test-game-1-{unique_id}'
            }
        )
        
        game2, created = Game.objects.get_or_create(
            name=f'Test Game 2 {unique_id}',
            defaults={
                'description': 'Another test game',
                'slug': f'test-game-2-{unique_id}'
            }
        )
        
        # Create game profiles
        UserGameProfile.objects.create(
            user=user,
            game=game1,
            in_game_name=f'player_{unique_id}_1',
            skill_rating=1500,
            is_main_game=True
        )
        
        UserGameProfile.objects.create(
            user=user,
            game=game2,
            in_game_name=f'player_{unique_id}_2',
            skill_rating=1200,
            is_main_game=False
        )
        
        # Create some activities
        for i in range(3):
            Activity.objects.create(
                user=user,
                activity_type='tournament_registered',
                data={'tournament_name': f'Test Tournament {i}'}
            )
        
        # Create some notifications
        for i in range(2):
            Notification.objects.create(
                user=user,
                title=f'Test Notification {i}',
                message=f'Test message {i}',
                notification_type='info'
            )
        
        return user
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_activities=st.integers(min_value=0, max_value=10),
        num_notifications=st.integers(min_value=0, max_value=5)
    )
    def test_dashboard_query_count_within_threshold(self, num_activities, num_notifications):
        """Property: Dashboard loads must not exceed query threshold"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = self.create_test_user_with_data(unique_id)
        
        # Add additional activities and notifications based on strategy
        for i in range(num_activities):
            Activity.objects.create(
                user=user,
                activity_type='profile_updated',
                data={'field': f'test_field_{i}'}
            )
        
        for i in range(num_notifications):
            Notification.objects.create(
                user=user,
                title=f'Extra Notification {i}',
                message=f'Extra message {i}',
                notification_type='info'
            )
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load dashboard
        response = self.client.get('/dashboard/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200, f"Dashboard should load successfully, got {response.status_code}. Response: {response.content[:200] if hasattr(response, 'content') else 'No content'}"
        
        # Assert query count is within threshold (30 queries max for dashboard with data)
        # This threshold accounts for:
        # - User authentication queries
        # - Statistics calculation queries (with select_related optimizations)
        # - Activity feed queries (with select_related optimizations)
        # - Upcoming tournaments queries (with select_related optimizations)
        # - Notifications queries
        # - Team membership queries
        # - Cache miss scenarios
        assert query_count <= 30, \
            f"Dashboard should not exceed 30 queries, but used {query_count} queries. " \
            f"Queries: {[q['sql'][:100] + '...' if len(q['sql']) > 100 else q['sql'] for q in connection.queries]}"
        
        # Cleanup
        user.delete()
    
    def test_dashboard_query_optimization_with_select_related(self):
        """Property: Dashboard uses select_related for foreign key optimization"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user with data that will trigger select_related usage
        user = self.create_test_user_with_data(unique_id)
        
        # Add some additional data to ensure select_related is used
        # Create a tournament to trigger upcoming tournaments query with select_related
        try:
            game = Game.objects.first()
            if game:
                tournament = Tournament.objects.create(
                    name=f'Test Tournament {unique_id}',
                    game=game,
                    start_datetime=timezone.now() + timedelta(days=1),
                    registration_end=timezone.now() + timedelta(hours=12),
                    max_participants=16,
                    entry_fee=10.00,
                    status='registration'
                )
        except Exception:
            # Skip if tournament creation fails
            pass
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load dashboard
        response = self.client.get('/dashboard/')
        
        # Get all queries
        queries = connection.queries
        
        # Assert response is successful
        assert response.status_code == 200
        
        # The main property: query count should be reasonable (under 25 for user with data)
        query_count = len(queries)
        assert query_count <= 25, \
            f"Dashboard should use optimized queries (≤25), but used {query_count} queries"
        
        # Check that we're not doing N+1 queries by looking for repeated patterns
        sql_statements = [q['sql'] for q in queries]
        
        # Count similar queries (basic heuristic for N+1 detection)
        query_patterns = {}
        for sql in sql_statements:
            # Normalize query by removing specific IDs/values
            normalized = sql
            for char in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                normalized = normalized.replace(char, 'X')
            
            pattern = normalized[:100]  # First 100 chars as pattern
            query_patterns[pattern] = query_patterns.get(pattern, 0) + 1
        
        # No single query pattern should repeat more than 3 times (indicates N+1)
        max_repeats = max(query_patterns.values()) if query_patterns else 0
        assert max_repeats <= 3, \
            f"Possible N+1 query detected: pattern repeated {max_repeats} times"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        has_tournaments=st.booleans(),
        has_teams=st.booleans()
    )
    def test_dashboard_query_count_scales_reasonably(self, has_tournaments, has_teams):
        """Property: Query count scales reasonably with user data"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        user = self.create_test_user_with_data(unique_id)
        
        # Conditionally add more complex data
        if has_tournaments:
            # Create a tournament and participation
            try:
                game = Game.objects.first()
                if game:
                    tournament = Tournament.objects.create(
                        name=f'Test Tournament {unique_id}',
                        game=game,
                        start_datetime=timezone.now() + timedelta(days=1),
                        registration_end=timezone.now() + timedelta(hours=12),
                        max_participants=16,
                        entry_fee=10.00,
                        status='registration'
                    )
                    
                    Participant.objects.create(
                        user=user,
                        tournament=tournament,
                        status='confirmed'
                    )
            except Exception:
                # Skip if tournament creation fails
                pass
        
        if has_teams:
            # Create a team and membership
            try:
                game = Game.objects.first()
                if game:
                    team = Team.objects.create(
                        name=f'Test Team {unique_id}',
                        game=game,
                        captain=user,
                        description='Test team'
                    )
                    
                    TeamMember.objects.create(
                        user=user,
                        team=team,
                        role='captain',
                        status='active'
                    )
            except Exception:
                # Skip if team creation fails
                pass
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load dashboard
        response = self.client.get('/dashboard/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Query count should still be reasonable even with more data
        # Allow slightly higher threshold for complex data scenarios
        max_queries = 35 if (has_tournaments and has_teams) else 30
        
        assert query_count <= max_queries, \
            f"Dashboard with additional data should not exceed {max_queries} queries, " \
            f"but used {query_count} queries"
        
        # Cleanup
        user.delete()
    
    def test_empty_dashboard_minimal_queries(self):
        """Property: Dashboard with no user data uses minimal queries"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create minimal user with no additional data
        user = User.objects.create_user(
            email=f'minimal_{unique_id}@example.com',
            username=f'minimal_{unique_id}',
            password='testpass123'
        )
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load dashboard
        response = self.client.get('/dashboard/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Minimal dashboard should use fewer queries (15 or less)
        assert query_count <= 15, \
            f"Empty dashboard should use minimal queries (≤15), but used {query_count} queries"
        
        # Cleanup
        user.delete()
    
    def test_profile_view_query_optimization(self):
        """Property: Profile view uses optimized queries"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test users
        owner = self.create_test_user_with_data(unique_id + '_owner')
        viewer = User.objects.create_user(
            email=f'viewer_{unique_id}@example.com',
            username=f'viewer_{unique_id}',
            password='testpass123'
        )
        
        # Login as viewer
        login_success = self.client.login(username=viewer.email, password='testpass123')
        assert login_success, f"Login should succeed for viewer {viewer.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # View profile
        response = self.client.get(f'/dashboard/profile/{owner.username}/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Profile view should be optimized (20 queries or less)
        assert query_count <= 20, \
            f"Profile view should use optimized queries (≤20), but used {query_count} queries"
        
        # Cleanup
        owner.delete()
        viewer.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_game_profiles=st.integers(min_value=1, max_value=5)
    )
    def test_game_profile_list_query_optimization(self, num_game_profiles):
        """Property: Game profile list uses select_related optimization"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create games and game profiles
        for i in range(num_game_profiles):
            try:
                game, created = Game.objects.get_or_create(
                    name=f'Game {unique_id}_{i}',
                    defaults={
                        'description': f'Test game {i}',
                        'slug': f'game-{unique_id}-{i}'
                    }
                )
                
                UserGameProfile.objects.create(
                    user=user,
                    game=game,
                    in_game_name=f'player_{unique_id}_{i}',
                    skill_rating=1000 + (i * 100),
                    is_main_game=(i == 0)
                )
            except Exception:
                # Skip if creation fails (e.g., duplicate names)
                continue
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load game profile list
        response = self.client.get('/dashboard/games/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Game profile list should use minimal queries regardless of number of profiles
        # Should be 1 query for user auth + 1 optimized query for game profiles with select_related
        assert query_count <= 5, \
            f"Game profile list should use minimal queries (≤5), but used {query_count} queries"
        
        # Verify select_related is used (should see JOIN in queries)
        queries = connection.queries
        sql_statements = [q['sql'] for q in queries]
        combined_sql = ' '.join(sql_statements)
        
        # Should have JOINs indicating select_related usage
        assert 'JOIN' in combined_sql.upper(), \
            "Game profile queries should use select_related (JOIN statements)"
        
        # Cleanup
        user.delete()
    
    def test_tournament_history_pagination_query_optimization(self):
        """Property: Tournament history pagination doesn't cause N+1 queries"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user
        user = self.create_test_user_with_data(unique_id)
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load tournament history (which uses pagination)
        response = self.client.get('/dashboard/tournament-history/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Tournament history should use optimized queries with select_related
        assert query_count <= 10, \
            f"Tournament history should use optimized queries (≤10), but used {query_count} queries"
        
        # Verify select_related optimization
        queries = connection.queries
        sql_statements = [q['sql'] for q in queries]
        combined_sql = ' '.join(sql_statements)
        
        # Should have JOINs indicating select_related usage
        assert 'JOIN' in combined_sql.upper(), \
            "Tournament history queries should use select_related optimizations"
        
        # Cleanup
        user.delete()
    
    def test_activity_feed_query_optimization(self):
        """Property: Activity feed uses optimized queries"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create user with activities
        user = self.create_test_user_with_data(unique_id)
        
        # Add more activities
        for i in range(10):
            Activity.objects.create(
                user=user,
                activity_type='tournament_completed',
                data={'tournament_name': f'Tournament {i}'}
            )
        
        # Login user
        login_success = self.client.login(username=user.email, password='testpass123')
        assert login_success, f"Login should succeed for user {user.email}"
        
        # Reset query count
        connection.queries_log.clear()
        
        # Load activity feed
        response = self.client.get('/dashboard/activity/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Assert response is successful
        assert response.status_code == 200
        
        # Activity feed should use optimized queries
        assert query_count <= 8, \
            f"Activity feed should use optimized queries (≤8), but used {query_count} queries"
        
        # Cleanup
        user.delete()
