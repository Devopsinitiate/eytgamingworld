"""
Tests for Venue views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
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
