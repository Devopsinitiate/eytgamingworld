"""Context processors for the accounts app."""
from django.conf import settings


def two_factor_status(request):
    """Provide 2FA setup status for the nag banner in base.html."""
    ctx = {}
    if getattr(request, 'two_factor_needs_setup', False):
        ctx.update({
            'requires_2fa': True,
            'two_factor_dismissed': request.session.get('two_factor_nag_dismissed', False),
        })
    return ctx
