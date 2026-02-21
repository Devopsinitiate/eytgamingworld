from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import VenueBooking, Venue, VenueReview


class VenueBookingForm(forms.ModelForm):
    """Form for creating venue bookings with validation"""
    
    class Meta:
        model = VenueBooking
        fields = ['start_datetime', 'end_datetime', 'expected_participants', 'notes', 'tournament']
        widgets = {
            'start_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-input',
                }
            ),
            'end_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-input',
                }
            ),
            'expected_participants': forms.NumberInput(
                attrs={
                    'min': '1',
                    'class': 'form-input',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-input',
                    'placeholder': 'Any special requirements or notes...',
                }
            ),
            'tournament': forms.Select(
                attrs={
                    'class': 'form-input',
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        self.venue = kwargs.pop('venue', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make tournament optional
        self.fields['tournament'].required = False
        
        # Filter tournaments to only show user's tournaments if user is provided
        if self.user:
            from tournaments.models import Tournament
            self.fields['tournament'].queryset = Tournament.objects.filter(
                organizer=self.user
            ).order_by('-created_at')
    
    def clean(self):
        """Validate the entire form"""
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        expected_participants = cleaned_data.get('expected_participants')
        
        # Validate date range (end > start)
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise ValidationError({
                    'end_datetime': 'End date must be after start date'
                })
        
        # Validate overlapping bookings
        if start_datetime and end_datetime and self.venue:
            overlapping = VenueBooking.objects.filter(
                venue=self.venue,
                status__in=['pending', 'confirmed']
            ).filter(
                Q(start_datetime__lt=end_datetime) & Q(end_datetime__gt=start_datetime)
            )
            
            # Exclude current booking if editing
            if self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            
            if overlapping.exists():
                raise ValidationError({
                    'start_datetime': 'This venue is already booked for the selected time period'
                })
        
        # Add capacity warning (not blocking, just a warning)
        if expected_participants and self.venue:
            if expected_participants > self.venue.capacity:
                self.add_warning('expected_participants', 
                               f'Warning: Expected participants ({expected_participants}) exceed venue capacity ({self.venue.capacity})')
        
        return cleaned_data
    
    def add_warning(self, field, message):
        """Add a warning message to a field (non-blocking)"""
        if not hasattr(self, '_warnings'):
            self._warnings = {}
        if field not in self._warnings:
            self._warnings[field] = []
        self._warnings[field].append(message)
    
    def get_warnings(self):
        """Get all warning messages"""
        return getattr(self, '_warnings', {})
    
    def calculate_cost(self):
        """Calculate total cost based on duration and venue rates"""
        if not self.venue:
            return Decimal('0.00')
        
        start_datetime = self.cleaned_data.get('start_datetime')
        end_datetime = self.cleaned_data.get('end_datetime')
        
        if not start_datetime or not end_datetime:
            return Decimal('0.00')
        
        # Calculate duration in hours
        duration = end_datetime - start_datetime
        duration_hours = Decimal(str(duration.total_seconds() / 3600))
        
        # If duration is 8 hours or more, use day rate
        if duration_hours >= 8 and self.venue.day_rate:
            # Calculate number of days (rounded up)
            import math
            num_days = math.ceil(float(duration_hours) / 24)
            return self.venue.day_rate * num_days
        
        # Otherwise use hourly rate
        if self.venue.hourly_rate:
            return self.venue.hourly_rate * duration_hours
        
        return Decimal('0.00')
    
    def save(self, commit=True):
        """Save the booking with calculated cost"""
        booking = super().save(commit=False)
        
        # Set the venue if provided
        if self.venue:
            booking.venue = self.venue
        
        # Set the user if provided
        if self.user:
            booking.booked_by = self.user
        
        # Calculate and set total cost
        if self.is_valid():
            booking.total_cost = self.calculate_cost()
        
        # Set status to pending
        booking.status = 'pending'
        
        if commit:
            booking.save()
        
        return booking


class VenueReviewForm(forms.ModelForm):
    """Form for submitting venue reviews with validation"""
    
    class Meta:
        model = VenueReview
        fields = ['rating', 'title', 'review', 'would_recommend']
        widgets = {
            'rating': forms.NumberInput(
                attrs={
                    'min': '1',
                    'max': '5',
                    'class': 'form-input',
                    'placeholder': 'Rate 1-5 stars',
                }
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Review title',
                    'maxlength': '200',
                }
            ),
            'review': forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-input',
                    'placeholder': 'Share your experience with this venue...',
                }
            ),
            'would_recommend': forms.CheckboxInput(
                attrs={
                    'class': 'form-checkbox',
                }
            ),
        }
    
    def clean_rating(self):
        """Validate rating is between 1 and 5"""
        rating = self.cleaned_data.get('rating')
        
        if rating is not None:
            if rating < 1 or rating > 5:
                raise ValidationError('Rating must be between 1 and 5 stars')
        
        return rating
