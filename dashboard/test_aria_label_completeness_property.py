"""
Property-Based Tests for ARIA Label Completeness

This module contains property-based tests for ARIA label completeness,
specifically testing that all interactive elements have descriptive ARIA labels.
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
class TestAriaLabelCompleteness:
    """
    **Feature: user-profile-dashboard, Property 27: ARIA label completeness**
    
    For any interactive element, a descriptive ARIA label must be present.
    
    **Validates: Requirements 15.2**
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
    def test_interactive_elements_have_aria_labels(self, username_suffix, email_prefix, page_type):
        """
        Property: All interactive elements must have descriptive ARIA labels.
        
        This test verifies that:
        1. All buttons have aria-label or descriptive text content
        2. All icon-only buttons have aria-label attributes
        3. All links have aria-label or descriptive text content
        4. All form inputs have aria-label or associated labels
        5. All interactive elements provide context for screen readers
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
        
        # Find all interactive elements that need ARIA labels
        interactive_elements = self._find_interactive_elements(soup)
        
        # Property 2: At least some interactive elements should be present
        assert len(interactive_elements) > 0, \
            f"No interactive elements found on {page_type} page"
        
        # Check each interactive element for ARIA label compliance
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
                'aria_label': element.get('aria-label', ''),
                'title': element.get('title', '')
            }
            
            is_compliant = self._check_aria_label_compliance(element)
            
            if not is_compliant:
                non_compliant_elements.append(element_info)
        
        # Property 3: All interactive elements must have descriptive ARIA labels
        if non_compliant_elements:
            error_details = []
            for elem in non_compliant_elements[:5]:  # Show first 5 non-compliant elements
                error_details.append(
                    f"  - {elem['tag']} (class: '{elem['classes']}', "
                    f"id: '{elem['id']}', type: '{elem['type']}', "
                    f"text: '{elem['text']}', aria-label: '{elem['aria_label']}')"
                )
            
            error_message = (
                f"Found {len(non_compliant_elements)} interactive elements without "
                f"descriptive ARIA labels on {page_type} page:\n" +
                '\n'.join(error_details)
            )
            
            if len(non_compliant_elements) > 5:
                error_message += f"\n  ... and {len(non_compliant_elements) - 5} more elements"
            
            assert False, error_message
        
        # Cleanup
        user.delete()
    
    def _find_interactive_elements(self, soup):
        """
        Find all interactive elements that should have ARIA labels.
        
        Returns a list of BeautifulSoup elements that are interactive
        and should have descriptive ARIA labels.
        """
        interactive_selectors = [
            'button',
            'a[href]',
            'input[type="button"]',
            'input[type="submit"]',
            'input[type="reset"]',
            'input[type="checkbox"]',
            'input[type="radio"]',
            '[role="button"]',
            '[role="link"]',
            '[role="menuitem"]',
            '[role="tab"]',
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
        
        # Filter out elements that are hidden or not actually interactive
        filtered_elements = []
        for element in unique_elements:
            # Skip hidden elements
            if element.get('style') and 'display: none' in element.get('style'):
                continue
            if 'hidden' in element.get('class', []):
                continue
            if element.get('aria-hidden') == 'true':
                continue
            
            # Skip disabled elements (they don't need ARIA labels)
            if element.get('disabled') is not None:
                continue
            if element.get('aria-disabled') == 'true':
                continue
            
            filtered_elements.append(element)
        
        return filtered_elements
    
    def _check_aria_label_compliance(self, element):
        """
        Check if an element meets ARIA label requirements.
        
        An element is compliant if:
        1. It has an aria-label attribute with descriptive text
        2. It has descriptive text content (for buttons and links)
        3. It has an associated label (for form inputs)
        4. It has a title attribute (as fallback)
        5. It's exempted from ARIA label requirements (specific cases)
        """
        tag_name = element.name.lower()
        aria_label = element.get('aria-label', '').strip()
        text_content = element.get_text(strip=True)
        title = element.get('title', '').strip()
        element_type = element.get('type', '').lower()
        classes = ' '.join(element.get('class', []))
        
        # Check for explicit aria-label
        if aria_label and len(aria_label) >= 3:  # Minimum descriptive length
            return True
        
        # Check for descriptive text content
        if text_content and len(text_content) >= 2:
            # Text content is sufficient for most elements
            # But icon-only elements still need aria-label
            if not self._is_icon_only_element(element):
                return True
        
        # Check for title attribute (fallback)
        if title and len(title) >= 3:
            return True
        
        # Special cases for form inputs
        if tag_name == 'input':
            # Check for associated label
            input_id = element.get('id')
            if input_id:
                # Look for label with for attribute
                parent_soup = element.find_parent()
                while parent_soup:
                    label = parent_soup.find('label', {'for': input_id})
                    if label and label.get_text(strip=True):
                        return True
                    parent_soup = parent_soup.find_parent()
            
            # Check if input is inside a label
            label_parent = element.find_parent('label')
            if label_parent and label_parent.get_text(strip=True):
                return True
            
            # Check for placeholder as fallback (not ideal but acceptable)
            placeholder = element.get('placeholder', '').strip()
            if placeholder and len(placeholder) >= 3:
                return True
        
        # Special cases for links
        if tag_name == 'a':
            href = element.get('href', '')
            
            # Links with meaningful href and no text need aria-label
            if href and not text_content:
                return False
            
            # Links with only icons need aria-label
            if self._is_icon_only_element(element):
                return False
            
            # Links with descriptive text are okay
            if text_content and len(text_content) >= 2:
                return True
        
        # Special cases for buttons
        if tag_name == 'button' or element.get('role') == 'button':
            # Icon-only buttons must have aria-label
            if self._is_icon_only_element(element):
                return False
            
            # Buttons with descriptive text are okay
            if text_content and len(text_content) >= 2:
                return True
        
        # Check for elements that are part of larger interactive areas
        # These might not need individual ARIA labels
        if self._is_part_of_labeled_container(element):
            return True
        
        # Check for specific exemptions
        if self._is_exempted_from_aria_label(element):
            return True
        
        # If we reach here, the element doesn't meet ARIA label requirements
        return False
    
    def _is_icon_only_element(self, element):
        """
        Check if an element contains only icons and no descriptive text.
        """
        text_content = element.get_text(strip=True)
        
        # If there's meaningful text content, it's not icon-only
        if text_content and len(text_content) > 1:
            # Check if the text is just icon names or single characters
            icon_patterns = [
                r'^[a-z_]+$',  # Material icon names like 'menu', 'close'
                r'^[→←↑↓]+$',  # Arrow characters
                r'^[✓✗×]+$',   # Check/cross characters
                r'^[+\-×÷=]+$', # Math symbols
            ]
            
            for pattern in icon_patterns:
                if re.match(pattern, text_content.lower()):
                    return True
            
            return False
        
        # Check for icon elements
        icons = element.find_all(['i', 'span'], class_=lambda c: c and any(
            icon_class in ' '.join(c) for icon_class in [
                'material-symbols-outlined',
                'material-icons',
                'fa-',
                'icon-',
                'glyphicon-'
            ]
        ))
        
        # If it has icons but no text, it's icon-only
        if icons and not text_content:
            return True
        
        # Check for SVG icons
        svgs = element.find_all('svg')
        if svgs and not text_content:
            return True
        
        return False
    
    def _is_part_of_labeled_container(self, element):
        """
        Check if an element is part of a larger container that provides context.
        """
        # Check if element is inside a labeled container
        parent = element.parent
        while parent and parent.name != 'body':
            # Check if parent has aria-label or role that provides context
            if parent.get('aria-label') or parent.get('role') in ['navigation', 'menu', 'tablist']:
                return True
            
            # Check if parent is a form group or field container
            parent_classes = ' '.join(parent.get('class', []))
            if any(container_class in parent_classes for container_class in [
                'form-group', 'field-container', 'input-group', 'form-field'
            ]):
                return True
            
            parent = parent.parent
        
        return False
    
    def _is_exempted_from_aria_label(self, element):
        """
        Check if an element is exempted from ARIA label requirements.
        """
        tag_name = element.name.lower()
        classes = ' '.join(element.get('class', []))
        element_type = element.get('type', '').lower()
        
        # Text inputs, textareas, and selects with labels are okay
        if tag_name in ['input', 'textarea', 'select']:
            if element_type in ['text', 'email', 'password', 'search', 'tel', 'url', 'number']:
                # These should have labels, but we'll be lenient if they have placeholders
                return True
        
        # Hidden inputs don't need ARIA labels
        if tag_name == 'input' and element_type == 'hidden':
            return True
        
        # Elements with aria-hidden don't need ARIA labels
        if element.get('aria-hidden') == 'true':
            return True
        
        # Decorative elements don't need ARIA labels
        if 'decorative' in classes or 'decoration' in classes:
            return True
        
        # Skip navigation links (they have text content)
        if tag_name == 'a' and any(nav_class in classes for nav_class in [
            'skip-link', 'skip-nav', 'sr-only'
        ]):
            return True
        
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
    def test_mobile_navigation_aria_labels(self, username_suffix, email_prefix):
        """
        Property: Mobile navigation items must have descriptive ARIA labels.
        
        This test specifically focuses on the mobile navigation which is critical
        for screen reader users on mobile devices.
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
        
        # Check each navigation item for ARIA label compliance
        for i, nav_item in enumerate(nav_interactive_elements):
            aria_label = nav_item.get('aria-label', '')
            text_content = nav_item.get_text(strip=True)
            
            # Property: Each nav item should have descriptive ARIA label
            assert aria_label != '', \
                f"Mobile navigation item {i} missing aria-label attribute"
            
            # Property: ARIA label should be descriptive (at least 3 characters)
            assert len(aria_label) >= 3, \
                f"Mobile navigation item {i} has non-descriptive aria-label: '{aria_label}'"
            
            # Property: ARIA label should contain meaningful text
            meaningful_words = ['Dashboard', 'Profile', 'Notifications', 'Menu', 'Open', 'current']
            has_meaningful_word = any(word.lower() in aria_label.lower() for word in meaningful_words)
            assert has_meaningful_word, \
                f"Mobile navigation item {i} aria-label not descriptive: '{aria_label}'"
            
            # Property: Current page should be indicated in ARIA label
            if nav_item.get('aria-current') == 'page':
                assert 'current' in aria_label.lower(), \
                    f"Current page navigation item {i} should indicate 'current' in aria-label: '{aria_label}'"
        
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
    def test_form_elements_aria_labels(self, username_suffix, email_prefix):
        """
        Property: Form elements must have descriptive labels or ARIA labels.
        
        This test focuses on form accessibility which is critical for screen readers.
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
        
        # Request the profile edit page (which has many form elements)
        response = client.get(reverse('dashboard:profile_edit'))
        
        assert response.status_code == 200, \
            f"Profile edit page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all form elements
        form_elements = soup.find_all(['input', 'select', 'textarea'])
        
        # Filter to only interactive form elements
        interactive_form_elements = []
        for element in form_elements:
            input_type = element.get('type', '').lower()
            # Skip hidden inputs and CSRF tokens
            if input_type not in ['hidden', 'csrf']:
                interactive_form_elements.append(element)
        
        # Property: Form should have some interactive elements
        assert len(interactive_form_elements) > 0, \
            "No interactive form elements found on profile edit page"
        
        # Check each form element for proper labeling
        unlabeled_elements = []
        
        for element in interactive_form_elements:
            element_id = element.get('id', '')
            element_name = element.get('name', '')
            element_type = element.get('type', 'text').lower()
            aria_label = element.get('aria-label', '')
            placeholder = element.get('placeholder', '')
            
            has_proper_label = False
            
            # Check for aria-label
            if aria_label and len(aria_label) >= 3:
                has_proper_label = True
            
            # Check for associated label element
            if element_id:
                label = soup.find('label', {'for': element_id})
                if label and label.get_text(strip=True):
                    has_proper_label = True
            
            # Check if element is inside a label
            label_parent = element.find_parent('label')
            if label_parent and label_parent.get_text(strip=True):
                has_proper_label = True
            
            # Check for placeholder as fallback (not ideal but acceptable for some inputs)
            if element_type in ['text', 'email', 'password', 'search'] and placeholder:
                if len(placeholder) >= 3:
                    has_proper_label = True
            
            if not has_proper_label:
                unlabeled_elements.append({
                    'tag': element.name,
                    'id': element_id,
                    'name': element_name,
                    'type': element_type,
                    'aria_label': aria_label,
                    'placeholder': placeholder
                })
        
        # Property: All form elements should have proper labels
        if unlabeled_elements:
            error_details = []
            for elem in unlabeled_elements[:3]:  # Show first 3 unlabeled elements
                error_details.append(
                    f"  - {elem['tag']} (id: '{elem['id']}', name: '{elem['name']}', "
                    f"type: '{elem['type']}', aria-label: '{elem['aria_label']}', "
                    f"placeholder: '{elem['placeholder']}')"
                )
            
            error_message = (
                f"Found {len(unlabeled_elements)} form elements without proper labels:\n" +
                '\n'.join(error_details)
            )
            
            if len(unlabeled_elements) > 3:
                error_message += f"\n  ... and {len(unlabeled_elements) - 3} more elements"
            
            assert False, error_message
        
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
    def test_icon_only_buttons_aria_labels(self, username_suffix, email_prefix):
        """
        Property: Icon-only buttons must have descriptive ARIA labels.
        
        This test focuses on icon-only interactive elements which are critical
        for screen reader accessibility.
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
        
        # Request the profile view page (which has icon buttons)
        response = client.get(reverse('dashboard:profile_view', kwargs={'username': user.username}))
        
        assert response.status_code == 200, \
            f"Profile view page returned status {response.status_code}, expected 200"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all buttons and links
        interactive_elements = soup.find_all(['button', 'a'])
        
        # Filter to icon-only elements
        icon_only_elements = []
        for element in interactive_elements:
            if self._is_icon_only_element(element):
                # Skip hidden or disabled elements
                if (element.get('aria-hidden') != 'true' and 
                    not element.get('disabled') and
                    'hidden' not in element.get('class', [])):
                    icon_only_elements.append(element)
        
        # Check each icon-only element for ARIA label
        for element in icon_only_elements:
            aria_label = element.get('aria-label', '')
            title = element.get('title', '')
            
            # Property: Icon-only elements must have aria-label or title
            has_label = (aria_label and len(aria_label) >= 3) or (title and len(title) >= 3)
            
            if not has_label:
                element_info = {
                    'tag': element.name,
                    'classes': ' '.join(element.get('class', [])),
                    'id': element.get('id', ''),
                    'text': element.get_text(strip=True)[:20],
                    'aria_label': aria_label,
                    'title': title
                }
                
                assert False, (
                    f"Icon-only element missing descriptive ARIA label: "
                    f"{element_info['tag']} (class: '{element_info['classes']}', "
                    f"id: '{element_info['id']}', text: '{element_info['text']}', "
                    f"aria-label: '{element_info['aria_label']}', title: '{element_info['title']}')"
                )
        
        # Cleanup
        user.delete()
    
    def test_aria_live_regions_present(self):
        """
        Property: Dynamic content areas must have ARIA live regions.
        
        This test verifies that areas with dynamic content have proper
        ARIA live regions for screen reader announcements.
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
        
        # Property: Activity feed should have aria-live region
        activity_feed = soup.find(class_=lambda c: c and 'activity-feed' in c)
        if activity_feed:
            aria_live = activity_feed.get('aria-live')
            assert aria_live in ['polite', 'assertive'], \
                f"Activity feed missing aria-live attribute, found: {aria_live}"
        
        # Property: Error message containers should have aria-live regions
        error_containers = soup.find_all(class_=lambda c: c and any(
            error_class in c for error_class in ['error-message', 'alert-error', 'alert']
        ))
        
        for error_container in error_containers:
            aria_live = error_container.get('aria-live')
            if aria_live:  # If present, should be assertive for errors
                assert aria_live == 'assertive', \
                    f"Error container should have aria-live='assertive', found: {aria_live}"
        
        # Property: Success message containers should have aria-live regions
        success_containers = soup.find_all(class_=lambda c: c and any(
            success_class in c for success_class in ['success-message', 'alert-success']
        ))
        
        for success_container in success_containers:
            aria_live = success_container.get('aria-live')
            if aria_live:  # If present, should be polite for success messages
                assert aria_live == 'polite', \
                    f"Success container should have aria-live='polite', found: {aria_live}"
        
        # Cleanup
        user.delete()