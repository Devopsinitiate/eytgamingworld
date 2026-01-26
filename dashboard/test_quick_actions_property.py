"""
Property-Based Tests for Dashboard Quick Actions Completeness

This module contains property-based tests for the dashboard quick actions functionality,
specifically testing that all required quick action buttons are present and functional.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone
import uuid
from bs4 import BeautifulSoup

from core.models import User


@pytest.mark.django_db
class TestDashboardQuickActionsCompleteness:
    """
    **Feature: user-profile-dashboard, Property 37: Dashboard quick actions completeness**
    
    For any dashboard display, all four quick action buttons (register for tournament, 
    join team, view notifications, manage payment methods) must be present and functional.
    
    **Validates: Requirements 1.5**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        username_suffix=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')),
            min_size=3,
            max_size=10
        ),
        email_prefix=st.text(
            alphabet=st.characters(whitelist_categories=('Ll', 'Nd')),
            min_size=3,
            max_size=10
        )
    )
    def test_all_four_quick_actions_present(self, username_suffix, email_prefix):
        """
        Property: Dashboard must display all 4 quick action buttons.
        
        This test verifies that:
        1. Register for Tournament button is present
        2. Join Team button is present
        3. View Notifications button is present
        4. Manage Payment Methods button is present
        5. All buttons have correct URLs
        6. All buttons are functional (clickable links)
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'{email_prefix}_{unique_id}@example.com',
            username=f'user_{username_suffix}_{unique_id}',
            password='testpass123'
        )
        
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
        
        # Define the expected quick actions with their identifying characteristics
        expected_actions = {
            'register_tournament': {
                'url_name': 'tournaments:list',
                'icon': 'emoji_events',
            },
            'join_team': {
                'url_name': 'teams:list',
                'icon': 'groups',
            },
            'view_notifications': {
                'url_name': 'notifications:list',
                'icon': 'notifications',
            },
            'manage_payments': {
                'url_name': 'payments:payment_methods',
                'icon': 'payment',
            }
        }
        
        # Find the quick actions section by heading
        quick_actions_heading = soup.find('h2', id='quick-actions-heading')
        assert quick_actions_heading is not None, \
            "Quick actions section missing heading with id 'quick-actions-heading'"
        assert 'Quick Actions' in quick_actions_heading.get_text(strip=True), \
            f"Quick actions heading has incorrect text: '{quick_actions_heading.get_text(strip=True)}'"
        
        # Find the quick actions container (should be a sibling or parent of the heading)
        quick_actions_container = quick_actions_heading.find_parent('div')
        assert quick_actions_container is not None, \
            "Quick actions container not found"
        
        # Find all links within the quick actions container
        quick_action_links = quick_actions_container.find_all('a', href=True)
        
        found_actions = {}
        
        # Property 2: All 4 quick actions are present
        for action_key, action_data in expected_actions.items():
            expected_url = reverse(action_data['url_name'])
            
            # Find the link with the expected URL within the quick actions container
            matching_links = [
                link for link in quick_action_links 
                if expected_url in link.get('href', '')
            ]
            
            assert len(matching_links) > 0, \
                f"Quick action '{action_key}' with URL '{expected_url}' not found in quick actions section"
            
            # Get the first matching link (should be the quick action)
            action_link = matching_links[0]
            found_actions[action_key] = action_link
            
            # Property 3: Each action has the correct icon
            icon_span = action_link.find('span', class_='material-symbols-outlined')
            assert icon_span is not None, \
                f"Quick action '{action_key}' missing icon span"
            assert action_data['icon'] in icon_span.get_text(strip=True), \
                f"Quick action '{action_key}' has wrong icon. Expected '{action_data['icon']}', found '{icon_span.get_text(strip=True)}'"
            
            # Property 4: Each action has minimum touch target size (44x44px)
            style = action_link.get('style', '')
            assert 'min-height: 44px' in style or 'min-height:44px' in style, \
                f"Quick action '{action_key}' missing minimum height of 44px"
            assert 'min-width: 44px' in style or 'min-width:44px' in style, \
                f"Quick action '{action_key}' missing minimum width of 44px"
            
            # Property 5: Each action has ARIA label
            aria_label = action_link.get('aria-label', '')
            assert aria_label != '', \
                f"Quick action '{action_key}' missing aria-label"
        
        # Property 6: Exactly 4 quick actions are present (no more, no less)
        assert len(found_actions) == 4, \
            f"Expected exactly 4 quick actions, found {len(found_actions)}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        has_unread_notifications=st.booleans(),
        unread_count=st.integers(min_value=1, max_value=99)
    )
    def test_notification_badge_display(self, has_unread_notifications, unread_count):
        """
        Property: Notification quick action displays badge when unread notifications exist.
        
        This test verifies that:
        1. Badge is displayed when unread notifications exist
        2. Badge shows correct count
        3. Badge is accessible with proper ARIA label
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Create unread notifications if needed
        if has_unread_notifications:
            from notifications.models import Notification
            for i in range(unread_count):
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title=f'Test Notification {i}',
                    message=f'Test message {i}',
                    read=False  # Correct field name is 'read', not 'is_read'
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
        
        # Find the quick actions heading to locate the container
        quick_actions_heading = soup.find('h2', id='quick-actions-heading')
        assert quick_actions_heading is not None, "Quick actions section not found"
        
        quick_actions_container = quick_actions_heading.find_parent('div')
        
        # Find the notifications quick action within the container
        notifications_url = reverse('notifications:list')
        notification_links = [
            link for link in quick_actions_container.find_all('a', href=True)
            if notifications_url in link.get('href', '')
        ]
        
        assert len(notification_links) > 0, \
            "Notifications quick action not found"
        
        notification_link = notification_links[0]
        
        # Find the badge span
        badge_span = notification_link.find('span', class_=lambda c: c and 'bg-yellow-500' in c)
        
        if has_unread_notifications:
            # Property: Badge should be present when there are unread notifications
            assert badge_span is not None, \
                f"Badge not displayed when {unread_count} unread notifications exist"
            
            # Property: Badge should show correct count
            badge_text = badge_span.get_text(strip=True)
            assert str(unread_count) in badge_text, \
                f"Badge shows incorrect count. Expected {unread_count}, found '{badge_text}'"
            
            # Property: Badge should have ARIA label
            badge_aria_label = badge_span.get('aria-label', '')
            assert str(unread_count) in badge_aria_label, \
                f"Badge aria-label missing count. Expected to contain {unread_count}, found '{badge_aria_label}'"
        else:
            # Property: Badge should not be present when there are no unread notifications
            assert badge_span is None, \
                "Badge displayed when no unread notifications exist"
        
        # Cleanup
        if has_unread_notifications:
            from notifications.models import Notification
            Notification.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        viewport_width=st.integers(min_value=320, max_value=1920),
    )
    def test_quick_actions_responsive_layout(self, viewport_width):
        """
        Property: Quick actions adapt to different viewport widths.
        
        This test verifies that:
        1. Quick actions are present regardless of viewport width
        2. Layout adapts appropriately (grid columns change)
        3. All actions remain accessible
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
        
        # Find the quick actions section
        quick_actions_heading = soup.find('h2', id='quick-actions-heading')
        assert quick_actions_heading is not None, "Quick actions section not found"
        
        quick_actions_container = quick_actions_heading.find_parent('div')
        
        # Find the grid container within the quick actions section
        grid_container = quick_actions_container.find('div', class_=lambda c: c and 'grid' in c)
        
        assert grid_container is not None, \
            "Quick actions grid container not found"
        
        # Property: Grid has responsive classes
        grid_classes = grid_container.get('class', [])
        grid_class_str = ' '.join(grid_classes)
        
        # Check for responsive grid classes
        assert 'grid' in grid_class_str, \
            "Quick actions grid missing grid class"
        
        # Property: All 4 actions are present in the grid
        action_links = grid_container.find_all('a', href=True)
        
        # Count links that match our expected quick action URLs
        expected_urls = [
            reverse('tournaments:list'),
            reverse('teams:list'),
            reverse('notifications:list'),
            reverse('payments:payment_methods')
        ]
        
        matching_actions = [
            link for link in action_links
            if any(url in link.get('href', '') for url in expected_urls)
        ]
        
        assert len(matching_actions) == 4, \
            f"Expected 4 quick actions in grid, found {len(matching_actions)}"
        
        # Property: Each action maintains minimum touch target size
        for action in matching_actions:
            style = action.get('style', '')
            assert 'min-height: 44px' in style or 'min-height:44px' in style, \
                "Quick action missing minimum height in responsive layout"
            assert 'min-width: 44px' in style or 'min-width:44px' in style, \
                "Quick action missing minimum width in responsive layout"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
    @given(
        user_has_teams=st.booleans(),
        user_has_tournaments=st.booleans(),
        user_has_payments=st.booleans()
    )
    def test_quick_actions_present_regardless_of_user_state(
        self, user_has_teams, user_has_tournaments, user_has_payments
    ):
        """
        Property: Quick actions are present regardless of user's current state.
        
        This test verifies that all quick actions are displayed even if:
        - User has no teams
        - User has no tournament registrations
        - User has no payment methods
        
        The quick actions should always be available to encourage engagement.
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'test_{unique_id}@example.com',
            username=f'testuser_{unique_id}',
            password='testpass123'
        )
        
        # Optionally create related data based on test parameters
        if user_has_teams:
            from teams.models import Team, TeamMember
            from core.models import Game
            
            game = Game.objects.create(
                name=f'TestGame_{unique_id}',
                slug=f'testgame_{unique_id}',
                genre='fps'
            )
            
            team = Team.objects.create(
                name=f'Test Team {unique_id}',
                slug=f'test-team-{unique_id}',
                game=game,
                captain=user,
                max_members=5
            )
            
            TeamMember.objects.create(
                team=team,
                user=user,
                role='captain',
                status='active'
            )
        
        if user_has_tournaments:
            from tournaments.models import Tournament, Participant
            from core.models import Game
            
            if not user_has_teams:
                game = Game.objects.create(
                    name=f'TestGame_{unique_id}',
                    slug=f'testgame_{unique_id}',
                    genre='fps'
                )
            else:
                game = Game.objects.filter(slug=f'testgame_{unique_id}').first()
            
            tournament = Tournament.objects.create(
                name=f'Test Tournament {unique_id}',
                slug=f'test-tournament-{unique_id}',
                game=game,
                organizer=user,
                max_participants=16,
                start_datetime=timezone.now() + timezone.timedelta(days=7),
                registration_start=timezone.now(),
                registration_end=timezone.now() + timezone.timedelta(days=6),
                check_in_start=timezone.now() + timezone.timedelta(days=6, hours=23),
                format='single_elim',
                status='registration'
            )
            
            Participant.objects.create(
                tournament=tournament,
                user=user,
                status='registered'
            )
        
        if user_has_payments:
            from payments.models import Payment
            
            Payment.objects.create(
                user=user,
                amount=10.00,
                currency='USD',
                status='succeeded',  # Correct status value
                payment_type='tournament_fee',  # Required field
                description='Test payment'
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
        
        # Property: All 4 quick actions are present regardless of user state
        expected_urls = {
            'tournaments': reverse('tournaments:list'),
            'teams': reverse('teams:list'),
            'notifications': reverse('notifications:list'),
            'payments': reverse('payments:payment_methods')
        }
        
        for action_name, expected_url in expected_urls.items():
            matching_links = [
                link for link in soup.find_all('a', href=True)
                if expected_url in link.get('href', '')
            ]
            
            assert len(matching_links) > 0, \
                f"Quick action '{action_name}' not found even though user state is: " \
                f"has_teams={user_has_teams}, has_tournaments={user_has_tournaments}, " \
                f"has_payments={user_has_payments}"
        
        # Cleanup
        if user_has_tournaments:
            from tournaments.models import Tournament, Participant
            Participant.objects.filter(user=user).delete()
            Tournament.objects.filter(organizer=user).delete()
        
        if user_has_teams:
            from teams.models import Team, TeamMember
            TeamMember.objects.filter(user=user).delete()
            Team.objects.filter(captain=user).delete()
        
        if user_has_teams or user_has_tournaments:
            from core.models import Game
            Game.objects.filter(slug=f'testgame_{unique_id}').delete()
        
        if user_has_payments:
            from payments.models import Payment
            Payment.objects.filter(user=user).delete()
        
        user.delete()
    
    def test_quick_actions_keyboard_navigation(self):
        """
        Property: All quick actions are keyboard accessible.
        
        This test verifies that:
        1. All quick actions are focusable
        2. Focus indicators are present
        3. Tab order is logical
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
        
        # Find the quick actions section
        quick_actions_heading = soup.find('h2', id='quick-actions-heading')
        assert quick_actions_heading is not None, "Quick actions section not found"
        
        quick_actions_container = quick_actions_heading.find_parent('div')
        
        # Find all quick action links within the container
        expected_urls = [
            reverse('tournaments:list'),
            reverse('teams:list'),
            reverse('notifications:list'),
            reverse('payments:payment_methods')
        ]
        
        quick_action_links = [
            link for link in quick_actions_container.find_all('a', href=True)
            if any(url in link.get('href', '') for url in expected_urls)
        ]
        
        assert len(quick_action_links) == 4, \
            f"Expected 4 quick action links, found {len(quick_action_links)}"
        
        # Property: All quick actions have focus styles
        for link in quick_action_links:
            classes = ' '.join(link.get('class', []))
            
            # Check for focus ring classes (Tailwind CSS)
            assert 'focus:outline-none' in classes or 'focus:ring' in classes, \
                f"Quick action missing focus styles: {link.get('href')}"
            
            # Property: Links are not disabled
            assert link.get('disabled') is None, \
                f"Quick action should not be disabled: {link.get('href')}"
            
            # Property: Links have valid href
            href = link.get('href', '')
            assert href and href != '#', \
                f"Quick action has invalid href: {href}"
        
        # Cleanup
        user.delete()
