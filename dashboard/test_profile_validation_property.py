"""
Property-based tests for profile field validation
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from core.models import User
from dashboard.forms import ProfileEditForm


@pytest.mark.django_db
class TestProfileFieldValidation:
    """
    **Feature: user-profile-dashboard, Property 17: Profile field validation**
    
    For any profile update with invalid data, the system must reject the update 
    and return specific field error messages.
    **Validates: Requirements 2.2**
    """

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test user and client"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        unique_email = f'test_{unique_id}@example.com'
        unique_username = f'testuser_{unique_id}'
        self.user = User.objects.create_user(
            email=unique_email,
            username=unique_username,
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client = Client()

    @given(
        bio_length=st.integers(min_value=501, max_value=1000)
    )
    @settings(max_examples=50, deadline=5000)
    def test_bio_length_validation(self, bio_length):
        """
        Property: For any bio longer than 500 characters, the form must reject 
        the update and return a specific error message.
        """
        # Generate bio text of specified length
        bio_text = 'a' * bio_length
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'bio': bio_text
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Bio over 500 characters must be rejected
        assert not form.is_valid()
        assert 'bio' in form.errors
        # Django's max_length validation message
        assert 'at most 500 characters' in str(form.errors['bio'])

    @given(
        display_name_length=st.integers(min_value=0, max_value=2)
    )
    @settings(max_examples=30, deadline=5000)
    def test_display_name_length_validation(self, display_name_length):
        """
        Property: For any display name shorter than 3 characters (when provided), 
        the form must reject the update and return a specific error message.
        """
        # Generate display name of specified length
        display_name = 'a' * display_name_length if display_name_length > 0 else ''
        
        # Only test non-empty short names (empty is allowed)
        if display_name_length > 0:
            form_data = {
                'first_name': 'Test',
                'last_name': 'User',
                'display_name': display_name
            }
            
            form = ProfileEditForm(data=form_data, instance=self.user)
            
            # Property: Display name under 3 characters must be rejected
            assert not form.is_valid()
            assert 'display_name' in form.errors
            assert 'at least 3 characters' in str(form.errors['display_name'])

    @given(
        days_in_future=st.integers(min_value=1, max_value=365)
    )
    @settings(max_examples=50, deadline=5000)
    def test_future_date_of_birth_validation(self, days_in_future):
        """
        Property: For any date of birth in the future, the form must reject 
        the update and return a specific error message.
        """
        future_date = date.today() + timedelta(days=days_in_future)
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': future_date.isoformat()
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Future dates must be rejected
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors
        assert 'must be in the past' in str(form.errors['date_of_birth'])

    @given(
        age_years=st.integers(min_value=1, max_value=12)
    )
    @settings(max_examples=30, deadline=5000)
    def test_underage_validation(self, age_years):
        """
        Property: For any date of birth indicating age under 13, the form must 
        reject the update and return a specific error message.
        """
        # Calculate date of birth for given age
        today = date.today()
        birth_date = date(today.year - age_years, today.month, today.day)
        
        # Adjust if birthday hasn't occurred this year
        if birth_date > today:
            birth_date = date(birth_date.year - 1, birth_date.month, birth_date.day)
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'date_of_birth': birth_date.isoformat()
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Users under 13 must be rejected
        assert not form.is_valid()
        assert 'date_of_birth' in form.errors
        assert 'at least 13 years old' in str(form.errors['date_of_birth'])

    @given(
        valid_bio_length=st.integers(min_value=1, max_value=500),
        valid_display_name_length=st.integers(min_value=3, max_value=50),
        valid_age=st.integers(min_value=13, max_value=100)
    )
    @settings(max_examples=100, deadline=5000)
    def test_valid_profile_data_acceptance(self, valid_bio_length, valid_display_name_length, valid_age):
        """
        Property: For any profile data that meets all validation criteria, 
        the form must accept the update without errors.
        """
        # Generate valid data
        bio_text = 'a' * valid_bio_length
        display_name = 'u' * valid_display_name_length
        
        # Calculate valid birth date
        today = date.today()
        birth_date = date(today.year - valid_age, today.month, today.day)
        
        # Adjust if birthday hasn't occurred this year
        if birth_date > today:
            birth_date = date(birth_date.year - 1, birth_date.month, birth_date.day)
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'display_name': display_name,
            'bio': bio_text,
            'date_of_birth': birth_date.isoformat(),
            'country': 'Test Country',
            'city': 'Test City'
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Valid data must be accepted
        assert form.is_valid(), f"Form should be valid but got errors: {form.errors}"

    @given(
        field_name=st.sampled_from(['first_name', 'last_name', 'country', 'city']),
        field_length=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=50, deadline=5000)
    def test_empty_optional_fields_acceptance(self, field_name, field_length):
        """
        Property: For any optional field that is empty or very short, 
        the form must accept the update (these fields don't have minimum length requirements).
        """
        field_value = 'a' * field_length if field_length > 0 else ''
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            field_name: field_value
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Optional fields can be empty or short
        assert form.is_valid(), f"Form should accept empty/short {field_name} but got errors: {form.errors}"

    @pytest.mark.django_db
    def test_profile_validation_form_level(self):
        """
        Test: Verify that profile validation works at the form level.
        This tests the core validation logic without the view layer.
        """
        # Test cases with expected validation failures
        invalid_test_cases = [
            {
                'data': {'bio': 'a' * 501},
                'field': 'bio',
                'expected_error': 'at most 500 characters'
            },
            {
                'data': {'display_name': 'ab'},
                'field': 'display_name',
                'expected_error': 'at least 3 characters'
            },
            {
                'data': {'date_of_birth': (date.today() + timedelta(days=1)).isoformat()},
                'field': 'date_of_birth',
                'expected_error': 'must be in the past'
            },
            {
                'data': {'date_of_birth': (date.today() - timedelta(days=365*5)).isoformat()},
                'field': 'date_of_birth',
                'expected_error': 'at least 13 years old'
            }
        ]
        
        for test_case in invalid_test_cases:
            form = ProfileEditForm(data=test_case['data'], instance=self.user)
            
            # Should be invalid
            assert not form.is_valid()
            
            # Should have error on expected field
            assert test_case['field'] in form.errors
            
            # Check that the expected error message appears
            assert test_case['expected_error'] in str(form.errors[test_case['field']])

    @given(
        bio_text=st.text(min_size=1, max_size=500, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')
        )),
        display_name=st.text(min_size=3, max_size=50, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd')
        ))
    )
    @settings(max_examples=100, deadline=10000)
    def test_text_field_character_handling(self, bio_text, display_name):
        """
        Property: For any text input with valid length and reasonable characters, 
        the form must handle the input correctly without errors.
        """
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'display_name': display_name,
            'bio': bio_text
        }
        
        form = ProfileEditForm(data=form_data, instance=self.user)
        
        # Property: Valid text input must be accepted
        assert form.is_valid(), f"Form should accept valid text but got errors: {form.errors}"
        
        # If form is valid, the cleaned data should be processed correctly
        # Note: Django forms may strip whitespace, so we check that the form processes the data
        if form.is_valid():
            # The cleaned data should be strings (not None or other types)
            assert isinstance(form.cleaned_data['bio'], str)
            assert isinstance(form.cleaned_data['display_name'], str)
            # Length should be within expected bounds after cleaning
            assert len(form.cleaned_data['bio']) <= 500
            assert len(form.cleaned_data['display_name']) <= 50

    @pytest.mark.django_db
    def test_form_error_message_specificity(self):
        """
        Property: For any validation error, the form must return specific, 
        actionable error messages that identify the problem clearly.
        """
        # Test specific error message patterns
        error_test_cases = [
            {
                'data': {'bio': 'a' * 600},
                'field': 'bio',
                'expected_patterns': ['500', 'characters', 'most']
            },
            {
                'data': {'display_name': 'ab'},
                'field': 'display_name', 
                'expected_patterns': ['3', 'characters']
            },
            {
                'data': {'date_of_birth': '2030-01-01'},
                'field': 'date_of_birth',
                'expected_patterns': ['past']
            },
            {
                'data': {'date_of_birth': '2020-01-01'},
                'field': 'date_of_birth',
                'expected_patterns': ['13', 'years', 'old']
            }
        ]
        
        for test_case in error_test_cases:
            form = ProfileEditForm(data=test_case['data'], instance=self.user)
            
            # Property: Form must be invalid for bad data
            assert not form.is_valid()
            
            # Property: Specific field must have error
            assert test_case['field'] in form.errors
            
            # Property: Error message must contain expected patterns
            error_message = str(form.errors[test_case['field']])
            for pattern in test_case['expected_patterns']:
                assert pattern.lower() in error_message.lower(), (
                    f"Error message '{error_message}' should contain '{pattern}'"
                )