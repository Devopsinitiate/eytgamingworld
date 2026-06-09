from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals  # noqa: F401

        # OTPMiddleware._init_user_fields overwrites user.is_verified with a
        # functools.partial (the OTP verification check), shadowing the email
        # verification BooleanField. Patch it to preserve the original value.
        from django_otp.middleware import OTPMiddleware

        original_init = OTPMiddleware._init_user_fields

        @staticmethod
        def _patched_init_user_fields(user):
            # Django's AuthenticationMiddleware wraps request.user in a
            # SimpleLazyObject.  Accessing .is_authenticated forces resolution
            # of the wrapped user, but _init_user_fields receives the
            # SimpleLazyObject wrapper itself, not the underlying model
            # instance.  Retrieve the real user so we can inspect __dict__.
            real_user = user._wrapped if hasattr(user, '_wrapped') else user
            if real_user is None and hasattr(user, '_setupfunc'):
                # Force resolution
                _ = user.is_authenticated
                real_user = user._wrapped
            if real_user is None:
                return original_init(user)

            original = real_user.__dict__.get('is_verified', False)
            if not isinstance(original, bool):
                original = False
            original_init(user)
            # Restore onto the real user's __dict__ (the wrapper forwards
            # attribute writes, so user.is_verified will reflect this).
            real_user.__dict__['is_verified'] = original

        OTPMiddleware._init_user_fields = _patched_init_user_fields
