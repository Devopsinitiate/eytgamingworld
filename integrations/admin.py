from django.contrib import admin
from django.utils.html import format_html
from .models import ExternalProvider, ExternalTournament, ExternalPlayer, ExternalMatch, SyncLog


@admin.register(ExternalProvider)
class ExternalProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'rate_limit_per_min', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    fieldsets = (
        (None, {'fields': ('name', 'base_url', 'api_key', 'is_active', 'rate_limit_per_min')}),
    )


@admin.register(ExternalTournament)
class ExternalTournamentAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'game', 'status', 'start_date', 'local_tournament_link', 'bracket_status']
    list_filter = ['provider', 'status', 'game']
    search_fields = ['title', 'external_id']
    date_hierarchy = 'start_date'
    actions = ['sync_tournament', 'import_bracket']
    readonly_fields = ['local_tournament']

    def bracket_status(self, obj):
        if not obj.local_tournament:
            return "-"
        has_brackets = obj.local_tournament.brackets.exists()
        if has_brackets:
            return format_html('<span style="color:#10B981;">&#10003; Imported</span>')
        return format_html('<span style="color:#6B7280;">Not imported</span>')
    bracket_status.short_description = "Bracket"

    def local_tournament_link(self, obj):
        if obj.local_tournament:
            return f"{obj.local_tournament.title} ({obj.local_tournament.status})"
        return "-"
    local_tournament_link.short_description = "Local Tournament"

    def sync_tournament(self, request, queryset):
        from .tasks import sync_tournament_from_startgg
        for obj in queryset:
            sync_tournament_from_startgg.delay(obj.id)
        self.message_user(request, f"Syncing {queryset.count()} tournament(s)")
    sync_tournament.short_description = "Sync selected with start.gg"

    def import_bracket(self, request, queryset):
        from .services.bracket_import import build_bracket_from_external_matches
        total = 0
        skipped = 0
        for obj in queryset:
            if not obj.local_tournament:
                skipped += 1
                continue
            bracket, count = build_bracket_from_external_matches(obj)
            if bracket:
                total += count
            else:
                skipped += 1
        msg = f"Imported {total} matches into bracket(s)"
        if skipped:
            msg += f" ({skipped} skipped — no local tournament or already imported)"
        self.message_user(request, msg)
    import_bracket.short_description = "Import bracket from External Matches"


@admin.register(ExternalPlayer)
class ExternalPlayerAdmin(admin.ModelAdmin):
    list_display = ['username', 'provider', 'game', 'local_user_link']
    list_filter = ['provider', 'game']
    search_fields = ['username', 'external_id']
    readonly_fields = ['local_user']

    def local_user_link(self, obj):
        if obj.local_user:
            return obj.local_user.get_display_name()
        return "-"
    local_user_link.short_description = "Local User"


@admin.register(ExternalMatch)
class ExternalMatchAdmin(admin.ModelAdmin):
    list_display = ['external_id', 'tournament', 'round', 'status', 'scheduled_at']
    list_filter = ['provider', 'status']
    search_fields = ['external_id']


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'provider', 'status', 'started_at', 'completed_at', 'items_processed']
    list_filter = ['provider', 'sync_type', 'status']
    date_hierarchy = 'started_at'
