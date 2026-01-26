from django import template
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.conf import settings
import os

register = template.Library()

@register.filter
def status_class(value):
    """Convert status to CSS class name"""
    return value.replace('_', '-')

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def percentage(value, total):
    """Calculate percentage of value from total"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_by_status(queryset, status):
    """Filter queryset by status"""
    try:
        return queryset.filter(status=status)
    except AttributeError:
        return []

@register.filter
def length(value):
    """Get length of a queryset or list"""
    try:
        return len(value)
    except (TypeError, AttributeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Add the argument to the value"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def calculate_prize_amount(prize_pool, percentage):
    """Calculate prize amount from pool and percentage"""
    try:
        return float(prize_pool) * (float(percentage) / 100)
    except (ValueError, TypeError):
        return 0

@register.filter
def format_currency(value):
    """Format value as currency"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def placement_ordinal(value):
    """Convert placement number to ordinal (1st, 2nd, 3rd, etc.)"""
    try:
        num = int(value)
        if 10 <= num % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(num % 10, 'th')
        return f"{num}{suffix}"
    except (ValueError, TypeError):
        return str(value)

@register.filter
def tournament_rounds(participants):
    """Calculate number of rounds for single elimination tournament"""
    try:
        import math
        return math.ceil(math.log2(int(participants)))
    except (ValueError, TypeError):
        return 1

@register.filter
def round_robin_matches(participants):
    """Calculate total matches for round robin tournament"""
    try:
        n = int(participants)
        return (n * (n - 1)) // 2
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def responsive_image(image_field, alt_text="", css_class="", sizes=""):
    """
    Generate responsive image HTML with WebP support and multiple sizes.
    
    Usage:
    {% responsive_image tournament.banner "Tournament Banner" "hero-image" %}
    """
    if not image_field:
        return ""
    
    # Get base image info
    image_url = image_field.url
    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    
    # Generate responsive image HTML
    html_parts = [f'<picture class="{css_class}">']
    
    # Define responsive sizes and their media queries
    responsive_sizes = [
        ('hero', '(min-width: 1920px)', f"{base_name}_hero"),
        ('large', '(min-width: 1200px)', f"{base_name}_large"),
        ('medium', '(min-width: 768px)', f"{base_name}_medium"),
        ('small', '(min-width: 480px)', f"{base_name}_small"),
        ('thumbnail', None, f"{base_name}_thumbnail")
    ]
    
    # Add WebP sources
    for size_name, media_query, filename in responsive_sizes:
        webp_path = f"tournaments/optimized/{filename}.webp"
        if media_query:
            html_parts.append(f'  <source media="{media_query}" srcset="{settings.MEDIA_URL}{webp_path}" type="image/webp">')
        else:
            html_parts.append(f'  <source srcset="{settings.MEDIA_URL}{webp_path}" type="image/webp">')
    
    # Add JPEG fallback sources
    for size_name, media_query, filename in responsive_sizes:
        jpeg_path = f"tournaments/optimized/{filename}.jpg"
        if media_query:
            html_parts.append(f'  <source media="{media_query}" srcset="{settings.MEDIA_URL}{jpeg_path}" type="image/jpeg">')
    
    # Fallback img tag
    html_parts.append(f'  <img src="{image_url}" alt="{alt_text}" loading="lazy" {f"sizes=\"{sizes}\"" if sizes else ""}>')
    html_parts.append('</picture>')
    
    return mark_safe('\n'.join(html_parts))

@register.simple_tag
def lazy_image(image_field, alt_text="", css_class="", placeholder_color="#f3f4f6"):
    """
    Generate lazy-loaded image with placeholder.
    
    Usage:
    {% lazy_image participant.user.avatar "User Avatar" "avatar-image" %}
    """
    if not image_field:
        return f'<div class="image-placeholder {css_class}" style="background-color: {placeholder_color};"></div>'
    
    return mark_safe(f'''
        <img 
            data-src="{image_field.url}" 
            alt="{alt_text}" 
            class="lazy-image {css_class}"
            style="background-color: {placeholder_color};"
            loading="lazy"
        >
    ''')

@register.simple_tag
def webp_image(image_field, alt_text="", css_class="", fallback_format="jpg"):
    """
    Generate WebP image with fallback.
    
    Usage:
    {% webp_image tournament.thumbnail "Tournament Thumbnail" "thumbnail-image" %}
    """
    if not image_field:
        return ""
    
    # Get base image info
    base_name = os.path.splitext(os.path.basename(image_field.name))[0]
    webp_path = f"tournaments/optimized/{base_name}.webp"
    fallback_path = f"tournaments/optimized/{base_name}.{fallback_format}"
    
    return mark_safe(f'''
        <picture class="{css_class}">
            <source srcset="{settings.MEDIA_URL}{webp_path}" type="image/webp">
            <img src="{settings.MEDIA_URL}{fallback_path}" alt="{alt_text}" loading="lazy">
        </picture>
    ''')

@register.filter
def cache_bust(value):
    """Add cache busting parameter to static files"""
    if not value:
        return value
    
    # In production, you might want to use a version number or file hash
    import time
    cache_param = int(time.time()) if settings.DEBUG else "v1"
    separator = "&" if "?" in value else "?"
    return f"{value}{separator}v={cache_param}"
def tournament_currency(value):
    """
    Format currency for consistent tournament display.
    Format: "$X,XXX.XX" or "Free" for 0
    
    Usage: {{ tournament.registration_fee|tournament_currency }}
    """
    try:
        amount = float(value)
        if amount == 0:
            return "Free"
        return f"${amount:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def tournament_status_badge(status):
    """
    Generate consistent status badge HTML with colors.
    
    Usage: {{ tournament.status|tournament_status_badge }}
    """
    status_config = {
        'registration': {'color': 'blue', 'icon': 'how_to_reg', 'text': 'Registration Open'},
        'upcoming': {'color': 'purple', 'icon': 'schedule', 'text': 'Upcoming'},
        'in_progress': {'color': 'green', 'icon': 'play_circle', 'text': 'In Progress'},
        'completed': {'color': 'gray', 'icon': 'check_circle', 'text': 'Completed'},
        'cancelled': {'color': 'red', 'icon': 'cancel', 'text': 'Cancelled'},
    }
    
    config = status_config.get(status, {'color': 'gray', 'icon': 'info', 'text': status.replace('_', ' ').title()})
    
    html = f'''
    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-{config['color']}-900/20 text-{config['color']}-400 border border-{config['color']}-800">
        <span class="material-symbols-outlined text-sm">{config['icon']}</span>
        {config['text']}
    </span>
    '''
    
    return mark_safe(html)
