from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Game, UserGameProfile, SiteSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    
    list_display = ['email', 'username', 'get_display_name', 'role', 'level', 
                    'total_points', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_verified', 'is_minor', 'skill_level', 'date_joined']
    search_fields = ['email', 'username', 'display_name', 'first_name', 'last_name', 
                     'discord_username', 'steam_id']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'display_name', 'avatar', 'bio',
                      'date_of_birth', 'phone_number')
        }),
        ('Gaming Profiles', {
            'fields': ('discord_username', 'steam_id', 'twitch_username')
        }),
        ('Role & Status', {
            'fields': ('role', 'skill_level', 'is_active', 'is_verified', 'is_staff', 
                      'is_superuser', 'is_minor')
        }),
        ('Location', {
            'fields': ('country', 'city', 'timezone')
        }),
        ('Parental Info', {
            'fields': ('parent_email', 'parental_consent'),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': ('total_points', 'level')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'push_notifications', 'private_profile')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login')
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'level']
    
    actions = ['verify_users', 'deactivate_users', 'make_coaches', 'make_organizers']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = 'Verify selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def make_coaches(self, request, queryset):
        updated = queryset.update(role='coach')
        self.message_user(request, f'{updated} users promoted to Coach.')
    make_coaches.short_description = 'Make selected users Coaches'
    
    def make_organizers(self, request, queryset):
        updated = queryset.update(role='organizer')
        self.message_user(request, f'{updated} users promoted to Organizer.')
    make_organizers.short_description = 'Make selected users Organizers'


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Game admin"""
    
    list_display = ['name', 'genre', 'supports_teams', 'team_size_range', 
                    'is_active', 'created_at']
    list_filter = ['genre', 'is_active', 'supports_teams']
    search_fields = ['name', 'developer', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'genre')
        }),
        ('Media', {
            'fields': ('logo', 'banner')
        }),
        ('Game Details', {
            'fields': ('developer', 'release_date', 'official_website')
        }),
        ('Team Settings', {
            'fields': ('supports_teams', 'min_team_size', 'max_team_size')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def team_size_range(self, obj):
        if obj.supports_teams:
            return f"{obj.min_team_size}-{obj.max_team_size}"
        return "N/A"
    team_size_range.short_description = 'Team Size'


@admin.register(UserGameProfile)
class UserGameProfileAdmin(admin.ModelAdmin):
    """User Game Profile admin"""
    
    list_display = ['user', 'game', 'in_game_name', 'skill_rating', 'rank', 
                    'win_rate_display', 'is_main_game']
    list_filter = ['game', 'is_main_game', 'created_at']
    search_fields = ['user__username', 'user__email', 'game__name', 'in_game_name']
    raw_id_fields = ['user', 'game']
    ordering = ['-skill_rating']
    
    fieldsets = (
        ('Profile', {
            'fields': ('user', 'game', 'in_game_name', 'is_main_game')
        }),
        ('Skill & Rank', {
            'fields': ('skill_rating', 'rank', 'preferred_role')
        }),
        ('Statistics', {
            'fields': ('matches_played', 'matches_won', 'matches_lost',
                      'tournaments_participated', 'tournaments_won')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def win_rate_display(self, obj):
        win_rate = obj.win_rate
        color = 'green' if win_rate >= 50 else 'orange' if win_rate >= 30 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, win_rate
        )
    win_rate_display.short_description = 'Win Rate'


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Site Settings admin (singleton)"""
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_tagline', 'contact_email', 'support_email')
        }),
        ('Social Media', {
            'fields': ('discord_server', 'twitter_url', 'twitch_url', 'youtube_url')
        }),
        ('Feature Toggles', {
            'fields': ('registrations_open', 'tournaments_enabled', 'coaching_enabled')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding more than one settings object"""
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False