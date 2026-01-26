# Quick Start: Template Integration

## Immediate Setup (30 minutes)

### Step 1: Prepare Static Files

```bash
# Create directories
mkdir -p static/images static/css static/js

# Copy logo
copy Tem\EYTLOGO.jpg static\images\

# Verify
dir static\images\EYTLOGO.jpg
```

### Step 2: Update Settings

Add to `config/settings.py`:

```python
# Static files configuration
STATICFILES_DIRS = [BASE_DIR / 'static']

# Template context processors (already exists, verify)
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'core.context_processors.site_settings',
])
```

### Step 3: Create Template Directories

```bash
# Create structure
mkdir templates\components
mkdir templates\account
```

### Step 4: Test Current Setup

```bash
python manage.py collectstatic --noinput
python manage.py runserver
```

Visit: http://127.0.0.1:8000/

---

## Phase 1: Base Template (2 hours)

### Create Base Template

Create `templates/base_eyt.html`:

```html
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}EYTGaming{% endblock %}</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    
    <!-- Alpine.js & HTMX -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
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
                },
            },
        }
    </script>
    
    <style>
        .material-symbols-outlined {
            font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body class="font-display bg-background-dark text-gray-300">
    {% block body %}
    <div class="flex min-h-screen">
        {% if user.is_authenticated %}
            {% include 'components/sidebar.html' %}
        {% endif %}
        
        <main class="flex-1 flex flex-col">
            {% if user.is_authenticated %}
                {% include 'components/header.html' %}
            {% endif %}
            
            <div class="flex-1 overflow-y-auto p-6 md:p-8">
                {% if messages %}
                    {% for message in messages %}
                    <div class="mb-4 p-4 rounded-lg {% if message.tags == 'error' %}bg-red-900/20 border border-red-900 text-red-200{% elif message.tags == 'success' %}bg-green-900/20 border border-green-900 text-green-200{% else %}bg-blue-900/20 border border-blue-900 text-blue-200{% endif %}">
                        {{ message }}
                    </div>
                    {% endfor %}
                {% endif %}
                
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
    {% endblock body %}
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Create Sidebar Component

Create `templates/components/sidebar.html`:

```html
{% load static %}
<aside class="w-64 flex-shrink-0 bg-background-dark border-r border-card-border-dark hidden md:flex flex-col">
    <div class="flex flex-col h-full p-4">
        <!-- Logo -->
        <div class="flex items-center gap-3 p-2 mb-6">
            <img src="{% static 'images/EYTLOGO.jpg' %}" alt="EYT Gaming" class="h-10 w-auto rounded">
            <h1 class="text-white text-xl font-bold">EYTGaming</h1>
        </div>
        
        <!-- Navigation -->
        <nav class="flex flex-col gap-2">
            <a href="{% url 'dashboard:index' %}" class="flex items-center gap-3 px-3 py-2 rounded-lg {% if request.resolver_match.url_name == 'index' %}bg-primary/20 text-primary{% else %}text-gray-300 hover:bg-card-dark{% endif %} transition-colors">
                <span class="material-symbols-outlined">dashboard</span>
                <span class="text-sm font-medium">Dashboard</span>
            </a>
            <a href="{% url 'tournaments:list' %}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors">
                <span class="material-symbols-outlined">emoji_events</span>
                <span class="text-sm font-medium">Tournaments</span>
            </a>
            <a href="{% url 'coaching:coach_list' %}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors">
                <span class="material-symbols-outlined">sports_esports</span>
                <span class="text-sm font-medium">Coaching</span>
            </a>
            <a href="{% url 'accounts:profile' user.username %}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors">
                <span class="material-symbols-outlined">person</span>
                <span class="text-sm font-medium">Profile</span>
            </a>
        </nav>
        
        <!-- Bottom Links -->
        <div class="mt-auto flex flex-col gap-2">
            <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors">
                <span class="material-symbols-outlined">settings</span>
                <span class="text-sm font-medium">Settings</span>
            </a>
            <a href="{% url 'account_logout' %}" class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:bg-card-dark transition-colors">
                <span class="material-symbols-outlined">logout</span>
                <span class="text-sm font-medium">Logout</span>
            </a>
        </div>
    </div>
</aside>
```

### Create Header Component

Create `templates/components/header.html`:

```html
<header class="flex items-center justify-between border-b border-card-border-dark px-6 py-3 h-16">
    <div class="flex flex-1 items-center gap-8">
        <!-- Search -->
        <div class="hidden md:flex flex-col min-w-40 max-w-64">
            <div class="flex w-full items-stretch rounded-lg h-10">
                <div class="text-gray-400 flex bg-card-dark items-center justify-center pl-3 rounded-l-lg">
                    <span class="material-symbols-outlined text-lg">search</span>
                </div>
                <input type="text" 
                       class="flex-1 bg-card-dark text-white border-none rounded-r-lg px-4 focus:outline-none focus:ring-2 focus:ring-primary/50" 
                       placeholder="Search...">
            </div>
        </div>
    </div>
    
    <div class="flex items-center gap-4">
        <!-- Mobile Search -->
        <button class="flex md:hidden h-10 w-10 items-center justify-center rounded-lg bg-card-dark text-gray-300">
            <span class="material-symbols-outlined">search</span>
        </button>
        
        <!-- Notifications -->
        <button class="flex h-10 w-10 items-center justify-center rounded-lg bg-card-dark text-gray-300 relative">
            <span class="material-symbols-outlined">notifications</span>
            <span class="absolute top-1 right-1 h-2 w-2 bg-primary rounded-full"></span>
        </button>
        
        <!-- User Menu -->
        <div class="flex items-center gap-3">
            {% if user.avatar %}
            <img src="{{ user.avatar.url }}" alt="{{ user.get_display_name }}" class="h-10 w-10 rounded-full object-cover">
            {% else %}
            <div class="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-white font-bold">
                {{ user.get_display_name|first|upper }}
            </div>
            {% endif %}
            <div class="hidden sm:flex flex-col text-right">
                <h1 class="text-white text-sm font-medium">{{ user.get_display_name }}</h1>
                <p class="text-gray-400 text-xs">Level {{ user.level }}</p>
            </div>
        </div>
    </div>
</header>
```

---

## Phase 2: Login Page (1 hour)

### Update Login Template

Create `templates/account/login.html`:

```html
{% extends 'base_eyt.html' %}
{% load static %}
{% load socialaccount %}

{% block title %}Login - EYTGaming{% endblock %}

{% block body %}
<div class="relative flex min-h-screen w-full flex-col items-center justify-center bg-background-dark p-4">
    <!-- Background Image -->
    <div class="absolute inset-0 z-0 h-full w-full bg-cover bg-center bg-no-repeat opacity-10" 
         style="background-image: url('https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1920');"></div>
    <div class="absolute inset-0 z-10 bg-gradient-to-t from-background-dark via-background-dark/80 to-transparent"></div>
    
    <!-- Login Card -->
    <div class="relative z-20 flex w-full max-w-md flex-col items-center rounded-xl bg-neutral-900/80 p-6 shadow-2xl backdrop-blur-md sm:p-8">
        <!-- Logo -->
        <div class="mb-8 flex flex-col items-center">
            <img src="{% static 'images/EYTLOGO.jpg' %}" alt="EYT Gaming" class="h-20 w-auto rounded-lg mb-4">
            <h1 class="text-white text-3xl font-bold text-center">Welcome Back to EYTGaming</h1>
        </div>
        
        <!-- Login Form -->
        <form method="post" class="w-full space-y-6">
            {% csrf_token %}
            
            <!-- Email/Username -->
            <div class="flex flex-col">
                <label class="text-neutral-300 text-sm font-medium mb-2">Email or Username</label>
                <div class="relative flex w-full items-center">
                    <span class="material-symbols-outlined absolute left-3 text-lg text-neutral-500">person</span>
                    <input type="text" 
                           name="login" 
                           class="w-full rounded-lg text-neutral-200 bg-neutral-900/70 border border-neutral-700 focus:border-primary focus:ring-2 focus:ring-primary/50 h-12 pl-10 pr-4" 
                           placeholder="Enter your email or username" 
                           required>
                </div>
            </div>
            
            <!-- Password -->
            <div class="flex flex-col">
                <label class="text-neutral-300 text-sm font-medium mb-2">Password</label>
                <div class="relative flex w-full items-center">
                    <span class="material-symbols-outlined absolute left-3 text-lg text-neutral-500">lock</span>
                    <input type="password" 
                           name="password" 
                           class="w-full rounded-lg text-neutral-200 bg-neutral-900/70 border border-neutral-700 focus:border-primary focus:ring-2 focus:ring-primary/50 h-12 pl-10 pr-4" 
                           placeholder="Enter your password" 
                           required>
                </div>
                <div class="flex justify-end pt-2">
                    <a href="{% url 'account_reset_password' %}" class="text-primary hover:text-primary/80 text-sm underline">Forgot Password?</a>
                </div>
            </div>
            
            <!-- Submit Button -->
            <button type="submit" class="w-full rounded-lg bg-primary h-12 px-4 text-base font-bold text-white shadow-lg shadow-primary/30 hover:bg-primary/90 transition-all focus:outline-none focus:ring-2 focus:ring-primary/50">
                Login
            </button>
        </form>
        
        <!-- Divider -->
        <div class="flex w-full items-center gap-4 py-6">
            <hr class="w-full border-t border-neutral-700">
            <p class="text-sm font-medium text-neutral-400">OR</p>
            <hr class="w-full border-t border-neutral-700">
        </div>
        
        <!-- Social Login -->
        <div class="w-full space-y-3">
            <a href="{% provider_login_url 'google' %}" class="flex w-full items-center justify-center gap-3 rounded-lg border border-neutral-700 bg-neutral-800/60 h-11 px-4 text-sm font-medium text-neutral-200 hover:bg-neutral-700/60 transition-colors">
                <svg class="h-5 w-5" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                <span>Continue with Google</span>
            </a>
            
            <a href="{% provider_login_url 'discord' %}" class="flex w-full items-center justify-center gap-3 rounded-lg border border-neutral-700 bg-neutral-800/60 h-11 px-4 text-sm font-medium text-neutral-200 hover:bg-neutral-700/60 transition-colors">
                <svg class="h-5 w-5" viewBox="0 0 24 24"><path fill="currentColor" d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/></svg>
                <span>Continue with Discord</span>
            </a>
            
            <a href="{% provider_login_url 'steam' %}" class="flex w-full items-center justify-center gap-3 rounded-lg border border-neutral-700 bg-neutral-800/60 h-11 px-4 text-sm font-medium text-neutral-200 hover:bg-neutral-700/60 transition-colors">
                <svg class="h-5 w-5" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2a10 10 0 0 1 10 10a10 10 0 0 1-10 10C6.47 22 2 17.5 2 12A10 10 0 0 1 12 2m0 2a8 8 0 0 0-8 8c0 .04.01.09.01.13l4.74-1.94c.31-.09.63-.13.96-.13c.7 0 1.38.23 1.94.66l2.98-4.17c.01-.01.01-.02.02-.03A6.89 6.89 0 0 1 18.9 12c0 3.79-3.11 6.89-6.9 6.89s-6.9-3.1-6.9-6.89c0-.04.01-.09.01-.13l4.74 1.94c.31.09.63.13.96.13c.7 0 1.38-.23 1.94-.66l2.98 4.17c.01.01.01.02.02.03A6.89 6.89 0 0 1 5.1 12c0-3.79 3.11-6.89 6.9-6.89z"/></svg>
                <span>Continue with Steam</span>
            </a>
        </div>
        
        <!-- Sign Up Link -->
        <p class="text-neutral-400 text-sm pt-8 text-center">
            Don't have an account? 
            <a href="{% url 'account_signup' %}" class="font-semibold text-primary hover:text-primary/80 underline">Sign Up</a>
        </p>
    </div>
</div>
{% endblock body %}
```

### Update URL Configuration

Update `accounts/urls.py`:

```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/<str:username>/', views.profile_view, name='profile'),
    # Add more as needed
]
```

---

## Testing

```bash
# Run server
python manage.py runserver

# Test URLs:
# http://127.0.0.1:8000/accounts/login/
# http://127.0.0.1:8000/dashboard/
```

---

## Next Steps

1. ✅ Complete base template
2. ✅ Convert login page
3. 🔄 Convert signup page
4. 🔄 Create dashboard
5. 🔄 Convert tournament pages
6. 🔄 Convert coaching pages

---

## Common Issues & Solutions

### Logo Not Showing
```bash
# Verify file exists
dir static\images\EYTLOGO.jpg

# Run collectstatic
python manage.py collectstatic --noinput
```

### Colors Not Matching
- Verify Tailwind config uses `#b91c1c`
- Check browser cache (Ctrl+Shift+R)
- Inspect element to verify CSS

### URLs Not Working
- Check URL names in `urls.py`
- Verify app names match
- Check namespace in templates

---

## Quick Reference

### Brand Colors
```css
Primary: #b91c1c
Background Dark: #121212
Card Dark: #151c2c
Border: #282e39
```

### Common Classes
```html
<!-- Button -->
<button class="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg">

<!-- Card -->
<div class="bg-card-dark border border-card-border-dark rounded-xl p-6">

<!-- Input -->
<input class="bg-neutral-900/70 border border-neutral-700 focus:border-primary rounded-lg">
```

### Template Tags
```django
{% load static %}
{% url 'app:view_name' %}
{% csrf_token %}
{% if user.is_authenticated %}
{% for item in items %}
```

---

**Ready to start? Run the commands in Step 1!**
