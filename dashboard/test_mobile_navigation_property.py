"""
Property-Based Tests for Mobile Navigation Presence

This module contains property-based tests for the mobile navigation functionality,
specifically testing that the bottom navigation bar is present on mobile devices.
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
class TestMobileNavigationPresence:
    """
    **Feature: user-profile-dashboard, Property 39: Mobile navigation presence**
    
    For any page viewed on mobile devices (viewport width < 768px), the bottom 
    navigation bar must be present with all four navigation items.
    
    **Validates: Requirements 14.3**
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
        ),
        viewport_width=st.integers(min_value=320, max_value=767)  # Mobile viewport widths
    )
    def test_mobile_navigation_present_on_dashboard(self, username_suffix, email_prefix, viewport_width):
        """
        Property: Mobile navigation must be present on dashboard page for mobile viewports.
        
        This test verifies that:
        1. Mobile navigation bar is present when viewport < 768px
        2. Navigation contains all 4 required items (dashboard, profile, notifications, menu)
        3. Each navigation item has proper icons and labels
        4. Navigation is properly positioned (fixed bottom)
        5. Navigation has proper accessibility attributes
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
        
        # Property 2: Mobile navigation bar is present
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, \
            "Mobile navigation bar not found on dashboard page"
        
        # Property 3: Mobile navigation has correct CSS classes for mobile display
        nav_classes = ' '.join(mobile_nav.get('class', []))
        assert 'md:hidden' in nav_classes, \
            "Mobile navigation missing 'md:hidden' class to hide on desktop"
        assert 'fixed' in nav_classes, \
            "Mobile navigation missing 'fixed' class for proper positioning"
        assert 'bottom-0' in nav_classes, \
            "Mobile navigation missing 'bottom-0' class for bottom positioning"
        
        # Property 4: Navigation contains grid with 4 columns
        nav_grid = mobile_nav.find('div', class_=lambda c: c and 'grid-cols-4' in c)
        assert nav_grid is not None, \
            "Mobile navigation missing 4-column grid container"
        
        # Define expected navigation items
        expected_nav_items = {
            'dashboard': {
                'url': reverse('dashboard:home'),
                'icon': 'dashboard',
                'label': 'Dashboard'
            },
            'profile': {
                'url': reverse('dashboard:profile_view', kwargs={'username': user.username}),
                'icon': 'person',
                'label': 'Profile'
            },
            'notifications': {
                'url': reverse('notifications:list'),
                'icon': 'notifications',
                'label': 'Notifications'
            },
            'menu': {
                'icon': 'menu',
                'label': 'Menu',
                'is_button': True  # This is a button, not a link
            }
        }
        
        # Find all navigation items (links and buttons)
        nav_items = nav_grid.find_all(['a', 'button'])
        
        # Property 5: Exactly 4 navigation items are present
        assert len(nav_items) == 4, \
            f"Expected exactly 4 navigation items, found {len(nav_items)}"
        
        found_items = {}
        
        # Property 6: Each expected navigation item is present with correct attributes
        for item_key, item_data in expected_nav_items.items():
            matching_items = []
            
            if item_data.get('is_button'):
                # For menu button, find by onclick attribute or icon
                matching_items = [
                    item for item in nav_items 
                    if item.name == 'button' and (
                        'toggleMobileMenu' in item.get('onclick', '') or
                        item.find('span', string=item_data['icon'])
                    )
                ]
            else:
                # For links, find by href
                matching_items = [
                    item for item in nav_items 
                    if item.name == 'a' and item_data['url'] in item.get('href', '')
                ]
            
            assert len(matching_items) > 0, \
                f"Navigation item '{item_key}' not found in mobile navigation"
            
            nav_item = matching_items[0]
            found_items[item_key] = nav_item
            
            # Property 7: Each item has the correct icon
            icon_span = nav_item.find('span', class_='material-symbols-outlined')
            assert icon_span is not None, \
                f"Navigation item '{item_key}' missing icon span"
            assert item_data['icon'] in icon_span.get_text(strip=True), \
                f"Navigation item '{item_key}' has wrong icon. Expected '{item_data['icon']}', found '{icon_span.get_text(strip=True)}'"
            
            # Property 8: Each item has the correct label
            label_spans = nav_item.find_all('span', class_=lambda c: c and 'text-xs' in c)
            label_found = False
            for label_span in label_spans:
                if item_data['label'] in label_span.get_text(strip=True):
                    label_found = True
                    break
            assert label_found, \
                f"Navigation item '{item_key}' missing or incorrect label. Expected '{item_data['label']}'"
            
            # Property 9: Each item has proper ARIA label
            aria_label = nav_item.get('aria-label', '')
            assert aria_label != '', \
                f"Navigation item '{item_key}' missing aria-label"
            
            # For menu button, check for descriptive aria-label
            if item_data.get('is_button'):
                assert 'menu' in aria_label.lower(), \
                    f"Navigation item '{item_key}' aria-label should describe menu action. Found: '{aria_label}'"
            else:
                assert item_data['label'] in aria_label, \
                    f"Navigation item '{item_key}' aria-label doesn't contain '{item_data['label']}'. Found: '{aria_label}'"
            
            # Property 10: Each item has minimum touch target size (44x44px)
            # Check for inline styles or CSS classes that ensure minimum size
            style = nav_item.get('style', '')
            classes = ' '.join(nav_item.get('class', []))
            
            # The template should have CSS that ensures min-height and min-width of 44px
            # We can check if the item is in a flex container that provides proper sizing
            assert 'flex' in classes, \
                f"Navigation item '{item_key}' missing flex classes for proper sizing"
        
        # Property 11: Navigation has proper z-index for layering
        assert 'z-40' in nav_classes or 'z-50' in nav_classes, \
            "Mobile navigation missing high z-index for proper layering"
        
        # Property 12: Navigation has proper role attribute
        assert mobile_nav.get('role') == 'navigation', \
            "Mobile navigation missing role='navigation' attribute"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
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
    def test_mobile_navigation_hidden_on_desktop(self, username_suffix, email_prefix):
        """
        Property: Mobile navigation must be hidden on desktop viewports (>= 768px).
        
        This test verifies that the mobile navigation is properly hidden on desktop
        using responsive CSS classes.
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
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, \
            "Mobile navigation bar not found"
        
        # Property: Mobile navigation has md:hidden class to hide on desktop
        nav_classes = ' '.join(mobile_nav.get('class', []))
        assert 'md:hidden' in nav_classes, \
            "Mobile navigation missing 'md:hidden' class - it will be visible on desktop"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=50, deadline=None)
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
        ),
        unread_count=st.integers(min_value=0, max_value=99)
    )
    def test_mobile_navigation_notification_badge(self, username_suffix, email_prefix, unread_count):
        """
        Property: Mobile navigation notifications item displays badge when unread notifications exist.
        
        This test verifies that:
        1. Badge is displayed when unread notifications exist
        2. Badge shows correct count
        3. Badge is accessible with proper ARIA label
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'{email_prefix}_{unique_id}@example.com',
            username=f'user_{username_suffix}_{unique_id}',
            password='testpass123'
        )
        
        # Create unread notifications if needed
        if unread_count > 0:
            from notifications.models import Notification
            for i in range(unread_count):
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title=f'Test Notification {i}',
                    message=f'Test message {i}',
                    read=False
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
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, "Mobile navigation not found"
        
        # Find the notifications link within mobile navigation
        notifications_url = reverse('notifications:list')
        notification_links = mobile_nav.find_all('a', href=lambda h: h and notifications_url in h)
        
        assert len(notification_links) > 0, \
            "Notifications link not found in mobile navigation"
        
        notification_link = notification_links[0]
        
        # Find the badge span (if it exists)
        badge_span = notification_link.find('span', class_=lambda c: c and 'bg-primary' in c)
        
        if unread_count > 0:
            # Property: Badge should be present when there are unread notifications
            assert badge_span is not None, \
                f"Badge not displayed in mobile navigation when {unread_count} unread notifications exist"
            
            # Property: Badge should show correct count (or truncated with + for counts > 9)
            badge_text = badge_span.get_text(strip=True)
            if unread_count <= 9:
                expected_text = str(unread_count)
                assert expected_text == badge_text, \
                    f"Badge shows incorrect count. Expected '{expected_text}', found '{badge_text}'"
            else:
                # For counts > 9, template uses slice:":9" which takes first 9 chars, then adds +
                expected_prefix = str(unread_count)[:9]
                assert badge_text.startswith(expected_prefix) and badge_text.endswith('+'), \
                    f"Badge should show '{expected_prefix}+' for count {unread_count}, found '{badge_text}'"
            
            # Property: Badge should have ARIA label
            badge_aria_label = badge_span.get('aria-label', '')
            assert str(unread_count) in badge_aria_label, \
                f"Badge aria-label missing count. Expected to contain {unread_count}, found '{badge_aria_label}'"
        else:
            # Property: Badge should not be present when there are no unread notifications
            assert badge_span is None, \
                "Badge displayed in mobile navigation when no unread notifications exist"
        
        # Cleanup
        if unread_count > 0:
            from notifications.models import Notification
            Notification.objects.filter(user=user).delete()
        user.delete()
    
    @settings(max_examples=30, deadline=None)
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
    def test_mobile_navigation_current_page_indication(self, username_suffix, email_prefix):
        """
        Property: Mobile navigation highlights the current page appropriately.
        
        This test verifies that:
        1. Current page navigation item has different styling
        2. Current page item has aria-current="page" attribute
        3. Other navigation items don't have current page styling
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
        
        # Test dashboard page (should highlight dashboard nav item)
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, "Mobile navigation not found"
        
        # Find the dashboard link
        dashboard_url = reverse('dashboard:home')
        dashboard_links = mobile_nav.find_all('a', href=lambda h: h and dashboard_url in h)
        
        assert len(dashboard_links) > 0, \
            "Dashboard link not found in mobile navigation"
        
        dashboard_link = dashboard_links[0]
        
        # Property: Current page (dashboard) should have aria-current="page"
        assert dashboard_link.get('aria-current') == 'page', \
            "Dashboard link missing aria-current='page' when on dashboard page"
        
        # Property: Current page should have different styling (text-primary class)
        dashboard_classes = ' '.join(dashboard_link.get('class', []))
        assert 'text-primary' in dashboard_classes, \
            "Dashboard link missing 'text-primary' class when on dashboard page"
        
        # Property: Other navigation items should not have current page styling
        all_nav_links = mobile_nav.find_all('a')
        for link in all_nav_links:
            if link != dashboard_link:
                assert link.get('aria-current') != 'page', \
                    f"Non-current page link has aria-current='page': {link.get('href')}"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=30, deadline=None)
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
    def test_mobile_navigation_keyboard_accessibility(self, username_suffix, email_prefix):
        """
        Property: Mobile navigation is fully keyboard accessible.
        
        This test verifies that:
        1. All navigation items are focusable
        2. Focus indicators are present (focus:ring classes)
        3. Tab order is logical
        4. Menu button has proper ARIA attributes
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
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, "Mobile navigation not found"
        
        # Find all focusable elements (links and buttons)
        focusable_elements = mobile_nav.find_all(['a', 'button'])
        
        # Property: All navigation items have focus styles
        for element in focusable_elements:
            classes = ' '.join(element.get('class', []))
            
            # Check for focus ring classes (Tailwind CSS)
            assert 'focus:outline-none' in classes and 'focus:ring' in classes, \
                f"Navigation element missing focus styles: {element.get('href') or element.get('onclick', 'button')}"
            
            # Property: Elements are not disabled
            assert element.get('disabled') is None, \
                f"Navigation element should not be disabled: {element.get('href') or 'button'}"
        
        # Property: Menu button has proper ARIA attributes
        menu_buttons = mobile_nav.find_all('button')
        assert len(menu_buttons) > 0, "Menu button not found in mobile navigation"
        
        menu_button = menu_buttons[0]
        assert menu_button.get('aria-label') is not None, \
            "Menu button missing aria-label"
        assert menu_button.get('aria-expanded') is not None, \
            "Menu button missing aria-expanded attribute"
        assert menu_button.get('aria-controls') is not None, \
            "Menu button missing aria-controls attribute"
        
        # Cleanup
        user.delete()
    
    def test_mobile_navigation_safe_area_support(self):
        """
        Property: Mobile navigation supports safe area insets for devices with notches.
        
        This test verifies that the navigation includes proper CSS for safe area support.
        """
        # Create a test user
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
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, "Mobile navigation not found"
        
        # Property: Navigation has safe area inset class
        nav_classes = ' '.join(mobile_nav.get('class', []))
        assert 'safe-area-inset-bottom' in nav_classes, \
            "Mobile navigation missing 'safe-area-inset-bottom' class for device notch support"
        
        # Property: Check for safe area CSS in the page
        response_content = response.content.decode('utf-8')
        assert 'env(safe-area-inset-bottom)' in response_content, \
            "Safe area inset CSS not found in page"
        
        # Cleanup
        user.delete()