"""
Property-Based Tests for Dashboard Statistics Cards Accuracy

This module contains property-based tests for the dashboard statistics cards,
specifically testing that the displayed statistics are accurate and correctly calculated.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid
from bs4 import BeautifulSoup
from decimal import Decimal

from core.models import User, Game
from tournaments.models import Tournament, Participant
from teams.models import Team, TeamMember
from notifications.models import Notification
from dashboard.services import StatisticsService


@pytest.mark.django_db
class TestDashboardStatisticsCardsAccuracy:
    """
    **Feature: user-profile-dashboard, Property 38: Dashboard statistics cards accuracy**
    
    For any dashboard display, the statistics cards must show accurate counts for 
    total tournaments, win rate, current teams, and unread notifications.
    
    **Validates: Requirements 1.2**
    """
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_tournaments=st.integers(min_value=0, max_value=5),
        num_teams=st.integers(min_value=0, max_value=3),
        num_notifications=st.integers(min_value=0, max_value=10),
        num_read_notifications=st.integers(min_value=0, max_value=5)
    )
    def test_statistics_cards_show_accurate_counts(
        self, num_tournaments, num_teams, num_notifications, num_read_notifications
    ):
        """
        Property: Statistics cards display accurate counts for all metrics.
        
        This test verifies that:
        1. Total tournaments count matches actual participations
        2. Current teams count matches active team memberships
        3. Unread notifications count matches unread notifications
        4. All counts are non-negative integers
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game for tournaments and teams
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create tournaments and participations
        tournament_ids = []
        for i in range(num_tournaments):
            tournament = Tournament.objects.create(
                name=f'Tournament {i}',
                slug=f'tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() - timedelta(days=i+1),
                registration_start=timezone.now() - timedelta(days=i+2),
                registration_end=timezone.now() - timedelta(days=i+1, hours=1),
                check_in_start=timezone.now() - timedelta(days=i+1, hours=2),
                format='single_elim',
                status='completed'
            )
            
            # Create participation with confirmed status
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                matches_won=i % 5,
                matches_lost=(i + 1) % 5,
                final_placement=i % 8 + 1
            )
            tournament_ids.append(tournament.id)
        
        # Create teams and memberships
        team_ids = []
        for i in range(num_teams):
            team = Team.objects.create(
                name=f'Team {i}',
                slug=f'team-{unique_id}-{i}',
                game=game,
                captain=user,
                max_members=5
            )
            
            # Create active team membership
            TeamMember.objects.create(
                team=team,
                user=user,
                role='captain' if i == 0 else 'member',
                status='active'
            )
            team_ids.append(team.id)
        
        # Create notifications (both read and unread)
        notification_ids = []
        total_notifications = num_notifications + num_read_notifications
        
        for i in range(total_notifications):
            is_read = i < num_read_notifications
            notification = Notification.objects.create(
                user=user,
                notification_type='system',
                title=f'Notification {i}',
                message=f'Test message {i}',
                read=is_read
            )
            notification_ids.append(notification.id)
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        # Property 1: Response is successful
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property 2: Total tournaments count is accurate
        # Find the tournaments stat card
        tournaments_stat = soup.find('div', {'data-stat': 'total-tournaments'})
        assert tournaments_stat is not None, \
            "Total tournaments stat card not found"
        
        tournaments_value = tournaments_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert tournaments_value is not None, \
            "Total tournaments value not found in stat card"
        
        displayed_tournaments = int(tournaments_value.get_text(strip=True))
        assert displayed_tournaments == num_tournaments, \
            f"Total tournaments mismatch. Expected {num_tournaments}, displayed {displayed_tournaments}"
        
        # Property 3: Current teams count is accurate
        teams_stat = soup.find('div', {'data-stat': 'current-teams'})
        assert teams_stat is not None, \
            "Current teams stat card not found"
        
        teams_value = teams_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert teams_value is not None, \
            "Current teams value not found in stat card"
        
        displayed_teams = int(teams_value.get_text(strip=True))
        assert displayed_teams == num_teams, \
            f"Current teams mismatch. Expected {num_teams}, displayed {displayed_teams}"
        
        # Property 4: Unread notifications count is accurate
        notifications_stat = soup.find('div', {'data-stat': 'unread-notifications'})
        assert notifications_stat is not None, \
            "Unread notifications stat card not found"
        
        notifications_value = notifications_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert notifications_value is not None, \
            "Unread notifications value not found in stat card"
        
        displayed_notifications = int(notifications_value.get_text(strip=True))
        assert displayed_notifications == num_notifications, \
            f"Unread notifications mismatch. Expected {num_notifications}, displayed {displayed_notifications}"
        
        # Property 5: All counts are non-negative
        assert displayed_tournaments >= 0, \
            f"Total tournaments count is negative: {displayed_tournaments}"
        assert displayed_teams >= 0, \
            f"Current teams count is negative: {displayed_teams}"
        assert displayed_notifications >= 0, \
            f"Unread notifications count is negative: {displayed_notifications}"
        
        # Cleanup
        Notification.objects.filter(id__in=notification_ids).delete()
        TeamMember.objects.filter(user=user).delete()
        Team.objects.filter(id__in=team_ids).delete()
        Participant.objects.filter(user=user).delete()
        Tournament.objects.filter(id__in=tournament_ids).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        matches_won=st.integers(min_value=0, max_value=20),
        matches_lost=st.integers(min_value=0, max_value=20)
    )
    def test_win_rate_calculation_accuracy(self, matches_won, matches_lost):
        """
        Property: Win rate is calculated correctly and displayed accurately.
        
        This test verifies that:
        1. Win rate = (matches_won / total_matches) * 100
        2. Win rate is between 0 and 100
        3. Win rate is displayed with proper formatting
        4. Win rate is 0 when no matches played
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create a tournament with participation
        if matches_won > 0 or matches_lost > 0:
            tournament = Tournament.objects.create(
                name=f'Tournament',
                slug=f'tournament-{unique_id}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() - timedelta(days=1),
                registration_start=timezone.now() - timedelta(days=2),
                registration_end=timezone.now() - timedelta(days=1, hours=1),
                check_in_start=timezone.now() - timedelta(days=1, hours=2),
                format='single_elim',
                status='completed'
            )
            
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                matches_won=matches_won,
                matches_lost=matches_lost,
                final_placement=1
            )
        
        # Calculate expected win rate
        total_matches = matches_won + matches_lost
        if total_matches > 0:
            expected_win_rate = round((matches_won / total_matches) * 100, 2)
        else:
            expected_win_rate = 0.0
        
        # Property 1: Win rate is between 0 and 100
        assert 0 <= expected_win_rate <= 100, \
            f"Expected win rate {expected_win_rate} is not between 0 and 100"
        
        # Get statistics from service
        stats = StatisticsService.get_user_statistics(user.id)
        
        # Property 2: Service calculates win rate correctly
        assert stats['win_rate'] == expected_win_rate, \
            f"Service win rate {stats['win_rate']} does not match expected {expected_win_rate}"
        
        # Property 3: Matches won + matches lost = total matches
        assert stats['matches_won'] + stats['matches_lost'] == stats['total_matches'], \
            f"Matches won ({stats['matches_won']}) + lost ({stats['matches_lost']}) != total ({stats['total_matches']})"
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the win rate stat card
        win_rate_stat = soup.find('div', {'data-stat': 'win-rate'})
        assert win_rate_stat is not None, \
            "Win rate stat card not found"
        
        win_rate_value = win_rate_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert win_rate_value is not None, \
            "Win rate value not found in stat card"
        
        # Extract the numeric value (remove % sign if present)
        win_rate_text = win_rate_value.get_text(strip=True).replace('%', '')
        displayed_win_rate = float(win_rate_text)
        
        # Property 4: Displayed win rate matches calculated win rate (within rounding tolerance)
        # The template uses floatformat:1 which rounds to 1 decimal place
        # So we allow a tolerance of 0.1 to account for rounding differences
        assert abs(displayed_win_rate - expected_win_rate) < 0.1, \
            f"Displayed win rate {displayed_win_rate}% does not match expected {expected_win_rate}% (tolerance: 0.1)"
        
        # Property 5: Displayed win rate is between 0 and 100
        assert 0 <= displayed_win_rate <= 100, \
            f"Displayed win rate {displayed_win_rate}% is not between 0 and 100"
        
        # Cleanup
        if matches_won > 0 or matches_lost > 0:
            Participant.objects.filter(user=user).delete()
            Tournament.objects.filter(organizer=user).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_active_teams=st.integers(min_value=0, max_value=3),
        num_inactive_teams=st.integers(min_value=0, max_value=3)
    )
    def test_current_teams_excludes_inactive(self, num_active_teams, num_inactive_teams):
        """
        Property: Current teams count only includes active team memberships.
        
        This test verifies that:
        1. Only teams with status='active' are counted
        2. Teams with status='left', 'kicked', 'pending' are excluded
        3. Count is accurate regardless of inactive teams
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create active teams
        active_team_ids = []
        for i in range(num_active_teams):
            team = Team.objects.create(
                name=f'Active Team {i}',
                slug=f'active-team-{unique_id}-{i}',
                game=game,
                captain=user,
                max_members=5
            )
            
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status='active'
            )
            active_team_ids.append(team.id)
        
        # Create inactive teams with various statuses
        inactive_team_ids = []
        inactive_statuses = ['left', 'kicked', 'pending']
        
        for i in range(num_inactive_teams):
            team = Team.objects.create(
                name=f'Inactive Team {i}',
                slug=f'inactive-team-{unique_id}-{i}',
                game=game,
                captain=user,
                max_members=5
            )
            
            status = inactive_statuses[i % len(inactive_statuses)]
            TeamMember.objects.create(
                team=team,
                user=user,
                role='member',
                status=status
            )
            inactive_team_ids.append(team.id)
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the current teams stat card
        teams_stat = soup.find('div', {'data-stat': 'current-teams'})
        assert teams_stat is not None, \
            "Current teams stat card not found"
        
        teams_value = teams_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert teams_value is not None, \
            "Current teams value not found in stat card"
        
        displayed_teams = int(teams_value.get_text(strip=True))
        
        # Property: Only active teams are counted
        assert displayed_teams == num_active_teams, \
            f"Current teams count {displayed_teams} does not match active teams {num_active_teams}. " \
            f"Inactive teams ({num_inactive_teams}) should not be counted."
        
        # Cleanup
        TeamMember.objects.filter(user=user).delete()
        Team.objects.filter(id__in=active_team_ids + inactive_team_ids).delete()
        game.delete()
        user.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_unread=st.integers(min_value=0, max_value=10),
        num_read=st.integers(min_value=0, max_value=10)
    )
    def test_unread_notifications_excludes_read(self, num_unread, num_read):
        """
        Property: Unread notifications count only includes notifications with read=False.
        
        This test verifies that:
        1. Only notifications with read=False are counted
        2. Read notifications are excluded from the count
        3. Count is accurate regardless of read notifications
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create unread notifications
        unread_ids = []
        for i in range(num_unread):
            notification = Notification.objects.create(
                user=user,
                notification_type='system',
                title=f'Unread Notification {i}',
                message=f'Unread message {i}',
                read=False
            )
            unread_ids.append(notification.id)
        
        # Create read notifications
        read_ids = []
        for i in range(num_read):
            notification = Notification.objects.create(
                user=user,
                notification_type='system',
                title=f'Read Notification {i}',
                message=f'Read message {i}',
                read=True
            )
            read_ids.append(notification.id)
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the unread notifications stat card
        notifications_stat = soup.find('div', {'data-stat': 'unread-notifications'})
        assert notifications_stat is not None, \
            "Unread notifications stat card not found"
        
        notifications_value = notifications_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert notifications_value is not None, \
            "Unread notifications value not found in stat card"
        
        displayed_notifications = int(notifications_value.get_text(strip=True))
        
        # Property: Only unread notifications are counted
        assert displayed_notifications == num_unread, \
            f"Unread notifications count {displayed_notifications} does not match unread {num_unread}. " \
            f"Read notifications ({num_read}) should not be counted."
        
        # Cleanup
        Notification.objects.filter(id__in=unread_ids + read_ids).delete()
        user.delete()
    
    @settings(max_examples=10, deadline=None)
    @given(
        num_confirmed=st.integers(min_value=0, max_value=5),
        num_pending=st.integers(min_value=0, max_value=3),
        num_cancelled=st.integers(min_value=0, max_value=3)
    )
    def test_total_tournaments_only_counts_confirmed(
        self, num_confirmed, num_pending, num_cancelled
    ):
        """
        Property: Total tournaments count only includes confirmed participations.
        
        This test verifies that:
        1. Only participations with status='confirmed' are counted
        2. Pending, cancelled, and other statuses are excluded
        3. Count is accurate regardless of non-confirmed participations
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a game
        game = Game.objects.create(
            name=f'TestGame_{unique_id}',
            slug=f'testgame_{unique_id}',
            genre='fps'
        )
        
        # Create confirmed participations
        confirmed_ids = []
        for i in range(num_confirmed):
            tournament = Tournament.objects.create(
                name=f'Confirmed Tournament {i}',
                slug=f'confirmed-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() - timedelta(days=i+1),
                registration_start=timezone.now() - timedelta(days=i+2),
                registration_end=timezone.now() - timedelta(days=i+1, hours=1),
                check_in_start=timezone.now() - timedelta(days=i+1, hours=2),
                format='single_elim',
                status='completed'
            )
            
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='confirmed',
                matches_won=0,
                matches_lost=0
            )
            confirmed_ids.append(tournament.id)
        
        # Create pending participations
        pending_ids = []
        for i in range(num_pending):
            tournament = Tournament.objects.create(
                name=f'Pending Tournament {i}',
                slug=f'pending-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() + timedelta(days=i+1),
                registration_start=timezone.now() - timedelta(days=1),
                registration_end=timezone.now() + timedelta(days=i),
                check_in_start=timezone.now() + timedelta(days=i, hours=22),
                format='single_elim',
                status='registration'
            )
            
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='registered',  # Not confirmed
                matches_won=0,
                matches_lost=0
            )
            pending_ids.append(tournament.id)
        
        # Create cancelled participations
        cancelled_ids = []
        for i in range(num_cancelled):
            tournament = Tournament.objects.create(
                name=f'Cancelled Tournament {i}',
                slug=f'cancelled-tournament-{unique_id}-{i}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() - timedelta(days=i+1),
                registration_start=timezone.now() - timedelta(days=i+2),
                registration_end=timezone.now() - timedelta(days=i+1, hours=1),
                check_in_start=timezone.now() - timedelta(days=i+1, hours=2),
                format='single_elim',
                status='cancelled'
            )
            
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='cancelled',
                matches_won=0,
                matches_lost=0
            )
            cancelled_ids.append(tournament.id)
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the total tournaments stat card
        tournaments_stat = soup.find('div', {'data-stat': 'total-tournaments'})
        assert tournaments_stat is not None, \
            "Total tournaments stat card not found"
        
        tournaments_value = tournaments_stat.find('p', class_=lambda c: c and 'text-3xl' in c)
        assert tournaments_value is not None, \
            "Total tournaments value not found in stat card"
        
        displayed_tournaments = int(tournaments_value.get_text(strip=True))
        
        # Property: Only confirmed participations are counted
        assert displayed_tournaments == num_confirmed, \
            f"Total tournaments count {displayed_tournaments} does not match confirmed {num_confirmed}. " \
            f"Pending ({num_pending}) and cancelled ({num_cancelled}) should not be counted."
        
        # Cleanup
        Participant.objects.filter(user=user).delete()
        Tournament.objects.filter(id__in=confirmed_ids + pending_ids + cancelled_ids).delete()
        game.delete()
        user.delete()
    
    def test_statistics_cards_present_on_dashboard(self):
        """
        Property: All four statistics cards are present on the dashboard.
        
        This test verifies that:
        1. Total tournaments card is present
        2. Win rate card is present
        3. Current teams card is present
        4. Unread notifications card is present
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Request the dashboard page
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property: All four stat cards are present
        required_stats = [
            'total-tournaments',
            'win-rate',
            'current-teams',
            'unread-notifications'
        ]
        
        for stat_name in required_stats:
            stat_card = soup.find('div', {'data-stat': stat_name})
            assert stat_card is not None, \
                f"Statistics card '{stat_name}' not found on dashboard"
            
            # Verify the card has a value
            stat_value = stat_card.find('p', class_=lambda c: c and 'text-3xl' in c)
            assert stat_value is not None, \
                f"Statistics card '{stat_name}' missing value element"
            
            # Verify the value is not empty
            value_text = stat_value.get_text(strip=True)
            assert value_text != '', \
                f"Statistics card '{stat_name}' has empty value"
        
        # Cleanup
        user.delete()
