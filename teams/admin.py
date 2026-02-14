from django.contrib import admin
from django.utils.html import format_html
from .models import Team, TeamMember, TeamInvite


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 0
    fields = ['user', 'role', 'status', 'matches_played', 'matches_won', 'joined_at']
    readonly_fields = ['joined_at']
    raw_id_fields = ['user']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'tag', 'game', 'captain', 'member_count_display', 
                    'status_badge', 'win_rate_display', 'is_recruiting']
    list_filter = ['status', 'game', 'is_recruiting', 'is_public', 'created_at']
    search_fields = ['name', 'tag', 'description', 'captain__username']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['captain', 'game']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'tag', 'description')
        }),
        ('Configuration', {
            'fields': ('game', 'captain', 'status', 'max_members')
        }),
        ('Media', {
            'fields': ('logo', 'banner')
        }),
        ('Settings', {
            'fields': ('is_public', 'is_recruiting', 'requires_approval')
        }),
        ('Social Links', {
            'fields': ('discord_server', 'twitter_url', 'twitch_url'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('tournaments_played', 'tournaments_won', 'total_wins', 'total_losses'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TeamMemberInline]
    
    actions = ['activate_teams', 'deactivate_teams', 'disband_teams']
    
    def member_count_display(self, obj):
        return f"{obj.member_count}/{obj.max_members}"
    member_count_display.short_description = 'Members'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'orange',
            'disbanded': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def win_rate_display(self, obj):
        win_rate = float(obj.win_rate)  # Ensure it's a float
        
        if win_rate >= 50:
            color = 'green'
        elif win_rate >= 30:
            color = 'orange'
        else:
            color = 'red'
        
        # Use string formatting instead of f-string in format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f'{win_rate:.1f}%'
        )
    win_rate_display.short_description = 'Win Rate'
    
    def activate_teams(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} teams activated.')
    activate_teams.short_description = 'Activate selected teams'
    
    def deactivate_teams(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} teams deactivated.')
    deactivate_teams.short_description = 'Deactivate selected teams'
    
    def disband_teams(self, request, queryset):
        updated = queryset.update(status='disbanded')
        self.message_user(request, f'{updated} teams disbanded.')
    disband_teams.short_description = 'Disband selected teams'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'status', 'match_record', 'joined_at']
    list_filter = ['role', 'status', 'team__game', 'joined_at']
    search_fields = ['user__username', 'user__email', 'team__name']
    raw_id_fields = ['team', 'user']
    
    fieldsets = (
        ('Membership', {
            'fields': ('team', 'user', 'role', 'status')
        }),
        ('Statistics', {
            'fields': ('matches_played', 'matches_won')
        }),
        ('Dates', {
            'fields': ('joined_at', 'approved_at', 'left_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['joined_at']
    
    actions = ['approve_members', 'promote_to_captain', 'remove_members']
    
    def match_record(self, obj):
        if obj.matches_played == 0:
            return "No matches"
        win_rate = (obj.matches_won / obj.matches_played) * 100
        return f"{obj.matches_won}W - {obj.matches_played - obj.matches_won}L ({win_rate:.1f}%)"
    match_record.short_description = 'Record'
    
    def approve_members(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='active', approved_at=timezone.now())
        self.message_user(request, f'{updated} members approved.')
    approve_members.short_description = 'Approve selected members'
    
    def promote_to_captain(self, request, queryset):
        for member in queryset:
            # Demote current captain to member
            TeamMember.objects.filter(
                team=member.team, role='captain'
            ).update(role='member')
            
            # Promote this member
            member.role = 'captain'
            member.save()
            
            # Update team captain
            member.team.captain = member.user
            member.team.save()
        
        self.message_user(request, f'{queryset.count()} members promoted to captain.')
    promote_to_captain.short_description = 'Promote to Captain'
    
    def remove_members(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='removed', left_at=timezone.now())
        self.message_user(request, f'{updated} members removed.')
    remove_members.short_description = 'Remove selected members'


@admin.register(TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ['team', 'invited_user', 'invited_by', 'status', 'created_at', 'expires_at']
    list_filter = ['status', 'created_at']
    search_fields = ['team__name', 'invited_user__username', 'invited_by__username']
    raw_id_fields = ['team', 'invited_by', 'invited_user']
    
    fieldsets = (
        ('Invitation', {
            'fields': ('team', 'invited_by', 'invited_user', 'message')
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'expires_at', 'responded_at')
        }),
    )
    
    readonly_fields = ['created_at', 'responded_at']
    
    actions = ['expire_invites']
    
    def expire_invites(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'{updated} invites expired.')
    expire_invites.short_description = 'Expire selected invites'