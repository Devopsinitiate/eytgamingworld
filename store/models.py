"""
Database models for the EYTGaming Store.

This module contains models for:
- Products and product variants
- Categories
- Shopping cart
- Orders
- Wishlist
- Product reviews
- Inventory tracking
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid


class Category(models.Model):
    """
    Product category model for organizing products.
    Supports hierarchical categories with parent-child relationships.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'display_order']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product model representing items available for purchase.
    Implements soft delete to preserve order history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)  # Soft delete flag
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['slug']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Soft delete implementation - marks product as inactive instead of deleting.
        This preserves order history integrity.
        """
        self.is_active = False
        self.save()

    def hard_delete(self, *args, **kwargs):
        """
        Permanently delete the product from the database.
        Use with caution - only for data cleanup.
        """
        super().delete(*args, **kwargs)

    @property
    def is_in_stock(self):
        """Check if product has stock available."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product stock is low (below 10 units)."""
        return 0 < self.stock_quantity < 10
    
    @property
    def average_rating(self):
        """
        Calculate average rating from all reviews.
        Returns None if no reviews exist.
        
        Requirements: 12.7
        """
        from django.db.models import Avg
        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        avg = result.get('avg_rating')
        return round(avg, 1) if avg is not None else None
    
    @property
    def review_count(self):
        """Get total number of reviews for this product."""
        return self.reviews.count()


class ProductVariant(models.Model):
    """
    Product variant model for different versions of a product.
    Examples: sizes (S, M, L, XL), colors (Red, Blue, Black).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(
        max_length=100,
        help_text='e.g., "Size: Large" or "Color: Red"'
    )
    sku = models.CharField(max_length=100, unique=True)
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Additional cost for this variant (can be negative for discounts)'
    )
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['product', 'is_available']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self):
        """Calculate the final price including the base product price and adjustment."""
        return self.product.price + self.price_adjustment

    @property
    def is_in_stock(self):
        """Check if variant has stock available."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if variant stock is low (below 10 units)."""
        return 0 < self.stock_quantity < 10


class ProductImage(models.Model):
    """
    Product image model for storing multiple images per product.
    Supports primary image designation and custom ordering.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='products/',
        help_text='Product image (JPEG, PNG, WebP - max 5MB)'
    )
    alt_text = models.CharField(
        max_length=200,
        help_text='Descriptive text for accessibility'
    )
    display_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary image displayed in product listings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-is_primary', 'created_at']
        indexes = [
            models.Index(fields=['product', 'display_order']),
            models.Index(fields=['product', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.display_order}"

    def save(self, *args, **kwargs):
        """
        Ensure only one primary image per product.
        If this image is set as primary, unset other primary images.
        """
        if self.is_primary:
            # Unset other primary images for this product
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class Cart(models.Model):
    """
    Shopping cart model for storing user cart data.
    Supports both authenticated users and guest sessions.
    
    For authenticated users: cart is linked to user account
    For guest users: cart is linked to session key
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carts',
        help_text='Authenticated user who owns this cart'
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text='Session key for guest users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Guest Cart ({self.session_key[:8]}...)"

    @property
    def item_count(self):
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def is_empty(self):
        """Check if cart has no items."""
        return not self.items.exists()


class CartItem(models.Model):
    """
    Cart item model representing a product in a shopping cart.
    Supports product variants and quantity tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cart_items',
        help_text='Optional product variant (e.g., size, color)'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantity of this item in the cart'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        if self.variant:
            return f"{self.product.name} - {self.variant.name} (x{self.quantity})"
        return f"{self.product.name} (x{self.quantity})"

    @property
    def unit_price(self):
        """Get the unit price for this item (product or variant price)."""
        if self.variant:
            return self.variant.final_price
        return self.product.price

    @property
    def total_price(self):
        """Calculate total price for this cart item (unit_price × quantity)."""
        return self.unit_price * self.quantity

    @property
    def is_available(self):
        """Check if the item is still available for purchase."""
        if not self.product.is_active:
            return False
        if self.variant and not self.variant.is_available:
            return False
        return True

    @property
    def has_sufficient_stock(self):
        """Check if there's sufficient stock for the requested quantity."""
        if self.variant:
            return self.variant.stock_quantity >= self.quantity
        return self.product.stock_quantity >= self.quantity


class Order(models.Model):
    """
    Order model representing a completed purchase.
    Stores all order details including pricing, shipping, payment, and status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paystack', 'Paystack'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique order number (e.g., EYT-2024-001234)'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        help_text='User who placed the order'
    )
    
    # Pricing fields
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Sum of all item prices before shipping and tax'
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Shipping cost'
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Tax amount'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total amount (subtotal + shipping + tax)'
    )
    
    # Shipping information
    shipping_name = models.CharField(max_length=200)
    shipping_address_line1 = models.CharField(max_length=200)
    shipping_address_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=20)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current order status'
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Shipping tracking number'
    )
    
    # Payment information
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        help_text='Payment method used (Stripe or Paystack)'
    )
    payment_intent_id = models.CharField(
        max_length=200,
        help_text='Payment gateway transaction ID'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when payment was confirmed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['payment_intent_id']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"
    
    @property
    def is_paid(self):
        """Check if order has been paid."""
        return self.paid_at is not None
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled (within 24 hours and not yet shipped)."""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status in ['shipped', 'delivered', 'cancelled']:
            return False
        
        # Check if order is within 24 hours
        time_since_order = timezone.now() - self.created_at
        return time_since_order < timedelta(hours=24)
    
    @property
    def item_count(self):
        """Get total number of items in order."""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """
    Order item model representing a product in an order.
    Stores product snapshots to preserve order history even if product changes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        help_text='Reference to the product (preserved even if product is deleted)'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='order_items',
        help_text='Optional product variant'
    )
    
    # Product snapshots - preserve product details at time of purchase
    product_name = models.CharField(
        max_length=200,
        help_text='Product name at time of purchase'
    )
    variant_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Variant name at time of purchase'
    )
    
    # Pricing and quantity
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantity ordered'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Price per unit at time of purchase'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total price for this item (unit_price × quantity)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        if self.variant_name:
            return f"{self.product_name} - {self.variant_name} (x{self.quantity})"
        return f"{self.product_name} (x{self.quantity})"
    
    def save(self, *args, **kwargs):
        """
        Auto-calculate total_price if not set.
        This ensures consistency between unit_price, quantity, and total_price.
        """
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)



# ============================================================================
# Wishlist Models
# ============================================================================

class Wishlist(models.Model):
    """
    Wishlist for authenticated users.
    
    A wishlist allows users to save products they're interested in
    for future purchase. Each user can have only one wishlist.
    
    Requirements: 11.1, 11.2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist',
        help_text='User who owns this wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Wishlist for {self.user.username}"
    
    @property
    def item_count(self):
        """Get total number of items in wishlist."""
        return self.items.count()
    
    @property
    def is_empty(self):
        """Check if wishlist is empty."""
        return self.item_count == 0


class WishlistItem(models.Model):
    """
    Individual item in a wishlist.
    
    Represents a product that a user has saved to their wishlist.
    Each product can only appear once in a user's wishlist.
    
    Requirements: 11.1, 11.2
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Wishlist this item belongs to'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        help_text='Product in wishlist'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ['wishlist', 'product']
        indexes = [
            models.Index(fields=['wishlist', 'product']),
            models.Index(fields=['-added_at']),
        ]
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"
    
    @property
    def is_available(self):
        """Check if product is still available for purchase."""
        return self.product.is_active and self.product.is_in_stock


# ============================================================================
# Product Review Models
# ============================================================================

class ProductReview(models.Model):
    """
    Product review model for customer feedback.
    
    Allows customers who have purchased a product to leave a rating
    and optional text review. Each user can only review a product once
    per order to prevent duplicate reviews.
    
    Requirements: 12.1, 12.2, 12.3, 12.5
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Product being reviewed'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        help_text='User who wrote the review'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text='Order in which the product was purchased'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5 stars'
    )
    comment = models.TextField(
        blank=True,
        help_text='Optional text review (will be sanitized)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        unique_together = ['product', 'user', 'order']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s review of {self.product.name} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        """
        Sanitize comment content before saving to prevent XSS attacks.
        """
        if self.comment:
            # Import here to avoid circular imports
            from .utils import InputValidator
            self.comment = InputValidator.sanitize_html(self.comment)
        super().save(*args, **kwargs)


# ============================================================================
# Newsletter Models
# ============================================================================

class NewsletterSubscriber(models.Model):
    """
    Newsletter subscriber model for email marketing.
    
    Stores email addresses of users who want to receive newsletters
    about new products, promotions, and updates. Includes unsubscribe
    functionality via unique token.
    
    Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True,
        help_text='Subscriber email address'
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether subscription is active'
    )
    unsubscribe_token = models.CharField(
        max_length=64,
        unique=True,
        help_text='Unique token for unsubscribe link'
    )
    
    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['unsubscribe_token']),
        ]
        ordering = ['-subscribed_at']
    
    def __str__(self):
        status = 'Active' if self.is_active else 'Unsubscribed'
        return f"{self.email} ({status})"
    
    def save(self, *args, **kwargs):
        """
        Generate unsubscribe token if not set.
        """
        if not self.unsubscribe_token:
            import secrets
            self.unsubscribe_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)
