from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.contrib.sitemaps.views import sitemap
from django.middleware.csrf import get_token
from core.views import LandingPageView
from core.sitemaps import sitemaps
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from api.views import complete_onboarding, onboarding_status
from accounts.auth_views import (
    RateLimitedLoginView,
    RateLimitedSignupView,
    RateLimitedPasswordResetView,
    RateLimitedPasswordResetConfirmView,
)
import os

# django-two-factor-auth defines urlpatterns as a tuple (patterns, 'two_factor')
# at module level instead of a plain list. Extract the patterns list for include().
from two_factor import urls as two_factor_urls
two_factor_patterns = (
    two_factor_urls.urlpatterns[0]
    if isinstance(two_factor_urls.urlpatterns, tuple)
    else two_factor_urls.urlpatterns
)

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

def security_txt(request):
    """Serve security.txt for vulnerability disclosure (RFC 9116)."""
    content = (
        "Contact: mailto:security@eytgaming.com\n"
        "Policy: https://eytgaming.com/security-policy\n"
        "Preferred-Languages: en\n"
        "Expires: 2027-05-31T00:00:00.000Z\n"
    )
    return HttpResponse(content, content_type='text/plain')


@ensure_csrf_cookie
def csrf_token_view(request):
    """Return a CSRF token for AJAX requests without reading the cookie."""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})


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
    path('.well-known/security.txt', security_txt, name='security_txt'),

    # Service Worker for performance optimization
    path('sw.js', service_worker, name='service_worker'),
    
    # CSRF token endpoint (for AJAX, no cookie reading needed)
    path('api/csrf-token/', csrf_token_view, name='csrf_token'),

    # Onboarding — status check and completion sync
    path('api/onboarding-status/', onboarding_status, name='onboarding_status'),
    path('api/complete-onboarding/', complete_onboarding, name='complete_onboarding'),

    # Two-Factor Authentication
    path('accounts/', include(two_factor_patterns)),

    # Rate-limited auth views (override allauth defaults for brute-force protection)
    path('accounts/login/', RateLimitedLoginView.as_view(), name='account_login'),
    path('accounts/signup/', RateLimitedSignupView.as_view(), name='account_signup'),
    path('accounts/password/reset/', RateLimitedPasswordResetView.as_view(), name='account_reset_password'),
    path(
        'accounts/password/reset/key/<uidb36>/<key>/',
        RateLimitedPasswordResetConfirmView.as_view(),
        name='account_reset_password_from_key',
    ),

    # Authentication (django-allauth) — remaining URLs
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
    
    # API documentation (OpenAPI / Swagger)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health checks (monitoring / k8s probes)
    path('health/', include('health.urls')),

    # API v1
    path('api/v1/', include('api.urls')),
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