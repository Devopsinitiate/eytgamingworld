"""
Signal handlers for account security:
- Invalidate all sessions on password change
- Auto-verify user when email is confirmed
"""
from allauth.account.signals import email_confirmed
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from core.models import User


@receiver(pre_save, sender=User)
def invalidate_sessions_on_password_change(sender, instance, **kwargs):
    """Delete all sessions for a user when password changes."""
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if old.password != instance.password:
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            data = session.get_decoded()
            if str(instance.pk) == data.get('_auth_user_id'):
                session.delete()


@receiver(email_confirmed)
def auto_verify_on_email_confirmed(request, email_address, **kwargs):
    """Set is_verified=True when user confirms their email via allauth."""
    user = email_address.user
    if not user.is_verified:
        user.is_verified = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=['is_verified', 'email_verified_at'])
