from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from core.models import User
import uuid


class Venue(models.Model):
    """Physical venue for local tournaments"""
    
    VENUE_TYPE_CHOICES = [
        ('gaming_lounge', 'Gaming Lounge'),
        ('esports_arena', 'Esports Arena'),
        ('cafe', 'Gaming Cafe'),
        ('convention_center', 'Convention Center'),
        ('community_center', 'Community Center'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    venue_type = models.CharField(max_length=30, choices=VENUE_TYPE_CHOICES, default='gaming_lounge')
    
    # Owner/Manager
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='owned_venues')
    
    # Location
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Coordinates (for mapping)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Capacity
    capacity = models.IntegerField(default=20, help_text="Maximum number of participants")
    setup_stations = models.IntegerField(default=10, help_text="Number of gaming stations/setups")
    
    # Media
    photo = models.ImageField(upload_to='venues/', null=True, blank=True)
    
    # Hours (stored as JSON)
    hours_of_operation = models.JSONField(default=dict, blank=True,
                                          help_text='e.g., {"monday": "9AM-10PM", ...}')
    
    # Amenities (stored as list)
    amenities = models.JSONField(default=list, blank=True,
                                 help_text='e.g., ["WiFi", "Parking", "Food/Drinks"]')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False, help_text="Verified by admin")
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    day_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'venues'
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'country']),
            models.Index(fields=['is_active', 'is_verified']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('venues:detail', kwargs={'slug': self.slug})
    
    @property
    def full_address(self):
        parts = [self.address, self.city]
        if self.state:
            parts.append(self.state)
        parts.extend([self.postal_code, self.country])
        return ', '.join(filter(None, parts))


class VenueBooking(models.Model):
    """Booking for venue usage"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venue_bookings')
    
    # Tournament (if applicable)
    tournament = models.ForeignKey('tournaments.Tournament', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='venue_bookings')
    
    # Booking details
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    expected_participants = models.IntegerField(default=0)
    
    # Payment
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Notes
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'venue_bookings'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['venue', 'status']),
            models.Index(fields=['start_datetime', 'end_datetime']),
        ]
    
    def __str__(self):
        return f"{self.venue.name} - {self.start_datetime.date()}"
    
    @property
    def duration_hours(self):
        """Calculate booking duration in hours"""
        delta = self.end_datetime - self.start_datetime
        return delta.total_seconds() / 3600


class VenueReview(models.Model):
    """User reviews for venues"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venue_reviews')
    
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)],
                                 help_text="1-5 stars")
    title = models.CharField(max_length=200)
    review = models.TextField()
    
    # Would recommend
    would_recommend = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'venue_reviews'
        ordering = ['-created_at']
        unique_together = ['venue', 'user']
    
    def __str__(self):
        return f"{self.venue.name} - {self.rating}★ by {self.user.get_display_name()}"