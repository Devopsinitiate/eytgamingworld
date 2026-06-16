from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def verified_badge(user, size=16):
    """Render a blue verified checkmark badge for celebrity users."""
    if not user or not hasattr(user, 'is_verified_personality') or not user.is_verified_personality:
        return ''
    return format_html(
        '<span class="verified-badge" style="display:inline-flex;align-items:center;vertical-align:middle;'
        'margin-left:4px;" title="Verified Personality">'
        '<svg width="{}" height="{}" viewBox="0 0 24 24" fill="#3B82F6" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>'
        '</svg></span>',
        size, size
    )
