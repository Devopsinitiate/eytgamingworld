from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from core.views import LandingPageView
import os

# Service Worker view for performance optimization
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    """Serve the service worker with proper headers for performance optimization"""
    sw_path = os.path.join(settings.STATIC_ROOT or settings.STATICFILES_DIRS[0], 'sw.js')
    try:
        with open(sw_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// Service worker not found', content_type='application/javascript', status=404)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Service Worker for performance optimization
    path('sw.js', service_worker, name='service_worker'),
    
    # Authentication (django-allauth)
    path('accounts/', include('allauth.urls')),
    
    # Core app URLs
    path('', include('core.urls')),
    path('', LandingPageView.as_view(), name='home'),
    
    # App URLs (will be created)
    path('dashboard/', include('dashboard.urls')),
    path('tournaments/', include('tournaments.urls')),
    path('teams/', include('teams.urls')),
    path('coaching/', include('coaching.urls')),
    path('venues/', include('venues.urls')),
    path('profile/', include('accounts.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('store/', include('store.urls')),
    
    # API endpoints (future)
    # path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    
    # Browser reload for development
    if 'django_browser_reload' in settings.INSTALLED_APPS:
        urlpatterns += [
            path('__reload__/', include('django_browser_reload.urls')),
        ]

# Customize admin site
admin.site.site_header = 'EYTGaming Administration'
admin.site.site_title = 'EYTGaming Admin'
admin.site.index_title = 'Dashboard'