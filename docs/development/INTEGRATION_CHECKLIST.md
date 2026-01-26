# Template Integration Checklist

## 📋 Progress Tracker

Track your progress as you integrate each template into the Django backend.

---

## Phase 1: Foundation & Setup ⏳

### Initial Setup
- [ ] Create `static/images/` directory
- [ ] Copy `EYTLOGO.jpg` to `static/images/`
- [ ] Create `templates/components/` directory
- [ ] Create `templates/account/` directory
- [ ] Run `python manage.py collectstatic`
- [ ] Verify logo accessible at `/static/images/EYTLOGO.jpg`

### Base Templates
- [ ] Create `templates/base_eyt.html`
  - [ ] Add Tailwind CDN
  - [ ] Add Google Fonts (Spline Sans)
  - [ ] Add Material Icons
  - [ ] Add Alpine.js
  - [ ] Add HTMX
  - [ ] Configure Tailwind with brand colors (#b91c1c)
  - [ ] Add Django messages support
  - [ ] Test base template renders

### Components
- [ ] Create `templates/components/sidebar.html`
  - [ ] Add EYTLOGO.jpg
  - [ ] Add navigation links
  - [ ] Add active state styling
  - [ ] Add logout link
  - [ ] Test on desktop
  - [ ] Test mobile responsiveness

- [ ] Create `templates/components/header.html`
  - [ ] Add search bar
  - [ ] Add notifications bell
  - [ ] Add user avatar/menu
  - [ ] Test all interactive elements

- [ ] Create `templates/components/messages.html`
  - [ ] Style success messages
  - [ ] Style error messages
  - [ ] Style info messages
  - [ ] Add dismiss functionality

---

## Phase 2: Authentication Pages 🔐

### Login Page
- [ ] Create `templates/account/login.html`
  - [ ] Convert `Tem/login_screen/code.html`
  - [ ] Add `{% extends 'base_eyt.html' %}`
  - [ ] Add `{% load static %}` and `{% load socialaccount %}`
  - [ ] Replace logo with `{% static 'images/EYTLOGO.jpg' %}`
  - [ ] Add Django form integration
  - [ ] Add `{% csrf_token %}`
  - [ ] Update social login URLs
  - [ ] Verify #b91c1c color used
  - [ ] Test login functionality
  - [ ] Test social auth buttons
  - [ ] Test "Forgot Password" link
  - [ ] Test mobile view

### Signup Page
- [ ] Create `templates/account/signup.html`
  - [ ] Convert `Tem/registration_screen/code.html`
  - [ ] Match login page styling
  - [ ] Add form fields (email, username, password)
  - [ ] Add password confirmation
  - [ ] Add terms & conditions checkbox
  - [ ] Add social signup options
  - [ ] Test registration flow
  - [ ] Test validation errors
  - [ ] Test mobile view

### Password Reset
- [ ] Create `templates/account/password_reset.html`
  - [ ] Match auth page styling
  - [ ] Add email input
  - [ ] Add submit button
  - [ ] Test reset flow

### Email Verification
- [ ] Create `templates/account/email_verification.html`
  - [ ] Match auth page styling
  - [ ] Add verification message
  - [ ] Add resend link

---

## Phase 3: Dashboard & Profile 👤

### User Dashboard
- [ ] Create `templates/dashboard/index.html`
  - [ ] Convert `Tem/user_dashboard/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Integrate with User model
  - [ ] Add upcoming tournaments section
  - [ ] Add recent coaching sessions
  - [ ] Add performance stats
  - [ ] Add recommendations widget
  - [ ] Add HTMX for live updates
  - [ ] Test with real data
  - [ ] Test mobile view

- [ ] Create `dashboard/views.py`
  - [ ] Create `dashboard_view` function
  - [ ] Query upcoming tournaments
  - [ ] Query recent sessions
  - [ ] Query user stats
  - [ ] Add recommendations logic
  - [ ] Test view returns correct data

- [ ] Update `dashboard/urls.py`
  - [ ] Add dashboard URL pattern
  - [ ] Test URL resolves

### User Profile
- [ ] Create `templates/accounts/profile.html`
  - [ ] Convert `Tem/user_profile_screen/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add profile header
  - [ ] Add avatar upload
  - [ ] Add bio section
  - [ ] Add game profiles
  - [ ] Add social links
  - [ ] Add stats display
  - [ ] Test profile view
  - [ ] Test profile edit
  - [ ] Test mobile view

- [ ] Create `accounts/views.py`
  - [ ] Create `profile_view` function
  - [ ] Create `profile_edit_view` function
  - [ ] Add avatar upload handling
  - [ ] Test views work correctly

---

## Phase 4: Tournament System 🏆

### Tournament List
- [ ] Create `templates/tournaments/tournament_list.html`
  - [ ] Convert `Tem/tournament_listing_page/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add filter sidebar
  - [ ] Add search bar
  - [ ] Create tournament cards
  - [ ] Add pagination
  - [ ] Add "Create Tournament" button
  - [ ] Add HTMX for filtering
  - [ ] Test with multiple tournaments
  - [ ] Test filters work
  - [ ] Test search works
  - [ ] Test mobile view

- [ ] Update `tournaments/views.py`
  - [ ] Update `TournamentListView`
  - [ ] Add filtering logic
  - [ ] Add search logic
  - [ ] Test queryset filtering

### Tournament Detail
- [ ] Create `templates/tournaments/tournament_detail.html`
  - [ ] Merge `detailed_tournament_page_1` and `_2`
  - [ ] Update colors to #b91c1c
  - [ ] Add tournament header
  - [ ] Add tabbed interface (Overview, Bracket, Participants, Rules)
  - [ ] Add registration button
  - [ ] Add check-in button
  - [ ] Add countdown timer
  - [ ] Add organizer info
  - [ ] Add share buttons
  - [ ] Test all tabs work
  - [ ] Test registration flow
  - [ ] Test mobile view

### Bracket View
- [ ] Create `templates/tournaments/bracket.html`
  - [ ] Design bracket layout
  - [ ] Add SVG bracket rendering
  - [ ] Add match cards
  - [ ] Add score reporting
  - [ ] Add HTMX for live updates
  - [ ] Test bracket displays correctly
  - [ ] Test match reporting
  - [ ] Test mobile view (horizontal scroll)

- [ ] Create bracket JavaScript
  - [ ] Add bracket generation logic
  - [ ] Add match click handlers
  - [ ] Add score update handlers
  - [ ] Test all interactions

---

## Phase 5: Coaching System 🎮

### Coach Directory
- [ ] Create `templates/coaching/coach_list.html`
  - [ ] Convert `Tem/select_coach/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add filter sidebar
  - [ ] Create coach cards
  - [ ] Add rating stars
  - [ ] Add "Book Now" buttons
  - [ ] Add search functionality
  - [ ] Test with multiple coaches
  - [ ] Test filters
  - [ ] Test mobile view

- [ ] Update `coaching/views.py`
  - [ ] Create `CoachListView`
  - [ ] Add filtering logic
  - [ ] Test view works

### Coach Dashboard
- [ ] Create `templates/coaching/coach_dashboard.html`
  - [ ] Convert `Tem/coach_dashboard/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add upcoming sessions
  - [ ] Add earnings summary
  - [ ] Add availability management
  - [ ] Add student reviews
  - [ ] Add session history
  - [ ] Test with coach account
  - [ ] Test mobile view

### Coach Profile
- [ ] Create `templates/coaching/coach_profile.html`
  - [ ] Convert `Tem/coach_profile_management/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add profile editing
  - [ ] Add rate settings
  - [ ] Add game expertise
  - [ ] Add availability settings
  - [ ] Test profile updates
  - [ ] Test mobile view

### Booking Calendar
- [ ] Create `templates/coaching/calendar.html`
  - [ ] Convert `Tem/coaching_calendar_page/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Integrate FullCalendar.js
  - [ ] Show available slots
  - [ ] Add time slot selection
  - [ ] Add duration selector
  - [ ] Add booking form
  - [ ] Test calendar displays
  - [ ] Test slot selection
  - [ ] Test mobile view

### Booking Confirmation
- [ ] Create `templates/coaching/booking_confirm.html`
  - [ ] Convert `Tem/booking_confirmation/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add booking summary
  - [ ] Add payment integration
  - [ ] Add confirmation button
  - [ ] Test booking flow
  - [ ] Test payment processing

- [ ] Create `templates/coaching/booking_review.html`
  - [ ] Convert `Tem/confirm_booking_details/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add booking details
  - [ ] Add edit button
  - [ ] Add confirm button
  - [ ] Test review page

---

## Phase 6: Messaging System 💬

### Inbox
- [ ] Create `templates/notifications/inbox.html`
  - [ ] Convert `Tem/messaging_inbox/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add message list
  - [ ] Add unread indicators
  - [ ] Add search/filter
  - [ ] Add compose button
  - [ ] Test message list
  - [ ] Test mobile view

### Chat View
- [ ] Create `templates/notifications/chat.html`
  - [ ] Convert `Tem/detailed_chat_view/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add message thread
  - [ ] Add message input
  - [ ] Add send button
  - [ ] Add real-time updates (Django Channels)
  - [ ] Test chat functionality
  - [ ] Test mobile view

### Compose Message
- [ ] Create `templates/notifications/compose.html`
  - [ ] Convert `Tem/compose_new_message/code.html`
  - [ ] Update colors to #b91c1c
  - [ ] Add recipient selector
  - [ ] Add subject field
  - [ ] Add message body
  - [ ] Add send button
  - [ ] Test compose flow
  - [ ] Test mobile view

---

## Phase 7: Testing & Quality Assurance ✅

### Visual Testing
- [ ] Test on Chrome
- [ ] Test on Firefox
- [ ] Test on Safari
- [ ] Test on Edge
- [ ] Test on iPhone (Safari)
- [ ] Test on Android (Chrome)
- [ ] Test on iPad
- [ ] Verify #b91c1c color everywhere
- [ ] Verify EYTLOGO.jpg displays correctly
- [ ] Check font consistency (Spline Sans)
- [ ] Check spacing consistency
- [ ] Check dark theme consistency

### Functional Testing
- [ ] Test all forms submit
- [ ] Test CSRF protection
- [ ] Test authentication required pages
- [ ] Test permission checks
- [ ] Test HTMX updates
- [ ] Test Alpine.js interactions
- [ ] Test pagination
- [ ] Test search functionality
- [ ] Test file uploads
- [ ] Test payment processing

### Performance Testing
- [ ] Check page load times (<2s)
- [ ] Optimize images
- [ ] Check database query counts
- [ ] Test with slow network
- [ ] Check mobile performance

### Accessibility Testing
- [ ] Check keyboard navigation
- [ ] Check screen reader compatibility
- [ ] Verify ARIA labels
- [ ] Check color contrast (WCAG AA)
- [ ] Test with accessibility tools

---

## Phase 8: Deployment Preparation 🚀

### Pre-Deployment
- [ ] Run `python manage.py collectstatic`
- [ ] Test with DEBUG=False
- [ ] Verify all static files load
- [ ] Check HTTPS for CDN resources
- [ ] Optimize EYTLOGO.jpg
- [ ] Minify CSS/JS (if custom)
- [ ] Set up CDN (optional)
- [ ] Configure caching
- [ ] Set up error monitoring (Sentry)

### Documentation
- [ ] Document template structure
- [ ] Document component usage
- [ ] Document color system
- [ ] Document deployment process
- [ ] Create user guide
- [ ] Create admin guide

### Post-Deployment
- [ ] Verify logo displays
- [ ] Check all colors render
- [ ] Test authentication flows
- [ ] Verify email templates
- [ ] Check mobile responsiveness
- [ ] Test payment integration
- [ ] Monitor error logs
- [ ] Check performance metrics

---

## Completion Summary

### Statistics
- **Total Templates**: 16
- **Total Components**: 6
- **Total Pages**: 22
- **Estimated Time**: 69 hours
- **Actual Time**: ___ hours

### Completed
- [ ] Phase 1: Foundation (8 hours)
- [ ] Phase 2: Authentication (8 hours)
- [ ] Phase 3: Dashboard (10 hours)
- [ ] Phase 4: Tournaments (22 hours)
- [ ] Phase 5: Coaching (18 hours)
- [ ] Phase 6: Messaging (11 hours)
- [ ] Phase 7: Testing (8 hours)
- [ ] Phase 8: Deployment (4 hours)

### Success Criteria Met
- [ ] All pages use #b91c1c
- [ ] EYTLOGO.jpg on all pages
- [ ] Consistent typography
- [ ] Unified dark theme
- [ ] Mobile responsive
- [ ] Fast page loads
- [ ] No console errors
- [ ] Accessible (WCAG AA)

---

## Notes & Issues

### Issues Encountered
```
Date: ___________
Issue: ___________
Solution: ___________

Date: ___________
Issue: ___________
Solution: ___________
```

### Improvements Made
```
Date: ___________
Improvement: ___________

Date: ___________
Improvement: ___________
```

### Future Enhancements
```
- [ ] ___________
- [ ] ___________
- [ ] ___________
```

---

**Last Updated**: [Date]
**Status**: [In Progress / Completed]
**Next Action**: [What to do next]
