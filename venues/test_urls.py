"""
Test URL routing for venue system.
Validates Requirements 1.1, 2.1, 3.1, 4.1
"""
from django.test import TestCase
from django.urls import reverse, resolve
from venues import views


class VenueURLTests(TestCase):
    """Test that all venue URLs are properly configured"""
    
    def test_venue_list_url_resolves(self):
        """Test that venue list URL resolves to VenueListView"""
        url = reverse('venues:list')
        self.assertEqual(url, '/venues/')
        self.assertEqual(resolve(url).func.view_class, views.VenueListView)
    
    def test_venue_detail_url_resolves(self):
        """Test that venue detail URL resolves to VenueDetailView"""
        url = reverse('venues:detail', kwargs={'slug': 'test-venue'})
        self.assertEqual(url, '/venues/test-venue/')
        self.assertEqual(resolve(url).func.view_class, views.VenueDetailView)
    
    def test_booking_create_url_resolves(self):
        """Test that booking create URL resolves to BookingCreateView"""
        url = reverse('venues:booking_create', kwargs={'slug': 'test-venue'})
        self.assertEqual(url, '/venues/test-venue/book/')
        self.assertEqual(resolve(url).func.view_class, views.BookingCreateView)
    
    def test_booking_list_url_resolves(self):
        """Test that booking list URL resolves to BookingListView"""
        url = reverse('venues:booking_list')
        self.assertEqual(url, '/venues/bookings/')
        self.assertEqual(resolve(url).func.view_class, views.BookingListView)
    
    def test_booking_cancel_url_resolves(self):
        """Test that booking cancel URL resolves to BookingCancelView"""
        import uuid
        test_uuid = uuid.uuid4()
        url = reverse('venues:booking_cancel', kwargs={'pk': test_uuid})
        self.assertEqual(url, f'/venues/bookings/{test_uuid}/cancel/')
        self.assertEqual(resolve(url).func.view_class, views.BookingCancelView)
