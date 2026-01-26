# Template Mapping Summary

## Visual Overview

```
Tem/ (Source Templates)          →    Django App Structure
├── EYTLOGO.jpg                  →    static/images/EYTLOGO.jpg
│
├── login_screen/                →    templates/account/login.html
│   └── code.html                     (django-allauth integration)
│
├── registration_screen/         →    templates/account/signup.html
│   └── code.html                     (django-allauth integration)
│
├── user_dashboard/              →    templates/dashboard/index.html
│   └── code.html                     (dashboard app)
│
├── user_profile_screen/         →    templates/accounts/profile.html
│   └── code.html                     (accounts app)
│
├── tournament_listing_page/     →    templates/tournaments/tournament_list.html
│   └── code.html                     (tournaments app)
│
├── detailed_tournament_page_1/  →    templates/tournaments/tournament_detail.html
│   └── code.html                     (tournaments app - Overview tab)
│
├── detailed_tournament_page_2/  →    templates/tournaments/tournament_detail.html
│   └── code.html                     (tournaments app - Bracket tab)
│
├── select_coach/                →    templates/coaching/coach_list.html
│   └── code.html                     (coaching app)
│
├── coach_profile_management/    →    templates/coaching/coach_profile.html
│   └── code.html                     (coaching app)
│
├── coach_dashboard/             →    templates/coaching/coach_dashboard.html
│   └── code.html                     (coaching app)
│
├── coaching_calendar_page/      →    templates/coaching/calendar.html
│   └── code.html                     (coaching app)
│
├── booking_confirmation/        →    templates/coaching/booking_confirm.html
│   └── code.html                     (coaching app)
│
├── confirm_booking_details/     →    templates/coaching/booking_review.html
│   └── code.html                     (coaching app)
│
├── messaging_inbox/             →    templates/notifications/inbox.html
│   └── code.html                     (notifications app)
│
├── detailed_chat_view/          →    templates/notifications/chat.html
│   └── code.html                     (notifications app)
│
└── compose_new_message/         →    templates/notifications/compose.html
    └── code.html                     (notifications app)
```

---

## Color Consistency Matrix

| Template | Original Primary | New Primary | Status |
|----------|-----------------|-------------|--------|
| login_screen | #b91c1c ✅ | #b91c1c | ✅ Reference |
| user_dashboard | #135bec | #b91c1c | 🔄 Update |
| tournament_listing | Various | #b91c1c | 🔄 Update |
| coach_dashboard | Various | #b91c1c | 🔄 Update |
| All others | Various | #b91c1c | 🔄 Update |

**Action Required**: Find and replace all color codes to #b91c1c

---

## Component Breakdown

### Shared Components (Create Once, Use Everywhere)

```
templates/components/
├── sidebar.html              ← Navigation sidebar
├── header.html               ← Top header with search/notifications
├── messages.html             ← Django messages display
├── tournament_card.html      ← Reusable tournament card
├── coach_card.html           ← Reusable coach card
├── match_card.html           ← Reusable match card
├── button.html               ← Button styles
└── form_field.html           ← Form input styles
```

### Base Templates

```
templates/
├── base_eyt.html             ← Main base (with sidebar/header)
├── base_auth.html            ← Auth pages (no sidebar)
└── base_public.html          ← Public pages (minimal nav)
```

---

## Integration Priority Matrix

### Week 1: Foundation (CRITICAL)
```
Priority: 🔴 HIGH
├── base_eyt.html             [2 hours]
├── components/sidebar.html   [1 hour]
├── components/header.html    [1 hour]
├── account/login.html        [2 hours]
└── account/signup.html       [2 hours]
Total: 8 hours
```

### Week 2: Core User Experience (CRITICAL)
```
Priority: 🔴 HIGH
├── dashboard/index.html      [4 hours]
├── accounts/profile.html     [3 hours]
└── Testing & Bug Fixes       [3 hours]
Total: 10 hours
```

### Week 3-4: Tournament System (HIGH)
```
Priority: 🟡 HIGH
├── tournaments/tournament_list.html    [4 hours]
├── tournaments/tournament_detail.html  [6 hours]
├── tournaments/bracket.html            [8 hours]
└── Testing & Integration               [4 hours]
Total: 22 hours
```

### Week 5-6: Coaching System (MEDIUM)
```
Priority: 🟢 MEDIUM
├── coaching/coach_list.html           [3 hours]
├── coaching/coach_dashboard.html      [4 hours]
├── coaching/calendar.html             [6 hours]
├── coaching/booking_confirm.html      [2 hours]
└── Testing & Integration              [3 hours]
Total: 18 hours
```

### Week 7: Messaging (LOW)
```
Priority: 🔵 LOW
├── notifications/inbox.html    [3 hours]
├── notifications/chat.html     [4 hours]
├── notifications/compose.html  [2 hours]
└── Testing                     [2 hours]
Total: 11 hours
```

**Total Estimated Time: 69 hours (~9 working days)**

---

## File Structure After Integration

```
eytgaming/
├── static/
│   ├── images/
│   │   └── EYTLOGO.jpg                    ← Brand logo
│   ├── css/
│   │   └── custom.css                     ← Additional styles
│   └── js/
│       └── main.js                        ← Custom JavaScript
│
├── templates/
│   ├── base_eyt.html                      ← Main base template
│   ├── base_auth.html                     ← Auth base template
│   ├── base_public.html                   ← Public base template
│   │
│   ├── components/                        ← Reusable components
│   │   ├── sidebar.html
│   │   ├── header.html
│   │   ├── messages.html
│   │   ├── tournament_card.html
│   │   ├── coach_card.html
│   │   └── match_card.html
│   │
│   ├── account/                           ← Authentication
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── password_reset.html
│   │   └── email_verification.html
│   │
│   ├── dashboard/                         ← User dashboard
│   │   └── index.html
│   │
│   ├── accounts/                          ← User profiles
│   │   ├── profile.html
│   │   └── settings.html
│   │
│   ├── tournaments/                       ← Tournament system
│   │   ├── tournament_list.html
│   │   ├── tournament_detail.html
│   │   ├── bracket.html
│   │   └── create.html
│   │
│   ├── coaching/                          ← Coaching system
│   │   ├── coach_list.html
│   │   ├── coach_dashboard.html
│   │   ├── coach_profile.html
│   │   ├── calendar.html
│   │   ├── booking_confirm.html
│   │   └── booking_review.html
│   │
│   └── notifications/                     ← Messaging
│       ├── inbox.html
│       ├── chat.html
│       └── compose.html
│
├── core/                                  ← Core app
│   ├── models.py                          ← User, Game, SiteSettings
│   └── context_processors.py             ← site_settings
│
├── accounts/                              ← Accounts app
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── dashboard/                             ← Dashboard app
│   ├── views.py
│   └── urls.py
│
├── tournaments/                           ← Tournaments app
│   ├── models.py                          ← Tournament, Bracket, Match
│   ├── views.py
│   └── urls.py
│
├── coaching/                              ← Coaching app
│   ├── models.py                          ← CoachProfile, Session
│   ├── views.py
│   └── urls.py
│
└── notifications/                         ← Notifications app
    ├── models.py
    ├── views.py
    └── urls.py
```

---

## Design System Reference

### Colors
```css
/* Brand Colors */
--primary: #b91c1c;              /* EYT Red */
--primary-dark: #991b1b;         /* Darker red */
--primary-light: #dc2626;        /* Lighter red */

/* Backgrounds */
--bg-light: #f6f6f8;             /* Light mode bg */
--bg-dark: #121212;              /* Dark mode bg */
--card-dark: #151c2c;            /* Card background */
--card-border: #282e39;          /* Card border */

/* Neutrals */
--neutral-900: #171717;
--neutral-800: #262626;
--neutral-700: #404040;
--neutral-600: #525252;
--neutral-500: #737373;
--neutral-400: #a3a3a3;
--neutral-300: #d4d4d4;
```

### Typography
```css
/* Font Family */
font-family: 'Spline Sans', sans-serif;

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Font Sizes */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
```

### Spacing
```css
/* Padding/Margin Scale */
--space-1: 0.25rem;      /* 4px */
--space-2: 0.5rem;       /* 8px */
--space-3: 0.75rem;      /* 12px */
--space-4: 1rem;         /* 16px */
--space-6: 1.5rem;       /* 24px */
--space-8: 2rem;         /* 32px */
```

### Border Radius
```css
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-full: 9999px;   /* Fully rounded */
```

---

## Quick Commands Reference

### Setup
```bash
# Create directories
mkdir templates\components templates\account templates\dashboard
mkdir static\images static\css static\js

# Copy logo
copy Tem\EYTLOGO.jpg static\images\

# Collect static
python manage.py collectstatic --noinput
```

### Development
```bash
# Run server
python manage.py runserver

# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations
python manage.py migrate
```

### Testing URLs
```
http://127.0.0.1:8000/                    ← Home
http://127.0.0.1:8000/accounts/login/     ← Login
http://127.0.0.1:8000/dashboard/          ← Dashboard
http://127.0.0.1:8000/tournaments/        ← Tournaments
http://127.0.0.1:8000/coaching/           ← Coaching
http://127.0.0.1:8000/admin/              ← Admin
```

---

## Checklist for Each Template

### Pre-Integration
- [ ] Read original HTML file
- [ ] Identify dynamic content areas
- [ ] Note form fields and actions
- [ ] List required context variables
- [ ] Check for JavaScript dependencies

### During Integration
- [ ] Add `{% load static %}` at top
- [ ] Extend appropriate base template
- [ ] Replace hardcoded URLs with `{% url %}`
- [ ] Add CSRF tokens to forms
- [ ] Replace static paths with `{% static %}`
- [ ] Add template variables
- [ ] Update colors to #b91c1c
- [ ] Replace logo with EYTLOGO.jpg
- [ ] Add conditional rendering
- [ ] Add loops for dynamic content

### Post-Integration
- [ ] Test in browser
- [ ] Check mobile responsiveness
- [ ] Verify all links work
- [ ] Test forms submit correctly
- [ ] Check authentication requirements
- [ ] Validate HTML
- [ ] Test with real data
- [ ] Check console for errors
- [ ] Verify HTMX functionality
- [ ] Test Alpine.js interactions

---

## Success Metrics

### Design Consistency
✅ All pages use #b91c1c as primary color
✅ EYTLOGO.jpg visible on all authenticated pages
✅ Consistent typography (Spline Sans)
✅ Unified dark theme
✅ Consistent spacing and layout
✅ Material Icons used throughout

### Functionality
✅ All forms work correctly
✅ Authentication flows complete
✅ HTMX updates work smoothly
✅ Mobile responsive (320px - 1920px)
✅ Fast page loads (<2 seconds)
✅ No console errors
✅ Proper error handling

### Code Quality
✅ DRY principles followed
✅ Reusable components created
✅ Proper template inheritance
✅ Clean, commented code
✅ Follows Django best practices
✅ Accessible (WCAG AA)

---

## Support & Resources

### Documentation
- **Full Plan**: `TEMPLATE_INTEGRATION_PLAN.md`
- **Quick Start**: `QUICK_START_INTEGRATION.md`
- **This File**: `TEMPLATE_MAPPING_SUMMARY.md`

### External Resources
- Django Templates: https://docs.djangoproject.com/en/5.0/topics/templates/
- Tailwind CSS: https://tailwindcss.com/docs
- HTMX: https://htmx.org/docs/
- Alpine.js: https://alpinejs.dev/

### Project Files
- Source Templates: `Tem/` folder
- Brand Logo: `Tem/EYTLOGO.jpg`
- Existing Models: `core/models.py`, `tournaments/models.py`, etc.
- Current Views: Various `views.py` files

---

**Ready to integrate? Start with QUICK_START_INTEGRATION.md!**
