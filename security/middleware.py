"""
Security middleware for EYTGaming platform.
Provides security headers and audit logging.
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    Implements OWASP recommended security headers.
    """
    
    def process_response(self, request, response):
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (basic - customize as needed)
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
            )
        
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """
    Log important user actions for security auditing.
    Tracks POST, PUT, DELETE, PATCH requests from authenticated users.
    """
    
    SENSITIVE_PATHS = [
        '/admin/',
        '/accounts/password',
        '/payments/',
    ]
    
    def process_request(self, request):
        # Only log authenticated users
        if not request.user.is_authenticated:
            return None
        
        # Only log state-changing methods
        if request.method not in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return None
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Log the action
        log_message = (
            f"User: {request.user.id} ({request.user.email}) | "
            f"Method: {request.method} | "
            f"Path: {request.path} | "
            f"IP: {ip_address}"
        )
        
        # Use different log levels for sensitive paths
        is_sensitive = any(path in request.path for path in self.SENSITIVE_PATHS)
        if is_sensitive:
            logger.warning(f"SENSITIVE ACTION: {log_message}")
        else:
            logger.info(f"ACTION: {log_message}")
        
        return None
    
    def process_exception(self, request, exception):
        """Log exceptions for authenticated users"""
        if request.user.is_authenticated:
            logger.error(
                f"EXCEPTION for user {request.user.id}: {exception} | "
                f"Path: {request.path}"
            )
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Basic rate limiting middleware.
    For production, consider using django-ratelimit or Redis-based solution.
    """
    
    def process_request(self, request):
        # Placeholder for rate limiting logic
        # In production, implement proper rate limiting
        # using django-ratelimit or similar
        return None
