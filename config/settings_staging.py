"""
Staging settings for EYT Gaming.

Inherits all production settings and overrides for staging:
- DEV_MODE=True (allows DEBUG checks to pass without DEBUG=True)
- Test payment keys
- Debug toolbar enabled
- Lower rate limits
- Separate database
"""
from .settings import *  # noqa: F403

import os

# ── Mode ────────────────────────────────────────────────────────────────────
DEBUG = False
DEV_MODE = True

# ── Hosts ────────────────────────────────────────────────────────────────────
ALLOWED_HOSTS = os.environ.get(
    'STAGING_ALLOWED_HOSTS',
    'staging.eytgaming.com,localhost,127.0.0.1'
).split(',')

# ── Database ─────────────────────────────────────────────────────────────────
# Use a separate staging database (default to SQLite for quick setup)
import dj_database_url  # noqa: E402

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///staging_db.sqlite3',
        conn_max_age=600,
    )
}

# ── Email ────────────────────────────────────────────────────────────────────
# Use console backend for staging to avoid sending real emails
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Payments (test keys) ────────────────────────────────────────────────────
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_TEST_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_TEST_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_TEST_WEBHOOK_SECRET', '')

PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_TEST_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_TEST_SECRET_KEY', '')
PAYSTACK_WEBHOOK_SECRET = os.environ.get('PAYSTACK_TEST_WEBHOOK_SECRET', '')

# ── Rate Limiting ────────────────────────────────────────────────────────────
# Disable rate limiting in staging for easier testing
RATELIMIT_ENABLE = False
STORE_RATE_LIMIT_ENABLED = False

# ── Debug Toolbar ────────────────────────────────────────────────────────────
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# ── Cache ────────────────────────────────────────────────────────────────────
# Use database cache in staging (simpler, no Redis dependency for staging)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'staging_cache_table',
        'TIMEOUT': 300,
    }
}

# ── Site URL ─────────────────────────────────────────────────────────────────
SITE_URL = os.environ.get(
    'SITE_URL',
    'https://staging.eytgaming.com'
)

# ── Celery ───────────────────────────────────────────────────────────────────
# Disable Celery in staging unless explicitly configured
if not os.environ.get('CELERY_BROKER_URL'):
    CELERY_TASK_ALWAYS_EAGER = True  # noqa: F405

# ── Security (relaxed for staging) ──────────────────────────────────────────
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# ── Logging ──────────────────────────────────────────────────────────────────
import logging  # noqa: E402
logging.getLogger().setLevel(logging.DEBUG)
