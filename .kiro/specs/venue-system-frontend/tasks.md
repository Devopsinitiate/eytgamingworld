# Implementation Plan: Venue System Frontend

## Overview

This implementation plan breaks down the venue system frontend into discrete coding tasks. The system will be built using Django views, forms, and templates with the EYTGaming gaming-themed design aesthetic. Each task builds incrementally, with testing integrated throughout to catch errors early.

## Tasks

- [x] 1. Set up URL routing and basic view structure
  - Create URL patterns in `venues/urls.py` for all venue pages
  - Create placeholder views in `venues/views.py` (VenueListView, VenueDetailView, BookingCreateView, BookingListView, BookingCancelView)
  - Update `config/urls.py` to include venues URLs
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [ ] 2. Implement venue list view with filtering
  - [x] 2.1 Create VenueListView with queryset filtering
    - Implement get_queryset() to filter by is_active=True and is_verified=True
    - Add filter logic for city, venue_type, min_capacity GET parameters
    - Add search logic for name, city, address fields
    - Implement pagination (12 venues per page)
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 9.1, 9.3_

  - [ ]* 2.2 Write property test for venue filtering
    - **Property 3: Venue Filtering Applies All Criteria**
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 9.1, 9.3**

  - [x] 2.3 Create venue_list.html template
    - Extend base.html
    - Create filter panel with search input, city dropdown, type dropdown, capacity slider
    - Create venue grid with responsive columns (1 on mobile, 2 on tablet, 3-4 on desktop)
    - Apply gaming design: skewed filter panel, neon borders, gradient heading
    - _Requirements: 1.1, 1.2, 1.7, 7.1-7.10, 8.1-8.4_

  - [ ]* 2.4 Write property test for venue card display
    - **Property 2: Venue Cards Display Required Information**
    - **Validates: Requirements 1.2**

  - [x] 2.5 Create venue_card.html component
    - Display venue name, city, type, capacity, photo, pricing
    - Add link to venue detail page
    - Apply gaming design: hover scale effect, glow, gunmetal background
    - _Requirements: 1.2, 1.8_

  - [ ]* 2.6 Write property test for venue card links
    - **Property 4: Venue Card Links Navigate Correctly**
    - **Validates: Requirements 1.8**

- [x] 3. Checkpoint - Ensure venue list works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement venue detail view
  - [x] 4.1 Create VenueDetailView with slug lookup
    - Implement get_object() to lookup by slug
    - Increment view_count on each visit
    - Calculate average_rating from reviews
    - Pass authentication status to template
    - _Requirements: 2.1-2.8_

  - [ ]* 4.2 Write property test for venue detail display
    - **Property 5: Venue Detail Displays Complete Information**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 4.3 Create venue_detail.html template
    - Create hero section with venue image, name (gradient text), quick stats
    - Create content grid with venue info and booking sidebar
    - Display amenities with icons, hours of operation, contact info
    - Create pricing card with neon border
    - Add booking button (skewed) for authenticated users
    - Apply gaming design: particle effects, neon borders, metallic stat displays
    - _Requirements: 2.1-2.8, 7.1-7.10_

  - [ ]* 4.4 Write property test for conditional displays
    - **Property 6: Venue Photo Display is Conditional**
    - **Property 8: Map Display is Conditional on Coordinates**
    - **Property 9: Booking Button Visibility Based on Authentication**
    - **Validates: Requirements 2.5, 2.7, 2.8**

  - [x] 4.5 Add map integration (optional)
    - Integrate Leaflet or Google Maps for venue location display
    - Only display when latitude and longitude exist
    - _Requirements: 2.7_

- [ ] 5. Implement booking system
  - [x] 5.1 Create VenueBookingForm
    - Define form fields: start_datetime, end_datetime, expected_participants, notes, tournament
    - Add custom validation for date range (end > start)
    - Add custom validation for overlapping bookings
    - Add capacity warning logic
    - Implement cost calculation method
    - _Requirements: 3.2, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 5.2 Write property tests for booking validation
    - **Property 13: Overlapping Bookings are Rejected**
    - **Property 14: Invalid Date Range is Rejected**
    - **Property 15: Capacity Warnings are Displayed**
    - **Validates: Requirements 3.5, 3.6, 3.7**

  - [ ]* 5.3 Write property test for cost calculation
    - **Property 12: Booking Cost Calculation is Accurate**
    - **Validates: Requirements 3.4**

  - [x] 5.4 Create BookingCreateView
    - Use LoginRequiredMixin for authentication
    - Implement form_valid() to set booked_by and calculate total_cost
    - Set status='pending' on creation
    - Redirect to booking confirmation on success
    - _Requirements: 3.1, 3.3, 3.8, 3.9_

  - [ ]* 5.5 Write property test for booking creation
    - **Property 11: Booking Creation Sets Pending Status**
    - **Property 16: Unauthenticated Booking Access Redirects to Login**
    - **Validates: Requirements 3.3, 3.9**

  - [x] 5.6 Create booking_form.html template
    - Display venue summary card
    - Create form with date/time pickers, participant input, notes textarea
    - Add live cost calculator with JavaScript
    - Apply gaming design: neon focus states, skewed submit button with glow
    - _Requirements: 3.1, 3.2, 7.1-7.10_

- [x] 6. Checkpoint - Ensure booking creation works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement booking management
  - [x] 7.1 Create BookingListView
    - Filter bookings by current user (booked_by=request.user)
    - Group bookings by status in template context
    - Order by start_datetime descending
    - _Requirements: 4.1, 4.3_

  - [ ]* 7.2 Write property test for booking filtering
    - **Property 17: User Bookings are Filtered by Owner**
    - **Validates: Requirements 4.1**

  - [x] 7.3 Create booking_list.html template
    - Create page header with gradient text and status filter tabs
    - Create booking timeline for upcoming bookings
    - Create booking grid grouped by status
    - Apply gaming design: skewed status tabs, status-colored borders
    - _Requirements: 4.1, 4.2, 4.3, 7.1-7.10_

  - [ ]* 7.4 Write property test for booking display
    - **Property 18: Booking Cards Display Required Information**
    - **Property 19: Bookings are Grouped by Status**
    - **Property 20: Cancel Button Visibility Based on Status**
    - **Validates: Requirements 4.2, 4.3, 4.4**

  - [x] 7.5 Create booking_card.html component
    - Display venue name, dates, status, total cost
    - Add cancel button for pending bookings
    - Apply gaming design: status-colored borders, hover effects
    - _Requirements: 4.2, 4.4_

  - [x] 7.6 Create BookingCancelView
    - Check user authorization (booking.booked_by == request.user)
    - Update status to 'cancelled' and set cancelled_at timestamp
    - Redirect back to booking list
    - _Requirements: 4.5_

  - [ ]* 7.7 Write property test for booking cancellation
    - **Property 21: Booking Cancellation Updates Status**
    - **Property 33: Booking Cancellation Requires Ownership**
    - **Validates: Requirements 4.5, 11.4**

- [ ] 8. Implement review system
  - [x] 8.1 Create VenueReviewForm
    - Define form fields: rating, title, review, would_recommend
    - Add validation for rating range (1-5)
    - _Requirements: 5.2, 5.6_

  - [ ]* 8.2 Write property test for review validation
    - **Property 26: Invalid Rating is Rejected**
    - **Validates: Requirements 5.6**

  - [x] 8.3 Add review submission to VenueDetailView
    - Handle POST requests for review submission
    - Check for existing review (unique constraint)
    - Create review with user and venue associations
    - Recalculate venue average rating
    - _Requirements: 5.1, 5.3, 5.4, 5.5, 5.7_

  - [ ]* 8.4 Write property tests for review creation
    - **Property 23: Review Form Visibility Based on Authentication**
    - **Property 25: Review Creation Associates User and Venue**
    - **Property 34: Duplicate Reviews are Prevented**
    - **Validates: Requirements 5.1, 5.3, 5.4, 5.5, 5.8, 11.5**

  - [x] 8.5 Update venue_detail.html with review section
    - Add review summary with average rating and distribution bars
    - Add review submission form (conditional on authentication and no existing review)
    - Add review list with pagination
    - Apply gaming design: star rating with electric red glow, gunmetal review cards
    - _Requirements: 5.1, 5.2, 6.1-6.6, 7.1-7.10_

  - [ ]* 8.6 Write property tests for review display
    - **Property 27: Reviews are Displayed on Venue Page**
    - **Property 28: Review Cards Display Required Information**
    - **Property 29: Reviews are Ordered by Recency**
    - **Property 30: Review Pagination Applies After 10 Reviews**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

  - [x] 8.7 Create review_card.html component
    - Display rating (stars), title, review text, author, date
    - Display would_recommend indicator
    - Apply gaming design: gunmetal background, neon cyan recommendation badge
    - _Requirements: 6.2, 6.3_

- [x] 9. Checkpoint - Ensure review system works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement security and validation
  - [x] 10.1 Add CSRF protection to all forms
    - Verify {% csrf_token %} in all form templates
    - Test CSRF validation on form submissions
    - _Requirements: 11.1, 11.2_

  - [ ]* 10.2 Write property test for CSRF protection
    - **Property 32: Forms Include CSRF Protection**
    - **Validates: Requirements 11.1, 11.2**

  - [x] 10.3 Add HTML escaping for user content
    - Verify Django's auto-escaping is enabled
    - Test with malicious input (script tags, HTML)
    - _Requirements: 11.6_

  - [ ]* 10.4 Write property test for XSS prevention
    - **Property 35: User Content is HTML Escaped**
    - **Validates: Requirements 11.6**

  - [x] 10.5 Add authorization checks
    - Verify LoginRequiredMixin on protected views
    - Add ownership checks in BookingCancelView
    - Test unauthorized access attempts
    - _Requirements: 3.9, 11.3, 11.4_

- [ ] 11. Implement gaming design styling
  - [x] 11.1 Create venues-gaming.css stylesheet
    - Define gaming design variables (colors, fonts, effects)
    - Implement skewed button styles with -12deg transform
    - Implement neon border effects with glow
    - Implement hover effects with scale and shadow
    - Implement gradient text effects
    - _Requirements: 7.1-7.10_

  - [x] 11.2 Add responsive design breakpoints
    - Define mobile (1 column), tablet (2 columns), desktop (3-4 columns) layouts
    - Implement collapsible filter panel for mobile
    - Ensure touch targets are minimum 44x44 pixels
    - _Requirements: 8.1-8.7_

  - [x] 11.3 Add interactive JavaScript enhancements
    - Implement live cost calculator for booking form
    - Implement interactive star rating selector
    - Implement filter updates without page reload (optional)
    - Add smooth animations for hover effects
    - _Requirements: 3.4, 5.2_

- [ ] 12. Implement accessibility features
  - [x] 12.1 Add ARIA labels and roles
    - Add aria-label to all interactive elements
    - Add role attributes for semantic structure
    - Add aria-live regions for dynamic content
    - _Requirements: 10.1, 10.5_

  - [x] 12.2 Ensure keyboard navigation
    - Test tab order through all interactive elements
    - Add focus indicators with neon glow
    - Ensure all actions are keyboard accessible
    - _Requirements: 10.2_

  - [x] 12.3 Add alt text and labels
    - Add alt text to all venue images
    - Associate labels with all form fields
    - Add descriptive link text
    - _Requirements: 10.4, 10.7_

  - [x] 12.4 Verify color contrast
    - Test all text against backgrounds for 4.5:1 ratio
    - Ensure non-color indicators for status
    - _Requirements: 10.3_

- [ ] 13. Implement performance optimizations
  - [x] 13.1 Add image optimization
    - Implement lazy loading for venue images
    - Add loading="lazy" attribute to img tags
    - Serve WebP format with fallbacks
    - _Requirements: 12.2, 12.5_

  - [x] 13.2 Add query optimization
    - Use select_related() for foreign key queries
    - Use prefetch_related() for reverse foreign key queries
    - Add database indexes for common filters
    - _Requirements: 12.1_

  - [x] 13.3 Add caching for venue data
    - Cache venue list queries for 5 minutes
    - Cache venue detail data for 10 minutes
    - Invalidate cache on venue updates
    - _Requirements: 12.4_

- [ ] 14. Final checkpoint - Integration testing
  - [x] 14.1 Test complete user flows
    - Browse venues → Filter → View detail → Create booking
    - View venue → Submit review → See review displayed
    - View bookings → Cancel booking → Verify status
    - Test unauthorized access attempts

  - [x] 14.2 Test responsive design
    - Test on mobile viewport (375px)
    - Test on tablet viewport (768px)
    - Test on desktop viewport (1920px)
    - Verify touch targets on mobile

  - [x] 14.3 Test accessibility
    - Test keyboard navigation
    - Test with screen reader (manual)
    - Verify color contrast
    - Verify ARIA labels

  - [x] 14.4 Test gaming design consistency
    - Verify all pages match home page aesthetic
    - Verify skewed elements, neon effects, gradient text
    - Verify hover effects and animations
    - Verify brand colors throughout

- [x] 15. Final verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Gaming design must match the EYTGaming home page aesthetic exactly
- All forms must include CSRF protection
- All user-facing features must be accessible via keyboard
- All images must have alt text for accessibility
