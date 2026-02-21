# Design Document: Venue System Frontend

## Overview

The venue system frontend provides a comprehensive user interface for discovering, booking, and reviewing physical gaming venues. The implementation leverages Django's template system with the EYTGaming gaming-themed design aesthetic, featuring electric red accents, neon effects, skewed elements, and bold typography.

The system consists of five main views:
1. **Venue List** - Browsable catalog with filtering and search
2. **Venue Detail** - Comprehensive venue information with booking capability
3. **Booking Creation** - Form-based venue reservation system
4. **Booking Management** - User's booking history and management
5. **Review System** - Integrated review submission and display

All views extend the existing `base.html` template and integrate with the current authentication system, maintaining consistency with the platform's gaming aesthetic.

## Architecture

### View Layer Architecture

```
venues/
├── views.py (Django class-based and function views)
├── forms.py (Form validation and processing)
├── urls.py (URL routing)
└── templates/venues/
    ├── venue_list.html
    ├── venue_detail.html
    ├── booking_form.html
    ├── booking_list.html
    └── components/
        ├── venue_card.html
        ├── filter_panel.html
        ├── review_card.html
        └── booking_card.html
```

### URL Structure

```
/venues/                          → Venue list with filters
/venues/<slug>/                   → Venue detail page
/venues/<slug>/book/              → Booking creation form
/venues/bookings/                 → User's booking list
/venues/bookings/<uuid>/          → Booking detail
/venues/bookings/<uuid>/cancel/   → Cancel booking
```

### Data Flow

```
User Request → URL Router → View → Form Validation → Model Update → Template Render → Response
                                ↓
                          Query Filters/Search
                                ↓
                          Database Query
```

## Components and Interfaces

### 1. Venue List View

**Purpose:** Display filterable, searchable catalog of venues

**Implementation:**
- Django ListView with custom queryset filtering
- GET parameters for filters: `city`, `venue_type`, `min_capacity`, `search`
- Pagination with 12 venues per page
- AJAX-ready for filter updates without page reload

**Template Structure:**
```html
<div class="venue-list-container">
  <aside class="filter-panel">
    <!-- Search input -->
    <!-- City filter dropdown -->
    <!-- Type filter dropdown -->
    <!-- Capacity slider -->
  </aside>
  
  <main class="venue-grid">
    <!-- Venue cards (3-4 columns on desktop) -->
  </main>
</div>
```

**Gaming Design Elements:**
- Skewed filter panel with neon red border
- Venue cards with hover scale effect and glow
- Grid background pattern
- Gradient text for section heading
- Electric red accent on active filters

### 2. Venue Detail View

**Purpose:** Display comprehensive venue information with booking capability

**Implementation:**
- Django DetailView with slug-based lookup
- Increment view_count on each visit
- Calculate average rating from reviews
- Check user authentication for booking button visibility

**Template Structure:**
```html
<div class="venue-detail-container">
  <section class="venue-hero">
    <!-- Large venue image with overlay -->
    <!-- Venue name with gradient text -->
    <!-- Quick stats (capacity, type, rating) -->
  </section>
  
  <div class="venue-content-grid">
    <main class="venue-info">
      <!-- Description -->
      <!-- Amenities with icons -->
      <!-- Hours of operation -->
      <!-- Contact information -->
    </main>
    
    <aside class="booking-sidebar">
      <!-- Pricing card with neon border -->
      <!-- Book now button (skewed) -->
      <!-- Quick info -->
    </aside>
  </div>
  
  <section class="venue-location">
    <!-- Map integration (optional) -->
    <!-- Full address -->
  </section>
  
  <section class="venue-reviews">
    <!-- Review submission form (if authenticated) -->
    <!-- Review list -->
  </section>
</div>
```

**Gaming Design Elements:**
- Hero section with particle effects
- Skewed booking button with glow
- Neon cyan borders on info cards
- Metallic borders on stat displays
- Gradient overlays on images

### 3. Booking Form View

**Purpose:** Create venue reservations with validation

**Implementation:**
- Django FormView with custom validation
- Check for booking conflicts (overlapping dates)
- Calculate total cost based on duration and rates
- Require authentication via LoginRequiredMixin

**Form Fields:**
```python
class VenueBookingForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(widget=DateTimeInput)
    end_datetime = forms.DateTimeField(widget=DateTimeInput)
    expected_participants = forms.IntegerField(min_value=1)
    notes = forms.CharField(widget=Textarea, required=False)
    tournament = forms.ModelChoiceField(queryset=Tournament.objects.filter(organizer=user), required=False)
```

**Validation Logic:**
1. Verify end_datetime > start_datetime
2. Check expected_participants <= venue.capacity
3. Query for overlapping bookings on same venue
4. Calculate cost: (duration_hours * hourly_rate) or day_rate if >= 8 hours

**Template Structure:**
```html
<div class="booking-form-container">
  <div class="venue-summary-card">
    <!-- Venue name, image, pricing -->
  </div>
  
  <form class="booking-form">
    <!-- Date/time pickers with gaming styling -->
    <!-- Participant count input -->
    <!-- Tournament selection (optional) -->
    <!-- Notes textarea -->
    <!-- Cost calculation display (live update) -->
    <!-- Submit button (skewed with glow) -->
  </form>
</div>
```

**Gaming Design Elements:**
- Form inputs with neon focus states
- Skewed submit button with electric red glow
- Live cost calculator with animated numbers
- Error messages with red neon borders

### 4. Booking Management View

**Purpose:** Display and manage user's venue bookings

**Implementation:**
- Django ListView filtered by current user
- Group bookings by status (pending, confirmed, cancelled, completed)
- Provide cancel action for pending bookings
- Display booking timeline

**Template Structure:**
```html
<div class="booking-management-container">
  <header class="page-header">
    <!-- Title with gradient text -->
    <!-- Status filter tabs -->
  </header>
  
  <div class="booking-timeline">
    <!-- Upcoming bookings -->
    <!-- Past bookings -->
  </div>
  
  <div class="booking-grid">
    <!-- Booking cards grouped by status -->
  </div>
</div>
```

**Gaming Design Elements:**
- Status tabs with skewed active indicator
- Booking cards with status-colored borders (red=cancelled, cyan=confirmed, orange=pending, green=completed)
- Timeline with neon connectors
- Hover effects on interactive cards

### 5. Review System

**Purpose:** Submit and display venue reviews

**Implementation:**
- Review submission via POST to venue detail view
- Unique constraint enforcement (one review per user per venue)
- Star rating input with visual feedback
- Review display with pagination

**Form Fields:**
```python
class VenueReviewForm(forms.ModelForm):
    rating = forms.IntegerField(min_value=1, max_value=5)
    title = forms.CharField(max_length=200)
    review = forms.CharField(widget=Textarea)
    would_recommend = forms.BooleanField(required=False, initial=True)
```

**Template Structure:**
```html
<div class="review-section">
  <div class="review-summary">
    <!-- Average rating with large stars -->
    <!-- Total review count -->
    <!-- Rating distribution bars -->
  </div>
  
  <div class="review-form">
    <!-- Star rating selector (interactive) -->
    <!-- Title input -->
    <!-- Review textarea -->
    <!-- Recommend checkbox -->
    <!-- Submit button -->
  </div>
  
  <div class="review-list">
    <!-- Individual review cards -->
  </div>
</div>
```

**Gaming Design Elements:**
- Star rating with electric red fill and glow
- Review cards with gunmetal background
- Recommendation badge with neon cyan
- Animated rating bars

## Data Models

The system uses existing models from `venues/models.py`:

### Venue Model
```python
{
    'id': UUID,
    'name': str,
    'slug': str,
    'description': str,
    'venue_type': str (choices),
    'owner': User FK,
    'address': str,
    'city': str,
    'state': str,
    'country': str,
    'postal_code': str,
    'latitude': Decimal,
    'longitude': Decimal,
    'phone': str,
    'email': str,
    'website': str,
    'capacity': int,
    'setup_stations': int,
    'photo': ImageField,
    'hours_of_operation': JSON,
    'amenities': JSON (list),
    'is_active': bool,
    'is_verified': bool,
    'hourly_rate': Decimal,
    'day_rate': Decimal,
    'view_count': int
}
```

### VenueBooking Model
```python
{
    'id': UUID,
    'venue': Venue FK,
    'booked_by': User FK,
    'tournament': Tournament FK (optional),
    'start_datetime': DateTime,
    'end_datetime': DateTime,
    'expected_participants': int,
    'total_cost': Decimal,
    'deposit_paid': Decimal,
    'is_paid': bool,
    'status': str (choices: pending, confirmed, cancelled, completed),
    'notes': str,
    'admin_notes': str
}
```

### VenueReview Model
```python
{
    'id': UUID,
    'venue': Venue FK,
    'user': User FK,
    'rating': int (1-5),
    'title': str,
    'review': str,
    'would_recommend': bool
}
```

### Computed Properties

**Venue.average_rating:**
```python
@property
def average_rating(self):
    reviews = self.reviews.all()
    if not reviews:
        return 0
    return sum(r.rating for r in reviews) / len(reviews)
```

**VenueBooking.duration_hours:**
```python
@property
def duration_hours(self):
    delta = self.end_datetime - self.start_datetime
    return delta.total_seconds() / 3600
```

**VenueBooking.can_cancel:**
```python
@property
def can_cancel(self):
    return self.status == 'pending' and self.start_datetime > timezone.now()
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Venue List Displays Active and Verified Venues

*For any* venue list page request, all displayed venues should be both active (is_active=True) and verified (is_verified=True), and all such venues in the database should be displayed.

**Validates: Requirements 1.1**

### Property 2: Venue Cards Display Required Information

*For any* venue displayed in the list, the rendered HTML should contain the venue's name, city, type, capacity, photo (if present), and pricing information.

**Validates: Requirements 1.2**

### Property 3: Venue Filtering Applies All Criteria

*For any* combination of filters (city, venue_type, min_capacity, search), the displayed venues should match all applied filter criteria, and no venues that don't match all criteria should be displayed.

**Validates: Requirements 1.3, 1.4, 1.5, 1.6, 9.1, 9.3**

### Property 4: Venue Card Links Navigate Correctly

*For any* venue card in the list, the card's link should point to that venue's detail page URL.

**Validates: Requirements 1.8**

### Property 5: Venue Detail Displays Complete Information

*For any* venue detail page, the rendered HTML should contain all venue fields including name, description, type, full address, capacity, setup stations, amenities, hours of operation, contact information, and pricing.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 6: Venue Photo Display is Conditional

*For any* venue with a photo, the detail page should display the photo; for any venue without a photo, no photo element should be rendered.

**Validates: Requirements 2.5**

### Property 7: Average Rating Calculation is Correct

*For any* venue with reviews, the displayed average rating should equal the sum of all review ratings divided by the number of reviews.

**Validates: Requirements 2.6, 5.7**

### Property 8: Map Display is Conditional on Coordinates

*For any* venue with latitude and longitude coordinates, the detail page should display a map; for any venue without coordinates, no map should be rendered.

**Validates: Requirements 2.7**

### Property 9: Booking Button Visibility Based on Authentication

*For any* authenticated user viewing a venue detail page, a booking button should be displayed; for any anonymous user, no booking button should be displayed.

**Validates: Requirements 2.8**

### Property 10: Booking Form Requires Essential Fields

*For any* booking form, the start_datetime, end_datetime, and expected_participants fields should be marked as required.

**Validates: Requirements 3.2**

### Property 11: Booking Creation Sets Pending Status

*For any* valid booking submission, the created booking record should have status='pending'.

**Validates: Requirements 3.3**

### Property 12: Booking Cost Calculation is Accurate

*For any* booking, if the duration is less than 8 hours, the total_cost should equal duration_hours * venue.hourly_rate; if duration is 8 hours or more, total_cost should equal venue.day_rate * number_of_days.

**Validates: Requirements 3.4**

### Property 13: Overlapping Bookings are Rejected

*For any* booking submission where another confirmed or pending booking exists for the same venue with overlapping start_datetime and end_datetime, the submission should be rejected with an error message.

**Validates: Requirements 3.5**

### Property 14: Invalid Date Range is Rejected

*For any* booking submission where end_datetime is before or equal to start_datetime, the submission should be rejected with an error message.

**Validates: Requirements 3.6**

### Property 15: Capacity Warnings are Displayed

*For any* booking submission where expected_participants exceeds venue.capacity, a warning message should be displayed.

**Validates: Requirements 3.7**

### Property 16: Unauthenticated Booking Access Redirects to Login

*For any* anonymous user attempting to access the booking creation page, the system should redirect to the login page.

**Validates: Requirements 3.9, 11.3**

### Property 17: User Bookings are Filtered by Owner

*For any* user viewing their bookings list, only bookings where booked_by equals that user should be displayed.

**Validates: Requirements 4.1**

### Property 18: Booking Cards Display Required Information

*For any* booking displayed in the list, the rendered HTML should contain the venue name, start and end dates, status, and total cost.

**Validates: Requirements 4.2**

### Property 19: Bookings are Grouped by Status

*For any* bookings list, bookings should be grouped into sections by their status (pending, confirmed, cancelled, completed).

**Validates: Requirements 4.3**

### Property 20: Cancel Button Visibility Based on Status

*For any* booking with status='pending', a cancel button should be displayed; for any booking with other statuses, no cancel button should be displayed.

**Validates: Requirements 4.4**

### Property 21: Booking Cancellation Updates Status

*For any* pending booking that is cancelled, the booking's status should be updated to 'cancelled' and cancelled_at should be set to the current timestamp.

**Validates: Requirements 4.5**

### Property 22: Booking Detail Displays Complete Information

*For any* booking detail page, the rendered HTML should contain all booking fields including venue, dates, participants, cost, status, and notes.

**Validates: Requirements 4.6**

### Property 23: Review Form Visibility Based on Authentication

*For any* authenticated user viewing a venue detail page who has not already reviewed the venue, a review submission form should be displayed; for any anonymous user or user who has already reviewed the venue, no form should be displayed.

**Validates: Requirements 5.1, 5.5, 5.8**

### Property 24: Review Form Requires Essential Fields

*For any* review form, the rating, title, and review fields should be marked as required.

**Validates: Requirements 5.2**

### Property 25: Review Creation Associates User and Venue

*For any* valid review submission, the created review record should have the correct user foreign key and venue foreign key.

**Validates: Requirements 5.3, 5.4**

### Property 26: Invalid Rating is Rejected

*For any* review submission where rating is less than 1 or greater than 5, the submission should be rejected with an error message.

**Validates: Requirements 5.6**

### Property 27: Reviews are Displayed on Venue Page

*For any* venue with reviews, all reviews for that venue should be displayed on the venue detail page.

**Validates: Requirements 6.1**

### Property 28: Review Cards Display Required Information

*For any* review displayed, the rendered HTML should contain the rating, title, review text, author name, date, and would_recommend indicator.

**Validates: Requirements 6.2, 6.3**

### Property 29: Reviews are Ordered by Recency

*For any* list of reviews, reviews should be ordered with the most recent created_at timestamp first.

**Validates: Requirements 6.4**

### Property 30: Review Pagination Applies After 10 Reviews

*For any* venue with more than 10 reviews, the review list should be paginated with 10 reviews per page.

**Validates: Requirements 6.5**

### Property 31: Search Reset Displays All Venues

*For any* venue list with an active search filter, when the search is cleared, all active and verified venues should be displayed again.

**Validates: Requirements 9.2**

### Property 32: Forms Include CSRF Protection

*For any* form submission (booking or review), the request should include a valid CSRF token, and submissions without valid tokens should be rejected.

**Validates: Requirements 11.1, 11.2**

### Property 33: Booking Cancellation Requires Ownership

*For any* booking cancellation attempt, if the requesting user is not the booking's booked_by user, the request should be denied with an authorization error.

**Validates: Requirements 11.4**

### Property 34: Duplicate Reviews are Prevented

*For any* user attempting to submit a second review for a venue they have already reviewed, the submission should be rejected with an error message.

**Validates: Requirements 11.5**

### Property 35: User Content is HTML Escaped

*For any* user-generated content (review text, booking notes), when displayed in HTML, special characters should be escaped to prevent XSS attacks.

**Validates: Requirements 11.6**

## Error Handling

### Form Validation Errors

**Booking Form Errors:**
- Invalid date range: "End date must be after start date"
- Overlapping booking: "This venue is already booked for the selected time period"
- Capacity exceeded: "Warning: Expected participants exceed venue capacity"
- Missing required fields: "This field is required"

**Review Form Errors:**
- Invalid rating: "Rating must be between 1 and 5 stars"
- Duplicate review: "You have already reviewed this venue"
- Missing required fields: "This field is required"

### Authentication Errors

- Unauthenticated access: Redirect to login with `next` parameter
- Unauthorized action: HTTP 403 with error message

### Database Errors

- Venue not found: HTTP 404 with custom error page
- Booking not found: HTTP 404 with custom error page
- Database connection error: HTTP 500 with generic error message (log details)

### Display Patterns

All form errors should:
1. Display near the relevant field with red neon border
2. Include an icon indicator
3. Be announced to screen readers
4. Persist until the field is corrected

## Testing Strategy

### Dual Testing Approach

The venue system requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of booking calculations
- Edge cases (empty results, no reviews, etc.)
- Integration points between views and forms
- Error conditions and validation messages

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Filtering and search logic across random data
- Form validation across random inputs
- Authorization rules across random users

### Property-Based Testing Configuration

**Library:** Use `hypothesis` for Python/Django property-based testing

**Configuration:**
- Minimum 100 iterations per property test
- Each test must reference its design document property
- Tag format: `# Feature: venue-system-frontend, Property {number}: {property_text}`

**Example Property Test Structure:**
```python
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase

class VenueFilteringPropertyTests(TestCase):
    @given(
        city=st.text(min_size=1, max_size=50),
        venues=st.lists(st.builds(Venue))
    )
    @settings(max_examples=100)
    def test_city_filter_property(self, city, venues):
        # Feature: venue-system-frontend, Property 3: Venue Filtering Applies All Criteria
        # Test that city filter returns only matching venues
        ...
```

### Unit Test Coverage

**Views to Test:**
- VenueListView: filtering, search, pagination
- VenueDetailView: data display, authentication checks
- BookingCreateView: form validation, cost calculation
- BookingListView: user filtering, status grouping
- BookingCancelView: authorization, status update
- ReviewCreateView: duplicate prevention, rating validation

**Forms to Test:**
- VenueBookingForm: date validation, overlap checking, cost calculation
- VenueReviewForm: rating validation, required fields

**Template Rendering:**
- Verify required fields are present in rendered HTML
- Verify conditional elements (buttons, forms) appear correctly
- Verify CSRF tokens are included in forms

### Integration Tests

Test complete user flows:
1. Browse venues → Filter by city → View detail → Create booking
2. View venue → Submit review → See review displayed
3. View bookings → Cancel pending booking → Verify status updated
4. Attempt unauthorized actions → Verify proper error handling

### Accessibility Testing

Manual testing required for:
- Keyboard navigation through all interactive elements
- Screen reader announcements for dynamic content
- Color contrast verification
- Touch target sizes on mobile devices
