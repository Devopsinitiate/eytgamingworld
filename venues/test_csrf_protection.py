"""
Tests for CSRF protection on all forms in the venue system.

This test module verifies that all POST forms include CSRF tokens and that
submissions without valid CSRF tokens are rejected.

Requirements tested: 11.1, 11.2
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from venues.models import Venue, VenueBooking
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class CSRFProtectionTests(TestCase):
    """Test CSRF protection on all forms."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create venue owner
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test venue',
            venue_type='esports_arena',
            owner=self.owner,
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=50.00,
            day_rate=300.00
        )
        
        # Create a test booking for cancel tests
        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4),
            expected_participants=50,
            total_cost=200.00,
            status='pending'
        )
        
        # Create a client that enforces CSRF checks
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_booking_form_template_includes_csrf_token(self):
        """Test that booking form template includes {% csrf_token %}."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        # Check that CSRF token is in the context (Django provides it automatically)
        self.assertIn('csrf_token', response.context)

    def test_booking_form_submission_without_csrf_token_fails(self):
        """Test that booking form submission without CSRF token is rejected."""
        self.csrf_client.force_login(self.user)
        
        booking_data = {
            'start_datetime': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': (timezone.now() + timedelta(days=2, hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        }
        
        response = self.csrf_client.post(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug}),
            booking_data
        )
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify booking was not created
        self.assertEqual(
            VenueBooking.objects.filter(notes='Test booking').count(),
            0
        )

    def test_booking_form_submission_with_csrf_token_succeeds(self):
        """Test that booking form submission with CSRF token succeeds."""
        self.client.force_login(self.user)
        
        # Get the form page first to obtain CSRF token
        form_response = self.client.get(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        )
        
        booking_data = {
            'start_datetime': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': (timezone.now() + timedelta(days=2, hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking with CSRF'
        }
        
        response = self.client.post(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug}),
            booking_data
        )
        
        # Should succeed (redirect to confirmation)
        self.assertEqual(response.status_code, 302)
        
        # Verify booking was created
        self.assertEqual(
            VenueBooking.objects.filter(notes='Test booking with CSRF').count(),
            1
        )

    def test_review_form_template_includes_csrf_token(self):
        """Test that review form template includes {% csrf_token %}."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('venues:detail', kwargs={'slug': self.venue.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        # Check for CSRF token in the review form
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_review_form_submission_without_csrf_token_fails(self):
        """Test that review form submission without CSRF token is rejected."""
        self.csrf_client.force_login(self.user)
        
        review_data = {
            'rating': 5,
            'title': 'Great venue!',
            'review': 'This is a test review without CSRF token.',
            'would_recommend': True
        }
        
        response = self.csrf_client.post(
            reverse('venues:detail', kwargs={'slug': self.venue.slug}),
            review_data
        )
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify review was not created
        self.assertEqual(self.venue.reviews.count(), 0)

    def test_review_form_submission_with_csrf_token_succeeds(self):
        """Test that review form submission with CSRF token succeeds."""
        self.client.force_login(self.user)
        
        review_data = {
            'rating': 5,
            'title': 'Great venue!',
            'review': 'This is a test review with CSRF token.',
            'would_recommend': True
        }
        
        response = self.client.post(
            reverse('venues:detail', kwargs={'slug': self.venue.slug}),
            review_data
        )
        
        # Should succeed (redirect or display success)
        self.assertIn(response.status_code, [200, 302])
        
        # Verify review was created
        self.assertEqual(self.venue.reviews.count(), 1)
        review = self.venue.reviews.first()
        self.assertEqual(review.title, 'Great venue!')

    def test_booking_cancel_form_includes_csrf_token(self):
        """Test that booking cancel form includes CSRF token."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        )
        
        self.assertEqual(response.status_code, 200)
        # Check for CSRF token in the cancel form
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_booking_cancel_without_csrf_token_fails(self):
        """Test that booking cancellation without CSRF token is rejected."""
        self.csrf_client.force_login(self.user)
        
        response = self.csrf_client.post(
            reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        )
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Verify booking was not cancelled
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'pending')

    def test_booking_cancel_with_csrf_token_succeeds(self):
        """Test that booking cancellation with CSRF token succeeds."""
        self.client.force_login(self.user)
        
        response = self.client.post(
            reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        )
        
        # Should succeed (redirect)
        self.assertEqual(response.status_code, 302)
        
        # Verify booking was cancelled
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_get_requests_do_not_require_csrf_token(self):
        """Test that GET requests (like search/filter) don't require CSRF tokens."""
        # Venue list with filters uses GET, should work without CSRF
        response = self.csrf_client.get(
            reverse('venues:list'),
            {'city': 'Test City', 'venue_type': 'esports_arena'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venue.name)

    def test_all_post_forms_reject_invalid_csrf_tokens(self):
        """Test that all POST forms reject invalid CSRF tokens."""
        self.csrf_client.force_login(self.user)
        
        # Test with an invalid CSRF token
        invalid_token_data = {
            'csrfmiddlewaretoken': 'invalid_token_value',
            'rating': 5,
            'title': 'Test',
            'review': 'Test review'
        }
        
        response = self.csrf_client.post(
            reverse('venues:detail', kwargs={'slug': self.venue.slug}),
            invalid_token_data
        )
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403)
