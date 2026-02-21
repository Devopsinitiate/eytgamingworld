"""
Authorization tests for venue views.

This module tests authentication and authorization requirements for venue system views.

Validates:
- Requirements 3.9: Booking creation requires authentication
- Requirements 11.3: Protected views require authentication
- Requirements 11.4: Booking cancellation requires ownership
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Venue, VenueBooking

User = get_user_model()


class LoginRequiredMixinTests(TestCase):
    """
    Test that LoginRequiredMixin is properly applied to protected views.
    
    Validates:
    - Requirements 3.9: Booking creation requires authentication
    - Requirements 11.3: Protected views require authentication
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='Test description',
            venue_type='esports_arena',
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            setup_stations=10,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('100.00'),
            day_rate=Decimal('800.00')
        )
        
        # Create test booking
        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4),
            expected_participants=20,
            total_cost=Decimal('400.00'),
            status='pending'
        )
    
    def test_booking_create_view_requires_login(self):
        """
        Test that BookingCreateView requires authentication.
        
        Validates: Requirements 3.9, 11.3
        """
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=', response.url)
    
    def test_booking_create_view_accessible_when_authenticated(self):
        """
        Test that authenticated users can access BookingCreateView.
        
        Validates: Requirements 3.9, 11.3
        """
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_form.html')
    
    def test_booking_list_view_requires_login(self):
        """
        Test that BookingListView requires authentication.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=', response.url)
    
    def test_booking_list_view_accessible_when_authenticated(self):
        """
        Test that authenticated users can access BookingListView.
        
        Validates: Requirements 11.3
        """
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_list.html')
    
    def test_booking_detail_view_requires_login(self):
        """
        Test that BookingDetailView requires authentication.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=', response.url)
    
    def test_booking_detail_view_accessible_when_authenticated(self):
        """
        Test that authenticated users can access their own BookingDetailView.
        
        Validates: Requirements 11.3
        """
        self.client.force_login(self.user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_detail.html')
    
    def test_booking_cancel_view_requires_login(self):
        """
        Test that BookingCancelView requires authentication.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        response = self.client.post(url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=', response.url)
    
    def test_booking_cancel_view_accessible_when_authenticated(self):
        """
        Test that authenticated users can access BookingCancelView for their bookings.
        
        Validates: Requirements 11.3
        """
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        response = self.client.post(url)
        
        # Should redirect to booking list (successful cancellation)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('venues:booking_list'))


class BookingOwnershipTests(TestCase):
    """
    Test ownership checks for booking operations.
    
    Validates:
    - Requirements 11.4: Booking cancellation requires ownership
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create two users
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='Test description',
            venue_type='esports_arena',
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            setup_stations=10,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('100.00'),
            day_rate=Decimal('800.00')
        )
        
        # Create booking owned by owner
        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.owner,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4),
            expected_participants=20,
            total_cost=Decimal('400.00'),
            status='pending'
        )
    
    def test_booking_cancel_owner_can_cancel(self):
        """
        Test that booking owner can cancel their own booking.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.owner)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Status should be updated to cancelled
        self.assertEqual(self.booking.status, 'cancelled')
        self.assertIsNotNone(self.booking.cancelled_at)
        
        # Check success message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Booking cancelled successfully.')
    
    def test_booking_cancel_non_owner_cannot_cancel(self):
        """
        Test that non-owners cannot cancel other users' bookings.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.other_user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Status should NOT be changed
        self.assertEqual(self.booking.status, 'pending')
        self.assertIsNone(self.booking.cancelled_at)
        
        # Check error message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'You do not have permission to cancel this booking.')
    
    def test_booking_detail_owner_can_view(self):
        """
        Test that booking owner can view their own booking details.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.owner)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        
        response = self.client.get(url)
        
        # Should return 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['booking'], self.booking)
    
    def test_booking_detail_non_owner_cannot_view(self):
        """
        Test that non-owners cannot view other users' booking details.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.other_user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        
        response = self.client.get(url)
        
        # Should return 404 (booking not found in user's bookings)
        self.assertEqual(response.status_code, 404)


class UnauthorizedAccessTests(TestCase):
    """
    Test various unauthorized access scenarios.
    
    Validates:
    - Requirements 3.9: Unauthenticated booking access redirects to login
    - Requirements 11.3: Protected views require authentication
    - Requirements 11.4: Ownership checks prevent unauthorized actions
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='Test description',
            venue_type='esports_arena',
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            setup_stations=10,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('100.00'),
            day_rate=Decimal('800.00')
        )
        
        # Create bookings for user1
        self.booking1 = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user1,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4),
            expected_participants=20,
            total_cost=Decimal('400.00'),
            status='pending'
        )
        
        self.booking2 = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user1,
            start_datetime=timezone.now() + timedelta(days=2),
            end_datetime=timezone.now() + timedelta(days=2, hours=4),
            expected_participants=30,
            total_cost=Decimal('400.00'),
            status='confirmed'
        )
    
    def test_anonymous_user_cannot_create_booking(self):
        """
        Test that anonymous users cannot create bookings.
        
        Validates: Requirements 3.9, 11.3
        """
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        # Try to access booking form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
        # Try to submit booking
        response = self.client.post(url, {
            'start_datetime': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': (timezone.now() + timedelta(days=1, hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 20,
            'notes': 'Test booking'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
        # Verify no booking was created
        self.assertEqual(VenueBooking.objects.filter(venue=self.venue).count(), 2)  # Only the 2 from setUp
    
    def test_anonymous_user_cannot_view_booking_list(self):
        """
        Test that anonymous users cannot view booking list.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_anonymous_user_cannot_view_booking_detail(self):
        """
        Test that anonymous users cannot view booking details.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_anonymous_user_cannot_cancel_booking(self):
        """
        Test that anonymous users cannot cancel bookings.
        
        Validates: Requirements 11.3
        """
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking1.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
        # Verify booking was not cancelled
        self.booking1.refresh_from_db()
        self.assertEqual(self.booking1.status, 'pending')
    
    def test_user_cannot_view_other_users_bookings_in_list(self):
        """
        Test that users only see their own bookings in the list.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.user2)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # user2 should have no bookings
        bookings = response.context['bookings']
        self.assertEqual(bookings.count(), 0)
        
        # user1's bookings should not be visible
        self.assertNotIn(self.booking1, bookings)
        self.assertNotIn(self.booking2, bookings)
    
    def test_user_cannot_view_other_users_booking_detail(self):
        """
        Test that users cannot view other users' booking details.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.user2)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking1.pk})
        response = self.client.get(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_user_cannot_cancel_other_users_booking(self):
        """
        Test that users cannot cancel other users' bookings.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.user2)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking1.pk})
        response = self.client.post(url)
        
        # Should redirect with error message
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Verify booking was not cancelled
        self.booking1.refresh_from_db()
        self.assertEqual(self.booking1.status, 'pending')
        
        # Check error message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]).lower())
    
    def test_login_redirect_preserves_next_parameter(self):
        """
        Test that login redirects preserve the 'next' parameter.
        
        Validates: Requirements 3.9, 11.3
        """
        # Try to access booking create
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('next=', response.url)
        self.assertIn(url, response.url)
        
        # Try to access booking list
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('next=', response.url)
        self.assertIn(url, response.url)
    
    def test_confirmed_booking_cannot_be_cancelled_by_owner(self):
        """
        Test that even owners cannot cancel confirmed bookings.
        
        Validates: Requirements 11.4
        """
        self.client.force_login(self.user1)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking2.pk})
        response = self.client.post(url)
        
        # Should redirect with error message
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Verify booking was not cancelled
        self.booking2.refresh_from_db()
        self.assertEqual(self.booking2.status, 'confirmed')
        
        # Check error message
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('pending', str(messages[0]).lower())
