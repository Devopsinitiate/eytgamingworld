from django.contrib import admin
from django.utils.html import format_html
from .models import Venue, VenueBooking, VenueReview


class VenueBookingInline(admin.TabularInline):
    model = VenueBooking
    extra = 0
    fields = ['booked_by', 'tournament', 'start_datetime', 'end_datetime', 
              'status', 'total_cost', 'is_paid']
    readonly_fields = ['created_at']
    raw_id_fields = ['booked_by', 'tournament']


class VenueReviewInline(admin.TabularInline):
    model = VenueReview
    extra = 0
    fields = ['user', 'rating', 'title', 'would_recommend']
    readonly_fields = ['created_at']
    raw_id_fields = ['user']


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'venue_type', 'capacity', 
                    'status_badge', 'is_verified', 'view_count']
    list_filter = ['venue_type', 'is_active', 'is_verified', 'country', 'city']
    search_fields = ['name', 'city', 'address', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'venue_type', 'owner')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code',
                      'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Capacity & Setup', {
            'fields': ('capacity', 'setup_stations')
        }),
        ('Operations', {
            'fields': ('hours_of_operation', 'amenities'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('hourly_rate', 'day_rate')
        }),
        ('Media', {
            'fields': ('photo',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Metadata', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'view_count']
    inlines = [VenueBookingInline, VenueReviewInline]
    
    actions = ['verify_venues', 'activate_venues', 'deactivate_venues']
    
    def status_badge(self, obj):
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'gray'
            text = 'Inactive'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'
    
    def verify_venues(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} venues verified.')
    verify_venues.short_description = 'Verify selected venues'
    
    def activate_venues(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} venues activated.')
    activate_venues.short_description = 'Activate selected venues'
    
    def deactivate_venues(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} venues deactivated.')
    deactivate_venues.short_description = 'Deactivate selected venues'


@admin.register(VenueBooking)
class VenueBookingAdmin(admin.ModelAdmin):
    list_display = ['venue', 'booked_by', 'start_datetime', 'duration', 
                    'status_badge', 'is_paid', 'total_cost']
    list_filter = ['status', 'is_paid', 'start_datetime', 'venue']
    search_fields = ['venue__name', 'booked_by__username', 'tournament__name']
    raw_id_fields = ['venue', 'booked_by', 'tournament']
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('venue', 'booked_by', 'tournament')
        }),
        ('Schedule', {
            'fields': ('start_datetime', 'end_datetime', 'expected_participants')
        }),
        ('Payment', {
            'fields': ('total_cost', 'deposit_paid', 'is_paid')
        }),
        ('Status', {
            'fields': ('status', 'confirmed_at', 'cancelled_at')
        }),
        ('Notes', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'cancelled_at']
    
    actions = ['confirm_bookings', 'cancel_bookings', 'mark_completed']
    
    def duration(self, obj):
        hours = obj.duration_hours
        return f"{hours:.1f} hours"
    duration.short_description = 'Duration'
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'cancelled': 'red',
            'completed': 'green',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def confirm_bookings(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='confirmed', confirmed_at=timezone.now())
        self.message_user(request, f'{updated} bookings confirmed.')
    confirm_bookings.short_description = 'Confirm selected bookings'
    
    def cancel_bookings(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='cancelled', cancelled_at=timezone.now())
        self.message_user(request, f'{updated} bookings cancelled.')
    cancel_bookings.short_description = 'Cancel selected bookings'
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} bookings marked as completed.')
    mark_completed.short_description = 'Mark as completed'


@admin.register(VenueReview)
class VenueReviewAdmin(admin.ModelAdmin):
    list_display = ['venue', 'user', 'rating_display', 'title', 
                    'would_recommend', 'created_at']
    list_filter = ['rating', 'would_recommend', 'created_at']
    search_fields = ['venue__name', 'user__username', 'title', 'review']
    raw_id_fields = ['venue', 'user']
    
    fieldsets = (
        ('Review', {
            'fields': ('venue', 'user', 'rating', 'title', 'review')
        }),
        ('Recommendation', {
            'fields': ('would_recommend',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_display.short_description = 'Rating'