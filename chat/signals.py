from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Message, ConversationParticipant

User = get_user_model()


@receiver(post_save, sender=Message)
def notify_recipient_on_message(sender, instance, created, **kwargs):
    if not created:
        return
    participants = ConversationParticipant.objects.filter(
        conversation=instance.conversation
    ).exclude(user=instance.sender).select_related('user')

    for membership in participants:
        recipient = membership.user
        if recipient.is_online:
            continue
        try:
            from notifications.models import Notification
            Notification.create_notification(
                user=recipient,
                title=f"New message from {instance.sender.get_display_name()}",
                message=instance.content[:200],
                notification_type='message',
                priority='normal',
                action_url=f"/dashboard/inbox?conv={instance.conversation.id}",
                content_object=instance,
            )
        except Exception:
            pass
