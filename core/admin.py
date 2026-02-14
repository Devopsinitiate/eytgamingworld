from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Game, UserGameProfile, SiteSettings, Player, Video, NewsArticle, Product


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
    
    list_display = ['name', 'genre', 'category', 'supports_teams', 'team_size_range', 
                    'is_active', 'display_order', 'created_at']
    list_filter = ['genre', 'is_active', 'supports_teams']
    search_fields = ['name', 'developer', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    list_editable = ['display_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'genre', 'category')
        }),
        ('Media', {
            'fields': ('logo', 'banner', 'key_art')
        }),
        ('Game Details', {
            'fields': ('developer', 'release_date', 'official_website')
        }),
        ('Team Settings', {
            'fields': ('supports_teams', 'min_team_size', 'max_team_size')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
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



@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Featured Player admin for landing page"""
    
    list_display = ['gamer_tag', 'game', 'role', 'country_flag', 'kd_ratio', 
                    'rank', 'wins', 'is_featured', 'display_order']
    list_filter = ['game', 'is_featured', 'created_at']
    search_fields = ['gamer_tag', 'role', 'rank']
    ordering = ['display_order', '-kd_ratio']
    list_editable = ['is_featured', 'display_order']
    
    fieldsets = (
        ('Player Information', {
            'fields': ('gamer_tag', 'role', 'game', 'country_flag')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Statistics', {
            'fields': ('kd_ratio', 'rank', 'wins')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'display_order')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['feature_players', 'unfeature_players']
    
    def feature_players(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} players featured on landing page.')
    feature_players.short_description = 'Feature selected players'
    
    def unfeature_players(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} players removed from landing page.')
    unfeature_players.short_description = 'Remove from landing page'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Video admin for landing page"""
    
    list_display = ['title', 'game', 'duration_formatted', 'views', 'published_date', 
                    'is_featured', 'is_published', 'display_order']
    list_filter = ['is_featured', 'is_published', 'game', 'published_date']
    search_fields = ['title', 'video_url']
    ordering = ['-published_date']
    list_editable = ['is_featured', 'is_published', 'display_order']
    date_hierarchy = 'published_date'
    
    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'video_url', 'thumbnail', 'duration')
        }),
        ('Metadata', {
            'fields': ('views', 'published_date', 'game')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_published', 'display_order')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['feature_videos', 'publish_videos', 'unpublish_videos']
    
    def feature_videos(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} videos featured on landing page.')
    feature_videos.short_description = 'Feature selected videos'
    
    def publish_videos(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} videos published.')
    publish_videos.short_description = 'Publish selected videos'
    
    def unpublish_videos(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} videos unpublished.')
    unpublish_videos.short_description = 'Unpublish selected videos'


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    """News Article admin for landing page"""
    
    list_display = ['title', 'category', 'author', 'published_date', 'is_published']
    list_filter = ['category', 'is_published', 'published_date', 'author']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-published_date']
    list_editable = ['is_published']
    date_hierarchy = 'published_date'
    raw_id_fields = ['author']
    
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Categorization', {
            'fields': ('category', 'author')
        }),
        ('Publishing', {
            'fields': ('published_date', 'is_published')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['publish_articles', 'unpublish_articles']
    
    def publish_articles(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} articles published.')
    publish_articles.short_description = 'Publish selected articles'
    
    def unpublish_articles(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} articles unpublished.')
    unpublish_articles.short_description = 'Unpublish selected articles'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin for landing page"""
    
    list_display = ['name', 'price', 'is_featured', 'is_available', 'display_order']
    list_filter = ['is_featured', 'is_available', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    list_editable = ['is_featured', 'is_available', 'display_order']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Pricing', {
            'fields': ('price',)
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_available', 'display_order')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['feature_products', 'mark_available', 'mark_unavailable']
    
    def feature_products(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products featured on landing page.')
    feature_products.short_description = 'Feature selected products'
    
    def mark_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} products marked as available.')
    mark_available.short_description = 'Mark as available'
    
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} products marked as unavailable.')
    mark_unavailable.short_description = 'Mark as unavailable'
