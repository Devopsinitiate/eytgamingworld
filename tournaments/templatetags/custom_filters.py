from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.template import TemplateSyntaxError
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary by key.
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return {}
    return dictionary.get(key, {})


@register.filter(name='dict_items')
def dict_items(dictionary):
    """
    Template filter to get items from a dictionary.
    Usage: {% for key, value in my_dict|dict_items %}
    """
    if dictionary is None:
        return []
    return dictionary.items()


@register.filter(name='safe_default')
def safe_default(value, default_value=""):
    """
    Template filter to provide safe default values for template variables.
    Usage: {{ tournament.name|safe_default:"Tournament Name Unavailable" }}
    Requirements: 2.1, 2.2, 2.5
    """
    if value is None or value == "":
        return escape(default_value)
    return value


@register.filter(name='format_currency')
def format_currency(value, currency_symbol="$"):
    """
    Template filter to format currency values safely and consistently.
    Usage: {{ tournament.prize_pool|format_currency }}
    Requirements: 6.4 - Consistent currency formatting
    """
    if value is None or value == 0:
        return "Free"
    try:
        # Use consistent formatting: $X,XXX (no decimals for whole numbers)
        return f"{currency_symbol}{float(value):,.0f}"
    except (ValueError, TypeError):
        return "Amount Unavailable"


@register.filter(name='format_currency_detailed')
def format_currency_detailed(value, currency_symbol="$"):
    """
    Template filter to format currency values with detailed formatting.
    Usage: {{ tournament.registration_fee|format_currency_detailed }}
    Requirements: 6.4 - Consistent currency formatting with decimals when needed
    """
    if value is None or value == 0:
        return "Free"
    try:
        # Always show 2 decimal places for consistency
        float_value = float(value)
        return f"{currency_symbol}{float_value:.2f}"
    except (ValueError, TypeError):
        return "Amount Unavailable"


@register.filter(name='format_date_consistent')
def format_date_consistent(value, format_type="full"):
    """
    Template filter to format dates consistently across all pages.
    Usage: {{ tournament.start_datetime|format_date_consistent:"full" }}
    Requirements: 6.2 - Consistent date formatting
    """
    if not value:
        return "Date TBD"
    
    try:
        if format_type == "full":
            return value.strftime('%b %d, %Y %I:%M %p')
        elif format_type == "date":
            return value.strftime('%b %d, %Y')
        elif format_type == "time":
            return value.strftime('%I:%M %p')
        elif format_type == "short":
            return value.strftime('%b %d')
        else:
            return value.strftime('%b %d, %Y %I:%M %p')
    except (AttributeError, ValueError):
        return "Date TBD"


@register.filter(name='format_tournament_name')
def format_tournament_name(value):
    """
    Template filter to format tournament names consistently.
    Usage: {{ tournament.name|format_tournament_name }}
    Requirements: 6.1 - Consistent tournament name display
    """
    if not value or value.strip() == "":
        return "Tournament Name Unavailable"
    return value.strip()


@register.filter(name='format_participant_count')
def format_participant_count(registered, max_participants):
    """
    Template filter to format participant counts consistently.
    Usage: {{ tournament.total_registered|format_participant_count:tournament.max_participants }}
    Requirements: 6.3 - Consistent participant count display
    """
    try:
        registered = int(registered or 0)
        max_participants = int(max_participants or 0)
        
        if max_participants == 0:
            return f"{registered} registered"
        
        return f"{registered}/{max_participants}"
    except (ValueError, TypeError):
        return "Registration info unavailable"


@register.filter(name='format_status_display')
def format_status_display(status):
    """
    Template filter to format tournament status consistently.
    Usage: {{ tournament.status|format_status_display }}
    Requirements: 6.5 - Consistent status indicators
    """
    status_mapping = {
        'draft': 'Draft',
        'registration': 'Registration Open',
        'check_in': 'Check-in Open',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'cancelled': 'Cancelled',
    }
    
    return status_mapping.get(status, status.replace('_', ' ').title() if status else 'Unknown Status')


@register.filter(name='format_percentage')
def format_percentage(value, decimal_places=0):
    """
    Template filter to format percentage values safely.
    Usage: {{ percentage|format_percentage }}
    Requirements: 2.3
    """
    if value is None:
        return "0%"
    try:
        return f"{float(value):.{decimal_places}f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter(name='material_icon')
def material_icon(icon_name, css_classes=""):
    """
    Template filter to render Material Symbols icons safely.
    Usage: {{ "emoji_events"|material_icon:"text-primary" }}
    Requirements: 2.4
    """
    if not icon_name:
        return ""
    
    safe_icon_name = escape(icon_name)
    safe_css_classes = escape(css_classes)
    
    html = f'<span class="material-symbols-outlined {safe_css_classes}" aria-hidden="true">{safe_icon_name}</span>'
    return mark_safe(html)


@register.filter(name='participant_count_display')
def participant_count_display(registered, max_participants):
    """
    Template filter to display participant count safely.
    Usage: {{ tournament.total_registered|participant_count_display:tournament.max_participants }}
    Requirements: 2.3
    """
    try:
        registered = int(registered or 0)
        max_participants = int(max_participants or 0)
        
        if max_participants == 0:
            return f"{registered} registered"
        
        return f"{registered}/{max_participants}"
    except (ValueError, TypeError):
        return "Registration info unavailable"


@register.filter(name='status_badge_class')
def status_badge_class(status):
    """
    Template filter to get CSS class for status badges with consistent styling.
    Usage: {{ tournament.status|status_badge_class }}
    Requirements: 6.5 - Consistent status indicators and colors
    """
    status_classes = {
        'draft': 'status-draft bg-gray-600 text-gray-100',
        'registration': 'status-registration bg-green-600 text-green-100',
        'check_in': 'status-check-in bg-blue-600 text-blue-100',
        'in_progress': 'status-in-progress bg-yellow-600 text-yellow-100',
        'completed': 'status-completed bg-purple-600 text-purple-100',
        'cancelled': 'status-cancelled bg-red-600 text-red-100',
    }
    
    return status_classes.get(status, 'status-unknown bg-gray-500 text-gray-100')


@register.filter(name='status_color')
def status_color(status):
    """
    Template filter to get consistent color for status indicators.
    Usage: {{ tournament.status|status_color }}
    Requirements: 6.5 - Consistent status colors
    """
    status_colors = {
        'draft': 'gray',
        'registration': 'green',
        'check_in': 'blue',
        'in_progress': 'yellow',
        'completed': 'purple',
        'cancelled': 'red',
    }
    
    return status_colors.get(status, 'gray')


@register.filter(name='status_icon')
def status_icon(status):
    """
    Template filter to get icon for tournament status.
    Usage: {{ tournament.status|status_icon }}
    Requirements: 2.4, 2.5
    """
    status_icons = {
        'draft': 'draft',
        'registration': 'how_to_reg',
        'check_in': 'check_circle',
        'in_progress': 'play_arrow',
        'completed': 'emoji_events',
        'cancelled': 'cancel',
    }
    
    icon_name = status_icons.get(status, 'help')
    return material_icon(icon_name)


@register.inclusion_tag('tournaments/partials/error_fallback.html', takes_context=True)
def error_fallback(context, error_type="general", fallback_message="Content unavailable"):
    """
    Template tag to provide error fallback content.
    Usage: {% error_fallback "template_error" "Tournament information is currently unavailable" %}
    Requirements: 2.5
    """
    return {
        'error_type': error_type,
        'fallback_message': fallback_message,
        'request': context.get('request'),
    }


@register.simple_tag(takes_context=True)
def safe_render(context, template_string, fallback=""):
    """
    Template tag to safely render template strings with fallback.
    Usage: {% safe_render "{{ tournament.name }}" "Tournament Name Unavailable" %}
    Requirements: 2.1, 2.5
    """
    try:
        from django.template import Template, Context
        template = Template(template_string)
        return template.render(Context(context))
    except (TemplateSyntaxError, Exception) as e:
        logger.warning(f"Template rendering error: {e}")
        return escape(fallback)


@register.filter(name='div')
def div(value, divisor):
    """
    Template filter to divide two values safely.
    Usage: {{ tournament.prize_pool|div:tournament.max_participants }}
    Requirements: 2.3
    """
    try:
        value = float(value or 0)
        divisor = float(divisor or 1)
        if divisor == 0:
            return 0
        return value / divisor
    except (ValueError, TypeError):
        return 0


@register.filter(name='sub')
def sub(value, subtrahend):
    """
    Template filter to subtract two values safely.
    Usage: {{ tournament.prize_pool|sub:tournament.registration_fee }}
    Requirements: 2.3
    """
    try:
        value = float(value or 0)
        subtrahend = float(subtrahend or 0)
        return value - subtrahend
    except (ValueError, TypeError):
        return 0


@register.filter(name='multiply')
def multiply(value, multiplier):
    """
    Template filter to multiply two values safely.
    Usage: {{ tournament.registration_fee|multiply:tournament.total_registered }}
    Requirements: 2.3
    """
    try:
        value = float(value or 0)
        multiplier = float(multiplier or 0)
        return value * multiplier
    except (ValueError, TypeError):
        return 0


@register.filter(name='render_with_fallback')
def render_with_fallback(value, fallback="Content unavailable"):
    """
    Template filter to render values with fallback for errors.
    Usage: {{ complex_template_variable|render_with_fallback:"Fallback content" }}
    Requirements: 2.5
    """
    try:
        if value is None:
            return escape(fallback)
        return value
    except Exception as e:
        logger.warning(f"Template value rendering error: {e}")
        return escape(fallback)


@register.filter(name='safe_timesince')
def safe_timesince(value, fallback="Recently"):
    """
    Template filter to safely apply timesince with fallback for invalid datetime values.
    Usage: {{ match.completed_at|safe_timesince:"Recently completed" }}
    Handles both datetime objects and string values that might cause AttributeError.
    """
    if not value:
        return fallback
    
    try:
        from django.utils.timesince import timesince
        from datetime import datetime
        from django.utils import timezone
        
        # If it's already a datetime object, use it directly
        if hasattr(value, 'year'):
            return f"{timesince(value)} ago"
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                # Handle ISO format strings
                if 'T' in value:
                    if value.endswith('Z'):
                        value = value[:-1] + '+00:00'
                    elif '+' not in value:
                        value += '+00:00'
                    
                    parsed_datetime = datetime.fromisoformat(value)
                    if parsed_datetime.tzinfo is None:
                        parsed_datetime = timezone.make_aware(parsed_datetime)
                    
                    return f"{timesince(parsed_datetime)} ago"
            except (ValueError, AttributeError):
                pass
        
        # If we can't parse it, return fallback
        return fallback
        
    except Exception as e:
        logger.warning(f"Safe timesince filter error: {e}")
        return fallback
