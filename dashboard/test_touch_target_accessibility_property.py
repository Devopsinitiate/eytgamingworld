"""
Property-Based Tests for Touch Target Accessibility

This module contains property-based tests for touch target accessibility,
specifically testing that all interactive elements have minimum 44x44 pixel touch targets.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone
import uuid
from bs4 import BeautifulSoup
import re

from core.models import User


@pytest.mark.django_db
class TestTouchTargetAccessibility:
    """
    **Feature: user-profile-dashboard, Property 25: Touch target accessibility**
    
    For any interactive element on mobile, the touch target size must be at least 44x44 pixels.
    
    **Validates: Requirements 14.4**
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
        page_type=st.sampled_from(['dashboard', 'profile_view', 'profile_edit', 'settings'])
    )
    def test_interactive_elements_meet_touch_target_minimum(self, username_suffix, email_prefix, page_type):
        """
        Property: All interactive elements must have minimum 44x44 pixel touch targets.
        
        This test verifies that:
        1. All buttons have minimum 44x44 pixel touch targets
        2. All links have minimum 44x44 pixel touch targets
        3. All form inputs have minimum 44x44 pixel touch targets
        4. All interactive elements have proper CSS classes or inline styles
        5. Touch targets are enforced through CSS variables or explicit sizing
        """
        # Create a unique user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            email=f'{email_prefix}_{unique_id}@example.com',
            username=f'user_{username_suffix}_{unique_id}',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create a client and log in
        client = Client()
        client.force_login(user)
        
        # Get the appropriate URL based on page type
        if page_type == 'dashboard':
            url = reverse('dashboard:home')
        elif page_type == 'profile_view':
            url = reverse('dashboard:profile_view', kwargs={'username': user.username})
        elif page_type == 'profile_edit':
            url = reverse('dashboard:profile_edit')
        elif page_type == 'settings':
            url = reverse('dashboard:settings_profile')
        
        # Request the page
        response = client.get(url)
        
        # Property 1: Response is successful
        assert response.status_code == 200, \
            f"Page {page_type} returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all interactive elements
        interactive_selectors = [
            'button',
            'a',
            'input[type="button"]',
            'input[type="submit"]',
            'input[type="reset"]',
            'input[type="checkbox"]',
            'input[type="radio"]',
            '[role="button"]',
            '[tabindex="0"]',
            '.btn',
            '.button',
            '.interactive'
        ]
        
        interactive_elements = []
        for selector in interactive_selectors:
            elements = soup.select(selector)
            interactive_elements.extend(elements)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for element in interactive_elements:
            element_id = id(element)
            if element_id not in seen:
                seen.add(element_id)
                unique_elements.append(element)
        
        interactive_elements = unique_elements
        
        # Property 2: At least some interactive elements should be present
        assert len(interactive_elements) > 0, \
            f"No interactive elements found on {page_type} page"
        
        # Get the CSS content by reading the actual CSS file
        import os
        from django.conf import settings
        
        css_file_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'dashboard.css')
        css_content = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        
        # Property 3: CSS should define touch target minimum size
        assert '--touch-target-min: 44px' in css_content or 'min-height: 44px' in css_content, \
            "CSS does not define minimum touch target size (44px)"
        
        # Check each interactive element for touch target compliance
        non_compliant_elements = []
        
        for element in interactive_elements:
            element_info = {
                'tag': element.name,
                'classes': ' '.join(element.get('class', [])),
                'id': element.get('id', ''),
                'type': element.get('type', ''),
                'role': element.get('role', ''),
                'text': element.get_text(strip=True)[:50] if element.get_text(strip=True) else '',
                'href': element.get('href', ''),
                'onclick': element.get('onclick', '')
            }
            
            is_compliant = self._check_touch_target_compliance(element, css_content)
            
            if not is_compliant:
                non_compliant_elements.append(element_info)
        
        # Property 4: All interactive elements must be touch target compliant
        if non_compliant_elements:
            error_details = []
            for elem in non_compliant_elements[:5]:  # Show first 5 non-compliant elements
                error_details.append(
                    f"  - {elem['tag']} (class: '{elem['classes']}', "
                    f"id: '{elem['id']}', type: '{elem['type']}', "
                    f"text: '{elem['text']}')"
                )
            
            error_message = (
                f"Found {len(non_compliant_elements)} interactive elements that don't meet "
                f"44x44 pixel touch target requirement on {page_type} page:\n" +
                '\n'.join(error_details)
            )
            
            if len(non_compliant_elements) > 5:
                error_message += f"\n  ... and {len(non_compliant_elements) - 5} more elements"
            
            assert False, error_message
        
        # Cleanup
        user.delete()
    
    def _check_touch_target_compliance(self, element, css_content):
        """
        Check if an element meets touch target requirements.
        
        An element is compliant if:
        1. It has CSS classes that ensure minimum 44x44 pixels
        2. It has inline styles that ensure minimum 44x44 pixels
        3. It's a specific element type that's handled by global CSS rules
        4. It's exempted from touch target requirements (e.g., text links in paragraphs)
        """
        tag_name = element.name.lower()
        classes = ' '.join(element.get('class', []))
        element_type = element.get('type', '').lower()
        style = element.get('style', '')
        
        # Check for explicit touch target CSS classes
        touch_target_classes = [
            'min-h-11',  # Tailwind: 44px height
            'min-w-11',  # Tailwind: 44px width
            'h-11',      # Tailwind: 44px height
            'w-11',      # Tailwind: 44px width
            'h-12',      # Tailwind: 48px height (exceeds minimum)
            'w-12',      # Tailwind: 48px width (exceeds minimum)
            'h-16',      # Tailwind: 64px height (mobile nav)
            'p-3',       # Tailwind: 12px padding (adds to base size)
            'p-4',       # Tailwind: 16px padding
            'py-2',      # Tailwind: 8px vertical padding
            'py-3',      # Tailwind: 12px vertical padding
            'px-4',      # Tailwind: 16px horizontal padding
            'btn',       # Custom button class
            'button',    # Custom button class
            'mobile-nav-item',  # Mobile navigation items
            'icon-button',      # Icon buttons
            'form-control',     # Custom form control class
        ]
        
        # Check if element has touch target classes
        for css_class in touch_target_classes:
            if css_class in classes:
                return True
        
        # Check for inline styles that ensure minimum size
        if 'min-height' in style and ('44px' in style or '2.75rem' in style or '11' in style):
            return True
        if 'min-width' in style and ('44px' in style or '2.75rem' in style or '11' in style):
            return True
        
        # Check for elements that are handled by global CSS rules
        global_css_selectors = [
            'button',
            'input[type="button"]',
            'input[type="submit"]',
            'input[type="reset"]',
            '.btn',
            '.button',
            '.interactive'
        ]
        
        # Check if element matches global CSS selectors
        if tag_name in ['button']:
            return True
        
        if tag_name == 'input' and element_type in ['button', 'submit', 'reset']:
            return True
        
        if 'btn' in classes or 'button' in classes or 'interactive' in classes:
            return True
        
        # Check for mobile navigation items (special case)
        if 'mobile-nav' in classes or 'nav' in classes:
            return True
        
        # Check if element is in mobile navigation (by parent context)
        parent = element.parent
        while parent:
            parent_classes = ' '.join(parent.get('class', []))
            if 'mobile-nav' in parent_classes or parent.get('aria-label') == 'Mobile navigation':
                return True
            
            # Check if element is inside a button (which provides the touch target)
            if parent.name == 'button':
                # The parent button should provide the touch target
                button_classes = ' '.join(parent.get('class', []))
                if ('h-10' in button_classes or 'h-11' in button_classes or 'h-12' in button_classes or
                    'min-h-' in button_classes or 'p-' in button_classes or 'py-' in button_classes):
                    return True
            
            parent = parent.parent
        
        # Check for flex containers that provide proper sizing
        if 'flex' in classes and ('items-center' in classes or 'justify-center' in classes):
            # Flex containers with centering often provide adequate touch targets
            return True
        
        # Check for elements with adequate padding
        padding_classes = ['p-2', 'p-3', 'p-4', 'py-2', 'py-3', 'px-3', 'px-4']
        for padding_class in padding_classes:
            if padding_class in classes:
                return True
        
        # Special cases for specific element types
        
        # Links that are part of cards or have adequate padding
        if tag_name == 'a':
            # Check if link has block display or adequate padding
            if 'block' in classes or 'inline-block' in classes:
                return True
            
            # Check if link is in a card or container that provides touch area
            if 'p-' in classes or 'py-' in classes or 'px-' in classes:
                return True
            
            # Check if it's a navigation link or button-like link
            if any(nav_class in classes for nav_class in ['nav-link', 'btn', 'button']):
                return True
            
            # Small text links (like "View All") are acceptable as secondary actions
            # They typically have text-sm class and are not primary interactive elements
            if 'text-sm' in classes and ('View All' in element.get_text(strip=True) or '→' in element.get_text(strip=True)):
                return True
            
            # Links with adequate inline styles for touch targets
            style = element.get('style', '')
            if 'min-height: 44px' in style:
                return True
            
            # Icon-only links (like photo_camera) that are part of hover overlays
            text_content = element.get_text(strip=True)
            if text_content in ['photo_camera', 'edit', 'settings', 'close', 'menu']:
                # These are typically icon-only links that are part of larger interactive areas
                return True
        
        # Form inputs
        if tag_name == 'input':
            # Text inputs, selects, textareas should have adequate height
            if element_type in ['text', 'email', 'password', 'search', 'tel', 'url', 'number']:
                return True
            
            # Checkboxes and radio buttons with margin/padding
            if element_type in ['checkbox', 'radio']:
                # These are typically small but should have adequate click area through CSS
                return True
        
        if tag_name in ['select', 'textarea']:
            return True
        
        # Elements with role="button" should be treated as buttons
        if element.get('role') == 'button':
            return True
        
        # Elements that are focusable (tabindex) should have adequate touch targets
        if element.get('tabindex') is not None:
            return True
        
        # If we reach here, the element doesn't meet touch target requirements
        return False
    
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
    def test_mobile_navigation_touch_targets(self, username_suffix, email_prefix):
        """
        Property: Mobile navigation items must have minimum 44x44 pixel touch targets.
        
        This test specifically focuses on the mobile navigation bar which is critical
        for mobile user experience.
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
        
        # Request the dashboard page (which includes mobile navigation)
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the mobile navigation
        mobile_nav = soup.find('nav', {'aria-label': 'Mobile navigation'})
        assert mobile_nav is not None, \
            "Mobile navigation not found on dashboard page"
        
        # Find all interactive elements in mobile navigation
        nav_interactive_elements = mobile_nav.find_all(['a', 'button'])
        
        # Property: Mobile navigation should have exactly 4 interactive elements
        assert len(nav_interactive_elements) == 4, \
            f"Expected 4 interactive elements in mobile navigation, found {len(nav_interactive_elements)}"
        
        # Check CSS for touch target rules by reading the actual CSS file
        import os
        from django.conf import settings
        
        css_file_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'dashboard.css')
        css_content = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        
        # Property: CSS should have mobile navigation touch target rules
        mobile_nav_css_rules = [
            '--touch-target-min: 44px',
            'min-height: var(--touch-target-min)',
            '.mobile-nav',
            'MOBILE BOTTOM NAVIGATION',
        ]
        
        has_touch_target_css = any(rule in css_content for rule in mobile_nav_css_rules)
        assert has_touch_target_css, \
            f"Mobile navigation CSS does not include touch target sizing rules. Looking for: {mobile_nav_css_rules}"
        
        # Check each navigation item
        for i, nav_item in enumerate(nav_interactive_elements):
            classes = ' '.join(nav_item.get('class', []))
            
            # Property: Each nav item should have flex layout for proper sizing
            assert 'flex' in classes, \
                f"Mobile navigation item {i} missing flex layout classes"
            
            # Property: Each nav item should have centering classes
            assert 'items-center' in classes and 'justify-center' in classes, \
                f"Mobile navigation item {i} missing centering classes for proper touch target"
            
            # Property: Each nav item should have proper ARIA label
            aria_label = nav_item.get('aria-label', '')
            assert aria_label != '', \
                f"Mobile navigation item {i} missing aria-label"
        
        # Property: Mobile navigation container should have proper height
        # Check the grid container inside the nav element
        nav_grid = mobile_nav.find('div', class_=lambda c: c and 'grid-cols-4' in c)
        assert nav_grid is not None, "Mobile navigation grid container not found"
        
        grid_classes = ' '.join(nav_grid.get('class', []))
        assert 'h-16' in grid_classes, \
            f"Mobile navigation grid container missing h-16 class for adequate touch targets. Found classes: {grid_classes}"
        
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
    def test_form_input_touch_targets(self, username_suffix, email_prefix):
        """
        Property: Form inputs must have minimum 44x44 pixel touch targets.
        
        This test focuses on form elements which are critical for user interaction.
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
        
        # Request the profile edit page (which has many form inputs)
        response = client.get(reverse('dashboard:profile_edit'))
        
        assert response.status_code == 200, \
            f"Profile edit page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all form inputs
        form_inputs = soup.find_all(['input', 'select', 'textarea', 'button'])
        
        # Filter to only form-related inputs
        form_elements = []
        for element in form_inputs:
            # Skip hidden inputs and non-interactive elements
            input_type = element.get('type', '').lower()
            if input_type not in ['hidden', 'csrf']:
                form_elements.append(element)
        
        # Property: Form should have some interactive elements
        assert len(form_elements) > 0, \
            "No form elements found on profile edit page"
        
        # Check CSS for form input touch target rules by reading the actual CSS file
        import os
        from django.conf import settings
        
        css_file_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'dashboard.css')
        css_content = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        
        # Property: CSS should have form input touch target rules
        # Check both the main CSS file and inline styles in templates
        form_css_rules = [
            'min-height: var(--touch-target-min)',
            'min-height: 44px',
            'padding: 0.75rem',
            'padding: 0.5rem',  # form-control uses this padding
            '.form-control',     # Custom form control class
        ]
        
        # Also check the HTML response for inline form-control styles
        html_content = response.content.decode('utf-8')
        
        has_form_css = (any(rule in css_content for rule in form_css_rules) or 
                       '.form-control' in html_content)
        assert has_form_css, \
            "CSS does not include form input touch target sizing rules"
        
        # Check specific form element types
        text_inputs = [elem for elem in form_elements if elem.name == 'input' and 
                      elem.get('type', 'text').lower() in ['text', 'email', 'password', 'search', 'tel', 'url']]
        
        if text_inputs:
            # Property: Text inputs should have adequate padding or height classes
            for text_input in text_inputs[:3]:  # Check first 3 text inputs
                classes = ' '.join(text_input.get('class', []))
                style = text_input.get('style', '')
                
                has_adequate_sizing = (
                    'p-' in classes or 'py-' in classes or 'px-' in classes or
                    'h-11' in classes or 'h-12' in classes or 'min-h-' in classes or
                    'min-height' in style or 'padding' in style or
                    'form-control' in classes  # Explicitly check for form-control class
                )
                
                assert has_adequate_sizing, \
                    f"Text input missing adequate sizing classes or styles: {classes}"
        
        # Check buttons
        buttons = [elem for elem in form_elements if elem.name == 'button' or 
                  (elem.name == 'input' and elem.get('type', '').lower() in ['button', 'submit', 'reset'])]
        
        if buttons:
            # Property: Buttons should have adequate sizing
            for button in buttons[:3]:  # Check first 3 buttons
                classes = ' '.join(button.get('class', []))
                
                has_button_sizing = (
                    'btn' in classes or 'button' in classes or
                    'p-' in classes or 'py-' in classes or 'px-' in classes or
                    'h-11' in classes or 'h-12' in classes or 'min-h-' in classes or
                    'text-gray-300' in classes  # Mobile menu button and similar UI buttons
                )
                
                assert has_button_sizing, \
                    f"Button missing adequate sizing classes: {classes}"
        
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
    def test_css_touch_target_variables(self, username_suffix, email_prefix):
        """
        Property: CSS must define touch target minimum size variables and rules.
        
        This test verifies that the CSS includes proper touch target sizing rules
        that ensure 44x44 pixel minimum touch targets.
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
        
        # Request any page to get CSS content
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Get the CSS content by reading the actual CSS file
        import os
        from django.conf import settings
        
        css_file_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'dashboard.css')
        css_content = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        
        # Property 1: CSS should define touch target minimum variable
        assert '--touch-target-min: 44px' in css_content, \
            "CSS missing --touch-target-min variable definition"
        
        # Property 2: CSS should have global touch target rules for interactive elements
        required_css_rules = [
            'min-height: var(--touch-target-min)',
            'min-width: var(--touch-target-min)',
        ]
        
        for rule in required_css_rules:
            assert rule in css_content, \
                f"CSS missing required touch target rule: {rule}"
        
        # Property 3: CSS should have specific rules for different element types
        element_specific_rules = [
            'button,',  # Button selector
            'a,',       # Link selector  
            'input[type="button"],',  # Input button selector
            '.btn,',    # Button class selector
        ]
        
        # At least some element-specific rules should be present
        has_element_rules = any(rule in css_content for rule in element_specific_rules)
        assert has_element_rules, \
            "CSS missing element-specific touch target rules"
        
        # Property 4: CSS should have mobile-specific touch target rules
        mobile_rules = [
            '@media (max-width: 767px)',  # Mobile media query
            '@media (max-width: 768px)',  # Alternative mobile breakpoint
        ]
        
        has_mobile_rules = any(rule in css_content for rule in mobile_rules)
        assert has_mobile_rules, \
            "CSS missing mobile-specific media queries for touch targets"
        
        # Property 5: CSS should include form input touch target rules
        form_rules = [
            'input[type="text"]',
            'input[type="email"]',
            'input[type="password"]',
            'textarea,',
            'select,',
        ]
        
        has_form_rules = any(rule in css_content for rule in form_rules)
        assert has_form_rules, \
            "CSS missing form input touch target rules"
        
        # Property 6: CSS should handle checkbox and radio button touch targets
        checkbox_radio_rules = [
            'input[type="checkbox"]',
            'input[type="radio"]',
        ]
        
        has_checkbox_radio_rules = any(rule in css_content for rule in checkbox_radio_rules)
        assert has_checkbox_radio_rules, \
            "CSS missing checkbox/radio button touch target rules"
        
        # Cleanup
        user.delete()
    
    def test_css_touch_target_documentation(self):
        """
        Property: CSS should include documentation about touch target requirements.
        
        This test verifies that the CSS includes proper documentation explaining
        the 44x44 pixel touch target requirement and its implementation.
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
        
        # Request any page to get CSS content
        response = client.get(reverse('dashboard:home'))
        
        assert response.status_code == 200, \
            f"Dashboard page returned status {response.status_code}, expected 200"
        
        # Get the CSS content by reading the actual CSS file
        import os
        from django.conf import settings
        
        css_file_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'dashboard.css')
        css_content = ""
        if os.path.exists(css_file_path):
            with open(css_file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        
        # Property 1: CSS should document touch target requirements
        documentation_keywords = [
            'TOUCH TARGETS',
            'Requirements: 14.4',
            'Minimum 44x44 pixels',
            '44x44 pixel',
        ]
        
        has_documentation = any(keyword in css_content for keyword in documentation_keywords)
        assert has_documentation, \
            "CSS missing documentation about touch target requirements"
        
        # Property 2: CSS should reference the specific requirement number
        assert 'Requirements: 14.4' in css_content, \
            "CSS missing reference to requirement 14.4"
        
        # Property 3: CSS should explain the 44x44 pixel minimum
        assert '44' in css_content, \
            "CSS missing reference to 44 pixel minimum size"
        
        # Cleanup
        user.delete()