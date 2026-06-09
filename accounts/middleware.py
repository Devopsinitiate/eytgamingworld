"""
Middleware to enforce two-factor authentication for admin/organizer roles.

Enforcement layers:
1. Sensitive paths (profile, payments, create/edit): hard block → 2FA setup
2. Non-sensitive paths with grace period: show nag banner, allow navigation
3. Session-scoped dismiss: user can dismiss nag for current session
4. Grace period (7 days): after expiry, all paths become hard block
"""
from datetime import timedelta
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.utils import timezone
from django.conf import settings
from django.db.utils import ProgrammingError, OperationalError


class TwoFactorMiddleware:
    """
    Enforce 2FA for admin/organizer users with layered strictness.
    Sensitive actions blocked immediately; nag shown on general pages
    during a 7-day grace period.
    """

    ENFORCED_ROLES = {'admin', 'organizer'}
    GRACE_DAYS = 7

    # Path prefixes NEVER blocked (auth, static, api, etc.)
    EXEMPT_PATHS = {
        '/accounts/',
        '/profile/2fa/',
        '/api/',
        '/static/',
        '/media/',
        '/admin/login/',
        '/admin/logout/',
    }

    # URL names NEVER blocked
    EXEMPT_NAMES = {
        'accounts:two_factor_setup',
        'accounts:two_factor_verify',
        'accounts:two_factor_dismiss',
        'account_login',
        'account_logout',
        'account_reset_password',
        'account_reset_password_from_key',
        'account_signup',
        'home',
        'about',
        'privacy',
        'terms',
        'robots_txt',
        'security_txt',
    }

    # Path prefixes ALWAYS blocked until 2FA is set up (regardless of grace/dismiss)
    SENSITIVE_PATHS = {
        '/profile/',
        '/payments/',
        '/store/checkout/',
        '/dashboard/profile/',
        '/dashboard/settings/',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.role not in self.ENFORCED_ROLES:
            return self.get_response(request)

        # Check if user already has TOTP configured
        if self._has_totp(request.user):
            return self.get_response(request)

        path = request.path

        # 1. Check exempt URL names
        try:
            match = resolve(path)
            if match.url_name:
                namespaced = f'{match.namespace}:{match.url_name}' if match.namespace else match.url_name
                if namespaced in self.EXEMPT_NAMES:
                    return self.get_response(request)
        except Exception:
            pass

        # 2. Check exempt path prefixes
        if any(path.startswith(p) for p in self.EXEMPT_PATHS):
            return self.get_response(request)

        # 3. Sensitive paths — hard block regardless of grace/dismiss
        if any(path.startswith(p) for p in self.SENSITIVE_PATHS):
            return redirect(reverse('accounts:two_factor_setup'))

        # 4. Start grace period on first detection
        if request.user.two_factor_grace_started_at is None:
            request.user.two_factor_grace_started_at = timezone.now()
            request.user.save(update_fields=['two_factor_grace_started_at'])

        # 5. Check if grace period expired
        grace_end = request.user.two_factor_grace_started_at + timedelta(days=self.GRACE_DAYS)
        if timezone.now() >= grace_end:
            return redirect(reverse('accounts:two_factor_setup'))

        # 6. Within grace period — check session dismiss
        if request.session.get('two_factor_nag_dismissed'):
            return self.get_response(request)

        # 7. Set request flag so context processor shows nag banner
        request.two_factor_needs_setup = True
        return self.get_response(request)

    def _has_totp(self, user):
        from django_otp.plugins.otp_totp.models import TOTPDevice
        try:
            return TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        except (ProgrammingError, OperationalError):
            return False
