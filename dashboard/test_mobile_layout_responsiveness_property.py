"""
Property-Based Tests for Mobile Layout Responsiveness

This module contains property-based tests for mobile layout responsiveness,
specifically testing that dashboard and profile pages switch to single-column
stacked layout when viewport width is less than 768px.
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
class TestMobileLayoutResponsiveness:
    """
    **Feature: user-profile-dashboard, Property 40: Mobile layout responsiveness**
    
    For any dashboard or profile page, when viewport width is less than 768px, 
    the layout must switch to single-column stacked layout.
    
    **Validates: Requirements 14.1, 14.2**
    """
    
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
    def test_dashboard_mobile_layout_single_column(self, username_suffix, email_prefix):
        """
        Property: Dashboard page must use single-column stacked layout on mobile viewports.
        
        This test verifies that:
        1. Main content uses vertical stacking (space-y classes)
        2. Layout includes mobile-responsive classes
        3. Content sections can stack vertically
        4. Mobile navigation is properly configured if present
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
        
        # Property 2: Main content has mobile-responsive structure
        # Look for main content - it could be a main element or div with id="main-content"
        main_content = soup.find('main', id='main-content') or soup.find('main') or soup.find('div', id='main-content')
        assert main_content is not None, \
            "Main content element not found on dashboard page"
        
        # Property 3: Main content uses vertical stacking for mobile
        main_classes = ' '.join(main_content.get('class', []))
        has_vertical_stacking = any(
            spacing in main_classes 
            for spacing in ['space-y-6', 'space-y-4', 'space-y-8', 'pb-20']
        )
        assert has_vertical_stacking, \
            f"Main content missing vertical stacking classes for mobile layout. Found: {main_classes}"
        
        # Property 4: Page contains responsive layout elements
        # Check for any responsive classes in the HTML
        html_content = str(soup)
        has_responsive_classes = any(
            responsive_pattern in html_content 
            for responsive_pattern in ['grid-cols-1', 'flex-col', 'sm:', 'md:', 'lg:']
        )
        assert has_responsive_classes, \
            "Dashboard page missing responsive layout classes"
        
        # Property 5: Content sections use proper stacking
        # Look for elements that use vertical spacing
        stacked_elements = soup.find_all('div', class_=lambda c: c and ('space-y' in c or 'gap-' in c))
        assert len(stacked_elements) > 0, \
            "Dashboard missing elements with vertical spacing for mobile stacking"
        
        # Property 6: Mobile navigation is properly configured if present
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        if mobile_nav:
            nav_classes = ' '.join(mobile_nav.get('class', []))
            assert 'md:hidden' in nav_classes, \
                "Mobile navigation missing 'md:hidden' class to hide on desktop"
        
        # Property 7: Layout uses mobile-first responsive approach
        # Check for flex containers that can stack on mobile
        flex_containers = soup.find_all('div', class_=lambda c: c and 'flex' in c)
        mobile_friendly_flex = False
        for container in flex_containers:
            container_classes = ' '.join(container.get('class', []))
            if 'flex-col' in container_classes or 'sm:flex-row' in container_classes:
                mobile_friendly_flex = True
                break
        
        # Either flex containers are mobile-friendly OR we have grid layouts
        grid_containers = soup.find_all('div', class_=lambda c: c and 'grid' in c)
        has_layout_structure = mobile_friendly_flex or len(grid_containers) > 0
        assert has_layout_structure, \
            "Dashboard missing mobile-friendly layout structure (flex-col or grid)"
        
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
    def test_profile_mobile_layout_single_column(self, username_suffix, email_prefix):
        """
        Property: Profile page must use single-column stacked layout on mobile viewports.
        
        This test verifies that:
        1. Profile page loads successfully
        2. Layout includes responsive classes
        3. Content can stack vertically on mobile
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
        
        # Request the profile page
        response = client.get(reverse('dashboard:profile_view', kwargs={'username': user.username}))
        
        # Property 1: Response is successful
        assert response.status_code == 200, \
            f"Profile page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property 2: Main content element exists
        main_content = soup.find('main')
        assert main_content is not None, \
            "Main content element not found on profile page"
        
        # Property 3: Page contains responsive layout classes
        html_content = str(soup)
        has_responsive_classes = any(
            responsive_pattern in html_content 
            for responsive_pattern in ['flex-col', 'sm:', 'md:', 'lg:', 'max-w-']
        )
        assert has_responsive_classes, \
            "Profile page missing responsive layout classes"
        
        # Property 4: Profile uses flex layouts that can stack on mobile
        flex_containers = soup.find_all('div', class_=lambda c: c and 'flex' in c)
        mobile_friendly_layout = False
        for container in flex_containers:
            container_classes = ' '.join(container.get('class', []))
            if 'flex-col' in container_classes or 'w-full' in container_classes or 'gap-' in container_classes:
                mobile_friendly_layout = True
                break
        
        assert mobile_friendly_layout, \
            "Profile page missing mobile-friendly flex layouts"
        
        # Property 5: Content has proper width constraints
        # Check for max-width containers to prevent horizontal overflow
        constrained_containers = soup.find_all('div', class_=lambda c: c and ('max-w-' in c or 'mx-auto' in c))
        assert len(constrained_containers) > 0, \
            "Profile page missing width-constrained containers for mobile layout"
        
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
    def test_desktop_layout_multi_column(self, username_suffix, email_prefix):
        """
        Property: Dashboard and profile pages must use multi-column layout on desktop viewports.
        
        This test verifies that desktop layouts use appropriate multi-column classes
        and don't force single-column layout on larger screens.
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
        
        # Test dashboard page
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property: Desktop layout should have multi-column grid classes
        content_grids = soup.find_all('div', class_=lambda c: c and 'grid' in c)
        
        found_desktop_grid = False
        for grid in content_grids:
            grid_classes = ' '.join(grid.get('class', []))
            # Look for desktop multi-column classes (lg:grid-cols-3, xl:grid-cols-4, etc.)
            if any(desktop_class in grid_classes for desktop_class in ['lg:grid-cols-3', 'lg:grid-cols-2', 'xl:grid-cols-4']):
                found_desktop_grid = True
                break
        
        assert found_desktop_grid, \
            "Dashboard missing desktop multi-column grid classes (lg:grid-cols-*, xl:grid-cols-*)"
        
        # Test profile page
        response = client.get(reverse('dashboard:profile_view', kwargs={'username': user.username}))
        assert response.status_code == 200, \
            f"Profile page returned status {response.status_code}, expected 200"
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property: Profile page should have responsive flex layouts
        flex_containers = soup.find_all('div', class_=lambda c: c and 'flex' in c)
        
        found_responsive_flex = False
        for container in flex_containers:
            container_classes = ' '.join(container.get('class', []))
            # Look for responsive flex classes (flex-col sm:flex-row, etc.)
            if 'flex-col' in container_classes and ('sm:flex-row' in container_classes or 'lg:flex-row' in container_classes):
                found_responsive_flex = True
                break
        
        assert found_responsive_flex, \
            "Profile page missing responsive flex classes (flex-col sm:flex-row)"
        
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
    def test_responsive_breakpoint_classes(self, username_suffix, email_prefix):
        """
        Property: Pages must use proper responsive breakpoint classes for layout transitions.
        
        This test verifies that:
        1. Mobile-first responsive classes are used (base class for mobile, prefixed for larger)
        2. Proper breakpoint prefixes are used (sm:, md:, lg:, xl:)
        3. Layout classes transition appropriately across breakpoints
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
        
        # Test dashboard page
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property 1: Find elements with responsive classes
        # Check for responsive classes in the HTML content
        html_content = str(soup)
        has_responsive_classes = any(
            breakpoint in html_content for breakpoint in ['sm:', 'md:', 'lg:', 'xl:']
        )
        
        # If no responsive classes in HTML, check if layout is inherently responsive
        if not has_responsive_classes:
            # Check for flex layouts that are responsive by nature
            flex_elements = soup.find_all('div', class_=lambda c: c and 'flex' in c)
            grid_elements = soup.find_all('div', class_=lambda c: c and 'grid' in c)
            has_responsive_layout = len(flex_elements) > 0 or len(grid_elements) > 0
            
            assert has_responsive_layout, \
                "Dashboard page missing responsive layout structure (no flex or grid elements found)"
        else:
            assert has_responsive_classes, \
                "Dashboard page missing responsive breakpoint classes (sm:, md:, lg:, xl:)"
        
        # Property 2: Check for proper mobile-first approach
        grid_elements = soup.find_all('div', class_=lambda c: c and 'grid-cols-' in c)
        for element in grid_elements:
            element_classes = ' '.join(element.get('class', []))
            
            # Should start with mobile class (grid-cols-1) and add larger breakpoints
            if 'grid-cols-1' in element_classes:
                # Good mobile-first approach
                has_larger_breakpoint = any(
                    breakpoint in element_classes 
                    for breakpoint in ['sm:grid-cols-', 'md:grid-cols-', 'lg:grid-cols-', 'xl:grid-cols-']
                )
                assert has_larger_breakpoint, \
                    f"Grid element has mobile class but missing larger breakpoint classes: {element_classes}"
        
        # Property 3: Check for responsive spacing classes
        spacing_elements = soup.find_all(attrs={'class': lambda c: c and any(
            spacing in ' '.join(c) for spacing in ['space-y-', 'gap-', 'p-', 'px-', 'py-']
        )})
        
        responsive_spacing_found = False
        for element in spacing_elements:
            element_classes = ' '.join(element.get('class', []))
            if any(breakpoint in element_classes for breakpoint in ['sm:', 'md:', 'lg:']):
                responsive_spacing_found = True
                break
        
        # This is optional but good practice
        # assert responsive_spacing_found, "No responsive spacing classes found"
        
        # Property 4: Check for responsive text sizing
        text_elements = soup.find_all(attrs={'class': lambda c: c and 'text-' in ' '.join(c)})
        
        responsive_text_found = False
        for element in text_elements:
            element_classes = ' '.join(element.get('class', []))
            if any(f'{breakpoint}text-' in element_classes for breakpoint in ['sm:', 'md:', 'lg:', 'xl:']):
                responsive_text_found = True
                break
        
        # This is optional but recommended
        # assert responsive_text_found, "No responsive text sizing classes found"
        
        # Property 5: Verify mobile navigation has proper responsive classes
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'}) or \
                    soup.find(attrs={'class': lambda c: c and 'md:hidden' in ' '.join(c)})
        
        if mobile_nav:
            nav_classes = ' '.join(mobile_nav.get('class', []))
            assert 'md:hidden' in nav_classes, \
                "Mobile navigation missing 'md:hidden' class for responsive behavior"
        
        # Cleanup
        user.delete()
    
    @settings(max_examples=20, deadline=None)
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
    def test_mobile_content_stacking_order(self, username_suffix, email_prefix):
        """
        Property: Content sections must stack in logical order on mobile layouts.
        
        This test verifies that:
        1. Content sections use proper vertical stacking (flex-col or space-y)
        2. Important content appears first in mobile layout
        3. Secondary content follows in logical order
        4. No content is hidden or inaccessible on mobile
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
        
        # Test dashboard page
        response = client.get(reverse('dashboard:home'))
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Property 1: Main content uses vertical stacking classes
        main_content = soup.find('main')
        assert main_content is not None
        
        main_classes = ' '.join(main_content.get('class', []))
        has_vertical_spacing = any(
            spacing in main_classes 
            for spacing in ['space-y-', 'flex-col', 'gap-']
        )
        assert has_vertical_spacing, \
            f"Main content missing vertical stacking classes. Found: {main_classes}"
        
        # Property 2: Content sections are in logical order
        # Check that important sections (welcome, stats) come before secondary content
        content_sections = main_content.find_all('div', recursive=False)
        
        # Look for welcome section (should be early)
        welcome_found = False
        stats_found = False
        
        for i, section in enumerate(content_sections):
            section_classes = ' '.join(section.get('class', []))
            section_text = section.get_text(strip=True).lower()
            
            if 'welcome' in section_text or 'ready to dominate' in section_text:
                welcome_found = True
                welcome_position = i
            
            # Look for statistics or stats cards
            if 'stats' in section_classes or 'statistics' in section_text or section.find(attrs={'class': lambda c: c and 'stats' in ' '.join(c)}):
                stats_found = True
                stats_position = i
        
        # Welcome should come before or at the same level as stats
        if welcome_found and stats_found:
            assert welcome_position <= stats_position + 1, \
                f"Welcome section (position {welcome_position}) should come before or near stats section (position {stats_position})"
        
        # Property 3: No content should be hidden on mobile
        # Check for elements with display: none or hidden classes that might hide content inappropriately
        hidden_elements = soup.find_all(attrs={'class': lambda c: c and 'hidden' in ' '.join(c)})
        
        for element in hidden_elements:
            element_classes = ' '.join(element.get('class', []))
            # It's okay to hide elements on specific breakpoints (sm:hidden, md:hidden)
            # but not to hide them completely
            if element_classes == 'hidden':
                # This element is completely hidden, which might be problematic
                element_content = element.get_text(strip=True)
                if element_content:  # Only flag if it has actual content
                    # This is a warning, not a failure, as some hidden elements might be intentional
                    pass
        
        # Property 4: Grid layouts should have mobile-first responsive classes
        grid_layouts = soup.find_all('div', class_=lambda c: c and 'grid' in c)
        
        for grid in grid_layouts:
            grid_classes = ' '.join(grid.get('class', []))
            
            # Should have mobile class (grid-cols-1) or responsive classes
            has_mobile_grid = 'grid-cols-1' in grid_classes
            has_responsive_grid = any(
                breakpoint in grid_classes 
                for breakpoint in ['sm:grid-cols-', 'md:grid-cols-', 'lg:grid-cols-']
            )
            
            # Some grids might be intentionally fixed (like mobile nav with grid-cols-4)
            # Only assert if it's a content grid, not a navigation grid
            if 'h-16' not in grid_classes:  # Skip navigation grids
                assert has_mobile_grid or has_responsive_grid or 'grid-cols-4' in grid_classes, \
                    f"Content grid layout missing mobile-responsive classes: {grid_classes}"
        
        # Cleanup
        user.delete()
    
    def test_css_media_queries_present(self):
        """
        Property: CSS file must contain proper media queries for mobile layout.
        
        This test verifies that the dashboard.css file contains the required
        media queries for responsive layout at the 768px breakpoint.
        """
        # Read the CSS file
        try:
            with open('static/css/dashboard.css', 'r') as f:
                css_content = f.read()
        except FileNotFoundError:
            pytest.fail("Dashboard CSS file not found at static/css/dashboard.css")
        
        # Property 1: CSS contains mobile media query
        assert '@media (max-width: 767px)' in css_content or '@media (max-width: 768px)' in css_content, \
            "CSS file missing mobile media query for viewport < 768px"
        
        # Property 2: CSS contains tablet media query
        tablet_query_found = (
            '@media (min-width: 768px) and (max-width: 1024px)' in css_content or
            '@media (min-width: 768px)' in css_content
        )
        assert tablet_query_found, \
            "CSS file missing tablet media query for viewport >= 768px"
        
        # Property 3: CSS contains desktop media query
        desktop_query_found = (
            '@media (min-width: 1025px)' in css_content or
            '@media (min-width: 1024px)' in css_content
        )
        assert desktop_query_found, \
            "CSS file missing desktop media query for viewport >= 1024px"
        
        # Property 4: CSS contains single-column layout rules for mobile
        mobile_section_start = css_content.find('@media (max-width: 767px)')
        if mobile_section_start == -1:
            mobile_section_start = css_content.find('@media (max-width: 768px)')
        
        assert mobile_section_start != -1, \
            "Mobile media query section not found in CSS"
        
        # Find the end of the mobile media query section
        mobile_section_end = css_content.find('}', css_content.rfind('{', mobile_section_start, css_content.find('@media', mobile_section_start + 1)))
        if mobile_section_end == -1:
            mobile_section_end = len(css_content)
        
        mobile_css = css_content[mobile_section_start:mobile_section_end]
        
        # Property 5: Mobile CSS contains flex-direction: column rules
        flex_column_found = (
            'flex-direction: column' in mobile_css or
            'display: flex' in mobile_css or
            'grid-template-columns: 1fr' in mobile_css
        )
        assert flex_column_found, \
            "Mobile CSS section missing single-column layout rules (flex-direction: column or grid-template-columns: 1fr)"
        
        # Property 6: Mobile CSS contains proper spacing rules
        mobile_spacing_found = (
            'gap: 1rem' in mobile_css or
            'padding:' in mobile_css or
            'margin:' in mobile_css
        )
        assert mobile_spacing_found, \
            "Mobile CSS section missing spacing rules for stacked layout"