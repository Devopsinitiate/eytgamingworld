"""
Prometheus metrics exporter for EYTGaming.

Exposes application metrics in Prometheus text format for scraping.
"""
import time
import functools
from django.db import connection, OperationalError
from django.http import HttpResponse
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count


def prometheus_metrics(request):
    """Generate Prometheus-formatted metrics text."""
    lines = []
    
    # Help and type headers
    lines.append('# HELP eyt_gaming_info Static information about EYTGaming')
    lines.append('# TYPE eyt_gaming_info gauge')
    lines.append(f'eyt_gaming_info{{version="1.0.0",environment="{"production" if not settings.DEBUG else "development"}"}} 1')
    
    # Database connection status
    lines.append('# HELP eyt_db_up Database connection status (1=up, 0=down)')
    lines.append('# TYPE eyt_db_up gauge')
    try:
        connection.ensure_connection()
        lines.append('eyt_db_up 1')
    except OperationalError:
        lines.append('eyt_db_up 0')
    
    # Cache status
    lines.append('# HELP eyt_cache_up Cache connection status (1=up, 0=down)')
    lines.append('# TYPE eyt_cache_up gauge')
    try:
        cache.set('__prom_health__', 1, timeout=5)
        lines.append('eyt_cache_up 1')
    except Exception:
        lines.append('eyt_cache_up 0')
    
    # App model counts
    lines.append('# HELP eyt_users_total Total number of users')
    lines.append('# TYPE eyt_users_total gauge')
    from core.models import User
    lines.append(f'eyt_users_total {User.objects.filter(is_active=True).count()}')
    
    lines.append('# HELP eyt_tournaments_total Total number of tournaments')
    lines.append('# TYPE eyt_tournaments_total gauge')
    from tournaments.models import Tournament
    lines.append(f'eyt_tournaments_total {Tournament.objects.count()}')
    
    lines.append('# HELP eyt_coaches_total Total number of active coaches')
    lines.append('# TYPE eyt_coaches_total gauge')
    from coaching.models import CoachProfile
    lines.append(f'eyt_coaches_total {CoachProfile.objects.filter(status="active").count()}')
    
    lines.append('# HELP eyt_sessions_total Total number of coaching sessions')
    lines.append('# TYPE eyt_sessions_total gauge')
    from coaching.models import CoachingSession
    lines.append(f'eyt_sessions_total {CoachingSession.objects.count()}')
    
    lines.append('# HELP eyt_payments_total Total number of payments')
    lines.append('# TYPE eyt_payments_total gauge')
    from payments.models import Payment
    lines.append(f'eyt_payments_total {Payment.objects.count()}')
    
    lines.append('# HELP eyt_notifications_total Total number of notifications sent')
    lines.append('# TYPE eyt_notifications_total gauge')
    from notifications.models import Notification
    lines.append(f'eyt_notifications_total {Notification.objects.count()}')
    
    return HttpResponse('\n'.join(lines) + '\n', content_type='text/plain; charset=utf-8')
