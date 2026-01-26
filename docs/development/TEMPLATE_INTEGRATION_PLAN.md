# EYTGaming Template Integration Plan

## Executive Summary

This document outlines the comprehensive plan to integrate the pre-designed templates from the `Tem/` folder into the existing Django backend infrastructure. The integration will maintain design consistency using the company's brand colors (primary red: #b91c1c) and the EYTLOGO.jpg as the brand logo.

---

## 1. Design System Analysis

### Brand Colors (from login_screen)
```css
Primary Red: #b91c1c (Company Brand Color)
Background Light: #f6f6f8
Background Dark: #121212
Card Dark: #151c2c
Card Border Dark: #282e39
Neutral 900: #171717
Neutral 800: #262626
Neutral 700: #404040
```

### Typography
- **Font Family**: Spline Sans (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700

### Design Patterns
- **Glassmorphism**: Cards with backdrop blur and transparency
- **Dark Theme**: Primary design mode
- **Material Icons**: Google Material Symbols Outlined
- **Rounded Corners**: 0.25rem (default), 0.5rem (lg), 0.75rem (xl)

---

## 2. Template Inventory & Mapping

### Available Templates in `Tem/` Folder

| Template Folder | Purpose | Django App | Priority | Status |
|----------------|---------|------------|----------|--------|
| `login_screen/` | User authentication | `accounts` | **HIGH** | ✅ Reference Design |
| `registration_screen/` | User signup | `accounts` | **HIGH** | 🔄 To Integrate |
| `user_dashboard/` | Player dashboard | `dashboard` | **HIGH** | 🔄 To Integrate |
| `user_profile_screen/` | User profile management | `accounts` | **HIGH** | 🔄 To Integrate |
| `tournament_listing_page/` | Browse tournaments | `tournaments` | **HIGH** | 🔄 To Integrate |
| `detailed_tournament_page_1/` | Tournament details (view 1) | `tournaments` | **HIGH** | 🔄 To Integrate |
| `detailed_tournament_page_2/` | Tournament details (view 2) | `tournaments` | **HIGH** | 🔄 To Integrate |
| `select_coach/` | Coach directory | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `coach_profile_management/` | Coach profile settings | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `coach_dashboard/` | Coach dashboard | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `coaching_calendar_page/` | Availability calendar | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `booking_confirmation/` | Session booking | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `confirm_booking_details/` | Booking review | `coaching` | **MEDIUM** | 🔄 To Integrate |
| `messaging_inbox/` | Message list | `notifications` | **LOW** | 🔄 To Integrate |
| `detailed_chat_view/` | Chat interface | `notifications` | **LOW** | 🔄 To Integrate |
| `compose_new_message/` | New message | `notifications` | **LOW** | 🔄 To Integrate |

---

## 3. Integration Strategy

### Phase 1: Foundation & Authentication (Week 1)
**Goal**: Establish base template system and authentication flows

#### 3.1 Create Base Template with Brand Identity
**File**: `templates/base.html`

**Tasks**:
1. ✅ Extract common layout structure from templates
2. ✅ Integrate EYTLOGO.jpg as brand logo
3. ✅ Set up navigation with sidebar (desktop) and mobile menu
4. ✅ Configure Tailwind with brand colors
5. ✅ Add Material Icons CDN
6. ✅ Set up Alpine.js for interactivity
7. ✅ Create reusable components (buttons, cards, forms)

**Key Features**:
- Responsive sidebar navigation
- Top header with search, notifications, user menu
- Dark theme by default
- HTMX integration for dynamic updates
- Django messages/alerts system

#### 3.2 Authentication Templates
**Files**: 
- `templates/account/login.html`
- `templates/account/signup.html`
- `templates/account/password_reset.html`
- `templates/account/email_verification.html`

**Tasks**:
1. ✅ Convert `login_screen/code.html` to Django template
2. ✅ Add Django form integration with django-allauth
3. ✅ Implement social auth buttons (Discord, Steam, Google)
4. ✅ Add CSRF tokens and form validation
5. ✅ Create consistent error messaging
6. ✅ Add "Remember Me" functionality
7. ✅ Integrate with existing User model

**Design Consistency**:
- Use #b91c1c as primary color throughout
- Maintain glassmorphism card design
- Keep background image with opacity overlay
- Use EYTLOGO.jpg in header

---

### Phase 2: Dashboard & Profile (Week 2)
**Goal**: User-facing dashboard and profile management

#### 3.3 User Dashboard
**File**: `templates/dashboard/index.html`

**Tasks**:
1. ✅ Convert `user_dashboard/code.html` to Django template
2. ✅ Integrate with existing models:
   - Tournament registrations
   - Coaching sessions
   - User stats from UserGameProfile
3. ✅ Add HTMX for live updates
4. ✅ Create dashboard widgets:
   - Upcoming tournaments
   - Recent coaching sessions
   - Performance stats
   - Recommendations
5. ✅ Add game selector dropdown
6. ✅ Implement notification bell with count

**Backend Integration**:
```python
# dashboard/views.py
def dashboard_view(request):
    user = request.user
    context = {
        'upcoming_tournaments': Tournament.objects.filter(
            participants__user=user,
            status__in=['registration', 'check_in', 'in_progress']
        )[:5],
        'recent_sessions': CoachingSession.objects.filter(
            student=user
        ).order_by('-scheduled_start')[:5],
        'user_stats': user.game_profiles.filter(is_main_game=True).first(),
        'recommendations': get_recommendations(user),
    }
    return render(request, 'dashboard/index.html', context)
```

#### 3.4 User Profile
**File**: `templates/accounts/profile.html`

**Tasks**:
1. ✅ Convert `user_profile_screen/code.html`
2. ✅ Add profile editing forms
3. ✅ Integrate avatar upload (Cloudinary/S3)
4. ✅ Add game profile management
5. ✅ Social links integration
6. ✅ Privacy settings
7. ✅ Account deletion option

---

### Phase 3: Tournament System (Week 3-4)
**Goal**: Complete tournament browsing and participation

#### 3.5 Tournament Listing
**File**: `templates/tournaments/tournament_list.html`

**Tasks**:
1. ✅ Convert `tournament_listing_page/code.html`
2. ✅ Add filtering system:
   - By game
   - By status (upcoming, live, completed)
   - By format (single elim, double elim, etc.)
   - By entry fee
3. ✅ Implement search with HTMX
4. ✅ Add pagination
5. ✅ Create tournament cards with:
   - Banner image
   - Status badge
   - Prize pool
   - Participant count
   - Registration deadline
6. ✅ Add "Create Tournament" button (for organizers)

**Backend Integration**:
```python
# tournaments/views.py
class TournamentListView(ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    paginate_by = 12
    
    def get_queryset(self):
        qs = Tournament.objects.filter(is_public=True)
        
        # Filters
        game = self.request.GET.get('game')
        status = self.request.GET.get('status')
        format = self.request.GET.get('format')
        
        if game:
            qs = qs.filter(game__slug=game)
        if status:
            qs = qs.filter(status=status)
        if format:
            qs = qs.filter(format=format)
            
        return qs.order_by('-start_datetime')
```

#### 3.6 Tournament Detail Pages
**Files**: 
- `templates/tournaments/tournament_detail.html`
- `templates/tournaments/bracket.html`

**Tasks**:
1. ✅ Merge `detailed_tournament_page_1` and `detailed_tournament_page_2`
2. ✅ Create tabbed interface:
   - Overview
   - Bracket
   - Participants
   - Rules
   - Matches
3. ✅ Add registration/check-in buttons
4. ✅ Implement countdown timer
5. ✅ Show organizer info
6. ✅ Add share buttons
7. ✅ Integrate bracket visualization
8. ✅ Add match reporting (for participants)
9. ✅ Show stream embed if available

**Bracket Visualization**:
- Use SVG for bracket rendering
- HTMX for live updates
- Click to expand match details
- Highlight user's matches

---

### Phase 4: Coaching System (Week 5-6)
**Goal**: Complete coaching booking and management

#### 3.7 Coach Directory
**File**: `templates/coaching/coach_list.html`

**Tasks**:
1. ✅ Convert `select_coach/code.html`
2. ✅ Add filtering:
   - By game
   - By price range
   - By rating
   - By availability
3. ✅ Create coach cards with:
   - Avatar
   - Name & title
   - Rating stars
   - Hourly rate
   - Games taught
   - Availability indicator
4. ✅ Add "Book Now" buttons
5. ✅ Implement search

#### 3.8 Coach Dashboard
**File**: `templates/coaching/coach_dashboard.html`

**Tasks**:
1. ✅ Convert `coach_dashboard/code.html`
2. ✅ Show upcoming sessions
3. ✅ Display earnings summary
4. ✅ Add availability management
5. ✅ Show student reviews
6. ✅ Add session history

#### 3.9 Booking Flow
**Files**:
- `templates/coaching/book_session.html`
- `templates/coaching/booking_confirmation.html`

**Tasks**:
1. ✅ Convert `coaching_calendar_page/code.html`
2. ✅ Integrate FullCalendar.js
3. ✅ Show available time slots
4. ✅ Add session duration selector
5. ✅ Implement Stripe payment
6. ✅ Create confirmation page
7. ✅ Send email notifications

---

### Phase 5: Messaging & Notifications (Week 7)
**Goal**: Communication system

#### 3.10 Messaging System
**Files**:
- `templates/notifications/inbox.html`
- `templates/notifications/chat.html`
- `templates/notifications/compose.html`

**Tasks**:
1. ✅ Convert messaging templates
2. ✅ Implement real-time chat (Django Channels)
3. ✅ Add message threading
4. ✅ Create notification system
5. ✅ Add unread count badges

---

## 4. Technical Implementation Details

### 4.1 Base Template Structure

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}EYTGaming{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Material Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    
    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Tailwind Config -->
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        "primary": "#b91c1c", // EYT Brand Red
                        "background-light": "#f6f6f8",
                        "background-dark": "#121212",
                        "card-dark": "#151c2c",
                        "card-border-dark": "#282e39"
                    },
                    fontFamily: {
                        "display": ["Spline Sans", "sans-serif"]
                    },
                },
            },
        }
    </script>
    
    {% block extra_css %}{% endblock %}
</head>
<body class="font-display bg-background-dark text-gray-300">
    <div class="flex min-h-screen">
        <!-- Sidebar Navigation -->
        {% include 'components/sidebar.html' %}
        
        <!-- Main Content -->
        <main class="flex-1 flex flex-col">
            <!-- Top Header -->
            {% include 'components/header.html' %}
            
            <!-- Page Content -->
            <div class="flex-1 overflow-y-auto p-6 md:p-8">
                <!-- Django Messages -->
                {% if messages %}
                    {% include 'components/messages.html' %}
                {% endif %}
                
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 4.2 Component Templates

#### Sidebar Component
**File**: `templates/components/sidebar.html`

```html
<aside class="w-64 flex-shrink-0 bg-background-dark border-r border-card-border-dark hidden md:flex flex-col">
    <div class="flex flex-col h-full p-4">
        <!-- Logo -->
        <div class="flex items-center gap-3 p-2 mb-6">
            <img src="{% static 'images/EYTLOGO.jpg' %}" alt="EYT Gaming" class="h-10 w-auto">
            <h1 class="text-white text-xl font-bold">EYTGaming</h1>
        </div>
        
        <!-- Navigation Links -->
        <nav class="flex flex-col gap-2">
            <a href="{% url 'dashboard:index' %}" class="nav-link {% if request.resolver_match.url_name == 'index' %}active{% endif %}">
                <span class="material-symbols-outlined">dashboard</span>
                <span>Dashboard</span>
            </a>
            <a href="{% url 'tournaments:list' %}" class="nav-link">
                <span class="material-symbols-outlined">emoji_events</span>
                <span>Tournaments</span>
            </a>
            <a href="{% url 'coaching:coach_list' %}" class="nav-link">
                <span class="material-symbols-outlined">sports_esports</span>
                <span>Coaching</span>
            </a>
            <a href="{% url 'accounts:profile' %}" class="nav-link">
                <span class="material-symbols-outlined">person</span>
                <span>Profile</span>
            </a>
        </nav>
        
        <!-- Bottom Links -->
        <div class="mt-auto flex flex-col gap-2">
            <a href="{% url 'accounts:settings' %}" class="nav-link">
                <span class="material-symbols-outlined">settings</span>
                <span>Settings</span>
            </a>
            <a href="{% url 'account_logout' %}" class="nav-link">
                <span class="material-symbols-outlined">logout</span>
                <span>Logout</span>
            </a>
        </div>
    </div>
</aside>

<style>
.nav-link {
    @apply flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors;
}
.nav-link.active {
    @apply bg-primary/20 text-primary;
}
</style>
```

### 4.3 URL Configuration Updates

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', include('dashboard.urls')),
    path('tournaments/', include('tournaments.urls')),
    path('coaching/', include('coaching.urls')),
    path('profile/', include('accounts.urls')),
    path('messages/', include('notifications.urls')),
]
```

### 4.4 Static Files Setup

```bash
# Create static directories
mkdir -p static/images
mkdir -p static/css
mkdir -p static/js

# Copy logo
cp Tem/EYTLOGO.jpg static/images/
```

**Update settings.py**:
```python
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

---

## 5. Color Consistency Implementation

### 5.1 Update All Templates to Use Brand Red

**Find and Replace**:
- `#135bec` → `#b91c1c` (primary blue to brand red)
- `#6366f1` → `#b91c1c` (indigo to brand red)
- `#8b5cf6` → `#b91c1c` (purple to brand red)

### 5.2 Tailwind Configuration

```javascript
// In all template <script> tags
tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "primary": "#b91c1c",
                "primary-dark": "#991b1b",
                "primary-light": "#dc2626",
                "background-light": "#f6f6f8",
                "background-dark": "#121212",
                "card-dark": "#151c2c",
                "card-border-dark": "#282e39"
            },
        },
    },
}
```

---

## 6. Django Integration Checklist

### 6.1 For Each Template

- [ ] Convert static HTML to Django template syntax
- [ ] Add `{% load static %}` at top
- [ ] Replace hardcoded URLs with `{% url %}` tags
- [ ] Add CSRF tokens to forms: `{% csrf_token %}`
- [ ] Replace static content with Django variables
- [ ] Add template inheritance: `{% extends 'base.html' %}`
- [ ] Define blocks: `{% block content %}{% endblock %}`
- [ ] Add conditional rendering: `{% if %}{% endif %}`
- [ ] Add loops: `{% for %}{% endfor %}`
- [ ] Replace logo path with `{% static 'images/EYTLOGO.jpg' %}`
- [ ] Add user authentication checks: `{% if user.is_authenticated %}`
- [ ] Integrate Django messages framework
- [ ] Add HTMX attributes for dynamic updates
- [ ] Test responsiveness
- [ ] Validate HTML
- [ ] Check accessibility (ARIA labels)

### 6.2 Backend View Requirements

For each template, create corresponding view:

```python
# Example: tournaments/views.py
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Tournament

class TournamentListView(ListView):
    model = Tournament
    template_name = 'tournaments/tournament_list.html'
    context_object_name = 'tournaments'
    paginate_by = 12
    
    def get_queryset(self):
        # Add filtering logic
        pass
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['games'] = Game.objects.filter(is_active=True)
        return context
```

---

## 7. Testing Strategy

### 7.1 Visual Testing
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test on mobile devices (iOS, Android)
- [ ] Test on tablets
- [ ] Verify dark theme consistency
- [ ] Check logo visibility on all pages
- [ ] Verify color consistency (#b91c1c everywhere)

### 7.2 Functional Testing
- [ ] Test all forms submit correctly
- [ ] Verify CSRF protection
- [ ] Test authentication flows
- [ ] Verify permission checks
- [ ] Test HTMX dynamic updates
- [ ] Check pagination
- [ ] Test search functionality
- [ ] Verify file uploads

### 7.3 Performance Testing
- [ ] Check page load times
- [ ] Optimize images
- [ ] Minify CSS/JS in production
- [ ] Test with slow network
- [ ] Check database query counts

---

## 8. Deployment Checklist

### 8.1 Pre-Deployment
- [ ] Run `python manage.py collectstatic`
- [ ] Test all templates in production mode (DEBUG=False)
- [ ] Verify all static files load
- [ ] Check HTTPS for CDN resources
- [ ] Optimize images (compress EYTLOGO.jpg)
- [ ] Set up CDN for static files (optional)

### 8.2 Post-Deployment
- [ ] Verify logo displays correctly
- [ ] Check all colors render properly
- [ ] Test authentication flows
- [ ] Verify email templates
- [ ] Check mobile responsiveness
- [ ] Test payment integration
- [ ] Monitor error logs

---

## 9. Timeline & Milestones

| Week | Phase | Deliverables | Status |
|------|-------|--------------|--------|
| 1 | Foundation | Base template, Auth pages | 🔄 In Progress |
| 2 | Dashboard | User dashboard, Profile | ⏳ Pending |
| 3-4 | Tournaments | List, Detail, Bracket | ⏳ Pending |
| 5-6 | Coaching | Directory, Booking, Dashboard | ⏳ Pending |
| 7 | Messaging | Inbox, Chat, Compose | ⏳ Pending |
| 8 | Testing | Full QA, Bug fixes | ⏳ Pending |
| 9 | Polish | Performance, Accessibility | ⏳ Pending |
| 10 | Deployment | Production launch | ⏳ Pending |

---

## 10. Next Steps

### Immediate Actions (This Week)

1. **Create Base Template**
   ```bash
   # Create directory structure
   mkdir -p templates/components
   mkdir -p templates/account
   mkdir -p templates/dashboard
   mkdir -p templates/tournaments
   mkdir -p templates/coaching
   mkdir -p templates/notifications
   
   # Copy logo
   cp Tem/EYTLOGO.jpg static/images/
   ```

2. **Convert Login Template**
   - Start with `Tem/login_screen/code.html`
   - Integrate with django-allauth
   - Test authentication flow

3. **Create Component Library**
   - Sidebar navigation
   - Top header
   - Message alerts
   - Button styles
   - Card styles
   - Form inputs

4. **Set Up Development Environment**
   - Install required packages
   - Configure Tailwind
   - Set up HTMX
   - Test Alpine.js

### Priority Order

1. **HIGH PRIORITY** (Week 1-2)
   - Base template
   - Authentication pages
   - User dashboard
   - Profile page

2. **MEDIUM PRIORITY** (Week 3-6)
   - Tournament system
   - Coaching system

3. **LOW PRIORITY** (Week 7+)
   - Messaging system
   - Advanced features

---

## 11. Resources & References

### Documentation
- Django Templates: https://docs.djangoproject.com/en/5.0/topics/templates/
- Tailwind CSS: https://tailwindcss.com/docs
- HTMX: https://htmx.org/docs/
- Alpine.js: https://alpinejs.dev/
- Django-allauth: https://django-allauth.readthedocs.io/

### Design Assets
- Logo: `static/images/EYTLOGO.jpg`
- Brand Color: #b91c1c
- Font: Spline Sans (Google Fonts)
- Icons: Material Symbols Outlined

### Code Examples
- Template files in `Tem/` folder
- Existing Django models in `core/`, `tournaments/`, `coaching/`
- Current views in respective app directories

---

## 12. Success Criteria

### Design Consistency
✅ All pages use #b91c1c as primary color
✅ EYTLOGO.jpg visible on all pages
✅ Consistent typography (Spline Sans)
✅ Unified dark theme
✅ Consistent spacing and layout

### Functionality
✅ All forms work correctly
✅ Authentication flows complete
✅ HTMX updates work smoothly
✅ Mobile responsive
✅ Fast page loads (<2s)

### Code Quality
✅ DRY principles followed
✅ Reusable components created
✅ Proper Django template inheritance
✅ Clean, commented code
✅ No console errors

---

## Conclusion

This integration plan provides a structured approach to converting the pre-designed templates into a fully functional Django application while maintaining brand consistency and design quality. The phased approach allows for iterative development and testing, ensuring each component works correctly before moving to the next.

**Key Success Factors**:
1. Maintain brand color (#b91c1c) throughout
2. Use EYTLOGO.jpg consistently
3. Follow Django best practices
4. Test thoroughly at each phase
5. Keep design responsive and accessible

**Next Action**: Begin Phase 1 - Create base template and convert authentication pages.
