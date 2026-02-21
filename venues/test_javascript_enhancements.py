"""
Tests for JavaScript enhancements in venue templates.
Tests Requirements 3.4 (live cost calculator) and 5.2 (interactive star rating).
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from venues.models import Venue, VenueReview
from decimal import Decimal

User = get_user_model()


class BookingFormJavaScriptTests(TestCase):
    """Test JavaScript enhancements in booking form."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            owner=self.user,
            city='Test City',
            country='Test Country',
            address='123 Test St',
            capacity=100,
            setup_stations=50,
            hourly_rate=Decimal('50.00'),
            day_rate=Decimal('300.00'),
            is_active=True,
            is_verified=True
        )
        # Login before each test
        self.client.force_login(self.user)
    
    def test_booking_form_contains_cost_calculator_script(self):
        """Test that booking form includes live cost calculator JavaScript."""
        response = self.client.get(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Check for cost calculator elements
        self.assertIn('id="costAmount"', content)
        self.assertIn('Live Cost Calculator', content)
        
        # Check for JavaScript function
        self.assertIn('calculateCost', content)
        self.assertIn('addEventListener', content)
        
        # Check for rate variables
        self.assertIn('hourlyRate', content)
        self.assertIn('dayRate', content)
        
        # Check for animation class
        self.assertIn('updating', content)
    
    def test_cost_calculator_uses_venue_rates(self):
        """Test that cost calculator includes venue's hourly and day rates."""
        response = self.client.get(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        )
        
        content = response.content.decode('utf-8')
        
        # Check that venue rates are passed to JavaScript
        self.assertIn('50', content)  # hourly_rate
        self.assertIn('300', content)  # day_rate
    
    def test_cost_calculator_has_real_time_updates(self):
        """Test that cost calculator listens to input changes."""
        response = self.client.get(
            reverse('venues:booking_create', kwargs={'slug': self.venue.slug})
        )
        
        content = response.content.decode('utf-8')
        
        # Check for event listeners on both change and input events
        self.assertIn("addEventListener('change', calculateCost)", content)
        self.assertIn("addEventListener('input', calculateCost)", content)


class VenueDetailJavaScriptTests(TestCase):
    """Test JavaScript enhancements in venue detail page."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            owner=self.user,
            city='Test City',
            country='Test Country',
            address='123 Test St',
            capacity=100,
            setup_stations=50,
            hourly_rate=Decimal('50.00'),
            is_active=True,
            is_verified=True
        )
    
    def test_venue_detail_contains_star_rating_script(self):
        """Test that venue detail includes interactive star rating JavaScript."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('venues:detail', kwargs={'slug': self.venue.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Check for star rating elements
        self.assertIn('star-rating-input', content)
        self.assertIn('star-label', content)
        self.assertIn('star-radio', content)
        
        # Check for JavaScript functionality
        self.assertIn('highlightStars', content)
        self.assertIn('mouseenter', content)
        self.assertIn('mouseleave', content)
    
    def test_star_rating_has_hover_effects(self):
        """Test that star rating includes hover effect handling."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('venues:detail', kwargs={'slug': self.venue.slug})
        )
        
        content = response.content.decode('utf-8')
        
        # Check for hover functionality
        self.assertIn('mouseenter', content)
        self.assertIn('scale(1.1)', content)
        self.assertIn('transition', content)
    
    def test_star_rating_has_visual_feedback(self):
        """Test that star rating includes visual feedback (color and glow)."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('venues:detail', kwargs={'slug': self.venue.slug})
        )
        
        content = response.content.decode('utf-8')
        
        # Check for visual effects
        self.assertIn('#DC2626', content)  # Electric red color
        self.assertIn('drop-shadow', content)  # Glow effect
        self.assertIn('filter', content)


class VenueListJavaScriptTests(TestCase):
    """Test JavaScript enhancements in venue list page."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_venue_list_contains_filter_toggle_script(self):
        """Test that venue list includes filter toggle JavaScript for mobile."""
        response = self.client.get(reverse('venues:list'))
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Check for filter toggle functionality
        self.assertIn('toggleFilters', content)
        self.assertIn('filter-content', content)
        self.assertIn('aria-expanded', content)
    
    def test_venue_list_has_optional_live_filter_code(self):
        """Test that venue list includes optional live filter update code."""
        response = self.client.get(reverse('venues:list'))
        
        content = response.content.decode('utf-8')
        
        # Check for optional live filter functionality (commented out)
        self.assertIn('Live filter updates', content)
        self.assertIn('updateFilters', content)
        self.assertIn('debounce', content)
    
    def test_venue_list_has_smooth_animations(self):
        """Test that venue list includes smooth animation CSS."""
        response = self.client.get(reverse('venues:list'))
        
        content = response.content.decode('utf-8')
        
        # Check for animation CSS
        self.assertIn('transition', content)
        self.assertIn('transform', content)
        self.assertIn('hover', content)
