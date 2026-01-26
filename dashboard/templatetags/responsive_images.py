"""
Responsive image template tags for dashboard
Requirements: 14.5 - Responsive image serving
Performance: 16.5 - WebP image optimization with fallback

Provides template tags for serving responsive images with srcset and WebP support
Avatar sizes: 50px, 100px, 200px, 400px
Banner sizes: 640px, 1280px, 1920px

WebP Support:
- Generates <picture> elements with WebP source and JPEG/PNG fallback
- Lazy loading for below-fold images
- Cache-control headers set to 24 hours (configured in settings/nginx)
"""

from django import template
from django.utils.safestring import mark_safe
from PIL import Image
import os

register = template.Library()


def get_webp_url(image_url):
    """
    Get WebP version URL for an image.
    
    In production, this would check if a WebP version exists or generate it.
    For now, we'll assume WebP versions are generated on upload and have .webp extension.
    
    Args:
        image_url: Original image URL
        
    Returns:
        WebP URL if available, otherwise None
    """
    if not image_url:
        return None
    
    # Replace extension with .webp
    # In production, you would check if the file exists
    base_url = os.path.splitext(image_url)[0]
    webp_url = f"{base_url}.webp"
    
    # For now, we'll return the webp URL
    # In production, you'd check if it exists first
    return webp_url


@register.simple_tag
def responsive_avatar(image_field, alt_text="", css_class="", lazy=True, img_id=""):
    """
    Generate responsive avatar image with WebP support and srcset
    
    Args:
        image_field: ImageField from model
        alt_text: Alt text for accessibility
        css_class: Additional CSS classes
        lazy: Whether to use lazy loading (default True)
        img_id: Optional id attribute for the img element
    
    Returns:
        HTML picture element with WebP source and fallback
        
    Performance: 16.5 - WebP optimization with JPEG/PNG fallback
    """
    if not image_field:
        # Return placeholder if no image
        return mark_safe(
            f'<div class="avatar-placeholder {css_class}" role="img" aria-label="{alt_text or "No avatar"}"></div>'
        )
    
    # Get the base URL
    base_url = image_field.url
    webp_url = get_webp_url(base_url)
    
    # Generate srcset for different sizes
    # Avatar sizes: 50px, 100px, 200px, 400px
    srcset = f"{base_url} 400w"
    webp_srcset = f"{webp_url} 400w" if webp_url else None
    
    # Responsive sizes based on viewport
    sizes = "(max-width: 768px) 100px, (max-width: 1024px) 200px, 400px"
    
    # Add id attribute if provided
    id_attr = f'id="{img_id}"' if img_id else ""
    
    # Build HTML with picture element for WebP support
    if webp_srcset:
        html = f'''<picture>
    <source type="image/webp" srcset="{webp_srcset}" sizes="{sizes}">
    <img 
        {id_attr}
        src="{base_url}" 
        srcset="{srcset}"
        sizes="{sizes}"
        alt="{alt_text}"
        class="responsive-image avatar {css_class}"
        loading="{'lazy' if lazy else 'eager'}"
        decoding="async"
    />
</picture>'''
    else:
        html = f'''<img 
        {id_attr}
        src="{base_url}" 
        srcset="{srcset}"
        sizes="{sizes}"
        alt="{alt_text}"
        class="responsive-image avatar {css_class}"
        loading="{'lazy' if lazy else 'eager'}"
        decoding="async"
    />'''
    
    return mark_safe(html)


@register.simple_tag
def responsive_banner(image_field, alt_text="", css_class="", img_id=""):
    """
    Generate responsive banner image with srcset
    
    Args:
        image_field: ImageField from model
        alt_text: Alt text for accessibility
        css_class: Additional CSS classes
        img_id: Optional id attribute for the img element
    
    Returns:
        HTML img tag with srcset for responsive loading
    """
    if not image_field:
        # Return placeholder if no image
        return mark_safe(
            f'<div class="banner-placeholder {css_class}" role="img" aria-label="{alt_text or "No banner"}"></div>'
        )
    
    # Get the base URL
    base_url = image_field.url
    
    # Generate srcset for different sizes
    # In production, these would be pre-generated or generated on-the-fly
    srcset = f"{base_url} 1920w"
    
    # Responsive sizes based on viewport
    sizes = "(max-width: 768px) 640px, (max-width: 1024px) 1280px, 1920px"
    
    # Add id attribute if provided
    id_attr = f'id="{img_id}"' if img_id else ""
    
    html = f'''<img 
        {id_attr}
        src="{base_url}" 
        srcset="{srcset}"
        sizes="{sizes}"
        alt="{alt_text}"
        class="responsive-image banner-image {css_class}"
        loading="lazy"
        decoding="async"
    />'''
    
    return mark_safe(html)


@register.simple_tag
def responsive_image(image_field, alt_text="", css_class="", sizes="100vw"):
    """
    Generate responsive image with srcset (generic)
    
    Args:
        image_field: ImageField from model
        alt_text: Alt text for accessibility
        css_class: Additional CSS classes
        sizes: Sizes attribute for responsive images
    
    Returns:
        HTML img tag with srcset for responsive loading
    """
    if not image_field:
        return mark_safe(
            f'<div class="image-placeholder {css_class}" role="img" aria-label="{alt_text or "No image"}"></div>'
        )
    
    base_url = image_field.url
    
    # Use the original image
    # In production, you would generate multiple sizes
    srcset = f"{base_url} 1x"
    
    html = f'''<img 
        src="{base_url}" 
        srcset="{srcset}"
        sizes="{sizes}"
        alt="{alt_text}"
        class="responsive-image {css_class}"
        loading="lazy"
        decoding="async"
    />'''
    
    return mark_safe(html)


@register.filter
def avatar_size(image_field, size="md"):
    """
    Get avatar URL for specific size
    
    Args:
        image_field: ImageField from model
        size: Size variant (sm=50px, md=100px, lg=200px, xl=400px)
    
    Returns:
        URL for the avatar at specified size
    """
    if not image_field:
        return ""
    
    # In production, this would return different sized versions
    # For now, return the original and let CSS handle sizing
    return image_field.url


@register.filter
def banner_size(image_field, size="lg"):
    """
    Get banner URL for specific size
    
    Args:
        image_field: ImageField from model
        size: Size variant (sm=640px, md=1280px, lg=1920px)
    
    Returns:
        URL for the banner at specified size
    """
    if not image_field:
        return ""
    
    # In production, this would return different sized versions
    # For now, return the original and let CSS handle sizing
    return image_field.url


@register.inclusion_tag('dashboard/components/responsive_avatar.html')
def avatar_with_srcset(user, size="md", show_online=False):
    """
    Render avatar with responsive srcset using inclusion tag
    
    Args:
        user: User object
        size: Size class (sm, md, lg, xl)
        show_online: Whether to show online status indicator
    
    Returns:
        Rendered template with avatar
    """
    size_map = {
        'sm': 'avatar-sm',
        'md': 'avatar-md',
        'lg': 'avatar-lg',
        'xl': 'avatar-xl'
    }
    
    return {
        'user': user,
        'size_class': size_map.get(size, 'avatar-md'),
        'show_online': show_online,
        'has_avatar': bool(user.avatar),
    }


@register.inclusion_tag('dashboard/components/responsive_banner.html')
def banner_with_srcset(user):
    """
    Render banner with responsive srcset using inclusion tag
    
    Args:
        user: User object
    
    Returns:
        Rendered template with banner
    """
    return {
        'user': user,
        'has_banner': bool(user.banner) if hasattr(user, 'banner') else False,
    }
