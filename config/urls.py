from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.contrib.sitemaps.views import sitemap
from core.views import LandingPageView
from core.sitemaps import sitemaps
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

def robots_txt(request):
    """Serve robots.txt dynamically so we can gate crawlers in DEBUG mode."""
    if settings.DEBUG:
        content = "User-agent: *\nDisallow: /\n"
    else:
        content = (
            "User-agent: *\n"
            "Disallow: /admin/\n"
            "Disallow: /accounts/\n"
            "Disallow: /dashboard/\n"
            "Disallow: /payments/\n"
            "Disallow: /notifications/\n"
            "Disallow: /store/cart/\n"
            "Disallow: /store/checkout/\n"
            "Disallow: /store/wishlist/\n"
            f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}\n"
        )
    return HttpResponse(content, content_type='text/plain')


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # About page - public, no auth required
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),

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