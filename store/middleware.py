"""
Security middleware for the EYTGaming Store.

This module implements rate limiting and other security features
to protect the store from abuse and attacks.
"""

import logging
from django.core.cache import cache
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger('security')


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent abuse and DDoS attacks.
    
    Implements different rate limits for different endpoints:
    - Checkout endpoints: 10 requests per minute per IP
    - General endpoints: 100 requests per minute per IP
    
    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = cache
        
    def __call__(self, request):
        # Check if rate limiting is enabled
        if not getattr(settings, 'RATE_LIMIT_ENABLED', True):
            return self.get_response(request)
        
        # Check if request should be rate limited
        if self.is_rate_limited(request):
            logger.warning(
                f'Rate limit exceeded for {request.META.get("REMOTE_ADDR")} on {request.path}',
                extra={
                    'event_type': 'rate_limit_violation',
                    'ip': request.META.get('REMOTE_ADDR'),
                    'path': request.path,
                    'method': request.method
                }
            )
            return HttpResponse(
                'Too Many Requests. Please try again later.',
                status=429,
                headers={'Retry-After': '60'}
            )
        
        return self.get_response(request)
    
    def is_rate_limited(self, request):
        """
        Check if the request exceeds the rate limit.
        
        Args:
            request: The HTTP request object
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        # Get client IP address
        ip_address = self.get_client_ip(request)
        
        # Determine rate limit based on path
        limit = self.get_limit(request.path)
        
        # Create cache key
        cache_key = f'rate_limit:{ip_address}:{request.path}'
        
        # Get current count
        count = self.cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if count >= limit:
            return True
        
        # Increment count with 60 second timeout
        self.cache.set(cache_key, count + 1, timeout=60)
        
        return False
    
    def get_limit(self, path):
        """
        Get the rate limit for a specific path.
        
        Args:
            path: The request path
            
        Returns:
            int: The rate limit (requests per minute)
        """
        # Stricter limits for checkout endpoints
        if '/store/checkout/' in path or '/store/payment/' in path:
            return 10
        
        # Default limit for other endpoints
        return 100
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        
        Handles proxy headers like X-Forwarded-For.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: The client's IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Get the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
