"""
Property-Based Tests for Upcoming Events Time Window

This module contains property-based tests for the upcoming events functionality
in the dashboard application, specifically testing the 7-day time window constraint.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from django.utils import timezone
from datetime import timedelta
import uuid

from core.models import User, Game
from tournaments.models import Tournament


@pytest.mark.django_db
class TestUpcomingEventsTimeWindow:
    """
    **Feature: user-profile-dashboard, Property 6: Upcoming events time window**
    
    For any dashboard display, upcoming events must only include items with dates 
    within the next 7 days from the current time.
    
    **Validates: Requirements 1.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=0, max_value=50),
        days_offset=st.integers(min_value=-30, max_value=30)
    )
    def test_upcoming_events_within_seven_days(self, num_tournaments, days_offset):
        """
        Property: All upcoming events must have start_datetime within 7 days from now.
        
        This test verifies that:
        1. Only tournaments starting within the next 7 days are included
        2. Tournaments starting before now are excluded
        3. Tournaments starting after 7 days are excluded
        4. The time window is calculated correctly
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create tournaments at various time offsets
        now = timezone.now()
        seven_days_from_now = now + timedelta(days=7)
        
        created_tournaments = []
        expected_upcoming_ids = []
        
        for i in range(num_tournaments):
            # Create tournaments at different time offsets
            # Some before now, some within 7 days, some after 7 days
            offset_days = days_offset + (i % 40) - 20  # Spread across -20 to +20 days
            start_datetime = now + timedelta(days=offset_days, hours=i)
            
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=start_datetime,
                registration_start=now - timedelta(days=1),
                registration_end=start_datetime - timedelta(hours=1),
                check_in_start=start_datetime - timedelta(hours=2),
                format='single_elim',
                status='registration'  # Valid status for upcoming events
            )
            created_tournaments.append(tournament)
            
            # Track which tournaments should be in upcoming events
            # Must be: start_datetime >= now AND start_datetime <= seven_days_from_now
            if now <= start_datetime <= seven_days_from_now:
                expected_upcoming_ids.append(tournament.id)
        
        # Query upcoming tournaments using the same logic as dashboard_home view
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        ).order_by('start_datetime')
        
        upcoming_ids = [t.id for t in upcoming_tournaments]
        
        # Property 1: All upcoming tournaments have start_datetime >= now
        for tournament in upcoming_tournaments:
            assert tournament.start_datetime >= now, \
                f"Tournament {tournament.id} starts at {tournament.start_datetime}, which is before now {now}"
        
        # Property 2: All upcoming tournaments have start_datetime <= seven_days_from_now
        for tournament in upcoming_tournaments:
            assert tournament.start_datetime <= seven_days_from_now, \
                f"Tournament {tournament.id} starts at {tournament.start_datetime}, which is after 7 days from now {seven_days_from_now}"
        
        # Property 3: All tournaments within the time window are included
        assert set(upcoming_ids) == set(expected_upcoming_ids), \
            f"Mismatch in upcoming tournaments. Expected {len(expected_upcoming_ids)}, got {len(upcoming_ids)}. " \
            f"Missing: {set(expected_upcoming_ids) - set(upcoming_ids)}, " \
            f"Extra: {set(upcoming_ids) - set(expected_upcoming_ids)}"
        
        # Property 4: Time window is exactly 7 days
        time_window_duration = seven_days_from_now - now
        expected_duration = timedelta(days=7)
        assert abs(time_window_duration - expected_duration) < timedelta(seconds=1), \
            f"Time window duration {time_window_duration} is not 7 days"
        
        # Property 5: Tournaments are ordered by start_datetime
        if len(upcoming_tournaments) > 1:
            for i in range(len(upcoming_tournaments) - 1):
                assert upcoming_tournaments[i].start_datetime <= upcoming_tournaments[i+1].start_datetime, \
                    f"Tournaments not ordered by start_datetime: {upcoming_tournaments[i].start_datetime} > {upcoming_tournaments[i+1].start_datetime}"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=100, deadline=None)
    @given(
        hours_from_now=st.floats(min_value=0.0, max_value=168.0),  # 0 to 7 days in hours
        status=st.sampled_from(['registration', 'draft', 'check_in'])
    )
    def test_upcoming_events_boundary_conditions(self, hours_from_now, status):
        """
        Property: Tournaments at the exact boundaries of the time window are handled correctly.
        
        This test verifies edge cases at the 0-hour and 7-day boundaries.
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create a tournament at the specified offset
        now = timezone.now()
        start_datetime = now + timedelta(hours=hours_from_now)
        seven_days_from_now = now + timedelta(days=7)
        
        tournament = Tournament.objects.create(
            name=f'Boundary Tournament',
            slug=f'boundary-tournament-{unique_id}',
            game=game,
            organizer=user,
            max_participants=16,
            start_datetime=start_datetime,
            registration_start=now - timedelta(days=1),
            registration_end=start_datetime - timedelta(hours=1) if start_datetime > now + timedelta(hours=1) else now,
            check_in_start=start_datetime - timedelta(hours=2) if start_datetime > now + timedelta(hours=2) else now,
            format='single_elim',
            status=status
        )
        
        # Query upcoming tournaments
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        )
        
        # Property: Tournament should be included if and only if it's within the window
        should_be_included = (now <= start_datetime <= seven_days_from_now)
        is_included = tournament in upcoming_tournaments
        
        assert is_included == should_be_included, \
            f"Tournament at {start_datetime} (offset {hours_from_now}h) should_be_included={should_be_included}, " \
            f"but is_included={is_included}. Now={now}, 7days={seven_days_from_now}"
        
        # Cleanup
        tournament.delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_past_tournaments=st.integers(min_value=0, max_value=20),
        num_future_tournaments=st.integers(min_value=0, max_value=20),
        num_within_window=st.integers(min_value=0, max_value=20)
    )
    def test_upcoming_events_excludes_past_and_far_future(self, num_past_tournaments, num_future_tournaments, num_within_window):
        """
        Property: Past tournaments and tournaments beyond 7 days are excluded.
        
        This test verifies that only tournaments within the correct time window are included.
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        now = timezone.now()
        seven_days_from_now = now + timedelta(days=7)
        
        past_tournament_ids = []
        future_tournament_ids = []
        within_window_ids = []
        
        # Create past tournaments (before now)
        for i in range(num_past_tournaments):
            days_ago = i + 1
            tournament = Tournament.objects.create(
                name=f'Past Tournament {i}',
                slug=f'past-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=now - timedelta(days=days_ago),
                registration_start=now - timedelta(days=days_ago+2),
                registration_end=now - timedelta(days=days_ago+1),
                check_in_start=now - timedelta(days=days_ago, hours=2),
                format='single_elim',
                status='registration'
            )
            past_tournament_ids.append(tournament.id)
        
        # Create far future tournaments (after 7 days)
        for i in range(num_future_tournaments):
            days_ahead = 8 + i  # Start at day 8 (beyond 7-day window)
            tournament = Tournament.objects.create(
                name=f'Future Tournament {i}',
                slug=f'future-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=now + timedelta(days=days_ahead),
                registration_start=now,
                registration_end=now + timedelta(days=days_ahead-1),
                check_in_start=now + timedelta(days=days_ahead, hours=-2),
                format='single_elim',
                status='registration'
            )
            future_tournament_ids.append(tournament.id)
        
        # Create tournaments within the 7-day window
        for i in range(num_within_window):
            # Distribute evenly across the 7-day window
            hours_offset = (i * 168.0 / max(num_within_window, 1)) if num_within_window > 0 else 84.0
            tournament = Tournament.objects.create(
                name=f'Within Window Tournament {i}',
                slug=f'within-window-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=now + timedelta(hours=hours_offset),
                registration_start=now - timedelta(hours=1),
                registration_end=now + timedelta(hours=hours_offset-1),
                check_in_start=now + timedelta(hours=hours_offset-2),
                format='single_elim',
                status='registration'
            )
            within_window_ids.append(tournament.id)
        
        # Query upcoming tournaments
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        )
        
        upcoming_ids = [t.id for t in upcoming_tournaments]
        
        # Property 1: No past tournaments are included
        past_in_upcoming = set(past_tournament_ids) & set(upcoming_ids)
        assert len(past_in_upcoming) == 0, \
            f"Found {len(past_in_upcoming)} past tournaments in upcoming events: {past_in_upcoming}"
        
        # Property 2: No far future tournaments are included
        future_in_upcoming = set(future_tournament_ids) & set(upcoming_ids)
        assert len(future_in_upcoming) == 0, \
            f"Found {len(future_in_upcoming)} far future tournaments in upcoming events: {future_in_upcoming}"
        
        # Property 3: All within-window tournaments are included
        assert set(within_window_ids) == set(upcoming_ids), \
            f"Mismatch in within-window tournaments. Expected {len(within_window_ids)}, got {len(upcoming_ids)}. " \
            f"Missing: {set(within_window_ids) - set(upcoming_ids)}, " \
            f"Extra: {set(upcoming_ids) - set(within_window_ids)}"
        
        # Property 4: Total count is correct
        assert len(upcoming_ids) == num_within_window, \
            f"Expected {num_within_window} upcoming tournaments, got {len(upcoming_ids)}"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        status=st.sampled_from(['completed', 'cancelled', 'in_progress'])
    )
    def test_upcoming_events_excludes_invalid_statuses(self, status):
        """
        Property: Only tournaments with valid statuses are included in upcoming events.
        
        This test verifies that tournaments with statuses other than 
        'registration', 'draft', or 'check_in' are excluded.
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        now = timezone.now()
        seven_days_from_now = now + timedelta(days=7)
        
        # Create a tournament within the time window but with invalid status
        tournament = Tournament.objects.create(
            name=f'Invalid Status Tournament',
            slug=f'invalid-status-tournament-{unique_id}',
            game=game,
            organizer=user,
            max_participants=16,
            start_datetime=now + timedelta(days=3),  # Within 7-day window
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=2),
            check_in_start=now + timedelta(days=2, hours=22),
            format='single_elim',
            status=status  # Invalid status for upcoming events
        )
        
        # Query upcoming tournaments
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        )
        
        # Property: Tournament with invalid status should not be included
        assert tournament not in upcoming_tournaments, \
            f"Tournament with status '{status}' should not be in upcoming events"
        
        # Cleanup
        tournament.delete()
        game.delete()
        user.delete()
    
    def test_upcoming_events_empty_result(self):
        """
        Property: When no tournaments exist within the time window, result is empty.
        
        Edge case test for when there are no upcoming tournaments.
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        now = timezone.now()
        seven_days_from_now = now + timedelta(days=7)
        
        # Create a tournament outside the time window
        Tournament.objects.create(
            name=f'Far Future Tournament',
            slug=f'far-future-tournament-{unique_id}',
            game=game,
            organizer=user,
            max_participants=16,
            start_datetime=now + timedelta(days=30),  # Way beyond 7 days
            registration_start=now,
            registration_end=now + timedelta(days=29),
            check_in_start=now + timedelta(days=29, hours=22),
            format='single_elim',
            status='registration'
        )
        
        # Query upcoming tournaments
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        )
        
        # Property: Result should be empty
        assert len(upcoming_tournaments) == 0, \
            f"Expected 0 upcoming tournaments, got {len(upcoming_tournaments)}"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=1, max_value=20),
        limit=st.integers(min_value=1, max_value=10)
    )
    def test_upcoming_events_respects_limit(self, num_tournaments, limit):
        """
        Property: When a limit is applied, only the specified number of tournaments are returned.
        
        This test verifies that the dashboard view's limit of 5 tournaments works correctly.
        """
        # Create a unique user and game for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        now = timezone.now()
        seven_days_from_now = now + timedelta(days=7)
        
        # Create tournaments within the time window
        for i in range(num_tournaments):
            hours_offset = (i * 168.0 / num_tournaments)  # Distribute across 7 days
            Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=now + timedelta(hours=hours_offset),
                registration_start=now - timedelta(hours=1),
                registration_end=now + timedelta(hours=hours_offset-1),
                check_in_start=now + timedelta(hours=hours_offset-2),
                format='single_elim',
                status='registration'
            )
        
        # Query upcoming tournaments with limit
        upcoming_tournaments = Tournament.objects.filter(
            start_datetime__gte=now,
            start_datetime__lte=seven_days_from_now,
            status__in=['registration', 'draft', 'check_in']
        ).order_by('start_datetime')[:limit]
        
        # Property: Number of returned tournaments should not exceed limit
        expected_count = min(num_tournaments, limit)
        assert len(upcoming_tournaments) == expected_count, \
            f"Expected {expected_count} tournaments (min of {num_tournaments} and limit {limit}), got {len(upcoming_tournaments)}"
        
        # Property: Returned tournaments should be the earliest ones
        if len(upcoming_tournaments) > 1:
            for i in range(len(upcoming_tournaments) - 1):
                assert upcoming_tournaments[i].start_datetime <= upcoming_tournaments[i+1].start_datetime, \
                    f"Tournaments not ordered by start_datetime"
        
        # Cleanup
        Tournament.objects.filter(game=game).delete()
        game.delete()
        user.delete()
