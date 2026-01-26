# Template Integration Plan - Phase 3

## Overview
This plan outlines the integration of the existing templates from the `Tem` folder with the robust backend built in Phases 1 & 2. The integration will maintain the company's design system and branding while connecting to Django views and models.

---

## Design System Analysis

### Color Palette (from login_screen)
```css
Primary Red: #b91c1c (Brand color from logo)
Background Light: #f6f6f8
Background Dark: #121212
Card Dark: #151c2c (from dashboard)
Card Border Dark: #282e39
Neutral 900: #171717
Neutral 800: #262626
Neutral 700: #404040
Neutral 500: #737373
Neutral 400: #a3a3a3
Neutral 300: #d4d4d4
Neutral 200: #e5e5e5
```

### Typography
- **Font Family**: Spline Sans (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700
- **Icons**: Material Symbols Outlined

### Components
- **Framework**: Tailwind CSS (via CDN)
- **Dark Mode**: Enabled by default
- **Border Radius**: 0.25rem (default), 0.5rem (lg), 0.75rem (xl)
- **Shadows**: Used for depth and elevation

### Logo
- **File**: `Tem/EYTLOGO.jpg`
- **Usage**: Brand identity across all pages
- **SVG Alternative**: Hexagonal logo with "EYT" in red (#b91c1c)

---

## Template Inventory

### Available Templates:
1. ✅ **login_screen** - Authentication
2. ✅ **registration_screen** - User signup
3. ✅ **user_dashboard** - Main dashboard
4. ✅ **user_profile_screen** - Profile management
5. ✅ **tournament_listing_page** - Browse tournaments
6. ✅ **detailed_tournament_page_1** - Tournament details
7. ✅ **detailed_tournament_page_2** - Tournament details (alt)
8. ✅ **coach_dashboard** - Coach-specific dashboard
9. ✅ **coach_profile_management** - Coach profile
10. ✅ **select_coach** - Browse coaches
11. ✅ **coaching_calendar_page** - Coach availability
12. ✅ **booking_confirmation** - Session confirmation
13. ✅ **confirm_booking_details** - Booking details
14. ✅ **messaging_inbox** - Message list
15. ✅ **compose_new_message** - New message
16. ✅ **detailed_chat_view** - Chat interface

---

## Integration Strategy

### Phase 3A: Base Templates & Authentication (Week 1)

#### Step 1: Create Base Template (Day 1)
**File**: `templates/base.html`

**Features**:
- Include Tailwind CSS CDN
- Include Google Fonts (Spline Sans)
- Include Material Icons
- Dark mode by default
- Company color scheme
- EYTLOGO.jpg integration
- Django template tags ({% load static %}, {% block %})
- CSRF token support
- Messages framework integration
- Notification dropdown placeholder

**Structure**:
```html
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    {% load static %}
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>{% block title %}EYTGaming{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com"/>
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
    <link href="https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300..700&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    
    <!-- Tailwind Config -->
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#b91c1c",
                        "background-light": "#f6f6f8",
                        "background-dark": "#121212",
                        "card-dark": "#151c2c",
                        "card-border-dark": "#282e39"
                    },
                    fontFamily: {
                        "display": ["Spline Sans", "sans-serif"]
                    },
                    borderRadius: {
                        "DEFAULT": "0.25rem",
                        "lg": "0.5rem",
                        "xl": "0.75rem",
                        "full": "9999px"
                    },
                },
            },
        }
    </script>
    
    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24
        }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body class="font-display bg-background-light dark:bg-background-dark text-gray-300">
    {% block body %}{% endblock %}
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### Step 2: Authentication Templates (Day 1-2)
**Files to Create**:
- `templates/account/login.html` (from login_screen)
- `templates/account/signup.html` (from registration_screen)
- `templates/account/password_reset.html`
- `templates/account/password_reset_done.html`
- `templates/account/password_reset_confirm.html`

**Integration Points**:
- Django allauth forms
- CSRF tokens
- Form validation errors
- Success messages
- Social auth buttons (Google, Twitch)

#### Step 3: Base Layout with Navigation (Day 2-3)
**File**: `templates/layouts/dashboard_base.html`

**Features**:
- Sidebar navigation (from user_dashboard)
- Top navigation bar
- User profile dropdown
- Notification bell with count
- Search bar
- Mobile responsive menu
- Active page highlighting
- Logout functionality

**Navigation Items**:
```python
- Dashboard (/)
- Tournaments (/tournaments/)
- Coaching (/coaching/)
- Teams (/teams/)
- Messages (/messages/)
- Profile (/profile/)
- Settings (/settings/)
- Logout (/accounts/logout/)
```

---

### Phase 3B: Dashboard & Profile (Week 1)

#### Step 4: User Dashboard (Day 3-4)
**File**: `templates/dashboard/home.html`

**Sections**:
- Welcome message with user name
- Quick stats cards (tournaments, sessions, messages)
- Upcoming tournaments widget
- Upcoming coaching sessions widget
- Recent notifications
- Quick actions (Register for tournament, Book session)

**Backend Integration**:
```python
# dashboard/views.py
@login_required
def dashboard_home(request):
    context = {
        'upcoming_tournaments': Tournament.objects.filter(
            start_date__gte=timezone.now()
        )[:5],
        'upcoming_sessions': CoachingSession.objects.filter(
            student=request.user,
            scheduled_time__gte=timezone.now()
        )[:5],
        'recent_notifications': Notification.objects.filter(
            user=request.user
        )[:10],
        'stats': {
            'tournaments_joined': Participant.objects.filter(
                user=request.user
            ).count(),
            'sessions_booked': CoachingSession.objects.filter(
                student=request.user
            ).count(),
            'unread_messages': 0,  # TODO: Implement messaging
        }
    }
    return render(request, 'dashboard/home.html', context)
```

#### Step 5: User Profile (Day 4-5)
**File**: `templates/accounts/profile.html`

**Sections**:
- Profile header with avatar
- Personal information form
- Gaming profiles (Discord, Steam, Twitch)
- Game profiles (skill ratings, ranks)
- Statistics (tournaments, coaching)
- Payment methods link
- Notification preferences link

**Backend Integration**:
```python
# accounts/views.py
@login_required
def profile_view(request):
    if request.method == 'POST':
        # Handle profile update
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'game_profiles': request.user.game_profiles.all(),
        'payment_methods': PaymentMethod.objects.filter(user=request.user),
    }
    return render(request, 'accounts/profile.html', context)
```

---

### Phase 3C: Tournament Templates (Week 2)

#### Step 6: Tournament Listing (Day 1-2)
**File**: `templates/tournaments/list.html`

**Features**:
- Tournament cards grid
- Filter by game, status, date
- Search functionality
- Pagination
- "Register" button with payment integration

**Backend Integration**:
```python
# tournaments/views.py
def tournament_list(request):
    tournaments = Tournament.objects.filter(
        is_active=True
    ).select_related('game', 'organizer')
    
    # Filters
    game_id = request.GET.get('game')
    status = request.GET.get('status')
    
    if game_id:
        tournaments = tournaments.filter(game_id=game_id)
    if status:
        tournaments = tournaments.filter(status=status)
    
    context = {
        'tournaments': tournaments,
        'games': Game.objects.filter(is_active=True),
    }
    return render(request, 'tournaments/list.html', context)
```

#### Step 7: Tournament Detail (Day 2-3)
**File**: `templates/tournaments/detail.html`

**Sections**:
- Tournament header (name, game, dates)
- Tournament info (format, rules, prize pool)
- Registration section with payment
- Participants list
- Brackets/Schedule
- Chat/Discussion (future)

**Payment Integration**:
```html
<!-- Registration button -->
{% if not user_registered %}
<button onclick="registerForTournament()" class="btn-primary">
    Register Now - ${{ tournament.entry_fee }}
</button>
{% endif %}

<script>
async function registerForTournament() {
    // Create payment intent
    const response = await fetch('/payments/create-intent/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({
            amount: '{{ tournament.entry_fee }}',
            payment_type: 'tournament_fee',
            description: 'Registration for {{ tournament.name }}',
            metadata: {
                tournament_id: '{{ tournament.id }}'
            }
        })
    });
    
    const {client_secret, payment_id} = await response.json();
    
    // Redirect to checkout
    window.location.href = `/payments/checkout/?client_secret=${client_secret}&payment_id=${payment_id}`;
}
</script>
```

---

### Phase 3D: Coaching Templates (Week 2)

#### Step 8: Coach Listing (Day 3-4)
**File**: `templates/coaching/coach_list.html`

**Features**:
- Coach cards with ratings
- Filter by game, price range
- Search by name
- View profile button
- Book session button

#### Step 9: Coach Profile (Day 4-5)
**File**: `templates/coaching/coach_profile.html`

**Sections**:
- Coach header (avatar, name, rating)
- About section
- Games & expertise
- Pricing
- Availability calendar
- Reviews
- Book session button

#### Step 10: Booking Flow (Day 5)
**Files**:
- `templates/coaching/select_session.html`
- `templates/coaching/confirm_booking.html`
- `templates/coaching/booking_success.html`

**Payment Integration**: Similar to tournament registration

---

### Phase 3E: Payment Templates (Week 3)

#### Step 11: Payment Checkout (Day 1-2)
**File**: `templates/payments/checkout.html`

**Features**:
- Order summary
- Stripe Elements card input
- Saved payment methods
- Processing state
- Error handling

**Stripe Integration**:
```html
<div id="payment-element"></div>
<button id="submit-button">Pay ${{ amount }}</button>

<script src="https://js.stripe.com/v3/"></script>
<script>
const stripe = Stripe('{{ stripe_public_key }}');
const elements = stripe.elements({clientSecret: '{{ client_secret }}'});
const paymentElement = elements.create('payment');
paymentElement.mount('#payment-element');

document.getElementById('submit-button').addEventListener('click', async () => {
    const {error} = await stripe.confirmPayment({
        elements,
        confirmParams: {
            return_url: '{{ success_url }}',
        },
    });
    
    if (error) {
        showError(error.message);
    }
});
</script>
```

#### Step 12: Payment Management (Day 2-3)
**Files**:
- `templates/payments/methods.html` - List saved cards
- `templates/payments/add_method.html` - Add new card
- `templates/payments/history.html` - Payment history
- `templates/payments/detail.html` - Payment receipt

---

### Phase 3F: Notification Templates (Week 3)

#### Step 13: Notification Center (Day 3-4)
**File**: `templates/notifications/dropdown.html` (component)

**Features**:
- Bell icon with unread count badge
- Dropdown with recent notifications
- Mark as read functionality
- View all link

**AJAX Integration**:
```javascript
// Load notifications
async function loadNotifications() {
    const response = await fetch('/notifications/recent/', {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    });
    const data = await response.json();
    
    // Update badge
    document.getElementById('notification-count').textContent = data.unread_count;
    
    // Render notifications
    renderNotifications(data.notifications);
}

// Poll every 30 seconds
setInterval(loadNotifications, 30000);
```

#### Step 14: Notification Pages (Day 4-5)
**Files**:
- `templates/notifications/list.html` - All notifications
- `templates/notifications/preferences.html` - Settings

---

### Phase 3G: Messaging Templates (Week 4)

#### Step 15: Messaging (Day 1-3)
**Files**:
- `templates/messages/inbox.html` (from messaging_inbox)
- `templates/messages/compose.html` (from compose_new_message)
- `templates/messages/conversation.html` (from detailed_chat_view)

**Note**: Messaging backend needs to be implemented

---

### Phase 3H: Coach Dashboard (Week 4)

#### Step 16: Coach-Specific Views (Day 3-5)
**Files**:
- `templates/coaching/coach_dashboard.html` (from coach_dashboard)
- `templates/coaching/manage_profile.html` (from coach_profile_management)
- `templates/coaching/calendar.html` (from coaching_calendar_page)

---

## Component Library

### Reusable Components to Create:

1. **Navigation Components**
   - `templates/components/sidebar.html`
   - `templates/components/topbar.html`
   - `templates/components/mobile_menu.html`

2. **Card Components**
   - `templates/components/tournament_card.html`
   - `templates/components/coach_card.html`
   - `templates/components/stat_card.html`

3. **Form Components**
   - `templates/components/form_field.html`
   - `templates/components/form_errors.html`
   - `templates/components/submit_button.html`

4. **Notification Components**
   - `templates/components/notification_bell.html`
   - `templates/components/notification_item.html`
   - `templates/components/toast.html`

5. **Payment Components**
   - `templates/components/payment_card.html`
   - `templates/components/price_display.html`

---

## Static Files Organization

```
static/
├── css/
│   └── custom.css (additional styles)
├── js/
│   ├── main.js (global functionality)
│   ├── payments.js (Stripe integration)
│   ├── notifications.js (notification handling)
│   └── tournaments.js (tournament-specific)
├── images/
│   ├── EYTLOGO.jpg (from Tem folder)
│   ├── logo.svg (SVG version)
│   └── placeholders/
└── icons/
    └── (Material Icons fallbacks)
```

---

## Django Template Tags & Filters

### Custom Template Tags to Create:

```python
# templatetags/eyt_tags.py

@register.simple_tag
def notification_count(user):
    """Get unread notification count"""
    return Notification.objects.filter(user=user, read=False).count()

@register.filter
def currency(value):
    """Format as currency"""
    return f"${value:,.2f}"

@register.inclusion_tag('components/tournament_card.html')
def tournament_card(tournament, user):
    """Render tournament card"""
    return {
        'tournament': tournament,
        'user_registered': Participant.objects.filter(
            tournament=tournament,
            user=user
        ).exists()
    }

@register.inclusion_tag('components/notification_bell.html')
def notification_bell(user):
    """Render notification bell"""
    return {
        'unread_count': Notification.objects.filter(
            user=user,
            read=False
        ).count()
    }
```

---

## URL Structure

```python
# config/urls.py
urlpatterns = [
    # Authentication
    path('accounts/', include('allauth.urls')),
    
    # Dashboard
    path('', dashboard_home, name='home'),
    path('dashboard/', include('dashboard.urls')),
    
    # Tournaments
    path('tournaments/', include('tournaments.urls')),
    
    # Coaching
    path('coaching/', include('coaching.urls')),
    
    # Teams
    path('teams/', include('teams.urls')),
    
    # Payments
    path('payments/', include('payments.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
    
    # Profile
    path('profile/', include('accounts.urls')),
    
    # Messages (future)
    # path('messages/', include('messages.urls')),
]
```

---

## Testing Checklist

### Visual Testing:
- [ ] All pages render correctly
- [ ] Dark mode works properly
- [ ] Colors match design system (#b91c1c primary)
- [ ] Logo displays correctly
- [ ] Fonts load properly (Spline Sans)
- [ ] Icons display correctly (Material Symbols)
- [ ] Mobile responsive
- [ ] Tablet responsive

### Functional Testing:
- [ ] Login/logout works
- [ ] Registration works
- [ ] Profile updates save
- [ ] Tournament registration with payment
- [ ] Coaching booking with payment
- [ ] Notifications display and update
- [ ] Payment methods can be added/removed
- [ ] Forms validate correctly
- [ ] Error messages display
- [ ] Success messages display

### Integration Testing:
- [ ] Stripe payment flow end-to-end
- [ ] Notification delivery
- [ ] Email sending
- [ ] Webhook processing
- [ ] Audit logging

---

## Implementation Timeline

### Week 1: Foundation
- Day 1: Base templates + Authentication
- Day 2-3: Dashboard layout + Navigation
- Day 4-5: User dashboard + Profile

### Week 2: Core Features
- Day 1-3: Tournament templates
- Day 3-5: Coaching templates

### Week 3: Payments & Notifications
- Day 1-3: Payment templates
- Day 3-5: Notification templates

### Week 4: Polish & Testing
- Day 1-3: Messaging templates
- Day 3-4: Coach dashboard
- Day 5: Testing & bug fixes

---

## Migration Strategy

### Step-by-Step:
1. Copy EYTLOGO.jpg to `static/images/`
2. Create base.html with design system
3. Create dashboard_base.html with navigation
4. Migrate one template at a time
5. Test each template before moving to next
6. Update views to use new templates
7. Test integration with backend
8. Deploy to staging
9. User acceptance testing
10. Deploy to production

---

## Success Criteria

- ✅ All templates use consistent design system
- ✅ Primary color #b91c1c used throughout
- ✅ EYTLOGO.jpg displayed on all pages
- ✅ Spline Sans font loads correctly
- ✅ Dark mode works properly
- ✅ Mobile responsive
- ✅ Payment integration works
- ✅ Notifications work
- ✅ All forms functional
- ✅ No console errors
- ✅ Fast page load times

---

## Next Steps

1. **Start with base.html** - Foundation for all pages
2. **Create authentication templates** - Login/signup
3. **Build dashboard layout** - Navigation + structure
4. **Integrate one feature at a time** - Tournaments first
5. **Test thoroughly** - Each template before moving on
6. **Deploy incrementally** - Staging → Production

---

**Ready to start implementation!** 🚀
