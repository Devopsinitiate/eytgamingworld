"""
Django system checks for production readiness.
"""
from django.core.checks import Warning, Critical, register
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@register()
def debug_check(app_configs, **kwargs):
    """Warn if DEBUG is enabled outside of dev mode."""
    if settings.DEBUG and not getattr(settings, 'DEV_MODE', False):
        return [Warning(
            'DEBUG is enabled in a non-development environment',
            hint='Set DEBUG=False in your .env file for production. '
                 'Set DEV_MODE=True if this is a development or staging instance.',
            id='config.W001',
        )]
    return []


@register()
def secret_key_check(app_configs, **kwargs):
    """Warn if SECRET_KEY is the default or too short."""
    sk = settings.SECRET_KEY
    if sk and len(sk) < 32:
        return [Critical(
            'SECRET_KEY is too short (minimum 32 characters)',
            hint='Generate a new secret key with: '
                 'python -c "from django.core.management.utils import get_random_secret_key; '
                 'print(get_random_secret_key())"',
            id='config.C001',
        )]
    return []
