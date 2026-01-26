"""
Security utilities for tournament system.
Provides XSS protection, input validation, and access control.
"""
import re
import html
import bleach
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.html import escape
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class TournamentSecurityValidator:
    """
    Validates and sanitizes tournament-related user input.
    Provides XSS protection and input validation.
    """
    
    # Allowed HTML tags for tournament descriptions and rules
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
    ]
    
    ALLOWED_ATTRIBUTES = {
        '*': ['class'],
    }
    
    # Regex patterns for validation
    SLUG_PATTERN = re.compile(r'^[a-z0-9-]+$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    @classmethod
    def sanitize_html_content(cls, content):
        """
        Sanitize HTML content to prevent XSS attacks.
        Allows only safe HTML tags and attributes.
        """
        if not content:
            return content
        
        # Use bleach to sanitize HTML
        cleaned_content = bleach.clean(
            content,
            tags=cls.ALLOWED_TAGS,
            attributes=cls.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned_content
    
    @classmethod
    def validate_tournament_name(cls, name):
        """Validate tournament name for security and format."""
        if not name:
            raise ValidationError("Tournament name is required")
        
        if len(name) > 200:
            raise ValidationError("Tournament name cannot exceed 200 characters")
        
        # Check for potentially malicious content
        if '<script' in name.lower() or 'javascript:' in name.lower():
            raise ValidationError("Tournament name contains invalid content")
        
        # Escape HTML entities
        return escape(name.strip())
    
    @classmethod
    def validate_tournament_slug(cls, slug):
        """Validate tournament slug format."""
        if not slug:
            raise ValidationError("Tournament slug is required")
        
        if not cls.SLUG_PATTERN.match(slug):
            raise ValidationError(
                "Slug can only contain lowercase letters, numbers, and hyphens"
            )
        
        if len(slug) > 200:
            raise ValidationError("Slug cannot exceed 200 characters")
        
        return slug
    
    @classmethod
    def validate_url(cls, url, field_name="URL"):
        """Validate URL format and security."""
        if not url:
            return url
        
        if not cls.URL_PATTERN.match(url):
            raise ValidationError(f"{field_name} must be a valid HTTP/HTTPS URL")
        
        # Check for potentially malicious URLs
        if 'javascript:' in url.lower() or 'data:' in url.lower():
            raise ValidationError(f"{field_name} contains invalid protocol")
        
        return url
    
    @classmethod
    def validate_description(cls, description):
        """Validate and sanitize tournament description."""
        if not description:
            return description
        
        if len(description) > 5000:
            raise ValidationError("Description cannot exceed 5000 characters")
        
        return cls.sanitize_html_content(description)
    
    @classmethod
    def validate_rules(cls, rules):
        """Validate and sanitize tournament rules."""
        if not rules:
            return rules
        
        if len(rules) > 10000:
            raise ValidationError("Rules cannot exceed 10000 characters")
        
        return cls.sanitize_html_content(rules)
    
    @classmethod
    def validate_participant_name(cls, name):
        """Validate participant display name."""
        if not name:
            raise ValidationError("Display name is required")
        
        if len(name) > 100:
            raise ValidationError("Display name cannot exceed 100 characters")
        
        # Check for potentially malicious content
        if '<' in name or '>' in name or 'script' in name.lower():
            raise ValidationError("Display name contains invalid characters")
        
        return escape(name.strip())


class TournamentAccessControl:
    """
    Handles tournament access control and permissions.
    """
    
    @staticmethod
    def can_view_tournament(user, tournament):
        """Check if user can view tournament."""
        # Public tournaments can be viewed by anyone
        if tournament.is_public:
            return True
        
        # Private tournaments can only be viewed by:
        # - Tournament organizer
        # - Participants
        # - Admins
        if not user.is_authenticated:
            return False
        
        if user == tournament.organizer or user.role == 'admin':
            return True
        
        # Check if user is a participant
        from .models import Participant
        return Participant.objects.filter(
            tournament=tournament,
            user=user
        ).exists()
    
    @staticmethod
    def can_edit_tournament(user, tournament):
        """Check if user can edit tournament."""
        if not user.is_authenticated:
            return False
        
        return user == tournament.organizer or user.role == 'admin'
    
    @staticmethod
    def can_register_for_tournament(user, tournament):
        """Check if user can register for tournament."""
        if not user.is_authenticated:
            return False
        
        # Use existing tournament method
        can_register, _ = tournament.can_user_register(user)
        return can_register
    
    @staticmethod
    def can_manage_participants(user, tournament):
        """Check if user can manage tournament participants."""
        if not user.is_authenticated:
            return False
        
        return user == tournament.organizer or user.role == 'admin'
    
    @staticmethod
    def can_report_match_score(user, match):
        """Check if user can report match score."""
        if not user.is_authenticated:
            return False
        
        # Tournament organizer or admin can always report
        if user == match.tournament.organizer or user.role == 'admin':
            return True
        
        # Participants in the match can report
        if match.participant1 and match.participant1.user == user:
            return True
        if match.participant2 and match.participant2.user == user:
            return True
        
        return False


def require_tournament_permission(permission_type):
    """
    Decorator to check tournament permissions.
    
    Args:
        permission_type: 'view', 'edit', 'manage_participants'
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Get tournament from kwargs or request
            tournament_slug = kwargs.get('slug')
            if not tournament_slug:
                return HttpResponseForbidden("Tournament not specified")
            
            from .models import Tournament
            try:
                tournament = Tournament.objects.get(slug=tournament_slug)
            except Tournament.DoesNotExist:
                return HttpResponseForbidden("Tournament not found")
            
            # Check permission
            access_control = TournamentAccessControl()
            
            if permission_type == 'view':
                has_permission = access_control.can_view_tournament(request.user, tournament)
            elif permission_type == 'edit':
                has_permission = access_control.can_edit_tournament(request.user, tournament)
            elif permission_type == 'manage_participants':
                has_permission = access_control.can_manage_participants(request.user, tournament)
            else:
                has_permission = False
            
            if not has_permission:
                logger.warning(
                    f"Access denied: User {request.user.id} attempted {permission_type} "
                    f"on tournament {tournament.slug}"
                )
                return HttpResponseForbidden("Access denied")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class ShareTrackingRateLimit:
    """
    Rate limiting for share tracking to prevent spam.
    """
    
    @staticmethod
    def is_rate_limited(ip_address, user_id=None):
        """
        Check if IP/user is rate limited for share tracking.
        Allows 10 shares per hour per IP, 20 per hour per authenticated user.
        """
        current_time = timezone.now()
        hour_key = current_time.strftime('%Y%m%d%H')
        
        # Check IP-based rate limit
        ip_key = f"share_rate_limit_ip_{ip_address}_{hour_key}"
        ip_count = cache.get(ip_key, 0)
        
        if ip_count >= 10:  # 10 shares per hour per IP
            return True
        
        # Check user-based rate limit for authenticated users
        if user_id:
            user_key = f"share_rate_limit_user_{user_id}_{hour_key}"
            user_count = cache.get(user_key, 0)
            
            if user_count >= 20:  # 20 shares per hour per user
                return True
        
        return False
    
    @staticmethod
    def increment_rate_limit(ip_address, user_id=None):
        """Increment rate limit counters."""
        current_time = timezone.now()
        hour_key = current_time.strftime('%Y%m%d%H')
        
        # Increment IP counter
        ip_key = f"share_rate_limit_ip_{ip_address}_{hour_key}"
        ip_count = cache.get(ip_key, 0)
        cache.set(ip_key, ip_count + 1, 3600)  # 1 hour timeout
        
        # Increment user counter for authenticated users
        if user_id:
            user_key = f"share_rate_limit_user_{user_id}_{hour_key}"
            user_count = cache.get(user_key, 0)
            cache.set(user_key, user_count + 1, 3600)  # 1 hour timeout


def sanitize_tournament_data(data):
    """
    Sanitize tournament form data before saving.
    
    Args:
        data: Dictionary of tournament data
    
    Returns:
        Dictionary of sanitized data
    """
    validator = TournamentSecurityValidator()
    sanitized = {}
    
    # Sanitize each field
    if 'name' in data:
        sanitized['name'] = validator.validate_tournament_name(data['name'])
    
    if 'slug' in data:
        sanitized['slug'] = validator.validate_tournament_slug(data['slug'])
    
    if 'description' in data:
        sanitized['description'] = validator.validate_description(data['description'])
    
    if 'rules' in data:
        sanitized['rules'] = validator.validate_rules(data['rules'])
    
    if 'stream_url' in data:
        sanitized['stream_url'] = validator.validate_url(data['stream_url'], 'Stream URL')
    
    if 'discord_invite' in data:
        sanitized['discord_invite'] = validator.validate_url(data['discord_invite'], 'Discord invite')
    
    # Copy other fields as-is (they should be validated by Django forms)
    for key, value in data.items():
        if key not in sanitized:
            sanitized[key] = value
    
    return sanitized


def log_security_event(event_type, user, details, severity='INFO'):
    """
    Log security-related events for monitoring.
    
    Args:
        event_type: Type of security event (e.g., 'XSS_ATTEMPT', 'ACCESS_DENIED')
        user: User object or None
        details: Additional details about the event
        severity: Log severity ('INFO', 'WARNING', 'ERROR')
    """
    if user and hasattr(user, 'id') and hasattr(user, 'email'):
        user_info = f"User {user.id} ({user.email})"
    elif user and hasattr(user, 'id'):
        user_info = f"User {user.id}"
    else:
        user_info = "Anonymous"
    
    log_message = f"SECURITY EVENT [{event_type}]: {user_info} - {details}"
    
    if severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    else:
        logger.info(log_message)