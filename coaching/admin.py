from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import (CoachProfile, CoachGameExpertise, CoachAvailability,
                     CoachingSession, SessionReview, CoachingPackage, PackagePurchase)


class CoachGameExpertiseInline(admin.TabularInline):
    model = CoachGameExpertise
    extra = 0
    fields = ['game', 'rank', 'is_primary', 'custom_hourly_rate']
    raw_id_fields = ['game']


class CoachAvailabilityInline(admin.TabularInline):
    model = CoachAvailability
    extra = 0
    fields = ['weekday', 'start_time', 'end_time', 'is_active']


class CoachingPackageInline(admin.TabularInline):
    model = CoachingPackage
    extra = 0
    fields = ['name', 'number_of_sessions', 'total_price', 'is_active']


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status_badge', 'hourly_rate', 'rating_display',
                    'total_sessions', 'total_students', 'total_earnings', 'is_verified']
    list_filter = ['status', 'experience_level', 'is_verified', 'accepting_students',
                   'offers_individual', 'offers_group']
    search_fields = ['user__username', 'user__email', 'bio', 'achievements']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Coach Information', {
            'fields': ('user', 'bio', 'specializations', 'achievements')
        }),
        ('Experience', {
            'fields': ('experience_level', 'years_experience')
        }),
        ('Pricing', {
            'fields': ('hourly_rate',)
        }),
        ('Availability', {
            'fields': ('status', 'accepting_students', 'max_students_per_week')
        }),
        ('Session Settings', {
            'fields': ('min_session_duration', 'max_session_duration', 'session_increment',
                      'offers_individual', 'offers_group', 'max_group_size')
        }),
        ('Video Platform', {
            'fields': ('preferred_platform', 'platform_username', 'profile_video'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_sessions', 'total_students', 'average_rating',
                      'total_reviews', 'total_earnings'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_notes')
        }),
    )
    
    readonly_fields = ['total_sessions', 'total_students', 'average_rating',
                       'total_reviews', 'total_earnings', 'created_at', 'updated_at']
    
    inlines = [CoachGameExpertiseInline, CoachAvailabilityInline, CoachingPackageInline]
    
    actions = ['verify_coaches', 'activate_coaches', 'deactivate_coaches']
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'on_break': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def rating_display(self, obj):
        if obj.average_rating > 0:
            stars = '★' * int(obj.average_rating) + '☆' * (5 - int(obj.average_rating))
            return format_html(
                '<span style="color: gold; font-size: 16px;">{}</span> <small>({:.2f})</small>',
                stars, obj.average_rating
            )
        return '-'
    rating_display.short_description = 'Rating'
    
    def verify_coaches(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} coaches verified.')
    verify_coaches.short_description = 'Verify selected coaches'
    
    def activate_coaches(self, request, queryset):
        updated = queryset.update(status='active', accepting_students=True)
        self.message_user(request, f'{updated} coaches activated.')
    activate_coaches.short_description = 'Activate selected coaches'
    
    def deactivate_coaches(self, request, queryset):
        updated = queryset.update(status='inactive', accepting_students=False)
        self.message_user(request, f'{updated} coaches deactivated.')
    deactivate_coaches.short_description = 'Deactivate selected coaches'


@admin.register(CoachGameExpertise)
class CoachGameExpertiseAdmin(admin.ModelAdmin):
    list_display = ['coach', 'game', 'rank', 'is_primary', 'custom_hourly_rate']
    list_filter = ['game', 'rank', 'is_primary']
    search_fields = ['coach__user__username', 'game__name']
    raw_id_fields = ['coach', 'game']


@admin.register(CoachAvailability)
class CoachAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['coach', 'weekday_display', 'time_range', 'is_active']
    list_filter = ['weekday', 'is_active']
    search_fields = ['coach__user__username']
    raw_id_fields = ['coach']
    
    def weekday_display(self, obj):
        return obj.get_weekday_display()
    weekday_display.short_description = 'Day'
    
    def time_range(self, obj):
        return f"{obj.start_time} - {obj.end_time}"
    time_range.short_description = 'Time'


@admin.register(CoachingSession)
class CoachingSessionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'coach_name', 'student_name', 'game',
                    'scheduled_start', 'duration_display', 'price', 
                    'status_badge', 'is_paid']
    list_filter = ['status', 'session_type', 'is_paid', 'game', 'scheduled_start']
    search_fields = ['coach__user__username', 'student__username', 'id']
    raw_id_fields = ['coach', 'student', 'game', 'cancelled_by']
    date_hierarchy = 'scheduled_start'
    
    fieldsets = (
        ('Session Information', {
            'fields': ('coach', 'student', 'game', 'session_type', 'additional_students')
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'scheduled_end', 'duration_minutes',
                      'actual_start', 'actual_end')
        }),
        ('Content', {
            'fields': ('topics', 'student_notes', 'coach_notes')
        }),
        ('Payment', {
            'fields': ('price', 'is_paid', 'payment_intent_id')
        }),
        ('Video', {
            'fields': ('video_link', 'recording_link'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Cancellation', {
            'fields': ('cancelled_by', 'cancellation_reason', 'cancellation_time'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['actual_start', 'actual_end', 'created_at', 'updated_at',
                       'cancellation_time']
    
    actions = ['confirm_sessions', 'complete_sessions', 'mark_paid']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def coach_name(self, obj):
        return obj.coach.user.get_display_name()
    coach_name.short_description = 'Coach'
    
    def student_name(self, obj):
        return obj.student.get_display_name()
    student_name.short_description = 'Student'
    
    def duration_display(self, obj):
        return f"{obj.duration_minutes} min"
    duration_display.short_description = 'Duration'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'in_progress': 'purple',
            'completed': 'green',
            'cancelled': 'red',
            'no_show': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def confirm_sessions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} sessions confirmed.')
    confirm_sessions.short_description = 'Confirm selected sessions'
    
    def complete_sessions(self, request, queryset):
        count = 0
        for session in queryset.filter(status='in_progress'):
            if session.complete_session():
                count += 1
        self.message_user(request, f'{count} sessions completed.')
    complete_sessions.short_description = 'Complete selected sessions'
    
    def mark_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f'{updated} sessions marked as paid.')
    mark_paid.short_description = 'Mark as paid'


@admin.register(SessionReview)
class SessionReviewAdmin(admin.ModelAdmin):
    list_display = ['coach', 'student', 'rating_display', 'would_recommend',
                    'is_approved', 'is_featured', 'created_at']
    list_filter = ['rating', 'would_recommend', 'is_approved', 'is_featured', 'created_at']
    search_fields = ['coach__user__username', 'student__username', 'review', 'title']
    raw_id_fields = ['session', 'coach', 'student']
    
    fieldsets = (
        ('Review Information', {
            'fields': ('session', 'coach', 'student')
        }),
        ('Ratings', {
            'fields': ('rating', 'communication_rating', 'knowledge_rating', 'patience_rating')
        }),
        ('Content', {
            'fields': ('title', 'review', 'would_recommend', 'improvement_seen')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'admin_notes')
        }),
        ('Coach Response', {
            'fields': ('coach_response', 'response_date'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'response_date']
    
    actions = ['approve_reviews', 'feature_reviews', 'disapprove_reviews']
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews approved.')
        
        # Update coach ratings
        for review in queryset:
            review.coach.update_rating()
    approve_reviews.short_description = 'Approve selected reviews'
    
    def feature_reviews(self, request, queryset):
        updated = queryset.update(is_featured=True, is_approved=True)
        self.message_user(request, f'{updated} reviews featured.')
    feature_reviews.short_description = 'Feature selected reviews'
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False, is_featured=False)
        self.message_user(request, f'{updated} reviews disapproved.')
        
        # Update coach ratings
        for review in queryset:
            review.coach.update_rating()
    disapprove_reviews.short_description = 'Disapprove selected reviews'


@admin.register(CoachingPackage)
class CoachingPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'coach', 'game', 'number_of_sessions',
                    'session_duration', 'total_price', 'discount_percentage', 'is_active']
    list_filter = ['is_active', 'game', 'number_of_sessions']
    search_fields = ['name', 'coach__user__username', 'description']
    raw_id_fields = ['coach', 'game']
    
    fieldsets = (
        ('Package Information', {
            'fields': ('coach', 'name', 'description')
        }),
        ('Details', {
            'fields': ('number_of_sessions', 'session_duration', 'game')
        }),
        ('Pricing', {
            'fields': ('total_price', 'discount_percentage')
        }),
        ('Validity', {
            'fields': ('valid_for_days', 'is_active')
        }),
    )
    
    actions = ['activate_packages', 'deactivate_packages']
    
    def activate_packages(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} packages activated.')
    activate_packages.short_description = 'Activate selected packages'
    
    def deactivate_packages(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} packages deactivated.')
    deactivate_packages.short_description = 'Deactivate selected packages'


@admin.register(PackagePurchase)
class PackagePurchaseAdmin(admin.ModelAdmin):
    list_display = ['student', 'package_name', 'sessions_display',
                    'amount_paid', 'status', 'purchased_at', 'expires_at']
    list_filter = ['status', 'purchased_at']
    search_fields = ['student__username', 'package__name']
    raw_id_fields = ['package', 'student']
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('package', 'student', 'amount_paid', 'payment_intent_id')
        }),
        ('Usage', {
            'fields': ('sessions_remaining', 'sessions_used')
        }),
        ('Validity', {
            'fields': ('purchased_at', 'expires_at', 'status')
        }),
    )
    
    readonly_fields = ['purchased_at']
    
    def package_name(self, obj):
        return obj.package.name
    package_name.short_description = 'Package'
    
    def sessions_display(self, obj):
        total = obj.sessions_remaining + obj.sessions_used
        return f"{obj.sessions_remaining}/{total} remaining"
    sessions_display.short_description = 'Sessions'