"""
Test for profile_edit view bug fix
"""

import pytest
from django.test import Client
from django.urls import reverse
from core.models import User


@pytest.mark.django_db
class TestProfileEditViewFix:
    """Test that the profile_edit view bug is fixed"""

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

    def test_profile_form_submission_no_unbound_error(self):
        """
        Test that profile form submission doesn't cause UnboundLocalError.
        This was the bug where avatar_form and banner_form were not defined
        in the POST request handling for profile updates.
        """
        self.client.login(email=self.user.email, password='testpass123')
        
        # Submit profile form data (not avatar or banner)
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'bio': 'Updated bio'
            }
        )
        
        # Should not crash with UnboundLocalError
        # Should either redirect (302) on success or show form (200) with errors
        assert response.status_code in [200, 302]
        
        # If successful, user should be updated
        if response.status_code == 302:
            self.user.refresh_from_db()
            assert self.user.first_name == 'Updated'
            assert self.user.last_name == 'Name'
            assert self.user.bio == 'Updated bio'

    def test_profile_form_validation_error_handling(self):
        """
        Test that profile form validation errors are handled correctly
        without causing UnboundLocalError.
        """
        self.client.login(email=self.user.email, password='testpass123')
        
        # Submit invalid profile data
        response = self.client.post(
            reverse('dashboard:profile_edit'),
            data={
                'bio': 'a' * 501,  # Too long
                'display_name': 'ab'  # Too short
            }
        )
        
        # Should return form with errors (200), not crash
        assert response.status_code == 200
        
        # Should contain error messages in the response
        content = response.content.decode()
        assert 'error' in content.lower() or 'invalid' in content.lower()

    def test_get_request_works_correctly(self):
        """
        Test that GET requests to profile_edit work correctly.
        """
        self.client.login(email=self.user.email, password='testpass123')
        
        response = self.client.get(reverse('dashboard:profile_edit'))
        
        # Should return the form page successfully
        assert response.status_code == 200
        
        # Should have all required forms in context
        assert 'profile_form' in response.context
        assert 'avatar_form' in response.context
        assert 'banner_form' in response.context
        assert 'completeness' in response.context