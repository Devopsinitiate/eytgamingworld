# Integration Flow Diagram

## Visual Integration Process

```
┌─────────────────────────────────────────────────────────────────┐
│                     TEMPLATE INTEGRATION FLOW                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Tem/ Folder │  (Source Templates)
│              │
│ • EYTLOGO.jpg│
│ • 16 HTML    │
│   templates  │
└──────┬───────┘
       │
       │ STEP 1: Analyze & Plan
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Analysis Phase                                               │
│  ✓ Identify brand colors (#b91c1c)                          │
│  ✓ Extract common patterns                                   │
│  ✓ Map templates to Django apps                             │
│  ✓ Identify reusable components                             │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ STEP 2: Setup Foundation
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Foundation Setup                                             │
│  1. Copy EYTLOGO.jpg → static/images/                       │
│  2. Create templates/components/                             │
│  3. Create base_eyt.html                                     │
│  4. Add Tailwind + Alpine.js + HTMX                         │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ STEP 3: Create Components
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Component Creation                                           │
│  • sidebar.html    (Navigation + Logo)                       │
│  • header.html     (Search + Notifications + User)          │
│  • messages.html   (Django messages display)                │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ STEP 4: Convert Templates (Phase by Phase)
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 1: Authentication                                      │
│  ┌────────────────┐                                          │
│  │ login_screen/  │ → templates/account/login.html          │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ registration/  │ → templates/account/signup.html         │
│  └────────────────┘                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 2: Dashboard                                           │
│  ┌────────────────┐                                          │
│  │ user_dashboard/│ → templates/dashboard/index.html        │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ user_profile/  │ → templates/accounts/profile.html       │
│  └────────────────┘                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 3: Tournaments                                         │
│  ┌────────────────┐                                          │
│  │ tournament_    │ → templates/tournaments/                 │
│  │ listing_page/  │    tournament_list.html                  │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ detailed_      │ → templates/tournaments/                 │
│  │ tournament_1&2/│    tournament_detail.html                │
│  └────────────────┘                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 4: Coaching                                            │
│  ┌────────────────┐                                          │
│  │ select_coach/  │ → templates/coaching/coach_list.html    │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ coach_         │ → templates/coaching/                    │
│  │ dashboard/     │    coach_dashboard.html                  │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ coaching_      │ → templates/coaching/calendar.html      │
│  │ calendar/      │                                          │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ booking_       │ → templates/coaching/                    │
│  │ confirmation/  │    booking_confirm.html                  │
│  └────────────────┘                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Phase 5: Messaging                                           │
│  ┌────────────────┐                                          │
│  │ messaging_     │ → templates/notifications/inbox.html    │
│  │ inbox/         │                                          │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ detailed_chat/ │ → templates/notifications/chat.html     │
│  └────────────────┘                                          │
│  ┌────────────────┐                                          │
│  │ compose_new_   │ → templates/notifications/compose.html  │
│  │ message/       │                                          │
│  └────────────────┘                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ STEP 5: Integration & Testing
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Backend Integration                                          │
│  • Connect to Django models                                   │
│  • Add view logic                                            │
│  • Configure URLs                                            │
│  • Add form handling                                         │
│  • Integrate HTMX for dynamic updates                        │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Testing Phase                                                │
│  ✓ Visual testing (all browsers)                            │
│  ✓ Functional testing (all features)                        │
│  ✓ Mobile responsiveness                                     │
│  ✓ Performance testing                                       │
│  ✓ Accessibility testing                                     │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Deployment                                                   │
│  ✓ Collect static files                                      │
│  ✓ Test in production mode                                   │
│  ✓ Deploy to server                                          │
│  ✓ Monitor & optimize                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Template Conversion Process

```
For Each Template:

┌─────────────────┐
│  Source HTML    │  (Tem/folder/code.html)
└────────┬────────┘
         │
         │ 1. Read & Analyze
         ▼
┌─────────────────────────────────────────┐
│  Identify:                               │
│  • Static content vs dynamic content    │
│  • Form fields                          │
│  • Links & navigation                   │
│  • Images & assets                      │
│  • JavaScript interactions              │
└────────┬────────────────────────────────┘
         │
         │ 2. Convert Structure
         ▼
┌─────────────────────────────────────────┐
│  Add Django Template Syntax:            │
│  • {% extends 'base_eyt.html' %}       │
│  • {% load static %}                    │
│  • {% block content %}                  │
│  • {% url 'app:view' %}                │
└────────┬────────────────────────────────┘
         │
         │ 3. Update Assets
         ▼
┌─────────────────────────────────────────┐
│  Replace:                                │
│  • Logo → {% static 'images/EYTLOGO.jpg' %}│
│  • Colors → #b91c1c                     │
│  • Hardcoded URLs → {% url %}          │
└────────┬────────────────────────────────┘
         │
         │ 4. Add Dynamic Content
         ▼
┌─────────────────────────────────────────┐
│  Integrate:                              │
│  • {{ user.get_display_name }}          │
│  • {% for item in items %}              │
│  • {% if condition %}                   │
│  • {{ form.field }}                     │
└────────┬────────────────────────────────┘
         │
         │ 5. Add Forms
         ▼
┌─────────────────────────────────────────┐
│  Forms:                                  │
│  • <form method="post">                 │
│  • {% csrf_token %}                     │
│  • {{ form.as_p }}                      │
│  • <button type="submit">               │
└────────┬────────────────────────────────┘
         │
         │ 6. Test
         ▼
┌─────────────────────────────────────────┐
│  Testing:                                │
│  • Visual check                         │
│  • Functionality check                  │
│  • Mobile check                         │
│  • Browser compatibility                │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Django Template│  (templates/app/page.html)
└─────────────────┘
```

---

## Color Update Process

```
┌──────────────────────────────────────────────────────────┐
│  Color Consistency Workflow                               │
└──────────────────────────────────────────────────────────┘

Step 1: Identify Current Colors
┌────────────────────────────────────────┐
│  Template: user_dashboard/code.html    │
│  Current Primary: #135bec (Blue)       │
└────────────────────────────────────────┘
         │
         │ Find & Replace
         ▼
┌────────────────────────────────────────┐
│  Find: #135bec                         │
│  Replace: #b91c1c                      │
│                                        │
│  Find: #6366f1                         │
│  Replace: #b91c1c                      │
│                                        │
│  Find: #8b5cf6                         │
│  Replace: #b91c1c                      │
└────────────────────────────────────────┘
         │
         │ Update Tailwind Config
         ▼
┌────────────────────────────────────────┐
│  tailwind.config = {                   │
│    theme: {                            │
│      extend: {                         │
│        colors: {                       │
│          "primary": "#b91c1c",  ✓     │
│        },                              │
│      },                                │
│    },                                  │
│  }                                     │
└────────────────────────────────────────┘
         │
         │ Verify
         ▼
┌────────────────────────────────────────┐
│  Check:                                │
│  ✓ Buttons use bg-primary              │
│  ✓ Links use text-primary              │
│  ✓ Borders use border-primary          │
│  ✓ Hover states use hover:bg-primary   │
└────────────────────────────────────────┘
```

---

## Component Reuse Pattern

```
┌──────────────────────────────────────────────────────────┐
│  Component-Based Architecture                             │
└──────────────────────────────────────────────────────────┘

Create Once:
┌────────────────────────────────────────┐
│  templates/components/sidebar.html     │
│  • Logo (EYTLOGO.jpg)                  │
│  • Navigation links                    │
│  • Active state logic                  │
│  • Logout button                       │
└────────────────────────────────────────┘

Use Everywhere:
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  Dashboard     │  │  Tournaments   │  │  Coaching      │
│  Page          │  │  Page          │  │  Page          │
│                │  │                │  │                │
│  {% include    │  │  {% include    │  │  {% include    │
│  'components/  │  │  'components/  │  │  'components/  │
│  sidebar.html' │  │  sidebar.html' │  │  sidebar.html' │
│  %}            │  │  %}            │  │  %}            │
└────────────────┘  └────────────────┘  └────────────────┘

Benefits:
✓ Update once, changes everywhere
✓ Consistent design
✓ Easier maintenance
✓ Faster development
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│  Django MVC Pattern with Templates                       │
└──────────────────────────────────────────────────────────┘

User Request
     │
     ▼
┌─────────────┐
│  urls.py    │  (URL routing)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  views.py   │  (Business logic)
└──────┬──────┘
       │
       │ Query Database
       ▼
┌─────────────┐
│  models.py  │  (Data layer)
│             │
│  • User     │
│  • Tournament│
│  • Coach    │
└──────┬──────┘
       │
       │ Return Data
       ▼
┌─────────────┐
│  views.py   │  (Prepare context)
└──────┬──────┘
       │
       │ Render Template
       ▼
┌─────────────────────────────────────┐
│  templates/app/page.html            │
│                                     │
│  {% extends 'base_eyt.html' %}     │
│  {% block content %}                │
│    <div>{{ user.name }}</div>      │
│    {% for item in items %}         │
│      <div>{{ item.title }}</div>   │
│    {% endfor %}                     │
│  {% endblock %}                     │
└──────┬──────────────────────────────┘
       │
       │ HTML Response
       ▼
┌─────────────┐
│  Browser    │  (Rendered page)
└─────────────┘
```

---

## Timeline Visualization

```
Week 1: Foundation
████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 10%
• Base template
• Components
• Auth pages

Week 2: Dashboard
████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25%
• User dashboard
• Profile page

Week 3-4: Tournaments
████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ 50%
• Tournament list
• Tournament detail
• Bracket system

Week 5-6: Coaching
████████████████████████████████████████████░░░░░░░░░░░░░░ 75%
• Coach directory
• Booking system
• Coach dashboard

Week 7: Messaging
████████████████████████████████████████████████████░░░░░░ 85%
• Inbox
• Chat
• Compose

Week 8-9: Testing & Polish
████████████████████████████████████████████████████████████ 100%
• QA testing
• Bug fixes
• Deployment
```

---

## Success Metrics Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Integration Progress                                     │
└──────────────────────────────────────────────────────────┘

Templates Converted:     [  0 / 16 ]  ░░░░░░░░░░░░░░░░░░░░  0%
Components Created:      [  0 /  6 ]  ░░░░░░░░░░░░░░░░░░░░  0%
Pages Tested:            [  0 / 22 ]  ░░░░░░░░░░░░░░░░░░░░  0%

Design Consistency:
  ✓ Brand Color (#b91c1c)     [ ] Not Started
  ✓ Logo (EYTLOGO.jpg)        [ ] Not Started
  ✓ Typography (Spline Sans)  [ ] Not Started
  ✓ Dark Theme                [ ] Not Started

Functionality:
  ✓ Authentication            [ ] Not Started
  ✓ Dashboard                 [ ] Not Started
  ✓ Tournaments               [ ] Not Started
  ✓ Coaching                  [ ] Not Started
  ✓ Messaging                 [ ] Not Started

Quality:
  ✓ Mobile Responsive         [ ] Not Started
  ✓ Browser Compatible        [ ] Not Started
  ✓ Accessible (WCAG AA)      [ ] Not Started
  ✓ Performance (<2s load)    [ ] Not Started
```

---

## Quick Reference: File Locations

```
Project Root
│
├── Tem/                          ← SOURCE TEMPLATES
│   ├── EYTLOGO.jpg              ← BRAND LOGO
│   ├── login_screen/            ← REFERENCE DESIGN
│   └── [15 other templates]
│
├── static/
│   └── images/
│       └── EYTLOGO.jpg          ← COPY LOGO HERE
│
├── templates/
│   ├── base_eyt.html            ← CREATE THIS
│   ├── components/              ← CREATE THIS
│   │   ├── sidebar.html
│   │   ├── header.html
│   │   └── messages.html
│   ├── account/                 ← CREATE THIS
│   ├── dashboard/               ← CREATE THIS
│   ├── tournaments/             ← CREATE THIS
│   ├── coaching/                ← CREATE THIS
│   └── notifications/           ← CREATE THIS
│
└── [Django apps]
    ├── core/
    ├── accounts/
    ├── dashboard/
    ├── tournaments/
    ├── coaching/
    └── notifications/
```

---

**Use this diagram as a visual reference while following the integration guides!**
