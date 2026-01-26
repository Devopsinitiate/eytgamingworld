from django.contrib import admin
from .models import Activity, Achievement, UserAchievement, Recommendation, ProfileCompleteness, UserReport


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__display_name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'rarity', 'is_progressive', 'target_value', 'points_reward', 'is_active']
    list_filter = ['achievement_type', 'rarity', 'is_active', 'is_hidden', 'is_progressive']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['id', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['achievement_type', 'name']
    actions = ['activate_achievements', 'deactivate_achievements']
    
    def activate_achievements(self, request, queryset):
        """Activate selected achievements"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} achievement(s) activated.')
    activate_achievements.short_description = 'Activate selected achievements'
    
    def deactivate_achievements(self, request, queryset):
        """Deactivate selected achievements"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} achievement(s) deactivated.')
    deactivate_achievements.short_description = 'Deactivate selected achievements'


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'current_value', 'is_completed', 'in_showcase', 'earned_at']
    list_filter = ['is_completed', 'in_showcase', 'earned_at']
    search_fields = ['user__username', 'user__email', 'achievement__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'progress_percentage']
    date_hierarchy = 'earned_at'
    ordering = ['-earned_at']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'recommendation_type', 'score', 'is_dismissed', 'created_at', 'expires_at']
    list_filter = ['recommendation_type', 'is_dismissed', 'created_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'reason']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-score', '-created_at']


@admin.register(ProfileCompleteness)
class ProfileCompletenessAdmin(admin.ModelAdmin):
    list_display = ['user', 'percentage', 'total_points', 'max_points', 'last_calculated']
    list_filter = ['percentage', 'last_calculated']
    search_fields = ['user__username', 'user__email', 'user__display_name']
    readonly_fields = ['id', 'total_points', 'max_points', 'percentage', 'completed_fields', 'incomplete_fields', 'last_calculated']
    ordering = ['-percentage', '-last_calculated']
    
    def has_add_permission(self, request):
        """Prevent manual creation - should be auto-calculated"""
        return False


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ['reported_user', 'reporter', 'category', 'status', 'created_at', 'reviewed_by']
    list_filter = ['status', 'category', 'created_at', 'reviewed_at']
    search_fields = ['reported_user__username', 'reported_user__email', 'reporter__username', 'reporter__email', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'reported_user', 'category', 'description')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'resolution_notes')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_investigating', 'mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_investigating(self, request, queryset):
        """Mark selected reports as under investigation"""
        from django.utils import timezone
        updated = queryset.update(
            status='investigating',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) marked as investigating.')
    mark_as_investigating.short_description = 'Mark as investigating'
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected reports as resolved"""
        from django.utils import timezone
        updated = queryset.update(
            status='resolved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_dismissed(self, request, queryset):
        """Mark selected reports as dismissed"""
        from django.utils import timezone
        updated = queryset.update(
            status='dismissed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} report(s) marked as dismissed.')
    mark_as_dismissed.short_description = 'Mark as dismissed'
