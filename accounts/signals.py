"""
Signal handlers for account security:
- Invalidate all sessions on password change
"""
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
