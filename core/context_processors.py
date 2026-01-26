"""
Context processors for the core app.
These functions add variables to the template context globally.
"""
from .models import SiteSettings


def site_settings(request):
    """
    Add site settings to the template context.
    This makes site settings available in all templates.
    """
    try:
        settings = SiteSettings.load()
    except Exception:
        # Return empty dict if settings don't exist yet (e.g., during migrations)
        settings = None
    
    return {
        'site_settings': settings,
    }
