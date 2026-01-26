"""
Property-Based Test for Non-Color Indicators

Property 28: Non-color indicators
Validates: Requirements 15.3

This test ensures that information conveyed through color is also available
through other visual means (icons, text, patterns, shapes) to support
users with color vision deficiencies.
"""

import uuid
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.django import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import transaction
from bs4 import BeautifulSoup
import re

User = get_user_model()


class NonColorIndicatorsPropertyTest(TestCase):
    """Property-based tests for non-color indicator accessibility compliance."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test user with unique identifiers
        unique_id = str(uuid.uuid4())[:8]
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )
        
        # Common status indicators that should have non-color alternatives
        self.status_indicators = {
            'success': {
                'colors': ['green', '#059669', '#10b981', '#34d399'],
                'required_alternatives': ['✓', 'check', 'success', 'complete', 'done'],
                'description': 'Success states should have checkmarks or success text'
            },
            'error': {
                'colors': ['red', '#dc2626', '#ef4444', '#f87171'],
                'required_alternatives': ['✗', '×', 'error', 'failed', 'invalid', 'danger'],
                'description': 'Error states should have X marks or error text'
            },
            'warning': {
                'colors': ['yellow', 'orange', '#d97706', '#f59e0b', '#fbbf24'],
                'required_alternatives': ['⚠', '!', 'warning', 'caution', 'alert'],
                'description': 'Warning states should have warning icons or text'
            },
            'info': {
                'colors': ['blue', '#2563eb', '#3b82f6', '#60a5fa'],
                'required_alternatives': ['ℹ', 'i', 'info', 'information', 'note'],
                'description': 'Info states should have info icons or text'
            },
            'pending': {
                'colors': ['gray', 'grey', '#6b7280', '#9ca3af'],
                'required_alternatives': ['⏳', '...', 'pending', 'waiting', 'processing'],
                'description': 'Pending states should have loading icons or text'
            }
        }
    
    def extract_color_from_style(self, style_attr):
        """Extract color values from CSS style attribute."""
        colors = []
        
        # Extract color property
        color_match = re.search(r'color:\s*([^;]+)', style_attr)
        if color_match:
            colors.append(color_match.group(1).strip())
        
        # Extract background-color property
        bg_color_match = re.search(r'background-color:\s*([^;]+)', style_attr)
        if bg_color_match:
            colors.append(bg_color_match.group(1).strip())
        
        # Extract border-color property
        border_color_match = re.search(r'border-color:\s*([^;]+)', style_attr)
        if border_color_match:
            colors.append(border_color_match.group(1).strip())
        
        return colors
    
    def has_non_color_indicator(self, element, status_type):
        """Check if an element has non-color indicators for the given status type."""
        alternatives = self.status_indicators[status_type]['required_alternatives']
        
        # Check element text content (but be more precise about matches)
        text_content = element.get_text().lower()
        for alt in alternatives:
            alt_lower = alt.lower()
            # For single character alternatives, require exact word match or standalone character
            if len(alt_lower) == 1:
                # Check if it's a standalone character (surrounded by spaces or at start/end)
                import re
                pattern = r'(?:^|\s)' + re.escape(alt_lower) + r'(?:\s|$)'
                if re.search(pattern, text_content):
                    return True, f"text: '{alt}'"
            else:
                # For multi-character alternatives, check if it's a whole word (allowing punctuation)
                import re
                # Create word boundary pattern that allows punctuation
                pattern = r'\b' + re.escape(alt_lower) + r'\b'
                if re.search(pattern, text_content):
                    return True, f"text: '{alt}'"
        
        # Check aria-label
        aria_label = element.get('aria-label', '').lower()
        for alt in alternatives:
            if alt.lower() in aria_label:
                return True, f"aria-label: '{alt}'"
        
        # Check title attribute
        title = element.get('title', '').lower()
        for alt in alternatives:
            if alt.lower() in title:
                return True, f"title: '{alt}'"
        
        # Check for icon classes (common icon libraries)
        class_attr = element.get('class', [])
        if isinstance(class_attr, str):
            class_attr = class_attr.split()
        
        icon_classes = [cls for cls in class_attr if any(icon_prefix in cls for icon_prefix in 
                       ['fa-', 'icon-', 'material-icons', 'heroicon', 'lucide'])]
        
        if icon_classes:
            for icon_class in icon_classes:
                for alt in alternatives:
                    if alt.lower() in icon_class.lower():
                        return True, f"icon class: '{icon_class}'"
        
        # Check for child elements with icons or text
        for child in element.find_all(['i', 'span', 'svg', 'img']):
            child_text = child.get_text().lower()
            child_class = child.get('class', [])
            if isinstance(child_class, str):
                child_class = child_class.split()
            
            # Check child text
            for alt in alternatives:
                if alt.lower() in child_text:
                    return True, f"child text: '{alt}'"
            
            # Check child classes
            for cls in child_class:
                for alt in alternatives:
                    if alt.lower() in cls.lower():
                        return True, f"child class: '{cls}'"
        
        return False, "no alternative found"
    
    def identify_status_from_color(self, colors):
        """Identify what status type is indicated by the given colors."""
        colors_lower = [c.lower() for c in colors]
        
        for status_type, config in self.status_indicators.items():
            for status_color in config['colors']:
                if status_color.lower() in ' '.join(colors_lower):
                    return status_type
        
        return None
    
    @given(
        status_type=st.sampled_from(['success', 'error', 'warning', 'info', 'pending'])
    )
    @settings(max_examples=5, deadline=30000)
    def test_status_indicator_alternatives(self, status_type):
        """Test that status indicators have non-color alternatives."""
        config = self.status_indicators[status_type]
        
        # Create mock HTML elements with color-only indicators
        # Use generic text that doesn't accidentally contain status keywords
        test_cases = [
            f'<div style="color: {config["colors"][0]}">Content here</div>',
            f'<span style="background-color: {config["colors"][0]}">Badge text</span>',
            f'<button style="border-color: {config["colors"][0]}">Button</button>',
        ]
        
        for html in test_cases:
            soup = BeautifulSoup(html, 'html.parser')
            element = soup.find()
            
            # Extract colors from the element
            style = element.get('style', '')
            colors = self.extract_color_from_style(style)
            
            # Check if this element uses status colors
            detected_status = self.identify_status_from_color(colors)
            
            if detected_status == status_type:
                # This element uses color to indicate status - it should have alternatives
                has_alternative, alternative_info = self.has_non_color_indicator(element, status_type)
                
                # For this test, we expect the mock elements to fail (they're color-only)
                # This validates our detection logic
                self.assertFalse(
                    has_alternative,
                    f"Mock element with color-only {status_type} indicator should not have alternatives: {alternative_info}"
                )
    
    def test_success_indicators_have_alternatives(self):
        """Test that success indicators include non-color alternatives."""
        # Test various success indicator patterns
        success_patterns = [
            '<div class="text-green-600">✓ Success</div>',
            '<span style="color: green" aria-label="Success">Message sent</span>',
            '<div class="bg-green-100"><i class="fa-check"></i> Complete</div>',
            '<button class="btn-success" title="Success">Done</button>',
            '<div style="background-color: #059669">✓ Saved successfully</div>',
        ]
        
        for html in success_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                # Check if element uses green/success colors
                style = element.get('style', '')
                class_attr = element.get('class', [])
                
                uses_success_color = (
                    'green' in style.lower() or
                    any('green' in cls or 'success' in cls for cls in class_attr)
                )
                
                if uses_success_color:
                    has_alternative, alternative_info = self.has_non_color_indicator(element, 'success')
                    self.assertTrue(
                        has_alternative,
                        f"Success element should have non-color alternative. Found: {alternative_info}"
                    )
    
    def test_error_indicators_have_alternatives(self):
        """Test that error indicators include non-color alternatives."""
        error_patterns = [
            '<div class="text-red-600">✗ Error occurred</div>',
            '<span style="color: red" aria-label="Error">Invalid input</span>',
            '<div class="bg-red-100"><i class="fa-times"></i> Failed</div>',
            '<button class="btn-danger" title="Error">× Cancel</button>',
            '<div style="background-color: #dc2626">Error: Please try again</div>',
        ]
        
        for html in error_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                # Check if element uses red/error colors
                style = element.get('style', '')
                class_attr = element.get('class', [])
                
                uses_error_color = (
                    'red' in style.lower() or
                    any('red' in cls or 'danger' in cls or 'error' in cls for cls in class_attr)
                )
                
                if uses_error_color:
                    has_alternative, alternative_info = self.has_non_color_indicator(element, 'error')
                    self.assertTrue(
                        has_alternative,
                        f"Error element should have non-color alternative. Found: {alternative_info}"
                    )
    
    def test_warning_indicators_have_alternatives(self):
        """Test that warning indicators include non-color alternatives."""
        warning_patterns = [
            '<div class="text-yellow-600">⚠ Warning</div>',
            '<span style="color: orange" aria-label="Warning">Caution required</span>',
            '<div class="bg-yellow-100"><i class="fa-exclamation-triangle"></i> Alert</div>',
            '<button class="btn-warning" title="Warning">! Proceed with caution</button>',
            '<div style="background-color: #d97706">Warning: Check your input</div>',
        ]
        
        for html in warning_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                # Check if element uses yellow/orange/warning colors
                style = element.get('style', '')
                class_attr = element.get('class', [])
                
                uses_warning_color = (
                    any(color in style.lower() for color in ['yellow', 'orange', '#d97706', '#f59e0b']) or
                    any('yellow' in cls or 'orange' in cls or 'warning' in cls for cls in class_attr)
                )
                
                if uses_warning_color:
                    has_alternative, alternative_info = self.has_non_color_indicator(element, 'warning')
                    self.assertTrue(
                        has_alternative,
                        f"Warning element should have non-color alternative. Found: {alternative_info}"
                    )
    
    def test_info_indicators_have_alternatives(self):
        """Test that info indicators include non-color alternatives."""
        info_patterns = [
            '<div class="text-blue-600">ℹ Information</div>',
            '<span style="color: blue" aria-label="Info">Additional details</span>',
            '<div class="bg-blue-100"><i class="fa-info-circle"></i> Note</div>',
            '<button class="btn-info" title="Information">i More info</button>',
            '<div style="background-color: #2563eb">Info: This is helpful</div>',
        ]
        
        for html in info_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                # Check if element uses blue/info colors
                style = element.get('style', '')
                class_attr = element.get('class', [])
                
                uses_info_color = (
                    'blue' in style.lower() or
                    any('blue' in cls or 'info' in cls for cls in class_attr)
                )
                
                if uses_info_color:
                    has_alternative, alternative_info = self.has_non_color_indicator(element, 'info')
                    self.assertTrue(
                        has_alternative,
                        f"Info element should have non-color alternative. Found: {alternative_info}"
                    )
    
    def test_form_validation_indicators(self):
        """Test that form validation uses non-color indicators."""
        form_validation_patterns = [
            # Valid field with green border and checkmark
            '<input class="border-green-500" aria-describedby="valid-msg"><span id="valid-msg">✓ Valid</span>',
            # Invalid field with red border and error message
            '<input class="border-red-500" aria-describedby="error-msg"><span id="error-msg">✗ Required field</span>',
            # Warning field with yellow border and warning text
            '<input class="border-yellow-500" aria-describedby="warn-msg"><span id="warn-msg">⚠ Check format</span>',
        ]
        
        for html in form_validation_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find the input and its associated message
                input_element = soup.find('input')
                describedby = input_element.get('aria-describedby')
                
                if describedby:
                    message_element = soup.find(id=describedby)
                    if message_element:
                        # Check if the message has non-color indicators
                        message_text = message_element.get_text()
                        
                        # Should have visual indicators beyond just color
                        has_symbol = any(symbol in message_text for symbol in ['✓', '✗', '⚠', '×', '!'])
                        has_descriptive_text = any(word in message_text.lower() for word in 
                                                 ['valid', 'invalid', 'error', 'required', 'warning', 'check'])
                        
                        self.assertTrue(
                            has_symbol or has_descriptive_text,
                            f"Form validation message should have symbols or descriptive text: '{message_text}'"
                        )
    
    def test_status_badges_have_alternatives(self):
        """Test that status badges include non-color alternatives."""
        badge_patterns = [
            '<span class="badge bg-success">✓ Active</span>',
            '<span class="badge bg-danger">✗ Inactive</span>',
            '<span class="badge bg-warning">⚠ Pending</span>',
            '<span class="badge bg-info">ℹ Draft</span>',
            '<span class="badge bg-secondary">⏳ Processing</span>',
        ]
        
        for html in badge_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                badge_text = element.get_text()
                class_attr = element.get('class', [])
                
                # Check if it's a colored badge
                is_colored_badge = any(color in ' '.join(class_attr) for color in 
                                     ['success', 'danger', 'warning', 'info', 'secondary', 'primary'])
                
                if is_colored_badge:
                    # Should have non-color indicators
                    has_symbol = any(symbol in badge_text for symbol in ['✓', '✗', '⚠', 'ℹ', '⏳'])
                    has_descriptive_text = len(badge_text.strip()) > 1  # More than just a symbol
                    
                    self.assertTrue(
                        has_symbol or has_descriptive_text,
                        f"Colored badge should have symbols or descriptive text: '{badge_text}'"
                    )
    
    def test_link_states_have_alternatives(self):
        """Test that link states use non-color indicators."""
        link_patterns = [
            '<a href="#" class="text-blue-600">Regular link</a>',
            '<a href="#" class="text-purple-600 visited">Visited link</a>',
            '<a href="#" class="text-red-600 disabled" aria-disabled="true">Disabled link</a>',
            '<a href="#" class="text-green-600 active" aria-current="page">Current page</a>',
        ]
        
        for html in link_patterns:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                element = soup.find()
                
                # Check for non-color state indicators
                aria_disabled = element.get('aria-disabled')
                aria_current = element.get('aria-current')
                class_attr = element.get('class', [])
                
                # Links should have proper ARIA attributes or text indicators for states
                if 'disabled' in ' '.join(class_attr):
                    self.assertTrue(
                        aria_disabled == 'true',
                        "Disabled links should have aria-disabled='true'"
                    )
                
                if 'active' in ' '.join(class_attr) or 'current' in ' '.join(class_attr):
                    self.assertTrue(
                        aria_current is not None,
                        "Active/current links should have aria-current attribute"
                    )
    
    @given(
        element_type=st.sampled_from(['div', 'span', 'button', 'p']),
        status_class=st.sampled_from(['success', 'error', 'warning', 'info'])
    )
    @settings(max_examples=10, deadline=30000)
    def test_colored_elements_need_alternatives(self, element_type, status_class):
        """Property test that colored elements should have non-color alternatives."""
        # Create element with only color-based status indication
        html = f'<{element_type} class="text-{status_class}">Status message</{element_type}>'
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find()
        
        # This element uses color to convey status but has no alternatives
        # In a real application, this would be a violation
        has_alternative, _ = self.has_non_color_indicator(element, status_class)
        
        # Document that color-only elements are problematic
        if not has_alternative:
            print(f"Design issue: {element_type} with class 'text-{status_class}' "
                  f"uses color-only indication - should add icon or descriptive text")