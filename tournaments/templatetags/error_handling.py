"""
Template tags for error handling and fallback content
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import logging

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def safe_display(value, fallback="Information unavailable"):
    """
    Safely display a value with fallback content
    
    Usage: {{ tournament.name|safe_display:"Tournament name unavailable" }}
    """
    try:
        if value is not None and str(value).strip():
            return escape(str(value))
        return escape(str(fallback))
    except Exception as e:
        logger.error(f"Template display error: {e}")
        return escape(str(fallback))

@register.filter
def safe_date(value, format_string="%b %d, %Y %I:%M %p", fallback="Date TBD"):
    """
    Safely format a date with fallback content
    
    Usage: {{ tournament.start_datetime|safe_date:"%b %d, %Y"|default:"Date TBD" }}
    """
    try:
        if value:
            return value.strftime(format_string)
        return fallback
    except Exception as e:
        logger.error(f"Date formatting error: {e}")
        return fallback

@register.filter
def safe_currency(value, currency_symbol="$", fallback="Free"):
    """
    Safely format currency with fallback content
    
    Usage: {{ tournament.registration_fee|safe_currency:"$"|default:"Free" }}
    """
    try:
        if value is not None and value > 0:
            return f"{currency_symbol}{value:,.0f}"
        return fallback
    except Exception as e:
        logger.error(f"Currency formatting error: {e}")
        return fallback

@register.filter
def safe_count(queryset_or_number, fallback="0"):
    """
    Safely get count from queryset or number with fallback
    
    Usage: {{ tournament.registrations.all|safe_count:"0" }}
    """
    try:
        if hasattr(queryset_or_number, 'count'):
            return str(queryset_or_number.count())
        elif isinstance(queryset_or_number, (int, float)):
            return str(int(queryset_or_number))
        elif queryset_or_number is not None:
            return str(len(queryset_or_number))
        return fallback
    except Exception as e:
        logger.error(f"Count error: {e}")
        return fallback

@register.inclusion_tag('tournaments/partials/error_fallback.html')
def error_fallback(error_type="general", title="Content Unavailable", message="", show_retry=True):
    """
    Render error fallback content
    
    Usage: {% error_fallback "tournament-info" "Tournament Unavailable" "Please refresh the page" %}
    """
    return {
        'error_type': error_type,
        'title': title,
        'message': message or "This content is temporarily unavailable. Please try refreshing the page.",
        'show_retry': show_retry
    }

@register.simple_tag
def safe_icon(icon_name, fallback_icon="help", css_classes="material-symbols-outlined"):
    """
    Safely render material icon with fallback
    
    Usage: {% safe_icon "emoji_events" "trophy" "material-symbols-outlined text-primary" %}
    """
    try:
        if icon_name and icon_name.strip():
            return mark_safe(f'<span class="{css_classes}">{escape(icon_name)}</span>')
        return mark_safe(f'<span class="{css_classes}">{escape(fallback_icon)}</span>')
    except Exception as e:
        logger.error(f"Icon rendering error: {e}")
        return mark_safe(f'<span class="{css_classes}">{escape(fallback_icon)}</span>')

@register.inclusion_tag('tournaments/partials/safe_tournament_info.html')
def safe_tournament_info(tournament, show_registration_button=True):
    """
    Safely render tournament information with comprehensive error handling
    
    Usage: {% safe_tournament_info tournament True %}
    """
    try:
        # Calculate statistics safely
        registered_count = 0
        try:
            registered_count = tournament.registrations.filter(status='confirmed').count()
        except Exception:
            pass
        
        # Format dates safely
        start_date = "Date TBD"
        registration_end = "Date TBD"
        try:
            if tournament.start_datetime:
                start_date = tournament.start_datetime.strftime('%b %d, %Y %I:%M %p')
        except Exception:
            pass
        
        try:
            if tournament.registration_end:
                registration_end = tournament.registration_end.strftime('%b %d, %Y %I:%M %p')
        except Exception:
            pass
        
        return {
            'tournament': tournament,
            'tournament_name': getattr(tournament, 'name', 'Tournament Name Unavailable'),
            'game_name': getattr(getattr(tournament, 'game', None), 'name', 'Game Information Unavailable'),
            'start_date': start_date,
            'registration_end': registration_end,
            'registered_count': registered_count,
            'max_participants': getattr(tournament, 'max_participants', 0),
            'registration_fee': getattr(tournament, 'registration_fee', 0),
            'prize_pool': getattr(tournament, 'prize_pool', 0),
            'show_registration_button': show_registration_button,
            'has_error': False
        }
    except Exception as e:
        logger.error(f"Tournament info rendering error: {e}")
        return {
            'tournament': None,
            'has_error': True,
            'error_message': "Tournament information is currently unavailable."
        }

@register.simple_tag(takes_context=True)
def render_with_fallback(context, template_name, fallback_template=None, **kwargs):
    """
    Render template with fallback on error
    
    Usage: {% render_with_fallback "tournaments/sidebar.html" "tournaments/sidebar_fallback.html" tournament=tournament %}
    """
    from django.template.loader import render_to_string
    
    try:
        # Merge context with kwargs
        render_context = context.flatten()
        render_context.update(kwargs)
        
        return mark_safe(render_to_string(template_name, render_context))
    except Exception as e:
        logger.error(f"Template rendering error for {template_name}: {e}")
        
        if fallback_template:
            try:
                render_context = context.flatten()
                render_context.update(kwargs)
                render_context['original_error'] = str(e)
                return mark_safe(render_to_string(fallback_template, render_context))
            except Exception as fallback_error:
                logger.error(f"Fallback template error for {fallback_template}: {fallback_error}")
        
        # Ultimate fallback
        return mark_safe(f'''
            <div class="error-fallback bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div class="flex items-center mb-2">
                    <span class="material-symbols-outlined text-yellow-400 mr-2">warning</span>
                    <h4 class="text-white font-medium">Content Unavailable</h4>
                </div>
                <p class="text-gray-300 text-sm mb-3">
                    This content is temporarily unavailable. Please refresh the page.
                </p>
                <button onclick="location.reload()" 
                        class="bg-primary hover:bg-primary-dark text-white px-3 py-1 rounded text-sm">
                    Refresh Page
                </button>
            </div>
        ''')