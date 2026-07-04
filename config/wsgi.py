"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import logging

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

logger = logging.getLogger(__name__)

# Startup check: run Django system checks on boot
try:
    call_command('check', deploy=True, verbosity=0)
except Exception as exc:
    logger.warning("Startup check failed: %s", exc)

if settings.DEBUG and not settings.DEV_MODE:
    logger.warning(
        "Running with DEBUG=True in non-dev mode. "
        "Set DEBUG=False in production or DEV_MODE=True for staging."
    )

application = get_wsgi_application()
