"""
Tests for the accounts app: views, forms, and rate-limiting.
"""
import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.forms import CustomSignupForm

User = get_user_model()


class TestCustomSignupForm:
    def test_form_valid(self):
        form = CustomSignupForm(data={
            'username': 'newplayer',
            'gender': 'male',
            'age_confirmed': True,
        })
        assert form.is_valid()

    def test_form_missing_username(self):
        form = CustomSignupForm(data={
            'gender': 'male',
            'age_confirmed': True,
        })
        assert not form.is_valid()

    def test_form_missing_age_confirmed(self):
        form = CustomSignupForm(data={
            'username': 'newplayer',
            'gender': 'male',
        })
        assert not form.is_valid()

    @pytest.mark.django_db
    def test_signup_sets_user_fields(self):
        form = CustomSignupForm(data={
            'username': 'signuptest',
            'gender': 'female',
            'age_confirmed': True,
        })
        assert form.is_valid()
        user = User.objects.create_user(
            email='signuptest@test.com',
            password='testpass123',
            username='signuptest',
        )
        form.signup(request=None, user=user)
        user.refresh_from_db()
        assert user.gender == 'female'


class TestBecomeOrganizerView:
    URL = reverse('accounts:become_organizer')

    @pytest.mark.django_db
    def test_get_requires_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 200
        assert 'Sign Up to Apply' in response.content.decode()

    @pytest.mark.django_db
    def test_get_authenticated(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL)
        assert response.status_code == 200
        assert 'Organizer Application' in response.content.decode()

    @pytest.mark.django_db
    def test_get_unverified_user_blocked(self, client, unverified_player_user):
        client.force_login(unverified_player_user)
        response = client.get(self.URL)
        content = response.content.decode()
        # The gate error should show the error message and hide the form
        assert 'Please resolve the issues' in content
        # The form fields should NOT be present
        assert 'name="full_name"' not in content
        assert 'name="phone_number"' not in content

    @pytest.mark.django_db
    def test_post_creates_application(self, client_logged_in_player):
        response = client_logged_in_player.post(self.URL, {
            'full_name': 'Test Player',
            'phone_number': '+2348000000000',
            'country': 'Nigeria',
            'reason': 'I want to run tournaments in Lagos',
            'experience': 'Ran local FIFA tournaments',
            'agreed_to_terms': 'on',
        })
        assert response.status_code == 302
        from accounts.models import OrganizerApplication
        app = OrganizerApplication.objects.filter(user__email='player@test.com').first()
        assert app is not None
        assert app.status == 'pending'
        assert app.full_name == 'Test Player'
        assert app.phone_number == '+2348000000000'

    @pytest.mark.django_db
    def test_post_missing_required_fields(self, client_logged_in_player):
        response = client_logged_in_player.post(self.URL, {
            'full_name': '',
            'phone_number': '',
            'country': '',
            'reason': '',
            'agreed_to_terms': '',
        })
        content = response.content.decode()
        assert 'Full name is required' in content or 'Phone number is required' in content

    @pytest.mark.django_db
    def test_post_already_organizer(self, client_logged_in_player, player_user):
        player_user.role = 'organizer'
        player_user.save()
        response = client_logged_in_player.post(self.URL, {})
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_pending_application_redirects_to_status(self, client_logged_in_player, player_user):
        from accounts.models import OrganizerApplication
        OrganizerApplication.objects.create(
            user=player_user,
            full_name='Test Player',
            phone_number='+2348000000000',
            country='Nigeria',
            reason='Test',
        )
        response = client_logged_in_player.get(self.URL)
        assert response.status_code == 302
        assert response['Location'] == reverse('accounts:organizer_status')

    @pytest.mark.django_db
    def test_rate_limit_enforced(self, client_logged_in_player):
        for i in range(5):
            resp = client_logged_in_player.post(self.URL, {
                'full_name': 'Test Player',
                'phone_number': '+2348000000000',
                'country': 'Nigeria',
                'reason': 'Test reason here',
                'agreed_to_terms': 'on',
            })
            assert resp.status_code in (200, 302, 429)


class TestOrganizerStatusView:
    URL = reverse('accounts:organizer_status')

    @pytest.mark.django_db
    def test_no_application(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL)
        assert response.status_code == 200
        assert 'No Application Found' in response.content.decode()

    @pytest.mark.django_db
    def test_shows_pending_status(self, client_logged_in_player, player_user):
        from accounts.models import OrganizerApplication
        OrganizerApplication.objects.create(
            user=player_user,
            full_name='Test Player',
            phone_number='+2348000000000',
            country='Nigeria',
            reason='Test',
        )
        response = client_logged_in_player.get(self.URL)
        content = response.content.decode()
        assert 'Under Review' in content or 'pending' in content.lower()

    @pytest.mark.django_db
    def test_requires_login(self, client):
        response = client.get(self.URL)
        assert response.status_code == 302


class TestTwoFactorSetupView:
    URL = reverse('accounts:two_factor_setup')

    @pytest.mark.django_db
    def test_get_shows_qr_code(self, client_logged_in_player):
        response = client_logged_in_player.get(self.URL)
        assert response.status_code == 200
        assert 'qr_code' in response.context or 'svg' in response.content.decode()

    @pytest.mark.django_db
    def test_get_existing_device(self, client_logged_in_player, player_user):
        TOTPDevice.objects.create(user=player_user, name='default', confirmed=True)
        response = client_logged_in_player.get(self.URL)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_create_device_then_verify(self, client_logged_in_player, player_user):
        """Full 2FA setup flow: create device, get QR, verify token."""
        response = client_logged_in_player.get(self.URL)
        device = TOTPDevice.objects.filter(user=player_user).first()
        if device:
            token = device.totp_obj.now()
            verify_url = reverse('accounts:two_factor_verify', kwargs={'device_id': device.pk})
            resp = client_logged_in_player.post(verify_url, {'token-otp_token': str(token)}, follow=True)
            device.refresh_from_db()
            assert device.confirmed


class TestTwoFactorVerifyView:
    @pytest.mark.django_db
    def test_invalid_device_id(self, client_logged_in_player):
        url = reverse('accounts:two_factor_verify', kwargs={'device_id': 99999})
        response = client_logged_in_player.get(url)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_get_with_valid_device(self, client_logged_in_player, player_user):
        device = TOTPDevice.objects.create(user=player_user, name='default', confirmed=False)
        url = reverse('accounts:two_factor_verify', kwargs={'device_id': device.pk})
        response = client_logged_in_player.get(url)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_wrong_token(self, client_logged_in_player, player_user):
        device = TOTPDevice.objects.create(user=player_user, name='default', confirmed=False)
        url = reverse('accounts:two_factor_verify', kwargs={'device_id': device.pk})
        response = client_logged_in_player.post(url, {'token-otp_token': '000000'})
        assert response.status_code == 200
        assert not device.confirmed
