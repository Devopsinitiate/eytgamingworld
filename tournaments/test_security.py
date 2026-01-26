"""
Unit tests for tournament security measures.
Tests XSS protection, rate limiting, permission validation, and content sanitization.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from unittest.mock import patch, MagicMock
from core.models import Game
from .models import Tournament, Participant, Match, Bracket, TournamentShare
from .security import (
    TournamentSecurityValidator,
    TournamentAccessControl,
    ShareTrackingRateLimit,
    sanitize_tournament_data,
    log_security_event
)
from .forms import TournamentForm, MatchReportForm, DisputeForm

User = get_user_model()


class TournamentSecurityValidatorTest(TestCase):
    """Test XSS protection and input validation."""
    
    def setUp(self):
        self.validator = TournamentSecurityValidator()
    
    def test_sanitize_html_content(self):
        """Test HTML content sanitization."""
        # Test basic HTML sanitization
        malicious_html = '<script>alert("xss")</script><p>Safe content</p>'
        sanitized = self.validator.sanitize_html_content(malicious_html)
        self.assertNotIn('<script>', sanitized)
        self.assertIn('<p>Safe content</p>', sanitized)
        
        # Test allowed tags
        allowed_html = '<p>Paragraph</p><strong>Bold</strong><em>Italic</em>'
        sanitized = self.validator.sanitize_html_content(allowed_html)
        self.assertEqual(sanitized, allowed_html)
        
        # Test empty content
        self.assertEqual(self.validator.sanitize_html_content(''), '')
        self.assertEqual(self.validator.sanitize_html_content(None), None)
    
    def test_validate_tournament_name(self):
        """Test tournament name validation."""
        # Valid name
        valid_name = "My Tournament"
        result = self.validator.validate_tournament_name(valid_name)
        self.assertEqual(result, valid_name)
        
        # XSS attempt
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_name('<script>alert("xss")</script>')
        
        # JavaScript protocol
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_name('javascript:alert("xss")')
        
        # Too long
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_name('x' * 201)
        
        # Empty name
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_name('')
    
    def test_validate_tournament_slug(self):
        """Test tournament slug validation."""
        # Valid slug
        valid_slug = "my-tournament-2024"
        result = self.validator.validate_tournament_slug(valid_slug)
        self.assertEqual(result, valid_slug)
        
        # Invalid characters
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_slug('My Tournament!')
        
        # Uppercase letters
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_slug('My-Tournament')
        
        # Too long
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_slug('x' * 201)
        
        # Empty slug
        with self.assertRaises(ValidationError):
            self.validator.validate_tournament_slug('')
    
    def test_validate_url(self):
        """Test URL validation."""
        # Valid URLs
        valid_urls = [
            'https://example.com',
            'http://localhost:8000',
            'https://twitch.tv/stream',
        ]
        for url in valid_urls:
            result = self.validator.validate_url(url)
            self.assertEqual(result, url)
        
        # Invalid protocols
        invalid_urls = [
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'ftp://example.com',
        ]
        for url in invalid_urls:
            with self.assertRaises(ValidationError):
                self.validator.validate_url(url)
        
        # Empty URL (should be allowed)
        result = self.validator.validate_url('')
        self.assertEqual(result, '')
    
    def test_validate_description(self):
        """Test description validation and sanitization."""
        # Valid description with HTML
        description = '<p>This is a <strong>tournament</strong> description.</p>'
        result = self.validator.validate_description(description)
        self.assertIn('<p>', result)
        self.assertIn('<strong>', result)
        
        # XSS attempt
        malicious_description = '<script>alert("xss")</script><p>Description</p>'
        result = self.validator.validate_description(malicious_description)
        self.assertNotIn('<script>', result)
        self.assertIn('<p>Description</p>', result)
        
        # Too long
        with self.assertRaises(ValidationError):
            self.validator.validate_description('x' * 5001)
    
    def test_validate_participant_name(self):
        """Test participant name validation."""
        # Valid name
        valid_name = "Player123"
        result = self.validator.validate_participant_name(valid_name)
        self.assertEqual(result, valid_name)
        
        # XSS attempt
        with self.assertRaises(ValidationError):
            self.validator.validate_participant_name('<script>alert("xss")</script>')
        
        # HTML tags
        with self.assertRaises(ValidationError):
            self.validator.validate_participant_name('<b>Bold Name</b>')
        
        # Too long
        with self.assertRaises(ValidationError):
            self.validator.validate_participant_name('x' * 101)
        
        # Empty name
        with self.assertRaises(ValidationError):
            self.validator.validate_participant_name('')


class TournamentAccessControlTest(TestCase):
    """Test tournament access control and permissions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        self.game = Game.objects.create(name='Test Game', slug='test-game')
        
        # Create tournaments
        self.public_tournament = Tournament.objects.create(
            name='Public Tournament',
            slug='public-tournament',
            description='A public tournament',
            game=self.game,
            organizer=self.organizer,
            is_public=True,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
            check_in_start=timezone.now() + timezone.timedelta(days=1),
            start_datetime=timezone.now() + timezone.timedelta(days=2),
        )
        
        self.private_tournament = Tournament.objects.create(
            name='Private Tournament',
            slug='private-tournament',
            description='A private tournament',
            game=self.game,
            organizer=self.organizer,
            is_public=False,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
            check_in_start=timezone.now() + timezone.timedelta(days=1),
            start_datetime=timezone.now() + timezone.timedelta(days=2),
        )
        
        self.access_control = TournamentAccessControl()
    
    def test_can_view_public_tournament(self):
        """Test viewing public tournaments."""
        # Anonymous user can view public tournament
        from django.contrib.auth.models import AnonymousUser
        anonymous = AnonymousUser()
        self.assertTrue(
            self.access_control.can_view_tournament(anonymous, self.public_tournament)
        )
        
        # Authenticated user can view public tournament
        self.assertTrue(
            self.access_control.can_view_tournament(self.user, self.public_tournament)
        )
    
    def test_can_view_private_tournament(self):
        """Test viewing private tournaments."""
        # Anonymous user cannot view private tournament
        from django.contrib.auth.models import AnonymousUser
        anonymous = AnonymousUser()
        self.assertFalse(
            self.access_control.can_view_tournament(anonymous, self.private_tournament)
        )
        
        # Regular user cannot view private tournament
        self.assertFalse(
            self.access_control.can_view_tournament(self.user, self.private_tournament)
        )
        
        # Organizer can view private tournament
        self.assertTrue(
            self.access_control.can_view_tournament(self.organizer, self.private_tournament)
        )
        
        # Admin can view private tournament
        self.assertTrue(
            self.access_control.can_view_tournament(self.admin, self.private_tournament)
        )
        
        # Participant can view private tournament
        Participant.objects.create(
            tournament=self.private_tournament,
            user=self.user,
            status='confirmed'
        )
        self.assertTrue(
            self.access_control.can_view_tournament(self.user, self.private_tournament)
        )
    
    def test_can_edit_tournament(self):
        """Test tournament editing permissions."""
        # Anonymous user cannot edit
        from django.contrib.auth.models import AnonymousUser
        anonymous = AnonymousUser()
        self.assertFalse(
            self.access_control.can_edit_tournament(anonymous, self.public_tournament)
        )
        
        # Regular user cannot edit
        self.assertFalse(
            self.access_control.can_edit_tournament(self.user, self.public_tournament)
        )
        
        # Organizer can edit
        self.assertTrue(
            self.access_control.can_edit_tournament(self.organizer, self.public_tournament)
        )
        
        # Admin can edit
        self.assertTrue(
            self.access_control.can_edit_tournament(self.admin, self.public_tournament)
        )
    
    def test_can_report_match_score(self):
        """Test match score reporting permissions."""
        # Create bracket and match
        bracket = Bracket.objects.create(
            tournament=self.public_tournament,
            name='Main Bracket',
            total_rounds=3
        )
        
        participant1 = Participant.objects.create(
            tournament=self.public_tournament,
            user=self.user,
            status='confirmed'
        )
        
        participant2 = Participant.objects.create(
            tournament=self.public_tournament,
            user=self.organizer,
            status='confirmed'
        )
        
        match = Match.objects.create(
            tournament=self.public_tournament,
            bracket=bracket,
            round_number=1,
            match_number=1,
            participant1=participant1,
            participant2=participant2
        )
        
        # Participant can report score
        self.assertTrue(
            self.access_control.can_report_match_score(self.user, match)
        )
        
        # Other participant can report score
        self.assertTrue(
            self.access_control.can_report_match_score(self.organizer, match)
        )
        
        # Tournament organizer can report score
        self.assertTrue(
            self.access_control.can_report_match_score(self.organizer, match)
        )
        
        # Admin can report score
        self.assertTrue(
            self.access_control.can_report_match_score(self.admin, match)
        )
        
        # Random user cannot report score
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.assertFalse(
            self.access_control.can_report_match_score(other_user, match)
        )


class ShareTrackingRateLimitTest(TestCase):
    """Test rate limiting for share tracking."""
    
    def setUp(self):
        cache.clear()
        self.ip_address = '192.168.1.1'
        self.user_id = 123
    
    def test_ip_rate_limiting(self):
        """Test IP-based rate limiting."""
        # Should not be rate limited initially
        self.assertFalse(
            ShareTrackingRateLimit.is_rate_limited(self.ip_address)
        )
        
        # Simulate 10 shares (IP limit)
        for i in range(10):
            ShareTrackingRateLimit.increment_rate_limit(self.ip_address)
        
        # Should now be rate limited
        self.assertTrue(
            ShareTrackingRateLimit.is_rate_limited(self.ip_address)
        )
    
    def test_user_rate_limiting(self):
        """Test user-based rate limiting."""
        # Should not be rate limited initially
        self.assertFalse(
            ShareTrackingRateLimit.is_rate_limited(self.ip_address, self.user_id)
        )
        
        # Simulate 20 shares (user limit)
        for i in range(20):
            ShareTrackingRateLimit.increment_rate_limit(self.ip_address, self.user_id)
        
        # Should now be rate limited
        self.assertTrue(
            ShareTrackingRateLimit.is_rate_limited(self.ip_address, self.user_id)
        )
    
    def test_rate_limit_separation(self):
        """Test that different IPs/users have separate limits."""
        other_ip = '192.168.1.2'
        other_user_id = 456
        
        # Max out first IP/user
        for i in range(10):
            ShareTrackingRateLimit.increment_rate_limit(self.ip_address, self.user_id)
        
        # Other IP/user should not be affected
        self.assertFalse(
            ShareTrackingRateLimit.is_rate_limited(other_ip, other_user_id)
        )


class SecurityIntegrationTest(TestCase):
    """Integration tests for security measures."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.organizer = User.objects.create_user(
            username='organizer',
            email='organizer@example.com',
            password='testpass123',
            role='organizer'  # Set organizer role
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        self.game = Game.objects.create(name='Test Game', slug='test-game')
        
        self.tournament = Tournament.objects.create(
            name='Test Tournament',
            slug='test-tournament',
            description='A test tournament',
            game=self.game,
            organizer=self.organizer,
            is_public=True,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
            check_in_start=timezone.now() + timezone.timedelta(days=1),
            start_datetime=timezone.now() + timezone.timedelta(days=2),
        )
    
    def test_xss_protection_in_forms(self):
        """Test XSS protection in tournament forms."""
        # Create a user with organizer permissions
        self.organizer.role = 'organizer'  # Use organizer role instead of admin
        self.organizer.save()
        
        self.client.login(username='organizer', password='testpass123')
        
        # Test XSS protection by checking form validation directly
        from .forms import TournamentForm
        
        # Attempt to create tournament with XSS payload
        xss_payload = '<script>alert("xss")</script>'
        form_data = {
            'name': f'Tournament {xss_payload}',
            'slug': 'xss-tournament',
            'description': f'Description {xss_payload}',
            'rules': f'Rules {xss_payload}',
            'game': self.game.id,
            'format': 'single_elim',
            'min_participants': 4,
            'max_participants': 16,
            'registration_start': timezone.now(),
            'registration_end': timezone.now() + timezone.timedelta(days=1),
            'check_in_start': timezone.now() + timezone.timedelta(days=1),
            'start_datetime': timezone.now() + timezone.timedelta(days=2),
        }
        
        # Test form validation directly
        form = TournamentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('contains invalid content', str(form.errors))
    
    def test_share_rate_limiting(self):
        """Test share tracking rate limiting."""
        # Clear cache to ensure clean test
        from django.core.cache import cache
        cache.clear()
        
        # Make 10 share requests (IP limit)
        for i in range(10):
            response = self.client.get(
                reverse('tournaments:share', kwargs={'slug': self.tournament.slug}),
                {'platform': 'direct'},  # Use direct platform to avoid redirects
                HTTP_X_FORWARDED_FOR='192.168.1.1'
            )
            # Verify each request succeeds initially
            self.assertEqual(response.status_code, 200, f"Request {i+1} should succeed")
        
        # Check if rate limit is triggered
        from tournaments.security import ShareTrackingRateLimit
        is_limited = ShareTrackingRateLimit.is_rate_limited('192.168.1.1')
        self.assertTrue(is_limited, "Should be rate limited after 10 requests")
        
        # 11th request should be rate limited
        response = self.client.get(
            reverse('tournaments:share', kwargs={'slug': self.tournament.slug}),
            {'platform': 'direct'},  # Use direct platform to avoid redirects
            HTTP_X_FORWARDED_FOR='192.168.1.1'
        )
        self.assertEqual(response.status_code, 429)
    
    def test_tournament_access_control(self):
        """Test tournament access control in views."""
        # Create private tournament
        private_tournament = Tournament.objects.create(
            name='Private Tournament',
            slug='private-tournament',
            description='A private tournament',
            game=self.game,
            organizer=self.organizer,
            is_public=False,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
            check_in_start=timezone.now() + timezone.timedelta(days=1),
            start_datetime=timezone.now() + timezone.timedelta(days=2),
        )
        
        # Anonymous user should be denied access
        response = self.client.get(
            reverse('tournaments:detail', kwargs={'slug': private_tournament.slug})
        )
        self.assertEqual(response.status_code, 403)
        
        # Regular user should be denied access
        login_success = self.client.login(email='test@example.com', password='testpass123')
        self.assertTrue(login_success, "Login should succeed")
        response = self.client.get(
            reverse('tournaments:detail', kwargs={'slug': private_tournament.slug})
        )
        self.assertEqual(response.status_code, 403)
        
        # Organizer should have access
        login_success = self.client.login(email='organizer@example.com', password='testpass123')
        self.assertTrue(login_success, "Organizer login should succeed")
        
        response = self.client.get(
            reverse('tournaments:detail', kwargs={'slug': private_tournament.slug})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        self.client.login(email='organizer@example.com', password='testpass123')
        
        # Force CSRF failure by using enforce_csrf_checks=True
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email='organizer@example.com', password='testpass123')
        
        # POST without CSRF token should be rejected
        response = csrf_client.post(
            reverse('tournaments:edit', kwargs={'slug': self.tournament.slug}),
            {
                'name': 'Updated Tournament',
                'slug': self.tournament.slug,
                'description': 'Updated description',
                'game': self.game.id,
                'format': 'single_elim',
                'min_participants': 4,
                'max_participants': 16,
                'registration_start': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'registration_end': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
                'check_in_start': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
                'start_datetime': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            }
        )
        # CSRF protection should cause a 403
        self.assertEqual(response.status_code, 403)


class ContentSanitizationTest(TestCase):
    """Test content sanitization functions."""
    
    def test_sanitize_tournament_data(self):
        """Test tournament data sanitization."""
        malicious_data = {
            'name': '<script>alert("xss")</script>Tournament',
            'slug': 'INVALID-SLUG!',
            'description': '<script>alert("xss")</script><p>Description</p>',
            'rules': '<iframe src="evil.com"></iframe><p>Rules</p>',
            'stream_url': 'javascript:alert("xss")',
            'discord_invite': 'data:text/html,<script>alert("xss")</script>',
            'other_field': 'unchanged'
        }
        
        # Should raise validation errors for malicious content
        with self.assertRaises(ValidationError):
            sanitize_tournament_data(malicious_data)
    
    @patch('tournaments.security.logger')
    def test_security_event_logging(self, mock_logger):
        """Test security event logging."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        log_security_event(
            'TEST_EVENT',
            user,
            'Test security event',
            'WARNING'
        )
        
        # Verify logger was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('TEST_EVENT', call_args)
        # The log message contains the user ID (UUID) and email, not username
        self.assertIn('test@example.com', call_args)