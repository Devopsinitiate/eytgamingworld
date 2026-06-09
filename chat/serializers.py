from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, ConversationParticipant, Message

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar_url', 'is_online']

    def get_display_name(self, obj):
        return obj.get_display_name()

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = UserBriefSerializer(read_only=True)
    sender_id = serializers.UUIDField(write_only=True)
    read_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_id', 'content', 'created_at', 'is_edited', 'reply_to', 'read_by']
        read_only_fields = ['id', 'conversation', 'sender', 'created_at', 'is_edited', 'read_by']

    def get_read_by(self, obj):
        return [
            {'id': str(m.user.id), 'display_name': m.user.get_display_name()}
            for m in obj.conversation.membership_set.filter(
                last_read_at__gte=obj.created_at
            ).select_related('user')
        ]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'last_read_at', 'is_muted']


class ConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    participants = UserBriefSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'title', 'created_at', 'updated_at', 'participants', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {
                'id': str(msg.id),
                'content': msg.content[:100],
                'sender_name': msg.sender.get_display_name() if msg.sender else 'Unknown',
                'created_at': msg.created_at.isoformat(),
            }
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        try:
            membership = obj.membership_set.get(user=user)
            if membership.last_read_at:
                return obj.messages.filter(created_at__gt=membership.last_read_at).count()
        except ConversationParticipant.DoesNotExist:
            pass
        return obj.messages.count()


class ConversationDetailSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'title', 'created_at', 'updated_at', 'participants']
