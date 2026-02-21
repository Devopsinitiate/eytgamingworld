from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db import models
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Venue, VenueBooking, VenueReview
from .forms import VenueBookingForm


@method_decorator(cache_page(60 * 5), name='dispatch')  # Cache for 5 minutes
class VenueListView(ListView):
    """
    Display list of active and verified venues with filtering and search.
    
    Validates:
    - Requirements 1.1: Display all active and verified venues
    - Requirements 1.3-1.6: Filter by city, venue_type, min_capacity
    - Requirements 9.1, 9.3: Search functionality
    - Requirements 12.4: Cache venue list queries for 5 minutes
    """
    model = Venue
    template_name = 'venues/venue_list.html'
    context_object_name = 'venues'
    paginate_by = 12
    
    def get_queryset(self):
        """Filter venues by active/verified status and apply user filters with optimization"""
        queryset = Venue.objects.filter(is_active=True, is_verified=True).select_related('owner')
        
        # Apply filters from GET parameters
        city = self.request.GET.get('city')
        venue_type = self.request.GET.get('venue_type')
        min_capacity = self.request.GET.get('min_capacity')
        search = self.request.GET.get('search')
        
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        if venue_type:
            queryset = queryset.filter(venue_type=venue_type)
        
        if min_capacity:
            try:
                queryset = queryset.filter(capacity__gte=int(min_capacity))
            except ValueError:
                pass
        
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(city__icontains=search) |
                models.Q(address__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options to context"""
        context = super().get_context_data(**kwargs)
        
        # Get unique cities for filter dropdown
        context['cities'] = Venue.objects.filter(
            is_active=True, is_verified=True
        ).values_list('city', flat=True).distinct().order_by('city')
        
        # Venue type choices
        context['venue_types'] = Venue.VENUE_TYPE_CHOICES
        
        # Current filter values
        context['current_city'] = self.request.GET.get('city', '')
        context['current_venue_type'] = self.request.GET.get('venue_type', '')
        context['current_min_capacity'] = self.request.GET.get('min_capacity', '')
        context['current_search'] = self.request.GET.get('search', '')
        
        return context


class VenueDetailView(DetailView):
    """
    Display detailed venue information with booking capability.

    Validates:
    - Requirements 2.1-2.8: Display comprehensive venue information
    - Requirements 2.6: Display average rating and review count
    - Requirements 5.1, 5.3, 5.4, 5.5, 5.7: Review submission
    - Requirements 12.4: Cache venue detail data for 10 minutes
    """
    model = Venue
    template_name = 'venues/venue_detail.html'
    context_object_name = 'venue'

    def get_queryset(self):
        """Only show active venues with optimized queries"""
        return Venue.objects.filter(is_active=True).select_related('owner').prefetch_related('reviews')

    def get_object(self, queryset=None):
        """
        Get venue object with caching.
        Cache is invalidated when venue is updated.
        """
        slug = self.kwargs.get('slug')
        cache_key = f'venue_detail_{slug}'
        
        # Try to get from cache
        obj = cache.get(cache_key)
        
        if obj is None:
            # Not in cache, get from database
            obj = super().get_object(queryset)
            # Cache for 10 minutes
            cache.set(cache_key, obj, 60 * 10)
        
        # Increment view count (don't cache this)
        Venue.objects.filter(pk=obj.pk).update(view_count=models.F('view_count') + 1)
        obj.refresh_from_db(fields=['view_count'])
        
        return obj

    def get_context_data(self, **kwargs):
        """Add reviews and average rating to context"""
        from django.core.paginator import Paginator
        
        context = super().get_context_data(**kwargs)
        venue = self.object

        # Get all reviews ordered by most recent
        all_reviews = venue.reviews.all().order_by('-created_at')
        context['review_count'] = all_reviews.count()

        # Paginate reviews (10 per page)
        paginator = Paginator(all_reviews, 10)
        page_number = self.request.GET.get('page', 1)
        reviews_page = paginator.get_page(page_number)
        context['reviews'] = reviews_page

        # Calculate average rating
        if all_reviews.exists():
            context['average_rating'] = sum(r.rating for r in all_reviews) / all_reviews.count()
        else:
            context['average_rating'] = 0

        # Calculate rating distribution (count of each rating 1-5)
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in all_reviews:
            rating_distribution[review.rating] = rating_distribution.get(review.rating, 0) + 1
        context['rating_distribution'] = rating_distribution

        # Check if user is authenticated
        context['is_authenticated'] = self.request.user.is_authenticated

        # Check if user has already reviewed this venue
        if self.request.user.is_authenticated:
            context['user_has_reviewed'] = venue.reviews.filter(user=self.request.user).exists()
        else:
            context['user_has_reviewed'] = False

        # Add review form for authenticated users who haven't reviewed yet
        if self.request.user.is_authenticated and not context['user_has_reviewed']:
            from .forms import VenueReviewForm
            context['review_form'] = VenueReviewForm()

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle review submission.

        Validates:
        - Requirements 5.1: Review submission for authenticated users
        - Requirements 5.3, 5.4: Associate review with user and venue
        - Requirements 5.5: Check for existing review (unique constraint)
        - Requirements 5.7: Update venue average rating
        """
        from .forms import VenueReviewForm

        # Get the venue object
        self.object = self.get_object()
        venue = self.object

        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to submit a review.')
            return redirect('venues:detail', slug=venue.slug)

        # Check if user has already reviewed this venue
        if venue.reviews.filter(user=request.user).exists():
            messages.error(request, 'You have already reviewed this venue.')
            return redirect('venues:detail', slug=venue.slug)

        # Process the review form
        form = VenueReviewForm(request.POST)

        if form.is_valid():
            # Create review with user and venue associations
            review = form.save(commit=False)
            review.user = request.user
            review.venue = venue
            review.save()

            messages.success(request, 'Review submitted successfully!')
            return redirect('venues:detail', slug=venue.slug)
        else:
            # Form is invalid, re-render with errors
            context = self.get_context_data()
            context['review_form'] = form
            return self.render_to_response(context)



class BookingCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new venue booking.
    
    Validates:
    - Requirements 3.1: Display booking form for authenticated users
    - Requirements 3.3: Create booking with status='pending'
    - Requirements 3.8: Redirect to booking confirmation on success
    - Requirements 3.9: Require authentication via LoginRequiredMixin
    """
    model = VenueBooking
    form_class = VenueBookingForm
    template_name = 'venues/booking_form.html'
    
    def get_form_kwargs(self):
        """Pass venue and user to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['venue'] = get_object_or_404(Venue, slug=self.kwargs['slug'])
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add venue to context"""
        context = super().get_context_data(**kwargs)
        context['venue'] = get_object_or_404(Venue, slug=self.kwargs['slug'])
        
        # Add warnings from form if they exist
        if hasattr(context['form'], '_warnings'):
            context['warnings'] = context['form'].get_warnings()
        
        return context
    
    def form_valid(self, form):
        """
        Set booked_by and calculate total_cost.
        The form's save() method handles:
        - Setting venue
        - Setting booked_by
        - Setting status='pending'
        - Calculating total_cost
        """
        booking = form.save()
        messages.success(self.request, 'Booking created successfully!')
        return redirect('venues:booking_detail', pk=booking.pk)


class BookingListView(LoginRequiredMixin, ListView):
    """
    Display user's venue bookings.
    
    Validates:
    - Requirements 4.1-4.3: Display and group user bookings
    """
    model = VenueBooking
    template_name = 'venues/booking_list.html'
    context_object_name = 'bookings'
    
    def get_queryset(self):
        """Filter bookings by current user with optimized queries"""
        return VenueBooking.objects.filter(
            booked_by=self.request.user
        ).select_related('venue', 'venue__owner', 'tournament')
    
    def get_context_data(self, **kwargs):
        """Group bookings by status"""
        context = super().get_context_data(**kwargs)
        bookings = self.get_queryset().order_by('-start_datetime')
        
        context['pending_bookings'] = bookings.filter(status='pending')
        context['confirmed_bookings'] = bookings.filter(status='confirmed')
        context['cancelled_bookings'] = bookings.filter(status='cancelled')
        context['completed_bookings'] = bookings.filter(status='completed')
        
        return context


class BookingCancelView(LoginRequiredMixin, View):
    """
    Cancel a pending booking.
    
    Validates:
    - Requirements 4.5: Update booking status to cancelled
    - Requirements 11.4: Verify user ownership
    """
    
    def post(self, request, pk):
        """Cancel the booking"""
        booking = get_object_or_404(VenueBooking, pk=pk)
        
        # Check ownership
        if booking.booked_by != request.user:
            messages.error(request, 'You do not have permission to cancel this booking.')
            return redirect('venues:booking_list')
        
        # Check if booking can be cancelled
        if booking.status != 'pending':
            messages.error(request, 'Only pending bookings can be cancelled.')
            return redirect('venues:booking_list')
        
        # Cancel the booking
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancelled_at'])
        
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('venues:booking_list')


class BookingDetailView(LoginRequiredMixin, DetailView):
    """
    Display booking confirmation and details.
    
    Validates:
    - Requirements 3.8: Booking confirmation page
    - Requirements 4.6: Display complete booking information
    """
    model = VenueBooking
    template_name = 'venues/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        """Only show bookings belonging to the current user with optimized queries"""
        return VenueBooking.objects.filter(
            booked_by=self.request.user
        ).select_related('venue', 'venue__owner', 'tournament', 'booked_by')
