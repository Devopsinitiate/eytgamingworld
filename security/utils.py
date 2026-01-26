"""
Security utility functions.
"""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxy headers correctly.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def get_user_agent(request):
    """Get the user agent string from the request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def log_audit_action(user, action, description='', severity='low', 
                     content_object=None, request=None, **metadata):
    """
    Log an audit action.
    
    Args:
        user: User performing the action
        action: Action type (e.g., 'create', 'update', 'delete', 'payment')
        description: Human-readable description
        severity: 'low', 'medium', 'high', or 'critical'
        content_object: Related object (optional)
        request: HTTP request object (optional)
        **metadata: Additional metadata
    
    Usage:
        log_audit_action(
            user=request.user,
            action='payment',
            description='Created payment intent',
            severity='medium',
            content_object=payment,
            request=request
        )
    """
    from .models import AuditLog
    from django.contrib.contenttypes.models import ContentType
    
    try:
        kwargs = {
            'user': user,
            'user_email': user.email if user else '',
            'action': action,
            'description': description,
            'severity': severity,
            'metadata': metadata
        }
        
        # Add content object if provided
        if content_object:
            kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
            kwargs['object_id'] = str(content_object.pk)
        
        # Add request details if provided
        if request:
            kwargs.update({
                'ip_address': get_client_ip(request),
                'user_agent': get_user_agent(request),
                'request_path': request.path[:500],
                'request_method': request.method
            })
        
        return AuditLog.objects.create(**kwargs)
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")
        return None


def log_security_event(event_type, description, user=None, request=None, 
                       risk_level='low', metadata=None):
    """
    Log a security event.
    
    Args:
        event_type: Type of security event
        description: Event description
        user: User involved (optional)
        request: HTTP request object (optional)
        risk_level: 'low', 'medium', 'high', or 'critical'
        metadata: Additional metadata
    
    Usage:
        log_security_event(
            event_type='failed_login',
            description='Failed login attempt',
            user=user,
            request=request,
            risk_level='medium',
            metadata={'attempts': 3}
        )
    """
    from .models import SecurityEvent
    
    try:
        event_data = {
            'event_type': event_type,
            'description': description,
            'user': user,
            'risk_level': risk_level,
            'request_data': metadata or {}
        }
        
        if request:
            event_data.update({
                'ip_address': get_client_ip(request),
                'user_agent': get_user_agent(request),
                'request_path': request.path[:500],
                'request_method': request.method
            })
        else:
            event_data['ip_address'] = 'unknown'
        
        return SecurityEvent.objects.create(**event_data)
    except Exception as e:
        logger.error(f"Failed to log security event: {e}")
        return None


def check_suspicious_activity(request, user=None):
    """Check for suspicious activity patterns"""
    from .models import SecurityEvent
    
    ip_address = get_client_ip(request)
    
    # Check for too many failed logins from this IP
    recent_failures = SecurityEvent.objects.filter(
        event_type='failed_login',
        ip_address=ip_address,
        created_at__gte=timezone.now() - timedelta(minutes=15)
    ).count()
    
    if recent_failures >= 5:
        log_security_event(
            event_type='brute_force',
            description=f"Potential brute force attack detected from {ip_address}",
            risk_level='high',
            user=user,
            request=request,
            metadata={'failed_attempts': recent_failures}
        )
        return True
    
    return False


def is_ip_blocked(ip_address):
    """Check if an IP address should be blocked"""
    from .models import SecurityEvent
    
    # Check for critical security events from this IP in the last hour
    critical_events = SecurityEvent.objects.filter(
        ip_address=ip_address,
        risk_level='critical',
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    return critical_events > 0


def sanitize_input(data):
    """Basic input sanitization"""
    if not isinstance(data, str):
        return str(data)
    
    # Remove potential XSS patterns
    dangerous_patterns = [
        '<script', '</script>', 'javascript:', 'onload=', 'onerror=',
        'onclick=', 'onmouseover=', 'onfocus=', 'onblur='
    ]
    
    cleaned = data
    for pattern in dangerous_patterns:
        cleaned = cleaned.replace(pattern.lower(), '')
        cleaned = cleaned.replace(pattern.upper(), '')
    
    return cleaned


class SecurityDecorator:
    """Decorator class for adding security logging to views"""
    
    def __init__(self, action, severity='low'):
        self.action = action
        self.severity = severity
    
    def __call__(self, func):
        def wrapper(request, *args, **kwargs):
            # Execute the view
            response = func(request, *args, **kwargs)
            
            # Log the action if user is authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                log_audit_action(
                    user=request.user,
                    action=self.action,
                    description=f"User accessed {func.__name__}",
                    severity=self.severity,
                    request=request
                )
            
            return response
        return wrapper


# Convenience decorator functions
def audit_action(action, severity='low'):
    """Decorator to automatically log audit actions"""
    return SecurityDecorator(action, severity)


def log_view_access(func):
    """Decorator to log view access"""
    return audit_action('view', 'low')(func)


def log_data_modification(func):
    """Decorator to log data modification actions"""
    return audit_action('update', 'medium')(func)
