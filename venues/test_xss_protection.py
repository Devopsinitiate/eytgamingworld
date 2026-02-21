"""
Tests for XSS protection and HTML escaping in venue system.

Validates Requirement 11.6: User-generated content must be HTML escaped to prevent XSS attacks.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from venues.models import Venue, VenueReview, VenueBooking
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class XSSProtectionTests(TestCase):
    """Test that user-generated content is properly HTML escaped."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='ownerpass123'
        )
        
        # Create test venue
        self.venue = Venue.objects.create(
            name='Test Venue',
            slug='test-venue',
            description='A test venue',
            venue_type='esports_arena',
            owner=self.owner,
            address='123 Test St',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=100,
            setup_stations=20,
            hourly_rate=50.00,
            day_rate=400.00,
            is_active=True,
            is_verified=True
        )
    
    def test_review_title_escapes_script_tags(self):
        """Test that script tags in review titles are escaped."""
        # Create a review with malicious script tag in title
        malicious_title = '<script>alert("XSS")</script>Hacked'
        
        review = VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=5,
            title=malicious_title,
            review='Great venue!',
            would_recommend=True
        )
        
        # Get the venue detail page
        response = self.client.get(reverse('venues:detail', kwargs={'slug': self.venue.slug}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the raw script tag is NOT in the response
        self.assertNotContains(response, '<script>alert("XSS")</script>')
        
        # Check that the escaped version IS in the response
        self.assertContains(response, '&lt;script&gt;')
        self.assertContains(response, '&lt;/script&gt;')
    
    def test_review_text_escapes_html_tags(self):
        """Test that HTML tags in review text are escaped."""
        # Create a review with malicious HTML in review text
        malicious_review = '<img src=x onerror="alert(\'XSS\')">Bad image'
        
        review = VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=4,
            title='Test Review',
            review=malicious_review,
            would_recommend=True
        )
        
        # Get the venue detail page
        response = self.client.get(reverse('venues:detail', kwargs={'slug': self.venue.slug}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the raw img tag is NOT in the response
        self.assertNotContains(response, '<img src=x onerror=')
        
        # Check that the escaped version IS in the response
        self.assertContains(response, '&lt;img')
        self.assertContains(response, '&gt;')
    
    def test_booking_notes_escape_script_tags(self):
        """Test that script tags in booking notes are escaped."""
        # Force login as user (bypasses authentication backend)
        self.client.force_login(self.user)
        
        # Create a booking with malicious script in notes
        malicious_notes = '<script>document.cookie="stolen"</script>Important notes'
        
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)
        
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_datetime=start_time,
            end_datetime=end_time,
            expected_participants=50,
            total_cost=200.00,
            status='pending',
            notes=malicious_notes
        )
        
        # Get the booking detail page
        response = self.client.get(reverse('venues:booking_detail', kwargs={'pk': booking.pk}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the raw script tag is NOT in the response
        self.assertNotContains(response, '<script>document.cookie=')
        
        # Check that the escaped version IS in the response
        self.assertContains(response, '&lt;script&gt;')
    
    def test_venue_description_escapes_html(self):
        """Test that HTML in venue description is escaped."""
        # Update venue with malicious description
        malicious_description = '<iframe src="http://evil.com"></iframe>Great venue'
        self.venue.description = malicious_description
        self.venue.save()
        
        # Get the venue detail page
        response = self.client.get(reverse('venues:detail', kwargs={'slug': self.venue.slug}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the raw iframe tag is NOT in the response
        self.assertNotContains(response, '<iframe src="http://evil.com">')
        
        # Check that the escaped version IS in the response
        self.assertContains(response, '&lt;iframe')
        self.assertContains(response, '&lt;/iframe&gt;')
    
    def test_review_title_escapes_html_entities(self):
        """Test that HTML entities in review titles are properly escaped."""
        # Create a review with HTML entities
        title_with_entities = 'Great & "Amazing" <Venue>'
        
        review = VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=5,
            title=title_with_entities,
            review='Excellent!',
            would_recommend=True
        )
        
        # Get the venue detail page
        response = self.client.get(reverse('venues:detail', kwargs={'slug': self.venue.slug}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that special characters are escaped
        self.assertContains(response, '&amp;')  # & escaped
        self.assertContains(response, '&quot;')  # " escaped
        self.assertContains(response, '&lt;')  # < escaped
        self.assertContains(response, '&gt;')  # > escaped
    
    def test_multiple_xss_vectors_in_review(self):
        """Test multiple XSS attack vectors in a single review."""
        # Create a review with multiple XSS attempts
        malicious_title = '<script>alert(1)</script><img src=x onerror=alert(2)>'
        malicious_review = '''
        <script>alert(3)</script>
        <img src=x onerror="alert(4)">
        <iframe src="javascript:alert(5)"></iframe>
        <svg onload="alert(6)">
        <body onload="alert(7)">
        '''
        
        review = VenueReview.objects.create(
            venue=self.venue,
            user=self.user,
            rating=3,
            title=malicious_title,
            review=malicious_review,
            would_recommend=False
        )
        
        # Get the venue detail page
        response = self.client.get(reverse('venues:detail', kwargs={'slug': self.venue.slug}))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Verify none of the raw malicious tags are present
        self.assertNotContains(response, '<script>alert(')
        self.assertNotContains(response, 'onerror="alert(')
        # Note: javascript:alert( will appear in escaped form as part of the iframe src
        # We check that the iframe tag itself is escaped
        self.assertNotContains(response, '<svg onload=')
        self.assertNotContains(response, '<body onload=')
        
        # Verify escaped versions are present
        self.assertContains(response, '&lt;script&gt;')
        self.assertContains(response, '&lt;img')
        self.assertContains(response, '&lt;iframe')
        self.assertContains(response, '&lt;svg')
        self.assertContains(response, '&lt;body')
    
    def test_venue_name_in_card_escapes_html(self):
        """Test that venue names with HTML are escaped in venue cards."""
        # Create a venue with HTML in the name
        malicious_venue = Venue.objects.create(
            name='<b>Bold</b> Venue <script>alert("xss")</script>',
            slug='bold-venue',
            description='Test',
            venue_type='lan_center',
            owner=self.owner,
            address='456 Test Ave',
            city='Test City',
            state='TS',
            country='Test Country',
            postal_code='12345',
            capacity=50,
            setup_stations=10,
            hourly_rate=30.00,
            is_active=True,
            is_verified=True
        )
        
        # Get the venue list page
        response = self.client.get(reverse('venues:list'))
        
        # Check that the response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that the raw HTML tags are NOT in the response
        self.assertNotContains(response, '<b>Bold</b>')
        self.assertNotContains(response, '<script>alert("xss")</script>')
        
        # Check that the escaped version IS in the response
        self.assertContains(response, '&lt;b&gt;')
        self.assertContains(response, '&lt;/b&gt;')
        self.assertContains(response, '&lt;script&gt;')
