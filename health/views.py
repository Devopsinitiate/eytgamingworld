"""
Health check endpoints for monitoring and load balancers.
"""
import time
from django.db import connection, DatabaseError
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache


def health_check(request):
    return JsonResponse({'status': 'healthy', 'timestamp': time.time()})


def health_db(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'healthy', 'database': 'connected'})
    except DatabaseError as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)


def health_cache(request):
    try:
        cache.set('__health_check__', 'ok', timeout=5)
        val = cache.get('__health_check__')
        if val == 'ok':
            return JsonResponse({'status': 'healthy', 'cache': 'connected'})
        return JsonResponse({'status': 'degraded', 'cache': 'write_failed'}, status=503)
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)


def health_redis(request):
    """More detailed Redis health check."""
    cache_key = '__health_redis__'
    try:
        cache.set(cache_key, 'ping', timeout=5)
        val = cache.get(cache_key)
        return JsonResponse({
            'status': 'healthy' if val == 'ping' else 'mismatch',
            'cache': 'connected' if val == 'ping' else 'read_mismatch',
            'backend': settings.CACHES.get('default', {}).get('BACKEND', 'unknown'),
        })
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)


def health_ready(request):
    """Readiness probe - is the app ready to serve traffic?"""
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'ready', 'database': 'connected'})
    except DatabaseError:
        return JsonResponse({'status': 'not_ready', 'database': 'disconnected'}, status=503)


def health_live(request):
    """Liveness probe - is the app process alive?"""
    return JsonResponse({'status': 'alive'})
