"""
Context processors for the core app.
These functions add variables to the template context globally.
"""
from django.conf import settings as django_settings
from .models import SiteSettings


def site_settings(request):
    """
    Add site settings and global config to the template context.
    This makes site settings available in all templates.
    """
    try:
        settings = SiteSettings.load()
    except Exception:
        settings = None
    
    return {
        'site_settings': settings,
        'vapid_public_key': django_settings.VAPID_PUBLIC_KEY,
    }
