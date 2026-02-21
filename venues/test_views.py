"""
Tests for Venue views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Venue, VenueBooking, VenueReview

User = get_user_model()


class VenueListViewTests(TestCase):
    """
    Test venue list view with filtering and search.
    
    Validates:
    - Requirements 1.1: Display all active and verified venues
    - Requirements 1.3-1.6: Filter by city, venue_type, min_capacity
    - Requirements 9.1, 9.3: Search functionality
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test venues
        self.venue1 = Venue.objects.create(
            name='Gaming Arena Alpha',
            slug='gaming-arena-alpha',
            description='Premier esports arena',
            venue_type='esports_arena',
            address='123 Main St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
        
        self.venue2 = Venue.objects.create(
            name='Cyber Cafe Beta',
            slug='cyber-cafe-beta',
            description='Cozy gaming cafe',
            venue_type='cafe',
            address='456 Oak Ave',
            city='Portland',
            state='OR',
            country='USA',
            postal_code='97201',
            capacity=30,
            setup_stations=15,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('50.00'),
            day_rate=Decimal('300.00')
        )
        
        self.venue3 = Venue.objects.create(
            name='Gaming Lounge Gamma',
            slug='gaming-lounge-gamma',
            description='Community gaming space',
            venue_type='gaming_lounge',
            address='789 Pine Rd',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98102',
            capacity=50,
            setup_stations=25,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('75.00'),
            day_rate=Decimal('500.00')
        )
        
        # Create inactive venue (should not appear)
        self.venue_inactive = Venue.objects.create(
            name='Inactive Venue',
            slug='inactive-venue',
            description='This is inactive',
            venue_type='cafe',
            address='999 Closed St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98103',
            capacity=20,
            setup_stations=10,
            is_active=False,
            is_verified=True,
            hourly_rate=Decimal('40.00')
        )
        
        # Create unverified venue (should not appear)
        self.venue_unverified = Venue.objects.create(
            name='Unverified Venue',
            slug='unverified-venue',
            description='Not verified yet',
            venue_type='cafe',
            address='888 Pending Ave',
            city='Portland',
            state='OR',
            country='USA',
            postal_code='97202',
            capacity=25,
            setup_stations=12,
            is_active=True,
            is_verified=False,
            hourly_rate=Decimal('45.00')
        )
    
    def test_venue_list_displays_only_active_verified(self):
        """Test that only active and verified venues are displayed"""
        response = self.client.get(reverse('venues:list'))
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 3)
        
        # Check that active and verified venues are present
        self.assertIn(self.venue1, venues)
        self.assertIn(self.venue2, venues)
        self.assertIn(self.venue3, venues)
        
        # Check that inactive and unverified venues are not present
        self.assertNotIn(self.venue_inactive, venues)
        self.assertNotIn(self.venue_unverified, venues)
    
    def test_filter_by_city(self):
        """Test filtering venues by city"""
        response = self.client.get(reverse('venues:list'), {'city': 'Seattle'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 2)
        
        # Only Seattle venues should be present
        self.assertIn(self.venue1, venues)
        self.assertIn(self.venue3, venues)
        self.assertNotIn(self.venue2, venues)
    
    def test_filter_by_venue_type(self):
        """Test filtering venues by type"""
        response = self.client.get(reverse('venues:list'), {'venue_type': 'cafe'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 1)
        self.assertIn(self.venue2, venues)
    
    def test_filter_by_min_capacity(self):
        """Test filtering venues by minimum capacity"""
        response = self.client.get(reverse('venues:list'), {'min_capacity': '50'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 2)
        
        # Only venues with capacity >= 50
        self.assertIn(self.venue1, venues)
        self.assertIn(self.venue3, venues)
        self.assertNotIn(self.venue2, venues)
    
    def test_filter_multiple_criteria(self):
        """Test applying multiple filters simultaneously"""
        response = self.client.get(reverse('venues:list'), {
            'city': 'Seattle',
            'venue_type': 'esports_arena'
        })
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 1)
        self.assertIn(self.venue1, venues)
    
    def test_search_by_name(self):
        """Test searching venues by name"""
        response = self.client.get(reverse('venues:list'), {'search': 'Alpha'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 1)
        self.assertIn(self.venue1, venues)
    
    def test_search_by_city(self):
        """Test searching venues by city in search field"""
        response = self.client.get(reverse('venues:list'), {'search': 'Portland'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 1)
        self.assertIn(self.venue2, venues)
    
    def test_search_by_address(self):
        """Test searching venues by address"""
        response = self.client.get(reverse('venues:list'), {'search': 'Pine'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 1)
        self.assertIn(self.venue3, venues)
    
    def test_search_combined_with_filters(self):
        """Test combining search with filters"""
        response = self.client.get(reverse('venues:list'), {
            'search': 'Gaming',
            'city': 'Seattle'
        })
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 2)
        self.assertIn(self.venue1, venues)
        self.assertIn(self.venue3, venues)
    
    def test_no_results_message(self):
        """Test that appropriate message is shown when no venues match"""
        response = self.client.get(reverse('venues:list'), {'city': 'NonexistentCity'})
        self.assertEqual(response.status_code, 200)
        
        venues = response.context['venues']
        self.assertEqual(venues.count(), 0)
    
    def test_context_contains_filter_options(self):
        """Test that context includes filter options"""
        response = self.client.get(reverse('venues:list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that cities are in context
        self.assertIn('cities', response.context)
        cities = list(response.context['cities'])
        self.assertIn('Seattle', cities)
        self.assertIn('Portland', cities)
        
        # Check that venue types are in context
        self.assertIn('venue_types', response.context)
    
    def test_current_filter_values_in_context(self):
        """Test that current filter values are passed to context"""
        response = self.client.get(reverse('venues:list'), {
            'city': 'Seattle',
            'venue_type': 'esports_arena',
            'min_capacity': '50',
            'search': 'Gaming'
        })
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['current_city'], 'Seattle')
        self.assertEqual(response.context['current_venue_type'], 'esports_arena')
        self.assertEqual(response.context['current_min_capacity'], '50')
        self.assertEqual(response.context['current_search'], 'Gaming')



class VenueDetailViewTests(TestCase):
    """
    Test venue detail view.
    
    Validates:
    - Requirements 2.1-2.8: Display comprehensive venue information
    - Slug-based lookup
    - View count increment
    - Average rating calculation
    - Authentication status
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test gaming arena for tournaments',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            phone='555-1234',
            email='test@venue.com',
            website='https://testvenue.com',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00'),
            latitude=Decimal('47.606209'),
            longitude=Decimal('-122.332069'),
            amenities=['WiFi', 'Parking', 'Food/Drinks'],
            hours_of_operation={'monday': '9AM-10PM', 'tuesday': '9AM-10PM'}
        )
        
        # Create venue without photo and coordinates
        self.venue_minimal = Venue.objects.create(
            name='Minimal Venue',
            slug='minimal-venue',
            description='Minimal venue',
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
            hourly_rate=Decimal('50.00')
        )
        
        # Create reviews for average rating test
        self.user2 = User.objects.create_user(
            username='reviewer1',
            email='reviewer1@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='reviewer2',
            email='reviewer2@example.com',
            password='testpass123'
        )
        
        VenueReview.objects.create(
            venue=self.venue,
            user=self.user2,
            rating=5,
            title='Excellent venue',
            review='Great place for tournaments',
            would_recommend=True
        )
        VenueReview.objects.create(
            venue=self.venue,
            user=self.user3,
            rating=4,
            title='Good venue',
            review='Nice facilities',
            would_recommend=True
        )
    
    def test_venue_detail_lookup_by_slug(self):
        """Test that venue is looked up by slug"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['venue'].slug, 'test-gaming-arena')
        self.assertEqual(response.context['venue'].name, 'Test Gaming Arena')
    
    def test_venue_detail_404_for_invalid_slug(self):
        """Test that 404 is returned for non-existent slug"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'nonexistent-venue'}))
        self.assertEqual(response.status_code, 404)
    
    def test_venue_detail_404_for_inactive_venue(self):
        """Test that inactive venues return 404"""
        inactive_venue = Venue.objects.create(
            name='Inactive Venue',
            slug='inactive-venue',
            description='This is inactive',
            venue_type='cafe',
            address='999 Closed St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98103',
            capacity=20,
            setup_stations=10,
            is_active=False,
            is_verified=True,
            hourly_rate=Decimal('40.00')
        )
        
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'inactive-venue'}))
        self.assertEqual(response.status_code, 404)
    
    def test_view_count_increments_on_visit(self):
        """Test that view_count increments on each visit"""
        initial_count = self.venue.view_count
        
        # Visit the venue detail page
        self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        
        # Refresh from database
        self.venue.refresh_from_db()
        self.assertEqual(self.venue.view_count, initial_count + 1)
        
        # Visit again
        self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.venue.refresh_from_db()
        self.assertEqual(self.venue.view_count, initial_count + 2)
    
    def test_average_rating_calculation(self):
        """Test that average rating is calculated correctly"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        # Average of 5 and 4 should be 4.5
        self.assertEqual(response.context['average_rating'], 4.5)
        self.assertEqual(response.context['review_count'], 2)
    
    def test_average_rating_zero_when_no_reviews(self):
        """Test that average rating is 0 when there are no reviews"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'minimal-venue'}))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(response.context['average_rating'], 0)
        self.assertEqual(response.context['review_count'], 0)
    
    def test_authentication_status_for_authenticated_user(self):
        """Test that authentication status is True for logged-in users"""
        # Force login using the user object directly
        self.client.force_login(self.user)
        
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        # Check if user is authenticated in the request
        self.assertTrue(response.wsgi_request.user.is_authenticated, "User not authenticated in request")
        self.assertTrue(response.context['is_authenticated'])
    
    def test_authentication_status_for_anonymous_user(self):
        """Test that authentication status is False for anonymous users"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(response.context['is_authenticated'])
    
    def test_venue_detail_displays_all_information(self):
        """Test that all venue information is available in context"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        venue = response.context['venue']
        
        # Basic info (Requirements 2.1)
        self.assertEqual(venue.name, 'Test Gaming Arena')
        self.assertEqual(venue.description, 'A test gaming arena for tournaments')
        self.assertEqual(venue.venue_type, 'esports_arena')
        
        # Address (Requirements 2.1)
        self.assertEqual(venue.address, '123 Test St')
        self.assertEqual(venue.city, 'Seattle')
        self.assertEqual(venue.state, 'WA')
        self.assertEqual(venue.country, 'USA')
        self.assertEqual(venue.postal_code, '98101')
        
        # Capacity and stations (Requirements 2.2)
        self.assertEqual(venue.capacity, 100)
        self.assertEqual(venue.setup_stations, 50)
        
        # Amenities and hours (Requirements 2.2)
        self.assertEqual(venue.amenities, ['WiFi', 'Parking', 'Food/Drinks'])
        self.assertEqual(venue.hours_of_operation, {'monday': '9AM-10PM', 'tuesday': '9AM-10PM'})
        
        # Contact info (Requirements 2.3)
        self.assertEqual(venue.phone, '555-1234')
        self.assertEqual(venue.email, 'test@venue.com')
        self.assertEqual(venue.website, 'https://testvenue.com')
        
        # Pricing (Requirements 2.4)
        self.assertEqual(venue.hourly_rate, Decimal('150.00'))
        self.assertEqual(venue.day_rate, Decimal('1000.00'))
        
        # Coordinates (Requirements 2.7)
        self.assertEqual(venue.latitude, Decimal('47.606209'))
        self.assertEqual(venue.longitude, Decimal('-122.332069'))
    
    def test_venue_with_photo(self):
        """Test that venue with photo has photo field populated"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        venue = response.context['venue']
        # Photo field exists (even if empty in test)
        self.assertIsNotNone(venue.photo)
    
    def test_venue_without_coordinates(self):
        """Test that venue without coordinates has None values"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'minimal-venue'}))
        self.assertEqual(response.status_code, 200)
        
        venue = response.context['venue']
        self.assertIsNone(venue.latitude)
        self.assertIsNone(venue.longitude)
    
    def test_user_has_reviewed_flag_for_authenticated_user_with_review(self):
        """Test that user_has_reviewed is True when user has reviewed"""
        # Force login using the user object directly
        self.client.force_login(self.user2)
        
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        # Check if user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated, "User not authenticated in request")
        self.assertTrue(response.context['user_has_reviewed'])
    
    def test_user_has_reviewed_flag_for_authenticated_user_without_review(self):
        """Test that user_has_reviewed is False when user hasn't reviewed"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(response.context['user_has_reviewed'])
    
    def test_user_has_reviewed_flag_for_anonymous_user(self):
        """Test that user_has_reviewed is False for anonymous users"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        self.assertFalse(response.context['user_has_reviewed'])
    
    def test_reviews_displayed_in_context(self):
        """Test that reviews are included in context"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        reviews = response.context['reviews']
        self.assertEqual(len(reviews), 2)
    
    def test_map_displayed_when_coordinates_exist(self):
        """Test that map is displayed when venue has latitude and longitude (Requirement 2.7)"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'test-gaming-arena'}))
        self.assertEqual(response.status_code, 200)
        
        # Check that venue has coordinates
        venue = response.context['venue']
        self.assertIsNotNone(venue.latitude)
        self.assertIsNotNone(venue.longitude)
        
        # Check that map div is in the rendered HTML
        self.assertContains(response, 'id="venue-map"')
        
        # Check that Leaflet JavaScript is included
        self.assertContains(response, 'leaflet.js')
        self.assertContains(response, 'L.map')
        
        # Check that coordinates are passed to JavaScript
        self.assertContains(response, str(venue.latitude))
        self.assertContains(response, str(venue.longitude))
    
    def test_map_not_displayed_when_coordinates_missing(self):
        """Test that map is not displayed when venue lacks coordinates (Requirement 2.7)"""
        response = self.client.get(reverse('venues:detail', kwargs={'slug': 'minimal-venue'}))
        self.assertEqual(response.status_code, 200)
        
        # Check that venue has no coordinates
        venue = response.context['venue']
        self.assertIsNone(venue.latitude)
        self.assertIsNone(venue.longitude)
        
        # Check that map div is NOT in the rendered HTML
        self.assertNotContains(response, 'id="venue-map"')
        
        # Check that Leaflet JavaScript is NOT included
        self.assertNotContains(response, 'L.map')



class BookingCreateViewTests(TestCase):
    """
    Test booking creation view.
    
    Validates:
    - Requirements 3.1: Display booking form for authenticated users
    - Requirements 3.3: Create booking with status='pending'
    - Requirements 3.8: Redirect to booking confirmation on success
    - Requirements 3.9: Require authentication via LoginRequiredMixin
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test gaming arena',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
    
    def test_booking_create_requires_authentication(self):
        """Test that unauthenticated users are redirected to login (Requirement 3.9)"""
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_booking_create_displays_form_for_authenticated_user(self):
        """Test that authenticated users can access the booking form (Requirement 3.1)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_form.html')
        self.assertIn('form', response.context)
        self.assertIn('venue', response.context)
        self.assertEqual(response.context['venue'], self.venue)
    
    def test_booking_create_sets_pending_status(self):
        """Test that new bookings are created with status='pending' (Requirement 3.3)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        })
        
        # Should redirect to booking detail
        self.assertEqual(response.status_code, 302)
        
        # Check that booking was created with pending status
        booking = VenueBooking.objects.filter(venue=self.venue, booked_by=self.user).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'pending')
    
    def test_booking_create_sets_booked_by(self):
        """Test that booked_by is set to the current user"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        })
        
        # Check that booking was created with correct user
        booking = VenueBooking.objects.filter(venue=self.venue).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.booked_by, self.user)
    
    def test_booking_create_calculates_total_cost_hourly(self):
        """Test that total_cost is calculated correctly for hourly bookings"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)  # 4 hours
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        })
        
        # Check that total_cost is calculated correctly (4 hours * $150/hour = $600)
        booking = VenueBooking.objects.filter(venue=self.venue).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.total_cost, Decimal('600.00'))
    
    def test_booking_create_calculates_total_cost_daily(self):
        """Test that total_cost uses day rate for 8+ hour bookings"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=10)  # 10 hours (should use day rate)
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        })
        
        # Check that total_cost uses day rate ($1000)
        booking = VenueBooking.objects.filter(venue=self.venue).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.total_cost, Decimal('1000.00'))
    
    def test_booking_create_redirects_to_confirmation(self):
        """Test that successful booking redirects to booking detail page (Requirement 3.8)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        })
        
        # Should redirect to booking detail
        self.assertEqual(response.status_code, 302)
        
        booking = VenueBooking.objects.filter(venue=self.venue).first()
        self.assertIsNotNone(booking)
        
        expected_url = reverse('venues:booking_detail', kwargs={'pk': booking.pk})
        self.assertRedirects(response, expected_url)
    
    def test_booking_create_displays_success_message(self):
        """Test that success message is displayed after booking creation"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        response = self.client.post(url, {
            'start_datetime': start.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end.strftime('%Y-%m-%dT%H:%M'),
            'expected_participants': 50,
            'notes': 'Test booking'
        }, follow=True)
        
        # Check for success message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Booking created successfully!')
    
    def test_booking_create_form_uses_venue_booking_form(self):
        """Test that the view uses VenueBookingForm with proper validation"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        response = self.client.get(url)
        
        # Check that form is VenueBookingForm
        from venues.forms import VenueBookingForm
        self.assertIsInstance(response.context['form'], VenueBookingForm)



class BookingDetailViewTests(TestCase):
    """
    Test booking detail/confirmation view.
    
    Validates:
    - Requirements 3.8: Booking confirmation page
    - Requirements 4.6: Display complete booking information
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test gaming arena',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
        
        # Create test booking
        from datetime import timedelta
        from django.utils import timezone
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=4)
        
        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=start,
            end_datetime=end,
            expected_participants=50,
            total_cost=Decimal('600.00'),
            status='pending',
            notes='Test booking notes'
        )
    
    def test_booking_detail_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_booking_detail_displays_for_owner(self):
        """Test that booking owner can view booking details"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_detail.html')
        self.assertEqual(response.context['booking'], self.booking)
    
    def test_booking_detail_404_for_non_owner(self):
        """Test that non-owners cannot view other users' bookings"""
        self.client.force_login(self.other_user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        # Should return 404 (not found in user's bookings)
        self.assertEqual(response.status_code, 404)
    
    def test_booking_detail_displays_all_information(self):
        """Test that all booking information is displayed (Requirement 4.6)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that booking details are in the response
        self.assertContains(response, str(self.booking.id))
        self.assertContains(response, self.booking.venue.name)
        self.assertContains(response, str(self.booking.expected_participants))
        self.assertContains(response, str(self.booking.total_cost))
        self.assertContains(response, self.booking.notes)
        self.assertContains(response, self.booking.get_status_display().upper())
    
    def test_booking_detail_shows_cancel_button_for_pending(self):
        """Test that cancel button is shown for pending bookings"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CANCEL BOOKING')
    
    def test_booking_detail_hides_cancel_button_for_confirmed(self):
        """Test that cancel button is hidden for confirmed bookings"""
        self.booking.status = 'confirmed'
        self.booking.save()
        
        self.client.force_login(self.user)
        url = reverse('venues:booking_detail', kwargs={'pk': self.booking.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'CANCEL BOOKING')



class BookingListViewTests(TestCase):
    """
    Test booking list view.
    
    Validates:
    - Requirements 4.1: Display bookings filtered by current user
    - Requirements 4.3: Group bookings by status
    - Task 7.1: Order by start_datetime descending
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test gaming arena',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
        
        # Create bookings for the test user with different statuses
        from datetime import timedelta
        from django.utils import timezone
        
        now = timezone.now()
        
        # Pending booking (most recent)
        self.booking_pending = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=now + timedelta(days=5),
            end_datetime=now + timedelta(days=5, hours=4),
            expected_participants=50,
            total_cost=Decimal('600.00'),
            status='pending',
            notes='Pending booking'
        )
        
        # Confirmed booking
        self.booking_confirmed = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=now + timedelta(days=3),
            end_datetime=now + timedelta(days=3, hours=4),
            expected_participants=40,
            total_cost=Decimal('600.00'),
            status='confirmed',
            notes='Confirmed booking'
        )
        
        # Cancelled booking
        self.booking_cancelled = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=now + timedelta(days=2),
            end_datetime=now + timedelta(days=2, hours=4),
            expected_participants=30,
            total_cost=Decimal('600.00'),
            status='cancelled',
            notes='Cancelled booking',
            cancelled_at=now
        )
        
        # Completed booking (oldest)
        self.booking_completed = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=now - timedelta(days=1),
            end_datetime=now - timedelta(days=1, hours=4),
            expected_participants=60,
            total_cost=Decimal('600.00'),
            status='completed',
            notes='Completed booking'
        )
        
        # Create booking for other user (should not appear)
        self.other_booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.other_user,
            start_datetime=now + timedelta(days=4),
            end_datetime=now + timedelta(days=4, hours=4),
            expected_participants=50,
            total_cost=Decimal('600.00'),
            status='pending',
            notes='Other user booking'
        )
    
    def test_booking_list_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_booking_list_filters_by_current_user(self):
        """Test that only current user's bookings are displayed (Requirement 4.1)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get all bookings from context
        bookings = response.context['bookings']
        
        # Should have 4 bookings for the test user
        self.assertEqual(bookings.count(), 4)
        
        # Check that user's bookings are present
        self.assertIn(self.booking_pending, bookings)
        self.assertIn(self.booking_confirmed, bookings)
        self.assertIn(self.booking_cancelled, bookings)
        self.assertIn(self.booking_completed, bookings)
        
        # Check that other user's booking is NOT present
        self.assertNotIn(self.other_booking, bookings)
    
    def test_booking_list_groups_by_status(self):
        """Test that bookings are grouped by status (Requirement 4.3)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check pending bookings
        pending = response.context['pending_bookings']
        self.assertEqual(pending.count(), 1)
        self.assertIn(self.booking_pending, pending)
        
        # Check confirmed bookings
        confirmed = response.context['confirmed_bookings']
        self.assertEqual(confirmed.count(), 1)
        self.assertIn(self.booking_confirmed, confirmed)
        
        # Check cancelled bookings
        cancelled = response.context['cancelled_bookings']
        self.assertEqual(cancelled.count(), 1)
        self.assertIn(self.booking_cancelled, cancelled)
        
        # Check completed bookings
        completed = response.context['completed_bookings']
        self.assertEqual(completed.count(), 1)
        self.assertIn(self.booking_completed, completed)
    
    def test_booking_list_orders_by_start_datetime_descending(self):
        """Test that bookings are ordered by start_datetime descending (Task 7.1)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get all bookings
        bookings = list(response.context['bookings'])
        
        # Should be ordered by start_datetime descending (most recent first)
        # Order: pending (day 5), confirmed (day 3), cancelled (day 2), completed (day -1)
        self.assertEqual(bookings[0], self.booking_pending)
        self.assertEqual(bookings[1], self.booking_confirmed)
        self.assertEqual(bookings[2], self.booking_cancelled)
        self.assertEqual(bookings[3], self.booking_completed)
    
    def test_booking_list_displays_empty_state(self):
        """Test that empty state is displayed when user has no bookings"""
        # Create a new user with no bookings
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        self.client.force_login(new_user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should have no bookings
        bookings = response.context['bookings']
        self.assertEqual(bookings.count(), 0)
        
        # Check that empty state message is displayed
        self.assertContains(response, "You don't have any bookings yet")
    
    def test_booking_list_uses_correct_template(self):
        """Test that the correct template is used"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'venues/booking_list.html')
    
    def test_booking_list_displays_venue_information(self):
        """Test that venue information is displayed for each booking (Requirement 4.2)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that venue name is displayed
        self.assertContains(response, self.venue.name)
        
        # Check that booking details are displayed
        self.assertContains(response, str(self.booking_pending.expected_participants))
        self.assertContains(response, str(self.booking_pending.total_cost))
    
    def test_booking_list_displays_status_for_each_booking(self):
        """Test that status is displayed for each booking (Requirement 4.2)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that status labels are displayed
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Confirmed')
        self.assertContains(response, 'Cancelled')
        self.assertContains(response, 'Completed')
    
    def test_booking_list_shows_cancel_button_for_pending(self):
        """Test that cancel button is shown for pending bookings (Requirement 4.4)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that cancel button is present
        self.assertContains(response, 'Cancel Booking')
        
        # Check that cancel form action points to the correct URL
        cancel_url = reverse('venues:booking_cancel', kwargs={'pk': self.booking_pending.pk})
        self.assertContains(response, cancel_url)
    
    def test_booking_list_uses_select_related_for_performance(self):
        """Test that select_related is used to optimize database queries"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_list')
        
        # Count queries
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        
        # Should use select_related to minimize queries
        # With select_related('venue'), we should have reasonable query count
        # Base queries: session, user, bookings with venue (1 query due to select_related)
        # Additional queries for auth, messages, etc.
        self.assertLess(len(queries), 20)  # Reasonable threshold for this view



class BookingCancelViewTests(TestCase):
    """
    Test booking cancellation view.
    
    Validates:
    - Requirements 4.5: Update booking status to cancelled
    - Requirements 11.4: Verify user ownership
    """
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='Test description',
            venue_type='esports_arena',
            owner=self.user,
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            setup_stations=10,
            is_active=True,
            is_verified=True,
            hourly_rate=100.00,
            day_rate=800.00
        )
        
        # Create pending booking
        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=4),
            expected_participants=20,
            total_cost=400.00,
            status='pending'
        )
    
    def test_cancel_booking_success(self):
        """Test successfully cancelling a pending booking (Requirement 4.5)"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check status is updated
        self.assertEqual(self.booking.status, 'cancelled')
        
        # Check cancelled_at is set
        self.assertIsNotNone(self.booking.cancelled_at)
        
        # Check success message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Booking cancelled successfully.')
    
    def test_cancel_booking_unauthorized_user(self):
        """Test that users cannot cancel other users' bookings (Requirement 11.4)"""
        self.client.force_login(self.other_user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check status is NOT updated
        self.assertEqual(self.booking.status, 'pending')
        
        # Check cancelled_at is NOT set
        self.assertIsNone(self.booking.cancelled_at)
        
        # Check error message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'You do not have permission to cancel this booking.')
    
    def test_cancel_booking_requires_authentication(self):
        """Test that unauthenticated users are redirected to login"""
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
    
    def test_cancel_confirmed_booking_fails(self):
        """Test that confirmed bookings cannot be cancelled"""
        self.booking.status = 'confirmed'
        self.booking.save()
        
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check status is NOT changed
        self.assertEqual(self.booking.status, 'confirmed')
        
        # Check error message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Only pending bookings can be cancelled.')
    
    def test_cancel_completed_booking_fails(self):
        """Test that completed bookings cannot be cancelled"""
        self.booking.status = 'completed'
        self.booking.save()
        
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check status is NOT changed
        self.assertEqual(self.booking.status, 'completed')
        
        # Check error message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Only pending bookings can be cancelled.')
    
    def test_cancel_already_cancelled_booking_fails(self):
        """Test that already cancelled bookings cannot be cancelled again"""
        self.booking.status = 'cancelled'
        self.booking.cancelled_at = timezone.now()
        self.booking.save()
        
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        response = self.client.post(url)
        
        # Should redirect to booking list
        self.assertRedirects(response, reverse('venues:booking_list'))
        
        # Check error message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Only pending bookings can be cancelled.')
    
    def test_cancel_nonexistent_booking_returns_404(self):
        """Test that cancelling a non-existent booking returns 404"""
        self.client.force_login(self.user)
        import uuid
        fake_uuid = uuid.uuid4()
        url = reverse('venues:booking_cancel', kwargs={'pk': fake_uuid})
        
        response = self.client.post(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
    
    def test_cancel_booking_sets_timestamp(self):
        """Test that cancelled_at timestamp is set correctly"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        # Record time before cancellation
        before_cancel = timezone.now()
        
        response = self.client.post(url)
        
        # Record time after cancellation
        after_cancel = timezone.now()
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check cancelled_at is between before and after times
        self.assertIsNotNone(self.booking.cancelled_at)
        self.assertGreaterEqual(self.booking.cancelled_at, before_cancel)
        self.assertLessEqual(self.booking.cancelled_at, after_cancel)
    
    def test_cancel_booking_only_accepts_post(self):
        """Test that GET requests to cancel URL don't cancel bookings"""
        self.client.force_login(self.user)
        url = reverse('venues:booking_cancel', kwargs={'pk': self.booking.pk})
        
        # Try GET request
        response = self.client.get(url)
        
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
        
        # Refresh booking from database
        self.booking.refresh_from_db()
        
        # Check status is NOT changed
        self.assertEqual(self.booking.status, 'pending')
        self.assertIsNone(self.booking.cancelled_at)



class VenueReviewSubmissionTests(TestCase):
    """
    Test review submission functionality in VenueDetailView.
    
    Validates:
    - Requirements 5.1: Review submission for authenticated users
    - Requirements 5.3, 5.4: Associate review with user and venue
    - Requirements 5.5: Check for existing review (unique constraint)
    - Requirements 5.7: Update venue average rating
    """
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Gaming Arena',
            slug='test-gaming-arena',
            description='A test gaming arena',
            venue_type='esports_arena',
            address='123 Test St',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            capacity=100,
            setup_stations=50,
            is_active=True,
            is_verified=True,
            hourly_rate=Decimal('150.00'),
            day_rate=Decimal('1000.00')
        )
    
    def test_review_submission_requires_authentication(self):
        """Test that unauthenticated users cannot submit reviews (Requirement 5.1)"""
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.post(url, {
            'rating': 5,
            'title': 'Great venue',
            'review': 'Excellent facilities and staff',
            'would_recommend': True
        })
        
        # Should redirect to venue detail with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that no review was created
        self.assertEqual(VenueReview.objects.count(), 0)
    
    def test_review_submission_creates_review(self):
        """Test that valid review submission creates a review (Requirements 5.3, 5.4)"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.post(url, {
            'rating': 5,
            'title': 'Great venue',
            'review': 'Excellent facilities and staff',
            'would_recommend': True
        })
        
        # Should redirect back to venue detail
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.venue.slug, response.url)
        
        # Check that review was created
        self.assertEqual(VenueReview.objects.count(), 1)
        
        review = VenueReview.objects.first()
        self.assertEqual(review.venue, self.venue)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Great venue')
        self.assertEqual(review.review, 'Excellent facilities and staff')
        self.assertTrue(review.would_recommend)
    
    def test_review_submission_associates_user_and_venue(self):
        """Test that review is correctly associated with user and venue (Requirements 5.3, 5.4)"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        self.client.post(url, {
            'rating': 4,
            'title': 'Good venue',
            'review': 'Nice place',
            'would_recommend': True
        })
        
        review = VenueReview.objects.first()
        
        # Check associations
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.venue, self.venue)
        
        # Check reverse relationships
        self.assertIn(review, self.user.venue_reviews.all())
        self.assertIn(review, self.venue.reviews.all())
    
    def test_review_submission_prevents_duplicates(self):
        """Test that users cannot submit multiple reviews for same venue (Requirement 5.5)"""
        # Create first review
        VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=5,
            title='First review',
            review='My first review',
            would_recommend=True
        )
        
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        # Try to submit second review
        response = self.client.post(url, {
            'rating': 4,
            'title': 'Second review',
            'review': 'Trying to submit again',
            'would_recommend': True
        })
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Check that only one review exists
        self.assertEqual(VenueReview.objects.filter(venue=self.venue, user=self.user).count(), 1)
        
        # Check that the original review is unchanged
        review = VenueReview.objects.get(venue=self.venue, user=self.user)
        self.assertEqual(review.title, 'First review')
    
    def test_review_submission_updates_average_rating(self):
        """Test that submitting a review updates venue average rating (Requirement 5.7)"""
        # Create first review
        VenueReview.objects.create(
            venue=self.venue,
            user=self.user2,
            rating=4,
            title='Good venue',
            review='Nice place',
            would_recommend=True
        )
        
        # Submit second review
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        self.client.post(url, {
            'rating': 5,
            'title': 'Great venue',
            'review': 'Excellent facilities',
            'would_recommend': True
        })
        
        # Get venue detail page to check average rating
        response = self.client.get(url)
        
        # Average of 4 and 5 should be 4.5
        self.assertEqual(response.context['average_rating'], 4.5)
        self.assertEqual(response.context['review_count'], 2)
    
    def test_review_submission_with_invalid_rating(self):
        """Test that invalid rating is rejected"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        # Try to submit review with rating > 5
        response = self.client.post(url, {
            'rating': 6,
            'title': 'Great venue',
            'review': 'Excellent facilities',
            'would_recommend': True
        })
        
        # Should re-render with form errors (status 200)
        self.assertEqual(response.status_code, 200)
        
        # Check that no review was created
        self.assertEqual(VenueReview.objects.count(), 0)
        
        # Check that form errors are in context
        self.assertIn('review_form', response.context)
        self.assertTrue(response.context['review_form'].errors)
    
    def test_review_submission_with_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        # Try to submit review without title
        response = self.client.post(url, {
            'rating': 5,
            'review': 'Excellent facilities',
            'would_recommend': True
        })
        
        # Should re-render with form errors
        self.assertEqual(response.status_code, 200)
        
        # Check that no review was created
        self.assertEqual(VenueReview.objects.count(), 0)
    
    def test_review_form_displayed_for_authenticated_user_without_review(self):
        """Test that review form is shown to authenticated users who haven't reviewed"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.get(url)
        
        # Check that review form is in context
        self.assertIn('review_form', response.context)
        self.assertFalse(response.context['user_has_reviewed'])
    
    def test_review_form_not_displayed_for_user_with_existing_review(self):
        """Test that review form is not shown to users who already reviewed"""
        # Create existing review
        VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=5,
            title='My review',
            review='Already reviewed',
            would_recommend=True
        )
        
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.get(url)
        
        # Check that review form is NOT in context
        self.assertNotIn('review_form', response.context)
        self.assertTrue(response.context['user_has_reviewed'])
    
    def test_review_form_not_displayed_for_anonymous_user(self):
        """Test that review form is not shown to anonymous users"""
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.get(url)
        
        # Check that review form is NOT in context
        self.assertNotIn('review_form', response.context)
        self.assertFalse(response.context['user_has_reviewed'])
    
    def test_review_submission_with_would_recommend_false(self):
        """Test that would_recommend can be set to False"""
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        response = self.client.post(url, {
            'rating': 2,
            'title': 'Not great',
            'review': 'Could be better',
            'would_recommend': False
        })
        
        # Should redirect successfully
        self.assertEqual(response.status_code, 302)
        
        # Check that review was created with would_recommend=False
        review = VenueReview.objects.first()
        self.assertFalse(review.would_recommend)
    
    def test_multiple_users_can_review_same_venue(self):
        """Test that different users can review the same venue"""
        # User 1 submits review
        self.client.force_login(self.user)
        url = reverse('venues:detail', kwargs={'slug': self.venue.slug})
        
        self.client.post(url, {
            'rating': 5,
            'title': 'User 1 review',
            'review': 'Great place',
            'would_recommend': True
        })
        
        # User 2 submits review
        self.client.force_login(self.user2)
        
        self.client.post(url, {
            'rating': 4,
            'title': 'User 2 review',
            'review': 'Good place',
            'would_recommend': True
        })
        
        # Check that both reviews exist
        self.assertEqual(VenueReview.objects.filter(venue=self.venue).count(), 2)
        self.assertEqual(VenueReview.objects.filter(venue=self.venue, user=self.user).count(), 1)
        self.assertEqual(VenueReview.objects.filter(venue=self.venue, user=self.user2).count(), 1)
