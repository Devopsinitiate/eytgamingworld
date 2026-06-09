from django.contrib import admin
from .models import Conversation, ConversationParticipant, Message


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0
    readonly_fields = ['user', 'last_read_at', 'is_muted']
    can_delete = False
    verbose_name = "Participant"
    verbose_name_plural = "Participants"


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'content', 'created_at', 'is_edited']
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'title', 'created_at', 'updated_at']
    list_filter = ['type', 'created_at']
    search_fields = ['title']
    inlines = [ConversationParticipantInline, MessageInline]
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'created_at', 'is_edited']
    list_filter = ['is_edited', 'created_at']
    search_fields = ['content']
    date_hierarchy = 'created_at'
    readonly_fields = ['sender', 'reply_to']
