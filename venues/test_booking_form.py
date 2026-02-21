"""
Unit tests for VenueBookingForm

Validates:
- Requirements 3.2: Form fields (start_datetime, end_datetime, expected_participants, notes, tournament)
- Requirements 3.4: Cost calculation based on duration and venue rates
- Requirements 3.5: Overlapping booking validation
- Requirements 3.6: Date range validation (end > start)
- Requirements 3.7: Capacity warning logic
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from .models import Venue, VenueBooking
from .forms import VenueBookingForm

User = get_user_model()


class VenueBookingFormTests(TestCase):
    """Unit tests for VenueBookingForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.venue = Venue.objects.create(
            name='Test Arena',
            slug='test-arena',
            description='Test venue',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=50,
            setup_stations=25,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('100.00'),
            day_rate=Decimal('600.00')
        )
    
    def test_form_has_required_fields(self):
        """Test that form includes all required fields"""
        form = VenueBookingForm(venue=self.venue, user=self.user)
        
        self.assertIn('start_datetime', form.fields)
        self.assertIn('end_datetime', form.fields)
        self.assertIn('expected_participants', form.fields)
        self.assertIn('notes', form.fields)
        self.assertIn('tournament', form.fields)
    
    def test_tournament_field_is_optional(self):
        """Test that tournament field is not required"""
        form = VenueBookingForm(venue=self.venue, user=self.user)
        self.assertFalse(form.fields['tournament'].required)
    
    def test_valid_booking_form(self):
        """Test form with valid data"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
            'notes': 'Test booking'
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_date_range_validation_end_before_start(self):
        """Test that end datetime must be after start datetime"""
        start = timezone.now() + timedelta(days=1)
        end = start - timedelta(hours=1)  # End before start
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('end_datetime', form.errors)
        self.assertIn('End date must be after start date', str(form.errors['end_datetime']))
    
    def test_date_range_validation_end_equals_start(self):
        """Test that end datetime cannot equal start datetime"""
        start = timezone.now() + timedelta(days=1)
        end = start  # End equals start
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('end_datetime', form.errors)
    
    def test_overlapping_booking_validation(self):
        """Test that overlapping bookings are rejected"""
        # Create existing booking
        start1 = timezone.now() + timedelta(days=1)
        end1 = start1 + timedelta(hours=4)
        
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=start1,
            end_datetime=end1,
            expected_participants=20,
            status='confirmed',
            total_cost=Decimal('400.00')
        )
        
        # Try to create overlapping booking
        start2 = start1 + timedelta(hours=2)  # Overlaps with existing
        end2 = start2 + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start2,
            'end_datetime': end2,
            'expected_participants': 25,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('start_datetime', form.errors)
        self.assertIn('already booked', str(form.errors['start_datetime']).lower())
    
    def test_non_overlapping_booking_is_valid(self):
        """Test that non-overlapping bookings are allowed"""
        # Create existing booking
        start1 = timezone.now() + timedelta(days=1)
        end1 = start1 + timedelta(hours=4)
        
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=start1,
            end_datetime=end1,
            expected_participants=20,
            status='confirmed',
            total_cost=Decimal('400.00')
        )
        
        # Create non-overlapping booking (after existing)
        start2 = end1 + timedelta(hours=1)
        end2 = start2 + timedelta(hours=3)
        
        form_data = {
            'start_datetime': start2,
            'end_datetime': end2,
            'expected_participants': 25,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_cancelled_bookings_dont_block(self):
        """Test that cancelled bookings don't prevent new bookings"""
        # Create cancelled booking
        start1 = timezone.now() + timedelta(days=1)
        end1 = start1 + timedelta(hours=4)
        
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=start1,
            end_datetime=end1,
            expected_participants=20,
            status='cancelled',
            total_cost=Decimal('400.00')
        )
        
        # Try to create booking at same time (should be allowed)
        form_data = {
            'start_datetime': start1,
            'end_datetime': end1,
            'expected_participants': 25,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
    
    def test_capacity_warning_when_exceeded(self):
        """Test that warning is added when participants exceed capacity"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 60,  # Exceeds venue capacity of 50
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        # Form should still be valid (warning, not error)
        self.assertTrue(form.is_valid(), form.errors)
        
        # Check for warning
        warnings = form.get_warnings()
        self.assertIn('expected_participants', warnings)
        self.assertIn('exceed venue capacity', warnings['expected_participants'][0].lower())
    
    def test_no_capacity_warning_when_within_limit(self):
        """Test that no warning when participants within capacity"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 40,  # Within venue capacity of 50
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        
        # Check no warning
        warnings = form.get_warnings()
        self.assertNotIn('expected_participants', warnings)
    
    def test_cost_calculation_hourly_rate(self):
        """Test cost calculation using hourly rate for short bookings"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        # 4 hours * $100/hour = $400
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('400.00'))
    
    def test_cost_calculation_day_rate(self):
        """Test cost calculation using day rate for 8+ hour bookings"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=10)  # 10 hours, should use day rate
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        # 10 hours >= 8, so use day rate: $600 * 1 day = $600
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('600.00'))
    
    def test_cost_calculation_multiple_days(self):
        """Test cost calculation for multi-day bookings"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=30)  # 30 hours = 2 days
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        # 30 hours / 24 = 1.25 days, rounded up to 2 days
        # $600 * 2 = $1200
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('1200.00'))
    
    def test_cost_calculation_exactly_8_hours(self):
        """Test cost calculation at 8 hour boundary"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=8)  # Exactly 8 hours
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        # 8 hours >= 8, so use day rate: $600
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('600.00'))
    
    def test_save_sets_pending_status(self):
        """Test that saving a booking sets status to pending"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
            'notes': 'Test booking'
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        booking = form.save()
        self.assertEqual(booking.status, 'pending')
    
    def test_save_calculates_total_cost(self):
        """Test that saving a booking calculates and sets total cost"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=5)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        booking = form.save()
        # 5 hours * $100/hour = $500
        self.assertEqual(booking.total_cost, Decimal('500.00'))
    
    def test_save_sets_venue_and_user(self):
        """Test that saving sets venue and user correctly"""
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 30,
        }
        
        form = VenueBookingForm(data=form_data, venue=self.venue, user=self.user)
        self.assertTrue(form.is_valid())
        
        booking = form.save()
        self.assertEqual(booking.venue, self.venue)
        self.assertEqual(booking.booked_by, self.user)
    
    def test_venue_without_day_rate_uses_hourly(self):
        """Test cost calculation when venue has no day rate"""
        venue_no_day_rate = Venue.objects.create(
            name='Hourly Only Venue',
            slug='hourly-only',
            description='Test venue',
            venue_type='cafe',
            address='456 Test Ave',
            city='Portland',
            state='OR',
            country='USA',
            postal_code='97201',
            capacity=30,
            setup_stations=15,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('50.00'),
            day_rate=None  # No day rate
        )
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=10)  # 10 hours
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 20,
        }
        
        form = VenueBookingForm(data=form_data, venue=venue_no_day_rate, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Should use hourly rate: 10 hours * $50/hour = $500
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('500.00'))
    
    def test_venue_without_hourly_rate(self):
        """Test cost calculation when venue has no hourly rate"""
        venue_no_hourly = Venue.objects.create(
            name='Day Rate Only Venue',
            slug='day-rate-only',
            description='Test venue',
            venue_type='convention_center',
            address='789 Test Blvd',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98102',
            capacity=200,
            setup_stations=100,
            is_active=True,
            is_verified=True,
            hourly_rate=None,  # No hourly rate
            day_rate=Decimal('2000.00')
        )
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)  # Less than 8 hours
        
        form_data = {
            'start_datetime': start,
            'end_datetime': end,
            'expected_participants': 100,
        }
        
        form = VenueBookingForm(data=form_data, venue=venue_no_hourly, user=self.user)
        self.assertTrue(form.is_valid())
        
        # No hourly rate available, should return 0
        cost = form.calculate_cost()
        self.assertEqual(cost, Decimal('0.00'))
