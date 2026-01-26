"""
Property-based tests for password change security functionality.

This module tests the password change security property using Hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.test import TestCase
import uuid

User = get_user_model()


@pytest.mark.django_db
class TestPasswordChangeSecurity:
    """
    **Feature: user-profile-dashboard, Property 18: Password change security**
    
    For any password change attempt, the current password must be verified, 
    new password strength must be validated, and the password hash must be 
    updated only when both checks pass.
    
    **Validates: Requirements 9.4**
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        current_password_correct=st.booleans(),
        new_password=st.one_of(
            # Valid passwords (meet Django's default requirements)
            st.text(min_size=8, max_size=50).filter(
                lambda x: any(c.isdigit() for c in x) and 
                         any(c.isalpha() for c in x) and
                         len(x) >= 8
            ),
            # Invalid passwords (too short, common, etc.)
            st.one_of(
                st.text(max_size=7),  # Too short
                st.just("password"),  # Too common
                st.just("12345678"),  # Too common
                st.just(""),          # Empty
            )
        )
    )
    def test_password_change_security_enforcement(self, current_password_correct, new_password):
        """
        Test that password change enforces security requirements:
        1. Current password must be verified
        2. New password strength must be validated
        3. Password hash updated only when both checks pass
        """
        # Create a test user with a known password
        original_password = "original_secure_pass123"
        user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password=original_password
        )
        
        # Store original password hash for comparison
        original_password_hash = user.password
        
        # Prepare form data
        old_password = original_password if current_password_correct else "wrong_password"
        form_data = {
            'old_password': old_password,
            'new_password1': new_password,
            'new_password2': new_password,  # Confirmation matches
        }
        
        # Create and validate the form
        form = PasswordChangeForm(user=user, data=form_data)
        is_valid = form.is_valid()
        
        # Property: Form should be valid only if both conditions are met
        should_be_valid = (
            current_password_correct and 
            self._is_password_strong_enough(new_password)
        )
        
        assert is_valid == should_be_valid, (
            f"Password change validation failed. "
            f"Current password correct: {current_password_correct}, "
            f"New password: '{new_password}', "
            f"Expected valid: {should_be_valid}, "
            f"Actually valid: {is_valid}, "
            f"Form errors: {form.errors}"
        )
        
        # If form is valid, test that password is actually changed
        if is_valid:
            saved_user = form.save()
            saved_user.refresh_from_db()
            
            # Property: Password hash should be different from original
            assert saved_user.password != original_password_hash, (
                "Password hash should be updated when form is valid"
            )
            
            # Property: New password should work for authentication
            assert saved_user.check_password(new_password), (
                "New password should be set correctly"
            )
            
            # Property: Old password should no longer work
            assert not saved_user.check_password(original_password), (
                "Old password should no longer work after change"
            )
        else:
            # Property: If form is invalid, password should remain unchanged
            user.refresh_from_db()
            assert user.password == original_password_hash, (
                "Password hash should not change when form is invalid"
            )
            
            # Property: Original password should still work
            assert user.check_password(original_password), (
                "Original password should still work when change fails"
            )
    
    def _is_password_strong_enough(self, password):
        """
        Check if password meets Django's default validation requirements.
        This mimics Django's built-in password validation.
        """
        if not password:
            return False
        
        # Too short
        if len(password) < 8:
            return False
        
        # Too common (basic check)
        common_passwords = [
            "password", "12345678", "qwerty", "abc123", 
            "password123", "admin", "letmein", "welcome"
        ]
        if password.lower() in common_passwords:
            return False
        
        # All numeric
        if password.isdigit():
            return False
        
        # Should have some complexity (at least letters and numbers)
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_letter and has_digit
    
    @settings(max_examples=50, deadline=None)
    @given(
        password_mismatch=st.booleans()
    )
    def test_password_confirmation_mismatch_security(self, password_mismatch):
        """
        Test that password confirmation mismatch is properly handled.
        """
        # Create a test user
        original_password = "original_secure_pass123"
        user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password=original_password
        )
        
        original_password_hash = user.password
        new_password = "new_secure_pass456"
        confirmation_password = "different_pass789" if password_mismatch else new_password
        
        form_data = {
            'old_password': original_password,
            'new_password1': new_password,
            'new_password2': confirmation_password,
        }
        
        form = PasswordChangeForm(user=user, data=form_data)
        is_valid = form.is_valid()
        
        # Property: Form should be invalid if passwords don't match
        if password_mismatch:
            assert not is_valid, "Form should be invalid when passwords don't match"
            assert 'new_password2' in form.errors, "Should have confirmation error"
            
            # Property: Password should not change
            user.refresh_from_db()
            assert user.password == original_password_hash, (
                "Password should not change when confirmation fails"
            )
        else:
            assert is_valid, "Form should be valid when passwords match"