"""
Django admin configuration for the EYTGaming Store.

Admin interfaces for managing products, orders, inventory, and other
store-related models.
"""

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.db.models import Q
from django import forms
from .models import (
    Category, Product, ProductVariant, ProductImage, 
    Cart, CartItem, Order, OrderItem, NewsletterSubscriber
)
import os


# Custom Form Classes with Validation

class ProductImageForm(forms.ModelForm):
    """
    Custom form for ProductImage with file validation.
    Validates file type and size according to requirements.
    """
    class Meta:
        model = ProductImage
        fields = '__all__'
    
    def clean_image(self):
        """
        Validate image file type and size.
        Requirements: 13.3 - Image validation (file type, size)
        """
        image = self.cleaned_data.get('image')
        
        if image:
            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if image.size > max_size:
                raise ValidationError(
                    f'Image file size must not exceed 5MB. '
                    f'Current size: {image.size / (1024 * 1024):.2f}MB'
                )
            
            # Validate file type (JPEG, PNG, WebP)
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            file_ext = os.path.splitext(image.name)[1].lower()
            
            if file_ext not in allowed_extensions:
                raise ValidationError(
                    f'Invalid file type. Allowed types: JPEG, PNG, WebP. '
                    f'Received: {file_ext}'
                )
            
            # Validate MIME type
            allowed_mime_types = ['image/jpeg', 'image/png', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_mime_types:
                raise ValidationError(
                    f'Invalid image format. Allowed formats: JPEG, PNG, WebP. '
                    f'Received: {image.content_type}'
                )
        
        return image


class ProductForm(forms.ModelForm):
    """
    Custom form for Product with enhanced validation.
    """
    class Meta:
        model = Product
        fields = '__all__'
    
    def clean_price(self):
        """Validate product price is positive."""
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError('Price must be greater than zero.')
        return price
    
    def clean_stock_quantity(self):
        """Validate stock quantity is non-negative."""
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock
    
    def clean_name(self):
        """Validate product name is not empty and within length limits."""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 1:
                raise ValidationError('Product name cannot be empty.')
            if len(name) > 200:
                raise ValidationError('Product name must not exceed 200 characters.')
        return name


class ProductVariantForm(forms.ModelForm):
    """
    Custom form for ProductVariant with validation.
    """
    class Meta:
        model = ProductVariant
        fields = '__all__'
    
    def clean_sku(self):
        """Validate SKU is unique and properly formatted."""
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.strip().upper()
            # Check uniqueness excluding current instance
            existing = ProductVariant.objects.filter(sku=sku)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(f'SKU "{sku}" already exists.')
        return sku
    
    def clean_stock_quantity(self):
        """Validate stock quantity is non-negative."""
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock


class ProductImageInline(admin.TabularInline):
    """Inline admin for product images with validation."""
    model = ProductImage
    form = ProductImageForm
    extra = 1
    fields = ('image', 'alt_text', 'display_order', 'is_primary', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        """Display thumbnail preview of the image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    """Inline admin for product variants with validation."""
    model = ProductVariant
    form = ProductVariantForm
    extra = 1
    fields = ('name', 'sku', 'price_adjustment', 'stock_quantity', 'is_available', 'final_price_display')
    readonly_fields = ('final_price_display',)
    
    def final_price_display(self, obj):
        """Display the calculated final price."""
        if obj.pk:
            return f"${obj.final_price:.2f}"
        return "N/A"
    final_price_display.short_description = 'Final Price'


# Custom Admin Filters for Inventory Tracking

class StockStatusFilter(admin.SimpleListFilter):
    """Filter products by stock status (in stock / out of stock)."""
    title = 'stock status'
    parameter_name = 'stock_status'
    
    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In Stock'),
            ('out_of_stock', 'Out of Stock'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock_quantity__gt=0)
        elif self.value() == 'out_of_stock':
            return queryset.filter(stock_quantity=0)
        return queryset


class LowStockFilter(admin.SimpleListFilter):
    """Filter products by low stock warning (below 10 units)."""
    title = 'low stock warning'
    parameter_name = 'low_stock'
    
    def lookups(self, request, model_admin):
        return (
            ('low', 'Low Stock (1-9 units)'),
            ('critical', 'Critical (Out of Stock)'),
            ('ok', 'Stock OK (10+ units)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(stock_quantity__gt=0, stock_quantity__lt=10)
        elif self.value() == 'critical':
            return queryset.filter(stock_quantity=0)
        elif self.value() == 'ok':
            return queryset.filter(stock_quantity__gte=10)
        return queryset


class VariantStockStatusFilter(admin.SimpleListFilter):
    """Filter product variants by stock status (in stock / out of stock)."""
    title = 'stock status'
    parameter_name = 'stock_status'
    
    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In Stock'),
            ('out_of_stock', 'Out of Stock'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock_quantity__gt=0)
        elif self.value() == 'out_of_stock':
            return queryset.filter(stock_quantity=0)
        return queryset


class VariantLowStockFilter(admin.SimpleListFilter):
    """Filter product variants by low stock warning (below 10 units)."""
    title = 'low stock warning'
    parameter_name = 'low_stock'
    
    def lookups(self, request, model_admin):
        return (
            ('low', 'Low Stock (1-9 units)'),
            ('critical', 'Critical (Out of Stock)'),
            ('ok', 'Stock OK (10+ units)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(stock_quantity__gt=0, stock_quantity__lt=10)
        elif self.value() == 'critical':
            return queryset.filter(stock_quantity=0)
        elif self.value() == 'ok':
            return queryset.filter(stock_quantity__gte=10)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ('name', 'slug', 'parent', 'display_order', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent', 'display_order')
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for Product model.
    Includes custom validation, bulk actions, and image upload validation.
    """
    form = ProductForm
    list_display = (
        'name',
        'category',
        'price',
        'stock_quantity',
        'is_active',
        'is_in_stock',
        'is_low_stock',
        'variant_count',
        'image_count',
        'created_at'
    )
    list_filter = ('is_active', 'category', 'created_at', 'updated_at', StockStatusFilter, LowStockFilter)
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'primary_image_preview')
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity'),
            'description': 'Set base price and stock quantity. Variants can have price adjustments.'
        }),
        ('Status', {
            'fields': ('is_active',),
            'description': 'Inactive products are soft-deleted and hidden from customers.'
        }),
        ('Preview', {
            'fields': ('primary_image_preview',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'duplicate_products',
        'adjust_stock',
        'apply_discount',
        'export_to_csv'
    ]
    
    def primary_image_preview(self, obj):
        """Display preview of the primary product image."""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px;" />',
                primary_image.image.url
            )
        return "No primary image set"
    primary_image_preview.short_description = 'Primary Image'
    
    def variant_count(self, obj):
        """Display count of product variants."""
        count = obj.variants.count()
        if count > 0:
            return format_html('<span style="color: green;">{}</span>', count)
        return count
    variant_count.short_description = 'Variants'
    
    def image_count(self, obj):
        """Display count of product images."""
        count = obj.images.count()
        if count == 0:
            return format_html('<span style="color: red;">0</span>')
        return count
    image_count.short_description = 'Images'
    
    def mark_as_active(self, request, queryset):
        """Bulk action to mark products as active."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) marked as active.')
    mark_as_active.short_description = 'Mark selected products as active'
    
    def mark_as_inactive(self, request, queryset):
        """Bulk action to mark products as inactive (soft delete)."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) marked as inactive.')
    mark_as_inactive.short_description = 'Mark selected products as inactive'
    
    def duplicate_products(self, request, queryset):
        """Bulk action to duplicate selected products."""
        count = 0
        for product in queryset:
            # Store original variants and images
            original_variants = list(product.variants.all())
            original_images = list(product.images.all())
            
            # Create a copy of the product
            product.pk = None
            product.id = None
            product.name = f"{product.name} (Copy)"
            product.slug = f"{product.slug}-copy-{count}"
            product.save()
            
            # Duplicate variants
            for variant in original_variants:
                variant.pk = None
                variant.id = None
                variant.product = product
                variant.sku = f"{variant.sku}-COPY-{count}"
                variant.save()
            
            # Duplicate images
            for image in original_images:
                image.pk = None
                image.id = None
                image.product = product
                image.save()
            
            count += 1
        self.message_user(request, f'{count} product(s) duplicated with variants and images.')
    duplicate_products.short_description = 'Duplicate selected products'
    
    def adjust_stock(self, request, queryset):
        """
        Bulk action to adjust stock levels.
        Note: This is a placeholder - in production, you'd want a form to input the adjustment.
        """
        # For now, just show a message
        self.message_user(
            request,
            f'Selected {queryset.count()} product(s). '
            'Use individual product edit to adjust stock levels.',
            level='warning'
        )
    adjust_stock.short_description = 'Adjust stock levels (edit individually)'
    
    def apply_discount(self, request, queryset):
        """
        Bulk action to apply discount.
        Note: This is a placeholder - in production, you'd want a form to input the discount.
        """
        self.message_user(
            request,
            f'Selected {queryset.count()} product(s). '
            'Use individual product edit to adjust prices.',
            level='warning'
        )
    apply_discount.short_description = 'Apply discount (edit individually)'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export products to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Slug', 'Category', 'Price', 'Stock', 'Active', 'Created'])
        
        for product in queryset:
            writer.writerow([
                product.name,
                product.slug,
                product.category.name,
                product.price,
                product.stock_quantity,
                product.is_active,
                product.created_at.strftime('%Y-%m-%d')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} product(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected products to CSV'
    
    def is_in_stock(self, obj):
        """Display stock status with visual indicator."""
        if obj.is_in_stock:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ In Stock</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Out of Stock</span>'
            )
    is_in_stock.short_description = 'Stock Status'
    
    def is_low_stock(self, obj):
        """Display low stock warning with visual indicator."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ Low Stock ({} units)</span>',
                obj.stock_quantity
            )
        elif not obj.is_in_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Out of Stock</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ OK ({} units)</span>',
                obj.stock_quantity
            )
    is_low_stock.short_description = 'Stock Warning'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Enhanced admin interface for ProductVariant model."""
    form = ProductVariantForm
    list_display = (
        'product',
        'name',
        'sku',
        'final_price',
        'stock_quantity',
        'is_available',
        'is_in_stock',
        'is_low_stock'
    )
    list_filter = ('is_available', 'product__category', 'created_at', VariantStockStatusFilter, VariantLowStockFilter)
    search_fields = ('name', 'sku', 'product__name')
    readonly_fields = ('created_at', 'updated_at', 'final_price_display')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'name', 'sku')
        }),
        ('Pricing & Inventory', {
            'fields': ('price_adjustment', 'final_price_display', 'stock_quantity'),
            'description': 'Price adjustment is added to the base product price.'
        }),
        ('Status', {
            'fields': ('is_available',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_available', 'mark_as_unavailable', 'export_to_csv']
    
    def final_price_display(self, obj):
        """Display the calculated final price."""
        if obj.pk:
            return format_html(
                '<strong style="color: green;">${:.2f}</strong> '
                '(Base: ${:.2f} + Adjustment: ${:.2f})',
                obj.final_price,
                obj.product.price,
                obj.price_adjustment
            )
        return "N/A"
    final_price_display.short_description = 'Final Price Breakdown'
    
    def mark_as_available(self, request, queryset):
        """Bulk action to mark variants as available."""
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} variant(s) marked as available.')
    mark_as_available.short_description = 'Mark selected variants as available'
    
    def mark_as_unavailable(self, request, queryset):
        """Bulk action to mark variants as unavailable."""
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} variant(s) marked as unavailable.')
    mark_as_unavailable.short_description = 'Mark selected variants as unavailable'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export variants to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_variants.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Product', 'Variant', 'SKU', 'Base Price', 'Adjustment', 'Final Price', 'Stock', 'Available'])
        
        for variant in queryset:
            writer.writerow([
                variant.product.name,
                variant.name,
                variant.sku,
                variant.product.price,
                variant.price_adjustment,
                variant.final_price,
                variant.stock_quantity,
                variant.is_available
            ])
        
        self.message_user(request, f'Exported {queryset.count()} variant(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected variants to CSV'
    
    def is_in_stock(self, obj):
        """Display stock status with visual indicator."""
        if obj.is_in_stock:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ In Stock</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Out of Stock</span>'
            )
    is_in_stock.short_description = 'Stock Status'
    
    def is_low_stock(self, obj):
        """Display low stock warning with visual indicator."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠ Low Stock ({} units)</span>',
                obj.stock_quantity
            )
        elif not obj.is_in_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Out of Stock</span>'
            )
        else:
            return format_html(
                '<span style="color: green;">✓ OK ({} units)</span>',
                obj.stock_quantity
            )
    is_low_stock.short_description = 'Stock Warning'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Enhanced admin interface for ProductImage model with validation."""
    form = ProductImageForm
    list_display = (
        'product',
        'alt_text',
        'display_order',
        'is_primary',
        'image_preview',
        'file_size',
        'created_at'
    )
    list_filter = ('is_primary', 'created_at', 'product__category')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('created_at', 'image_preview', 'file_size', 'file_type')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'image', 'alt_text')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'is_primary')
        }),
        ('File Information', {
            'fields': ('image_preview', 'file_size', 'file_type'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['set_as_primary', 'export_to_csv']
    
    def image_preview(self, obj):
        """Display larger preview of the image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 300px; border: 1px solid #ddd; padding: 5px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = 'Image Preview'
    
    def file_size(self, obj):
        """Display file size in human-readable format."""
        if obj.image:
            size_bytes = obj.image.size
            if size_bytes < 1024:
                return f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            else:
                size_mb = size_bytes / (1024 * 1024)
                color = 'red' if size_mb > 5 else 'green'
                return format_html(
                    '<span style="color: {};">{:.2f} MB</span>',
                    color,
                    size_mb
                )
        return "N/A"
    file_size.short_description = 'File Size'
    
    def file_type(self, obj):
        """Display file type/extension."""
        if obj.image:
            ext = os.path.splitext(obj.image.name)[1].lower()
            return ext or "Unknown"
        return "N/A"
    file_type.short_description = 'File Type'
    
    def set_as_primary(self, request, queryset):
        """
        Bulk action to set selected image as primary.
        Only works if one image is selected.
        """
        if queryset.count() != 1:
            self.message_user(
                request,
                'Please select exactly one image to set as primary.',
                level='error'
            )
            return
        
        image = queryset.first()
        # Unset other primary images for this product
        ProductImage.objects.filter(
            product=image.product,
            is_primary=True
        ).update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        self.message_user(request, f'Set "{image.alt_text}" as primary image for {image.product.name}.')
    set_as_primary.short_description = 'Set as primary image (select one)'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export images to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_images.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Product', 'Alt Text', 'Display Order', 'Is Primary', 'Image URL', 'Created'])
        
        for image in queryset:
            writer.writerow([
                image.product.name,
                image.alt_text,
                image.display_order,
                image.is_primary,
                image.image.url if image.image else '',
                image.created_at.strftime('%Y-%m-%d')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} image(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected images to CSV'



class CartItemInline(admin.TabularInline):
    """Inline admin for cart items."""
    model = CartItem
    extra = 0
    fields = ('product', 'variant', 'quantity', 'unit_price_display', 'total_price_display', 'added_at')
    readonly_fields = ('unit_price_display', 'total_price_display', 'added_at')
    
    def unit_price_display(self, obj):
        """Display the unit price."""
        if obj.pk:
            return f"${obj.unit_price:.2f}"
        return "N/A"
    unit_price_display.short_description = 'Unit Price'
    
    def total_price_display(self, obj):
        """Display the total price."""
        if obj.pk:
            return f"${obj.total_price:.2f}"
        return "N/A"
    total_price_display.short_description = 'Total Price'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin interface for Cart model."""
    list_display = (
        'id_short',
        'user_display',
        'session_key_short',
        'item_count_display',
        'is_empty',
        'created_at',
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'item_count_display', 'cart_total_display')
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('id', 'user', 'session_key')
        }),
        ('Cart Summary', {
            'fields': ('item_count_display', 'cart_total_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['clear_empty_carts', 'export_to_csv']
    
    def id_short(self, obj):
        """Display shortened cart ID."""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'Cart ID'
    
    def user_display(self, obj):
        """Display user or 'Guest'."""
        if obj.user:
            return format_html(
                '<a href="/admin/core/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return format_html('<span style="color: gray;">Guest</span>')
    user_display.short_description = 'User'
    
    def session_key_short(self, obj):
        """Display shortened session key."""
        if obj.session_key:
            return obj.session_key[:12] + '...'
        return '-'
    session_key_short.short_description = 'Session Key'
    
    def item_count_display(self, obj):
        """Display item count with color coding."""
        count = obj.item_count
        if count == 0:
            return format_html('<span style="color: gray;">0</span>')
        elif count > 10:
            return format_html('<span style="color: orange;">{}</span>', count)
        return count
    item_count_display.short_description = 'Items'
    
    def cart_total_display(self, obj):
        """Display cart total price."""
        total = sum(item.total_price for item in obj.items.all())
        return format_html('<strong style="color: green;">${:.2f}</strong>', total)
    cart_total_display.short_description = 'Cart Total'
    
    def clear_empty_carts(self, request, queryset):
        """Bulk action to delete empty carts."""
        empty_carts = queryset.filter(items__isnull=True)
        count = empty_carts.count()
        empty_carts.delete()
        self.message_user(request, f'Deleted {count} empty cart(s).')
    clear_empty_carts.short_description = 'Delete empty carts'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export carts to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="carts.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Cart ID', 'User', 'Session Key', 'Item Count', 'Created', 'Updated'])
        
        for cart in queryset:
            writer.writerow([
                str(cart.id),
                cart.user.username if cart.user else 'Guest',
                cart.session_key or '',
                cart.item_count,
                cart.created_at.strftime('%Y-%m-%d %H:%M'),
                cart.updated_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} cart(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected carts to CSV'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin interface for CartItem model."""
    list_display = (
        'id_short',
        'cart_user_display',
        'product',
        'variant',
        'quantity',
        'unit_price_display',
        'total_price_display',
        'is_available',
        'has_sufficient_stock',
        'added_at'
    )
    list_filter = ('added_at', 'product__category')
    search_fields = (
        'cart__user__username',
        'cart__user__email',
        'product__name',
        'variant__name',
        'cart__id'
    )
    readonly_fields = (
        'id',
        'added_at',
        'unit_price_display',
        'total_price_display',
        'availability_status'
    )
    
    fieldsets = (
        ('Cart Item Information', {
            'fields': ('id', 'cart', 'product', 'variant', 'quantity')
        }),
        ('Pricing', {
            'fields': ('unit_price_display', 'total_price_display')
        }),
        ('Availability', {
            'fields': ('availability_status',)
        }),
        ('Timestamp', {
            'fields': ('added_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['remove_unavailable_items', 'export_to_csv']
    
    def id_short(self, obj):
        """Display shortened cart item ID."""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'Item ID'
    
    def cart_user_display(self, obj):
        """Display cart user or 'Guest'."""
        if obj.cart.user:
            return obj.cart.user.username
        return format_html('<span style="color: gray;">Guest</span>')
    cart_user_display.short_description = 'Cart User'
    
    def unit_price_display(self, obj):
        """Display the unit price."""
        return format_html('${:.2f}', obj.unit_price)
    unit_price_display.short_description = 'Unit Price'
    
    def total_price_display(self, obj):
        """Display the total price."""
        return format_html('<strong>${:.2f}</strong>', obj.total_price)
    total_price_display.short_description = 'Total Price'
    
    def availability_status(self, obj):
        """Display availability and stock status."""
        status_parts = []
        
        if not obj.is_available:
            status_parts.append(
                format_html('<span style="color: red;">❌ Unavailable</span>')
            )
        else:
            status_parts.append(
                format_html('<span style="color: green;">✓ Available</span>')
            )
        
        if not obj.has_sufficient_stock:
            status_parts.append(
                format_html('<span style="color: orange;">⚠ Insufficient Stock</span>')
            )
        else:
            status_parts.append(
                format_html('<span style="color: green;">✓ Stock OK</span>')
            )
        
        return format_html('<br>'.join(status_parts))
    availability_status.short_description = 'Status'
    
    def remove_unavailable_items(self, request, queryset):
        """Bulk action to remove unavailable cart items."""
        unavailable = queryset.filter(
            Q(product__is_active=False) | Q(variant__is_available=False)
        )
        count = unavailable.count()
        unavailable.delete()
        self.message_user(request, f'Removed {count} unavailable cart item(s).')
    remove_unavailable_items.short_description = 'Remove unavailable items'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export cart items to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="cart_items.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Cart ID', 'User', 'Product', 'Variant', 'Quantity',
            'Unit Price', 'Total Price', 'Available', 'Stock OK', 'Added'
        ])
        
        for item in queryset:
            writer.writerow([
                str(item.cart.id),
                item.cart.user.username if item.cart.user else 'Guest',
                item.product.name,
                item.variant.name if item.variant else '',
                item.quantity,
                f'${item.unit_price:.2f}',
                f'${item.total_price:.2f}',
                'Yes' if item.is_available else 'No',
                'Yes' if item.has_sufficient_stock else 'No',
                item.added_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} cart item(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected cart items to CSV'



# Order Admin Classes

class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""
    model = OrderItem
    extra = 0
    fields = (
        'product',
        'variant',
        'product_name',
        'variant_name',
        'quantity',
        'unit_price',
        'total_price'
    )
    readonly_fields = ('product_name', 'variant_name', 'unit_price', 'total_price')
    can_delete = False  # Don't allow deleting order items after order is placed
    
    def has_add_permission(self, request, obj=None):
        """Prevent adding items to existing orders."""
        return False


class OrderStatusFilter(admin.SimpleListFilter):
    """Filter orders by status."""
    title = 'order status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class PaymentStatusFilter(admin.SimpleListFilter):
    """Filter orders by payment status."""
    title = 'payment status'
    parameter_name = 'payment_status'
    
    def lookups(self, request, model_admin):
        return (
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'paid':
            return queryset.filter(paid_at__isnull=False)
        elif self.value() == 'unpaid':
            return queryset.filter(paid_at__isnull=True)
        return queryset


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for Order model.
    Provides comprehensive order management with status tracking and payment information.
    """
    list_display = (
        'order_number',
        'user',
        'status_display',
        'payment_status_display',
        'total',
        'item_count_display',
        'payment_method',
        'created_at',
        'can_be_cancelled_display'
    )
    list_filter = (
        OrderStatusFilter,
        PaymentStatusFilter,
        'payment_method',
        'created_at',
        'updated_at'
    )
    search_fields = (
        'order_number',
        'user__username',
        'user__email',
        'shipping_name',
        'shipping_email',
        'payment_intent_id'
    )
    readonly_fields = (
        'id',
        'order_number',
        'user',
        'created_at',
        'updated_at',
        'payment_intent_id',
        'paid_at',
        'subtotal',
        'shipping_cost',
        'tax',
        'total',
        'item_count_display',
        'can_be_cancelled_display',
        'payment_status_display'
    )
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'id',
                'order_number',
                'user',
                'status',
                'tracking_number'
            )
        }),
        ('Pricing', {
            'fields': (
                'subtotal',
                'shipping_cost',
                'tax',
                'total',
                'item_count_display'
            )
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_name',
                'shipping_address_line1',
                'shipping_address_line2',
                'shipping_city',
                'shipping_state',
                'shipping_postal_code',
                'shipping_country',
                'shipping_phone'
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method',
                'payment_intent_id',
                'paid_at',
                'payment_status_display'
            )
        }),
        ('Status & Timestamps', {
            'fields': (
                'can_be_cancelled_display',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_processing',
        'mark_as_shipped',
        'mark_as_delivered',
        'mark_as_cancelled',
        'export_to_csv'
    ]
    
    def status_display(self, obj):
        """Display order status with color coding."""
        status_colors = {
            'pending': 'orange',
            'processing': 'blue',
            'shipped': 'purple',
            'delivered': 'green',
            'cancelled': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def payment_status_display(self, obj):
        """Display payment status with visual indicator."""
        if obj.is_paid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Paid</span><br>'
                '<small>{}</small>',
                obj.paid_at.strftime('%Y-%m-%d %H:%M') if obj.paid_at else ''
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unpaid</span>'
            )
    payment_status_display.short_description = 'Payment Status'
    
    def item_count_display(self, obj):
        """Display item count."""
        count = obj.item_count
        return format_html('<strong>{}</strong> item(s)', count)
    item_count_display.short_description = 'Items'
    
    def can_be_cancelled_display(self, obj):
        """Display whether order can be cancelled."""
        if obj.can_be_cancelled:
            return format_html(
                '<span style="color: green;">✓ Can be cancelled</span>'
            )
        else:
            return format_html(
                '<span style="color: gray;">✗ Cannot be cancelled</span>'
            )
    can_be_cancelled_display.short_description = 'Cancellation Status'
    
    def mark_as_processing(self, request, queryset):
        """Bulk action to mark orders as processing."""
        updated = queryset.filter(status='pending').update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as processing.')
    mark_as_processing.short_description = 'Mark as Processing'
    
    def mark_as_shipped(self, request, queryset):
        """Bulk action to mark orders as shipped."""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = 'Mark as Shipped'
    
    def mark_as_delivered(self, request, queryset):
        """Bulk action to mark orders as delivered."""
        updated = queryset.filter(status='shipped').update(status='delivered')
        self.message_user(request, f'{updated} order(s) marked as delivered.')
    mark_as_delivered.short_description = 'Mark as Delivered'
    
    def mark_as_cancelled(self, request, queryset):
        """Bulk action to mark orders as cancelled."""
        # Only allow cancellation of orders that can be cancelled
        cancellable = [order for order in queryset if order.can_be_cancelled]
        count = 0
        for order in cancellable:
            order.status = 'cancelled'
            order.save()
            count += 1
        
        if count > 0:
            self.message_user(request, f'{count} order(s) marked as cancelled.')
        else:
            self.message_user(
                request,
                'No orders could be cancelled. Orders can only be cancelled within 24 hours and if not yet shipped.',
                level='warning'
            )
    mark_as_cancelled.short_description = 'Mark as Cancelled (if eligible)'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export orders to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order Number', 'User', 'Status', 'Payment Method', 'Total',
            'Items', 'Paid', 'Created', 'Shipping Name', 'Shipping City',
            'Shipping Country'
        ])
        
        for order in queryset:
            writer.writerow([
                order.order_number,
                order.user.username,
                order.get_status_display(),
                order.get_payment_method_display(),
                f'${order.total:.2f}',
                order.item_count,
                'Yes' if order.is_paid else 'No',
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.shipping_name,
                order.shipping_city,
                order.shipping_country
            ])
        
        self.message_user(request, f'Exported {queryset.count()} order(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected orders to CSV'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of orders to preserve order history."""
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model."""
    list_display = (
        'id_short',
        'order_number_display',
        'product_name',
        'variant_name',
        'quantity',
        'unit_price',
        'total_price',
        'created_at'
    )
    list_filter = ('created_at', 'product__category')
    search_fields = (
        'order__order_number',
        'order__user__username',
        'product_name',
        'variant_name',
        'product__name'
    )
    readonly_fields = (
        'id',
        'order',
        'product',
        'variant',
        'product_name',
        'variant_name',
        'quantity',
        'unit_price',
        'total_price',
        'created_at'
    )
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order')
        }),
        ('Product Information', {
            'fields': (
                'product',
                'variant',
                'product_name',
                'variant_name'
            )
        }),
        ('Pricing', {
            'fields': (
                'quantity',
                'unit_price',
                'total_price'
            )
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['export_to_csv']
    
    def id_short(self, obj):
        """Display shortened order item ID."""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'Item ID'
    
    def order_number_display(self, obj):
        """Display order number with link."""
        return format_html(
            '<a href="/admin/store/order/{}/change/">{}</a>',
            obj.order.id,
            obj.order.order_number
        )
    order_number_display.short_description = 'Order Number'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export order items to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="order_items.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order Number', 'User', 'Product', 'Variant', 'Quantity',
            'Unit Price', 'Total Price', 'Order Date'
        ])
        
        for item in queryset:
            writer.writerow([
                item.order.order_number,
                item.order.user.username,
                item.product_name,
                item.variant_name or '',
                item.quantity,
                f'${item.unit_price:.2f}',
                f'${item.total_price:.2f}',
                item.order.created_at.strftime('%Y-%m-%d')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} order item(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected order items to CSV'
    
    def has_add_permission(self, request):
        """Prevent adding order items directly (should be created with orders)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of order items to preserve order history."""
        return False


# ============================================================================
# Newsletter Admin
# ============================================================================

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """
    Admin interface for NewsletterSubscriber model.
    
    Allows managing newsletter subscriptions, viewing subscriber lists,
    and exporting subscriber data.
    """
    list_display = (
        'email',
        'is_active',
        'subscribed_at',
        'status_display'
    )
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at', 'unsubscribe_token', 'unsubscribe_link')
    
    fieldsets = (
        ('Subscriber Information', {
            'fields': ('email', 'is_active')
        }),
        ('Subscription Details', {
            'fields': ('subscribed_at', 'unsubscribe_token', 'unsubscribe_link'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'export_to_csv']
    
    def status_display(self, obj):
        """Display subscription status with visual indicator."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Unsubscribed</span>'
            )
    status_display.short_description = 'Status'
    
    def unsubscribe_link(self, obj):
        """Display unsubscribe link for testing."""
        if obj.unsubscribe_token:
            from django.urls import reverse
            url = reverse('store:newsletter_unsubscribe', args=[obj.unsubscribe_token])
            full_url = f"http://localhost:8000{url}"  # In production, use actual domain
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                full_url,
                full_url
            )
        return "N/A"
    unsubscribe_link.short_description = 'Unsubscribe Link'
    
    def activate_subscriptions(self, request, queryset):
        """Bulk action to activate subscriptions."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscription(s) activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'
    
    def deactivate_subscriptions(self, request, queryset):
        """Bulk action to deactivate subscriptions."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscription(s) deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'
    
    def export_to_csv(self, request, queryset):
        """Bulk action to export subscribers to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="newsletter_subscribers.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Status', 'Subscribed Date'])
        
        for subscriber in queryset:
            writer.writerow([
                subscriber.email,
                'Active' if subscriber.is_active else 'Unsubscribed',
                subscriber.subscribed_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        self.message_user(request, f'Exported {queryset.count()} subscriber(s) to CSV.')
        return response
    export_to_csv.short_description = 'Export selected subscribers to CSV'
