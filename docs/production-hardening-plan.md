# Production Hardening & Standardization Plan

## Overview

Refine EYT Gaming from a feature-rich codebase into a production-grade, resilient, industry-standard esports platform. Six phases covering production readiness, ecosystem expansion, real-time infrastructure, code quality, security compliance, and UX polish.

---

## Phase 1: Production Blockers (P0)

**Goal:** Fix the critical gaps that prevent reliable deployment.

### 1.1 — Dockerfile

The `docker-compose.yml` references `build: .` but no Dockerfile exists. Create a multi-stage build:

```dockerfile
# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

Files to create:
- `Dockerfile` — multi-stage as above
- `docker-compose.prod.yml` — overrides for production (no volume mounts, restart: always)
- `.dockerignore` — exclude `node_modules`, `__pycache__`, `.git`, `db.sqlite3`, `logs`

### 1.2 — Production DEBUG Hardening

Current state: `DEBUG = config('DEBUG', default=True, cast=bool)` — defaults to `True`.

Actions:
- Add `config/checks.py` with Django system check:

```python
from django.core.checks import Warning, register
from django.conf import settings

@register()
def debug_check(app_configs, **kwargs):
    if settings.DEBUG and not settings.DEV_MODE:
        return [Warning(
            'DEBUG is enabled in a non-development environment',
            hint='Set DEBUG=False in production',
            id='config.W001',
        )]
    return []
```

- Add `DEV_MODE` setting — `bool(config('DEV_MODE', default=settings.DEBUG))`
- Startup guard in `manage.py` and `wsgi.py`:

```python
if settings.DEBUG and not settings.DEV_MODE:
    raise ImproperlyConfigured("Refusing to start: DEBUG=True in production")
```

- Add startup log: `logger.warning("Running with DEBUG=True")` when DEBUG is on

### 1.3 — Database Backup Automation

Current state: No backup system.

Actions:
- Create `core/management/commands/backup_db.py`:

  | Option | Database | Output |
  |---|---|---|
  | `--database` | PostgreSQL | `pg_dump` → `.sql.gz` |
  | `--database` | SQLite | `.dump` → `.sqlite3.bak` |
  | `--s3` | Any | Upload to S3 |
  | `--local` | Any | Save to `backups/` dir |

- Add Celery beat task (or cron management command) for daily backup
- Retention: keep 7 daily, 4 weekly, 3 monthly backups
- S3 bucket: `eytgaming-backups/` with lifecycle policy

### 1.4 — Staging Environment

Files to create:
- `config/settings_staging.py`

```python
from .settings import *
import os

DEBUG = False
DEV_MODE = True
ALLOWED_HOSTS = ['staging.eytgaming.com']

# Test payment keys
STRIPE_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_TEST_SECRET_KEY')

# Debug toolbar for staging debugging
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Lower rate limits for staging testing
RATELIMIT_ENABLE = False

# Separate database
DATABASE_URL = os.environ.get('STAGING_DATABASE_URL')
```

---

## Phase 2: Verified Entity Ecosystem (P1)

**Goal:** Replace the stub `celebrity` app with a unified `verified_entities` app covering individuals, organizations, brands, and media — creating an inclusive ecosystem.

### 2.1 — Architecture

```
verified_entities/
├── models.py          # All entity models
├── views.py           # Entity CRUD, relationships, content management
├── urls.py            # /entities/ namespace
├── admin.py           # Admin configuration for all entity types
├── signals.py         # Tier progression, verification expiry
├── tasks.py           # Celery tasks: verification reminders, tier recalculation
├── api/               # DRF serializers + viewsets
│   ├── serializers.py
│   └── viewsets.py
├── templates/
│   └── verified_entities/
│       ├── profile.html
│       ├── dashboard.html
│       ├── verification.html
│       ├── sponsorship.html
│       └── content_list.html
└── tests/
    ├── test_models.py
    ├── test_views.py
    └── test_api.py
```

### 2.2 — Models

```python
class EntityType(models.Model):
    """Enum-like: individual, organization, brand, media"""
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    requires_registration_number = models.BooleanField(default=False)
    max_tier = models.IntegerField(default=5)

class EntityProfile(models.Model):
    """Unified profile for all verified entities"""
    ENTITY_TYPES = [
        ('individual', 'Individual'),
        ('organization', 'Organization'),
        ('brand', 'Brand'),
        ('media', 'Media'),
    ]
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entities')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    bio = models.TextField(blank=True)
    logo = models.ImageField(upload_to='entities/logos/', blank=True)
    banner = models.ImageField(upload_to='entities/banners/', blank=True)
    website = models.URLField(blank=True)
    social_links = models.JSONField(default=dict)  # {twitch, twitter, youtube, discord}
    is_verified = models.BooleanField(default=False)
    current_tier = models.ForeignKey('EntityTier', on_delete=models.SET_NULL, null=True)
    follower_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class EntityTier(models.Model):
    """Tier definition per entity type"""
    entity_type = models.ForeignKey(EntityType, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # Bronze, Silver, Gold, Platinum, Diamond
    level = models.IntegerField()  # 1-5
    min_followers = models.IntegerField(default=0)
    revenue_share_percent = models.DecimalField(max_digits=5, decimal_places=2)
    can_post_content = models.BooleanField(default=True)
    can_host_events = models.BooleanField(default=False)
    can_sponsor = models.BooleanField(default=False)
    max_sponsored_entities = models.IntegerField(default=0)
    badge_color = models.CharField(max_length=7, default='#CD7F32')  # hex color

class EntityVerification(models.Model):
    """Verification application and review"""
    entity = models.ForeignKey(EntityProfile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], default='pending')
    documents = models.JSONField(default=dict)
    # Individuals: govt ID, selfie
    # Organizations: registration cert, tax ID
    # Brands: trademark reg, business license
    # Media: press credentials, portfolio
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True)

class EntityRelationship(models.Model):
    """Relationships between entities"""
    RELATION_TYPES = [
        ('member_of', 'Member of'),
        ('sponsored_by', 'Sponsored by'),
        ('partner', 'Partner'),
        ('subsidiary', 'Subsidiary'),
        ('affiliated', 'Affiliated'),
    ]
    source = models.ForeignKey(EntityProfile, on_delete=models.CASCADE, related_name='outgoing_relationships')
    target = models.ForeignKey(EntityProfile, on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(max_length=20, choices=RELATION_TYPES)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ], default='pending')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EntityContent(models.Model):
    """Tier-gated exclusive content"""
    entity = models.ForeignKey(EntityProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    media = models.JSONField(default=list)  # [ {type: image|video, url: ...} ]
    min_tier = models.IntegerField(default=1)  # minimum tier level to view
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class EntityRevenue(models.Model):
    """Revenue tracking for entities"""
    entity = models.ForeignKey(EntityProfile, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=[
        ('sponsorship', 'Sponsorship'),
        ('marketplace', 'Marketplace Fee'),
        ('content', 'Content Revenue'),
        ('tip', 'Tip/Donation'),
    ])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='NGN')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ], default='pending')
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2.3 — Migration Path

1. Rename `celebrity/` → `verified_entities/` in code (or create new app)
2. Create data migration:
   - Existing `User.is_verified_personality=True` → `EntityProfile(entity_type='individual')`
   - Copy existing celebrity-specific fields
3. Update all `{% url 'celebrity:...' %}` references to `{% url 'verified_entities:...' %}`
4. Update `dashboard_base.html` and `celebrity_base.html` sidebar links
5. Keep old `celebrity:home` as a redirect for backward compat

### 2.4 — Template Updates

- `templates/verified_entities/` — adapt from existing `templates/celebrity/` templates
- Entity-agnostic profile page: renders differently based on `entity_type`
- Dashboard for entity owners: manage relationships, view revenue, post content
- Public directory: browse entities by type, tier, game

---

## Phase 3: Real-Time & Esports Core (P1)

**Goal:** Low-latency live updates (match scores, chat, notifications) with graceful degradation when Redis is unavailable.

### 3.1 — Celery/Redis Redundancy (Cross-Cutting)

**Problem:** If Redis goes down mid-session, Celery tasks fail silently, Channels stops working, and caching breaks.

**Solution — Layered fallback:**

| Layer | Primary | Fallback 1 | Fallback 2 |
|---|---|---|---|
| **Async tasks** | Celery + Redis broker | `CELERY_TASK_ALWAYS_EAGER=True` → sync execution | N/A |
| **Beat schedule** | Celery Beat + Redis | Cron running management commands | Manual trigger via admin |
| **Caching** | Redis cache (django-redis) | Database cache (fallback already exists) | LocMem (single process only) |
| **WebSockets** | Channels + Redis channel layer | SSE (Server-Sent Events) — no Redis needed | HTTP polling (5-min existing) |

**Implementation — Task wrapper (`core/utils/task_runner.py`):**

```python
import logging
from celery import Task
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

class ResilientTask:
    """
    Wrapper that catches broker failures and falls back to synchronous execution.
    Usage: ResilientTask.delay(task_func, arg1, arg2)
    """
    @staticmethod
    def delay(task_func, *args, **kwargs):
        if not settings.CELERY_BROKER_URL:
            # No broker configured — run synchronously
            return task_func(*args, **kwargs)

        try:
            return task_func.delay(*args, **kwargs)
        except (ConnectionError, ConnectionRefusedError, OSError) as e:
            logger.warning(f"Broker unreachable, running task synchronously: {e}")
            return task_func(*args, **kwargs)

    @staticmethod
    def is_broker_available():
        """Health check — import within function to avoid circular imports"""
        if not settings.CELERY_BROKER_URL:
            return False
        try:
            from redis import Redis
            r = Redis.from_url(settings.CELERY_BROKER_URL)
            r.ping()
            return True
        except Exception:
            return False
```

**Implementation — Channels layer health check:**

```python
# In consumers.py or middleware
class RedisHealthCheckMixin:
    """Mixin for consumers that degrades gracefully when Redis is down."""

    async def connect(self):
        try:
            self.channel_layer = await self.get_channel_layer()
            await self.channel_layer.check_available()  # redis ping
            await self.accept()
        except Exception:
            # Redis down — send 503 Service Unavailable
            await self.close(code=3501)  # custom code for "channel layer unavailable"
            # Client-side JS catches this and falls back to SSE or polling

    async def get_channel_layer(self):
        from channels.layers import get_channel_layer
        return get_channel_layer()
```

**Client-side fallback (JS):**

```javascript
function connectWebSocket(url) {
    const ws = new WebSocket(url);
    ws.onclose = (event) => {
        if (event.code === 3501) {
            // Channel layer unavailable — fall back to HTTP polling
            console.warn('WebSocket unavailable (code 3501), falling back to polling');
            startPollingFallback();
        }
    };
}

function startPollingFallback() {
    // Use existing 30-second polling for match updates
    setInterval(() => {
        fetch('/api/v1/matches/live-updates/')
            .then(r => r.json())
            .then(data => updateMatchUI(data));
    }, 30000);
}
```

### 3.2 — Django Channels Setup

New dependencies:
- `channels~=4.2` — WebSocket framework
- `channels_redis~=4.2` — Redis channel layer
- `daphne~=4.1` — ASGI server (replaces gunicorn for WS endpoints)

**`config/asgi.py`:**

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from config import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
```

**Channel layer configuration in `settings.py`:**

```python
# Channels configuration
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL', default='redis://localhost:6379/0')],
        },
    },
}

# Fallback channel layer for development/Redis-down scenarios
if config('REDIS_URL', default=None) is None:
    CHANNEL_LAYERS['default'] = {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
```

### 3.3 — Real-Time Features

| Feature | WebSocket Channel | Polling Fallback |
|---|---|---|
| **Match live updates** | `ws://.../ws/match/{id}/` — round scores, timer, winner | `GET /api/v1/matches/{id}/live/` every 30s |
| **Tournament check-in** | `ws://.../ws/tournament/{id}/checkin/` — countdown, participant count | `GET /api/v1/tournaments/{id}/checkin/status/` every 15s |
| **Chat** | `ws://.../ws/chat/{conversation_id}/` — new messages, typing indicator | `GET /api/v1/chat/{id}/messages/?after={timestamp}` every 10s |
| **Notifications** | `ws://.../ws/notifications/` — per-user notification stream | `GET /notifications/unread-count/` every 5min (existing) |

### 3.4 — Match Replay / VOD System

**Model:**

```python
class MatchRecording(models.Model):
    match = models.ForeignKey('tournaments.Match', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    platform = models.CharField(max_length=20, choices=[
        ('upload', 'Direct Upload'),
        ('twitch', 'Twitch'),
        ('youtube', 'YouTube'),
    ])
    video_file = models.FileField(upload_to='vod/', blank=True)  # for direct upload
    external_url = models.URLField(blank=True)  # for Twitch/YouTube
    duration = models.DurationField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to='vod/thumbnails/', blank=True)
    is_processed = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Upload pipeline:**
1. User uploads video → Django view validates size/format
2. Celery task (ResilientTask) processes: transcode to MP4 H.264 → generate thumbnail → mark processed
3. Embeddable player with scrub bar, volume, fullscreen
4. VOD library: filter by game, tournament, date, player

### 3.5 — Team Recruitment / LFG System

**Models:**

```python
class PlayerRecruitmentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    game = models.ForeignKey('core.Game', on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # e.g., "DPS", "Support", "Entry Fragger"
    skill_level = models.IntegerField()  # 1-10
    availability = models.CharField(max_length=100)  # "Weekends", "Daily 6-10pm"
    is_looking = models.BooleanField(default=True)
    looking_for = models.CharField(max_length=200, blank=True)  # "Need a team for competitive"

class TeamListing(models.Model):
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE)
    game = models.ForeignKey('core.Game', on_delete=models.CASCADE)
    needed_roles = models.JSONField(default=list)
    requirements = models.TextField(blank=True)
    tryout_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Matchmaking:** Django ORM query that matches `PlayerRecruitmentProfile` with `TeamListing` by game + role + compatibility.

### 3.6 — Streaming Integration

- Twitch API: store `access_token`, `refresh_token` per user; poll `GET /helix/streams?user_id={id}` every 60s
- YouTube Live API: same pattern with `youtube.googleapis.com`
- Display: live indicator on profile, "LIVE NOW" section on homepage and tournament detail pages

---

## Phase 4: Code Quality (P2)

**Goal:** Professional codebase organization without breaking PythonAnywhere free tier compatibility.

### 4.1 — JS Organization (django-compressor, No Bundler)

PythonAnywhere free has **no Node.js runtime** — cannot run Vite/Webpack/esbuild. Solution: ES modules + `django-compressor`.

**Actions:**

1. Install `django-compressor`:
   ```
   pip install django-compressor
   ```

2. Organize JS into ES modules under `static/js/modules/`:

   ```
   static/js/
   ├── main.js                 # Entry point — imports modules
   ├── modules/
   │   ├── chat.js
   │   ├── bracket.js
   │   ├── checkout.js
   │   ├── notifications.js
   │   ├── tournament-form.js
   │   ├── venue-map.js
   │   ├── player-directory.js
   │   └── onboarding.js
   ├── vendor/                 # Third-party libs, pinned versions
   │   ├── alpine.min.js
   │   ├── htmx.min.js
   │   └── chart.min.js
   └── legacy/                 # Files not yet converted to modules
   ```

3. Configure compressor in `settings.py`:

   ```python
   INSTALLED_APPS += ['compressor']
   STATICFILES_FINDERS += ['compressor.finders.CompressorFinder']
   COMPRESS_ENABLED = not DEBUG
   COMPRESS_OUTPUT_DIR = 'compressed'
   ```

4. In templates, replace individual script tags:

   ```django
   {% load compress %}
   {% compress js %}
   <script src="{% static 'js/modules/chat.js' %}"></script>
   <script src="{% static 'js/modules/bracket.js' %}"></script>
   {% endcompress %}
   ```

5. In production, compressor concatenates and minifies automatically. No build step needed.

### 4.2 — CSS Consolidation

**Current state:** 30+ CSS files, many with dead rules and overlapping selectors.

**Target structure (8 files):**

| File | Contents | Lines (est.) |
|---|---|---|
| `core.css` | Reset, typography, CSS variables, brand colors | 200 |
| `layout.css` | Grid system, sidebar, header, footer, containers | 300 |
| `components.css` | Cards, buttons, forms, modals, badges, alerts | 500 |
| `dashboard.css` | Sidebar nav, dashboard-specific widgets | 400 |
| `tournaments.css` | Bracket view, match cards, check-in UI | 600 |
| `venues.css` | Venue list, detail, map, booking form | 400 |
| `chat.css` | Message bubbles, conversation list, input | 300 |
| `mobile.css` | All responsive overrides, bottom nav, touch targets | 500 |

**Process:**
1. Run an audit: for each CSS file, note which templates actually use each rule
2. Remove dead code (rules not referenced by any template)
3. Consolidate into the target files
4. Update all `<link>` references in templates

### 4.3 — Dark Mode Rework

**Current approach (BAD):**
```css
.bg-white { background-color: #111318 !important; }
```

**Target approach (GOOD):**
```html
<html class="dark">
```
```css
.bg-white { background-color: #ffffff; }
.dark .bg-white { background-color: #111318; }
```

Using Tailwind's built-in `dark:` variant:
```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
```

**Implementation:**
1. Add `dark` class to `<html>` based on user preference or system setting
2. Add a `dark-mode-toggle.js` that persists preference to localStorage
3. Remove all forced `!important` overrides from the `<style>` block in `dashboard_base.html`
4. Replace each override with the proper Tailwind `dark:` equivalent

### 4.4 — API Versioning

Current: all endpoints under `/api/`
Target: `/api/v1/` with backward compat headers

```python
# config/urls.py
from api.v1.urls import urlpatterns as v1_urlpatterns

urlpatterns = [
    path('api/v1/', include(v1_urlpatterns)),
    path('api/', include(v1_urlpatterns)),  # backward compat
]
```

Add deprecation middleware:
```python
class APIVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/') and not request.path.startswith('/api/v1/'):
            response['Deprecation'] = 'true'
            response['Sunset'] = 'Sat, 31 Dec 2026 23:59:59 GMT'
            response['Link'] = '</api/v1/>; rel="successor-version"'
        return response
```

### 4.5 — Test Coverage to 80%

Current threshold: 60%

Priority targets for new tests:

| App | Current coverage (est.) | Target | Key gaps |
|---|---|---|---|
| `verified_entities` | 0% (new) | 85% | New code — write tests alongside |
| `chat` | ~30% | 80% | Conversation CRUD, permissions, real-time |
| `store` | ~60% | 85% | Cart edge cases, checkout flow, webhooks |
| `sponsorships` | ~40% | 80% | Deal lifecycle, payment integration |
| `tournaments` | ~70% | 90% | Bracket edge cases, check-in race conditions |

Add `pytest-cov` configuration:
```ini
# pyproject.toml
[tool.coverage.run]
source = ["core", "accounts", "tournaments", "teams", "chat", "store", "verified_entities", "sponsorships"]
omit = ["*/tests/*", "*/migrations/*", "*/management/*"]
```

### 4.6 — Selective TypeScript (Optional)

Convert only the 5 highest-traffic JS files:
1. `static/js/chat.js` → `static/js/chat.ts` — message handling, conversation list
2. `static/js/bracket.js` → `static/js/bracket.ts` — bracket rendering, match state
3. `static/js/checkout.js` → `static/js/checkout.ts` — cart, payment form
4. `static/js/notifications.js` → `static/js/notifications.ts` — polling, badge update
5. `static/js/tournament-form.js` → `static/js/tournament-form.ts` — datepicker, dynamic fields

Add JSDoc annotations to all non-converted files:
```javascript
/** @param {string} userId @param {number} count @returns {boolean} */
```

---

## Phase 5: Security & Compliance (P2)

**Goal:** Meet industry security standards and legal compliance requirements.

### 5.1 — Idle Session Timeout

```python
# security/middleware.py
class IdleSessionTimeoutMiddleware:
    IDLE_TIMEOUT = 1800  # 30 minutes
    WARNING_AT = 300      # warn 5 minutes before

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith('/api/'):
            last_activity = request.session.get('last_activity')
            now = time.time()

            if last_activity and (now - last_activity) > self.IDLE_TIMEOUT:
                from django.contrib.auth import logout
                logout(request)
                return redirect('/accounts/login/?timeout=1')

            if last_activity and (now - last_activity) > (self.IDLE_TIMEOUT - self.WARNING_AT):
                # Add header for JS to show warning dialog
                response = self.get_response(request)
                response['X-Session-Timeout-Warning'] = 'true'
                return response

            request.session['last_activity'] = now

        return self.get_response(request)
```

### 5.2 — Content Moderation

**Report model:**

```python
class ContentReport(models.Model):
    CONTENT_TYPES = [
        ('chat_message', 'Chat Message'),
        ('venue_review', 'Venue Review'),
        ('product_review', 'Product Review'),
        ('team_announcement', 'Team Announcement'),
        ('entity_content', 'Entity Post'),
        ('user_profile', 'User Profile'),
    ]
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('impersonation', 'Impersonation'),
        ('other', 'Other'),
    ]
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES)
    object_id = models.PositiveIntegerField()
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('dismissed', 'Dismissed'),
        ('actioned', 'Action Taken'),
    ], default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='moderation_actions')
    action_taken = models.CharField(max_length=50, blank=True)  # "Content hidden", "User warned", "User banned"
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True)
```

**Admin workflow:**
1. Report submitted → email alert to moderators
2. Moderation dashboard: queue of pending reports with context
3. Actions: dismiss, hide content, warn user, temp ban, permanent ban
4. Appeals process: user can appeal within 7 days

### 5.3 — GDPR Compliance

**Account deletion workflow:**

```
User requests deletion
    → 7-day cooldown period (can cancel)
    → Anonymize profile data
        ─ Replace name with "Deleted User"
        ─ Replace email with hash
        ─ Remove avatar, bio, social links
    → Hard-delete non-essential data
        ─ Chat messages older than 90 days
        ─ Notification history
        ─ Session data
    → Retain legally required data
        ─ Payment records (7 years)
        ─ Tournament results (anonymized)
    → Log deletion event to audit trail
```

**Privacy notice acceptance:**
- Track which version of privacy policy user accepted
- Show banner when policy is updated
- Block access to data-gathering features until accepted

### 5.4 — Security Hardening

- `.well-known/security.txt` — vulnerability disclosure policy:

  ```
  Contact: https://eytgaming.com/security-report
  Encryption: https://keybase.io/eytgaming/pgp-key.asc
  Policy: https://eytgaming.com/.well-known/security-policy.txt
  ```

- `Permissions-Policy` header:

  ```python
  response['Permissions-Policy'] = (
      'camera=(), microphone=(), geolocation=(), '
      'interest-cohort=(), payment=(self)'
  )
  ```

- CSP report-uri:

  ```python
  "report-uri /api/v1/security/csp-violation/"
  ```

- Rate-limit auth endpoints:

  ```python
  # In each auth view
  @ratelimit(key='ip', rate='5/m', method='POST')
  def login_view(request):
      ...
  ```

---

## Phase 6: Performance & UX (P2-P3)

### 6.1 — Image Optimization Pipeline

Add `django-imagekit`:

```python
INSTALLED_APPS += ['imagekit']
```

```python
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill, ResizeToFit

class EntityProfile(models.Model):
    logo = ProcessedImageField(
        upload_to='entities/logos/',
        processors=[ResizeToFit(300, 300)],
        format='WEBP',
        options={'quality': 85},
        blank=True,
    )
    banner = ProcessedImageField(
        upload_to='entities/banners/',
        processors=[ResizeToFit(1200, 400)],
        format='WEBP',
        options={'quality': 80},
        blank=True,
    )
```

Apply same processing to:
- Product images (store)
- Venue images
- User avatars
- Tournament banners
- VOD thumbnails

### 6.2 — Progressive Web App

**Upgrade `sw.js`:**
- Pre-cache: CSS, core JS, logo, fonts, offline page
- Runtime cache: API responses (stale-while-revalidate)
- Background sync: queue failed chat messages, form submissions

**`manifest.json`:**
```json
{
  "name": "EYT Gaming",
  "short_name": "EYT",
  "start_url": "/dashboard/",
  "display": "standalone",
  "background_color": "#0A0A0A",
  "theme_color": "#DC2626",
  "icons": [
    { "src": "/static/images/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/images/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 6.3 — Accessibility Audit

**Automated checks:**
- Run axe-core in CI: `npx axe-core --exit --url https://staging.eytgaming.com/dashboard/`
- Add to pre-commit: `husky` hook that lints for a11y issues in templates

**Manual checklist:**
- [ ] All form inputs have associated labels
- [ ] All images have alt text
- [ ] All interactive elements are keyboard-focusable (tabindex)
- [ ] Color contrast meets WCAG AA (4.5:1 for normal text)
- [ ] Focus indicators are visible (not `outline: none`)
- [ ] ARIA landmarks on every page (`role="main"`, `role="navigation"`, etc.)
- [ ] Error messages are associated with inputs via `aria-describedby`
- [ ] Live regions for dynamic content (`aria-live="polite"`)

---

## Celery/Redis Redundancy — Summary

This strategy applies across all phases that depend on async processing.

### Task Execution Fallback Chain

```
                    ┌─────────────────────────┐
                    │   task.delay() called    │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  Is CELERY_BROKER_URL   │
                    │      configured?        │
                    └──────┬─────────┬────────┘
                           │ No      │ Yes
                    ┌──────▼──┐   ┌──▼────────────┐
                    │ Execute  │   │ Try .delay()  │
                    │ sync     │   └──┬────────────┘
                    │ (apply)  │      │
                    └─────────┘   ┌──▼────────────┐
                                 │ Exception?     │
                                 └──┬─────────┬───┘
                                    │ No      │ Yes
                              ┌─────▼──┐  ┌──▼──────────┐
                              │ Return  │  │ Fallback to │
                              │ task ID │  │ .apply()    │
                              └─────────┘  │ sync        │
                                           └─────────────┘
```

### Detection & Recovery

```python
# core/checks/redis_health.py
from django.core.cache import cache
from django.conf import settings

def is_redis_available():
    """Ping Redis. Returns True if available, False otherwise."""
    if not settings.REDIS_URL:
        return False
    try:
        cache.set('__health_check__', 1, 5)
        return True
    except Exception:
        return False
```

Recovery flow:
- Every 5 minutes, check if Redis is back
- When restored, log event, send admin notification, switch back to async mode
- Until restored, serve degraded experience (polling instead of WS, sync tasks)

---

## Dependencies

| Package | Version | Phase | Purpose | PA Free Compatible |
|---|---|---|---|---|
| `channels` | ~4.2 | P3 | WebSocket framework | No (needs Redis) |
| `channels_redis` | ~4.2 | P3 | Redis channel layer | No (needs Redis) |
| `daphne` | ~4.1 | P3 | ASGI server | No (needs Redis) |
| `django-imagekit` | latest | P6 | Image processing pipeline | Yes |
| `django-compressor` | latest | P4 | JS/CSS minification | **Yes** |
| `django-sesame` | latest | P5 | Magic link auth (optional) | Yes |

PA Free compatible packages work without Redis, Node.js, or any external service.

---

## Effort & Timeline

| Phase | Days | Parallelizable | Dependencies |
|---|---|---|---|
| **P1: Production Blockers** | 2-3 | No | None |
| **P2: Verified Entities** | 7-10 | No | P1 (for secure deployment) |
| **P3: Real-Time & Esports** | 8-12 | No | P1 (infrastructure) |
| **P4: Code Quality** | 5-7 | **Yes** (with P2, P3) | None |
| **P5: Security & Compliance** | 3-5 | **Yes** (with P2, P3) | P1 |
| **P6: Performance & UX** | 3-5 | **Yes** (with P2, P3) | P4 (image pipeline) |
| **Total** | **28-42** | | |

Parallel execution: P4 + P5 can run alongside P2/P3. P6 can start once P4's image pipeline is in place.
