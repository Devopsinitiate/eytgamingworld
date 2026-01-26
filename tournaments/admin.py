from django.contrib import admin
from .models import Tournament, Participant, Match, Bracket, MatchDispute, Payment, WebhookEvent
import json





# Tournament, Participant, Match, Bracket and MatchDispute are registered elsewhere; avoid double registration
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import Tournament, Participant, Bracket, Match, MatchDispute, Payment


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    fields = ['user', 'team', 'status', 'checked_in', 'seed', 'final_placement']
    readonly_fields = ['registered_at']
    raw_id_fields = ['user', 'team']


class MatchInline(admin.TabularInline):
    model = Match
    extra = 0
    fields = ['round_number', 'match_number', 'participant1', 'participant2', 
              'score_p1', 'score_p2', 'winner', 'status']
    # Remove readonly_fields to allow editing round_number and match_number when creating matches
    raw_id_fields = ['participant1', 'participant2', 'winner']


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'format', 'status_badge', 'participant_count',
                    'start_datetime', 'organizer', 'is_public']
    list_filter = ['status', 'format', 'tournament_type', 'game', 'is_public', 
                   'is_featured', 'start_datetime']
    search_fields = ['name', 'description', 'organizer__username', 'organizer__email']
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at', 'total_registered', 
                       'total_checked_in', 'view_count', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'rules', 'game')
        }),
        ('Tournament Configuration', {
            'fields': ('format', 'tournament_type', 'status', 'organizer', 'venue')
        }),
        ('Participants', {
            'fields': ('is_team_based', 'min_participants', 'max_participants', 
                      'team_size', 'total_registered', 'total_checked_in')
        }),
        ('Registration', {
            'fields': ('registration_start', 'registration_end', 'requires_approval',
                      'registration_fee')
        }),
        ('Schedule', {
            'fields': ('check_in_start', 'start_datetime', 'estimated_end', 'actual_end')
        }),
        ('Prizes', {
            'fields': ('prize_pool', 'prize_distribution')
        }),
        ('Bracket Settings', {
            'fields': ('seeding_method', 'best_of'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('banner', 'thumbnail')
        }),
        ('Visibility & Access', {
            'fields': ('is_public', 'is_featured', 'requires_verification', 
                      'skill_requirement')
        }),
        ('Social', {
            'fields': ('stream_url', 'discord_invite'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'published_at', 'view_count'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ParticipantInline]
    
    actions = ['publish_tournaments', 'start_tournaments', 'complete_tournaments',
               'feature_tournaments']
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'registration': 'blue',
            'check_in': 'orange',
            'in_progress': 'green',
            'completed': 'purple',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def participant_count(self, obj):
        return f"{obj.total_registered}/{obj.max_participants}"
    participant_count.short_description = 'Participants'
    
    def publish_tournaments(self, request, queryset):
        updated = queryset.filter(status='draft').update(
            status='registration',
            published_at=timezone.now()
        )
        self.message_user(request, f'{updated} tournaments published.')
    publish_tournaments.short_description = 'Publish selected tournaments'
    
    def start_tournaments(self, request, queryset):
        count = 0
        for tournament in queryset.filter(status='check_in'):
            if tournament.start_tournament():
                count += 1
        self.message_user(request, f'{count} tournaments started.')
    start_tournaments.short_description = 'Start selected tournaments'
    
    def complete_tournaments(self, request, queryset):
        updated = queryset.filter(status='in_progress').update(
            status='completed',
            actual_end=timezone.now()
        )
        self.message_user(request, f'{updated} tournaments completed.')
    complete_tournaments.short_description = 'Complete selected tournaments'
    
    def feature_tournaments(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} tournaments featured.')
    feature_tournaments.short_description = 'Feature selected tournaments'


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'tournament', 'status', 'seed', 'checked_in',
                    'match_record', 'final_placement']
    list_filter = ['status', 'checked_in', 'tournament__game', 'registered_at']
    search_fields = ['user__username', 'user__email', 'team__name', 
                     'tournament__name']
    raw_id_fields = ['tournament', 'user', 'team']
    
    fieldsets = (
        ('Participant Info', {
            'fields': ('tournament', 'user', 'team', 'status', 'seed')
        }),
        ('Check-in', {
            'fields': ('checked_in', 'check_in_time')
        }),
        ('Statistics', {
            'fields': ('matches_won', 'matches_lost', 'games_won', 'games_lost')
        }),
        ('Results', {
            'fields': ('final_placement', 'prize_won')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['registered_at', 'check_in_time']
    
    actions = ['check_in_participants', 'confirm_participants', 'disqualify_participants']
    
    def match_record(self, obj):
        return f"{obj.matches_won}W - {obj.matches_lost}L ({obj.win_rate}%)"
    match_record.short_description = 'Record'
    
    def check_in_participants(self, request, queryset):
        count = 0
        for participant in queryset:
            if participant.check_in_participant():
                count += 1
        self.message_user(request, f'{count} participants checked in.')
    check_in_participants.short_description = 'Check in selected participants'
    
    def confirm_participants(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} participants confirmed.')
    confirm_participants.short_description = 'Confirm selected participants'
    
    def disqualify_participants(self, request, queryset):
        updated = queryset.update(status='disqualified')
        self.message_user(request, f'{updated} participants disqualified.')
    disqualify_participants.short_description = 'Disqualify selected participants'


@admin.register(Bracket)
class BracketAdmin(admin.ModelAdmin):
    list_display = ['name', 'tournament', 'bracket_type', 'progress', 'completed']
    list_filter = ['bracket_type', 'completed', 'tournament__game']
    search_fields = ['name', 'tournament__name']
    raw_id_fields = ['tournament']
    
    readonly_fields = ['created_at', 'completed_at']
    inlines = [MatchInline]
    
    def progress(self, obj):
        return f"Round {obj.current_round}/{obj.total_rounds}"
    progress.short_description = 'Progress'
    
    def save_formset(self, request, form, formset, change):
        """
        Override to automatically set tournament on inline matches.
        
        When creating matches inline with a bracket, the Match model requires
        both bracket AND tournament foreign keys. This method automatically
        sets the tournament from the bracket's tournament.
        """
        instances = formset.save(commit=False)
        bracket = form.instance
        
        for instance in instances:
            # Set tournament from the bracket if not already set
            if isinstance(instance, Match) and not instance.tournament_id:
                instance.tournament = bracket.tournament
            instance.save()
        
        formset.save_m2m()


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['match_id', 'tournament', 'round_number', 'match_number',
                    'matchup', 'score', 'status_badge', 'scheduled_time']
    list_filter = ['status', 'tournament', 'bracket__bracket_type', 'round_number']
    search_fields = ['tournament__name', 'participant1__user__username',
                     'participant2__user__username']
    raw_id_fields = ['tournament', 'bracket', 'participant1', 'participant2',
                     'winner', 'loser', 'next_match_winner', 'next_match_loser']
    
    fieldsets = (
        ('Match Information', {
            'fields': ('tournament', 'bracket', 'round_number', 'match_number')
        }),
        ('Participants', {
            'fields': ('participant1', 'participant2')
        }),
        ('Results', {
            'fields': ('score_p1', 'score_p2', 'winner', 'loser')
        }),
        ('Bracket Progression', {
            'fields': ('next_match_winner', 'next_match_loser'),
            'classes': ('collapse',)
        }),
        ('Status & Schedule', {
            'fields': ('status', 'scheduled_time', 'started_at', 'completed_at')
        }),
        ('Special', {
            'fields': ('is_grand_finals', 'bracket_reset', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['started_at', 'completed_at']
    
    actions = ['mark_ready', 'mark_completed']
    
    def match_id(self, obj):
        return f"R{obj.round_number}M{obj.match_number}"
    match_id.short_description = 'Match ID'
    
    def matchup(self, obj):
        p1 = obj.participant1.display_name if obj.participant1 else "TBD"
        p2 = obj.participant2.display_name if obj.participant2 else "TBD"
        return f"{p1} vs {p2}"
    matchup.short_description = 'Matchup'
    
    def score(self, obj):
        if obj.status == 'completed':
            return f"{obj.score_p1} - {obj.score_p2}"
        return "-"
    score.short_description = 'Score'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'ready': 'blue',
            'in_progress': 'orange',
            'completed': 'green',
            'disputed': 'red',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def mark_ready(self, request, queryset):
        updated = queryset.filter(participant1__isnull=False, 
                                  participant2__isnull=False).update(status='ready')
        self.message_user(request, f'{updated} matches marked as ready.')
    mark_ready.short_description = 'Mark selected matches as ready'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} matches marked as completed.')
    mark_completed.short_description = 'Mark selected matches as completed'


@admin.register(MatchDispute)
class MatchDisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'match', 'reporter', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['match__tournament__name', 'reporter__username', 'reason']
    raw_id_fields = ['match', 'reporter', 'resolved_by']
    
    fieldsets = (
        ('Dispute Information', {
            'fields': ('match', 'reporter', 'reason', 'evidence')
        }),
        ('Resolution', {
            'fields': ('status', 'admin_notes', 'resolution', 'resolved_by', 
                      'resolved_at')
        }),
    )
    
    readonly_fields = ['created_at', 'resolved_at']
    
    actions = ['resolve_disputes', 'dismiss_disputes']
    
    def resolve_disputes(self, request, queryset):
        updated = queryset.update(
            status='resolved',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} disputes resolved.')
    resolve_disputes.short_description = 'Resolve selected disputes'
    
    def dismiss_disputes(self, request, queryset):
        updated = queryset.update(
            status='dismissed',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(request, f'{updated} disputes dismissed.')
    dismiss_disputes.short_description = 'Dismiss selected disputes'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant', 'amount', 'provider', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    search_fields = ('participant__user__email', 'provider_transaction_id')
    readonly_fields = ('metadata_pretty',)

    def metadata_pretty(self, obj):
        try:
            return format_html('<pre style="max-width:800px; white-space:pre-wrap">{}</pre>', json.dumps(obj.metadata or {}, indent=2))
        except Exception:
            return str(obj.metadata)
    metadata_pretty.short_description = 'metadata'


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'received_at')
    readonly_fields = ('id', 'provider', 'payload_pretty', 'received_at')
    search_fields = ('id',)
    list_filter = ('provider',)

    def payload_pretty(self, obj):
        try:
            pretty = json.dumps(obj.payload or {}, indent=2)
            return format_html('<pre style="max-width:900px; white-space:pre-wrap">{}</pre>', pretty)
        except Exception:
            return str(obj.payload)

    payload_pretty.short_description = 'payload'