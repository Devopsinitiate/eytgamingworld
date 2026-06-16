from django.contrib import admin
from django.utils.html import format_html
from .models import Sponsor, SponsorshipDeal


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SponsorshipDeal)
class SponsorshipDealAdmin(admin.ModelAdmin):
    list_display = ['title', 'sponsor', 'celebrity', 'budget_display', 'status_badge', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'sponsor__name', 'celebrity__username', 'celebrity__display_name']
    raw_id_fields = ['sponsor', 'celebrity']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Deal Information', {
            'fields': ('title', 'description', 'sponsor', 'celebrity')
        }),
        ('Financial', {
            'fields': ('budget',)
        }),
        ('Timeline', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Details', {
            'fields': ('terms', 'metadata'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_deals', 'complete_deals', 'cancel_deals']

    def budget_display(self, obj):
        return format_html(
            '<span style="font-weight:bold;color:#eab308;">${:,.0f}</span>', obj.budget
        )
    budget_display.short_description = 'Budget'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'active': '#22c55e',
            'completed': '#6b7280',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{}20;color:{};padding:2px 10px;border-radius:999px;font-weight:600;font-size:0.75rem;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def activate_deals(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='active', start_date=timezone.now().date())
        self.message_user(request, f'{updated} deal(s) activated.')
    activate_deals.short_description = 'Activate selected deals'

    def complete_deals(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', end_date=timezone.now().date())
        self.message_user(request, f'{updated} deal(s) completed.')
    complete_deals.short_description = 'Complete selected deals'

    def cancel_deals(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} deal(s) cancelled.')
    cancel_deals.short_description = 'Cancel selected deals'
