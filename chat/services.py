from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, ConversationParticipant, Message

User = get_user_model()


def create_conversation(user_a, user_b):
    existing = Conversation.objects.filter(
        type='direct',
        membership_set__user=user_a,
    ).filter(
        membership_set__user=user_b,
        type='direct',
    ).first()
    if existing:
        return existing, False

    conv = Conversation.objects.create(type='direct')
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conv, user=user_a),
        ConversationParticipant(conversation=conv, user=user_b),
    ])
    return conv, True


def create_group_conversation(creator, user_ids, title=''):
    users = list(User.objects.filter(id__in=user_ids, is_active=True))
    if not users:
        return None, False
    if creator not in users:
        users.insert(0, creator)
    conv = Conversation.objects.create(type='group', title=title or 'Group')
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conv, user=u) for u in users
    ])
    return conv, True


def send_message(conversation, sender, content):
    msg = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=content,
    )
    conversation.save(update_fields=['updated_at'])
    return msg


def mark_as_read(conversation, user):
    ConversationParticipant.objects.filter(
        conversation=conversation, user=user
    ).update(last_read_at=timezone.now())


def get_read_by(message):
    """Return list of users who have read up to (or past) this message."""
    return [
        (m.user.id, m.user.get_display_name())
        for m in message.conversation.membership_set.filter(
            last_read_at__gte=message.created_at
        ).select_related('user')
    ]
