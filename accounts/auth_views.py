"""
Rate-limited wrappers around django-allauth authentication views.
"""
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from allauth.account import views as allauth_views


LOGIN_RATE = '10/m'
AUTH_RATE = '5/m'


class RateLimitedLoginView(allauth_views.LoginView):
    @method_decorator(ratelimit(key='ip', rate=LOGIN_RATE, method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class RateLimitedSignupView(allauth_views.SignupView):
    @method_decorator(ratelimit(key='ip', rate=AUTH_RATE, method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class RateLimitedPasswordResetView(allauth_views.PasswordResetView):
    @method_decorator(ratelimit(key='ip', rate=AUTH_RATE, method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class RateLimitedPasswordResetConfirmView(allauth_views.PasswordResetFromKeyView):
    @method_decorator(ratelimit(key='ip', rate=AUTH_RATE, method='POST', block=True))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
