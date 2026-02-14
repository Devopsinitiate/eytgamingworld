"""
Business logic managers for the EYTGaming Store.

This module contains manager classes that encapsulate business logic:
- CartManager: Shopping cart operations
- OrderManager: Order creation and management
- InventoryManager: Stock management
- PaymentProcessor: Payment processing (abstract interface)
- StripePaymentProcessor: Stripe payment gateway integration
- PaystackPaymentProcessor: Paystack payment gateway integration
"""

from abc import ABC, abstractmethod
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import stripe
import requests
import hmac
import hashlib
import logging
from .models import Cart, CartItem, Product, ProductVariant, Order, OrderItem

# Configure logger
logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Raised when attempting to add more items than available in stock."""
    pass


class InventoryManager:
    """
    Business logic manager for inventory and stock management.
    
    Handles:
    - Stock availability checking
    - Stock reservation with atomic transactions
    - Stock restoration on order cancellation
    - Prevention of race conditions using SELECT FOR UPDATE
    
    This manager is critical for preventing overselling by ensuring
    that stock operations are atomic and properly locked.
    """
    
    @staticmethod
    def check_availability(product, variant=None, quantity=1):
        """
        Check if product/variant has sufficient stock.
        
        Args:
            product: Product object to check
            variant: ProductVariant object (optional)
            quantity: Quantity to check (default: 1)
            
        Returns:
            bool: True if sufficient stock available, False otherwise
        """
        if variant:
            return variant.stock_quantity >= quantity
        return product.stock_quantity >= quantity
    
    @staticmethod
    @transaction.atomic
    def reserve_stock(product, variant=None, quantity=1):
        """
        Reserve stock for order (atomic operation with row-level locking).
        
        Uses SELECT FOR UPDATE to prevent race conditions when multiple
        users attempt to purchase the same product simultaneously.
        
        This method MUST be called within a transaction to ensure atomicity.
        
        Args:
            product: Product object to reserve stock from
            variant: ProductVariant object (optional)
            quantity: Quantity to reserve
            
        Returns:
            None
            
        Raises:
            InsufficientStockError: If insufficient stock available
        """
        if variant:
            # Lock the variant row for update to prevent race conditions
            locked_variant = ProductVariant.objects.select_for_update().get(id=variant.id)
            
            if locked_variant.stock_quantity < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for {product.name} - {variant.name}. "
                    f"Available: {locked_variant.stock_quantity}, Requested: {quantity}"
                )
            
            locked_variant.stock_quantity -= quantity
            locked_variant.save()
        else:
            # Lock the product row for update to prevent race conditions
            locked_product = Product.objects.select_for_update().get(id=product.id)
            
            if locked_product.stock_quantity < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {locked_product.stock_quantity}, Requested: {quantity}"
                )
            
            locked_product.stock_quantity -= quantity
            locked_product.save()
    
    @staticmethod
    @transaction.atomic
    def restore_stock(order):
        """
        Restore stock when order is cancelled.
        
        Uses SELECT FOR UPDATE to ensure atomic stock restoration.
        Iterates through all order items and restores their quantities.
        
        Args:
            order: Order object whose stock should be restored
            
        Returns:
            None
        """
        for item in order.items.all():
            if item.variant:
                # Lock the variant row for update
                locked_variant = ProductVariant.objects.select_for_update().get(
                    id=item.variant.id
                )
                locked_variant.stock_quantity += item.quantity
                locked_variant.save()
            else:
                # Lock the product row for update
                locked_product = Product.objects.select_for_update().get(
                    id=item.product.id
                )
                locked_product.stock_quantity += item.quantity
                locked_product.save()


class CartManager:
    """
    Business logic manager for shopping cart operations.
    
    Handles:
    - Cart creation and retrieval
    - Adding items with stock validation
    - Updating quantities
    - Removing items
    - Merging carts on login
    - Total calculation
    """
    
    @staticmethod
    def get_or_create_cart(user=None, session_key=None):
        """
        Get existing cart or create new one.
        
        For authenticated users: retrieves cart by user
        For guest users: retrieves cart by session_key
        
        Args:
            user: Authenticated User object (optional)
            session_key: Session key for guest users (optional)
            
        Returns:
            Cart: The user's cart (existing or newly created)
            
        Raises:
            ValueError: If neither user nor session_key is provided
        """
        if not user and not session_key:
            raise ValueError("Either user or session_key must be provided")
        
        if user:
            # For authenticated users, get or create cart by user
            cart, created = Cart.objects.get_or_create(
                user=user,
                defaults={'session_key': None}
            )
        else:
            # For guest users, get or create cart by session_key
            cart, created = Cart.objects.get_or_create(
                session_key=session_key,
                user=None,
                defaults={'session_key': session_key}
            )
        
        return cart
    
    @staticmethod
    def add_item(cart, product, variant=None, quantity=1):
        """
        Add item to cart with stock validation.
        
        If the item already exists in the cart, increases the quantity.
        Validates that sufficient stock is available before adding.
        
        Args:
            cart: Cart object to add item to
            product: Product object to add
            variant: ProductVariant object (optional)
            quantity: Quantity to add (default: 1)
            
        Returns:
            CartItem: The created or updated cart item
            
        Raises:
            ValidationError: If quantity is invalid
            InsufficientStockError: If insufficient stock available
        """
        from django.core.cache import cache
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            raise ValidationError("Quantity must be between 1 and 100")
        
        # Check if product is active
        if not product.is_active:
            raise ValidationError("This product is no longer available")
        
        # Check if variant is available (if specified)
        if variant and not variant.is_available:
            raise ValidationError("This product variant is not available")
        
        # Check stock availability
        available_stock = variant.stock_quantity if variant else product.stock_quantity
        
        # Check if item already exists in cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=product,
                variant=variant
            )
            # Item exists, check if we can add more
            new_quantity = cart_item.quantity + quantity
            if new_quantity > available_stock:
                raise InsufficientStockError(
                    f"Only {available_stock} units available. "
                    f"You already have {cart_item.quantity} in your cart."
                )
            cart_item.quantity = new_quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # Item doesn't exist, create new cart item
            if quantity > available_stock:
                raise InsufficientStockError(
                    f"Only {available_stock} units available"
                )
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )
        
        # Invalidate cart total cache
        cache.delete(f'cart_total_{cart.id}')
        
        return cart_item
    
    @staticmethod
    def update_quantity(cart_item, quantity):
        """
        Update item quantity with validation.
        
        Args:
            cart_item: CartItem object to update
            quantity: New quantity value
            
        Returns:
            CartItem: The updated cart item
            
        Raises:
            ValidationError: If quantity is invalid
            InsufficientStockError: If insufficient stock available
        """
        from django.core.cache import cache
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            raise ValidationError("Quantity must be between 1 and 100")
        
        # Check stock availability
        available_stock = (
            cart_item.variant.stock_quantity 
            if cart_item.variant 
            else cart_item.product.stock_quantity
        )
        
        if quantity > available_stock:
            raise InsufficientStockError(
                f"Only {available_stock} units available"
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        # Invalidate cart total cache
        cache.delete(f'cart_total_{cart_item.cart.id}')
        
        return cart_item
    
    @staticmethod
    def remove_item(cart_item):
        """
        Remove item from cart.
        
        Args:
            cart_item: CartItem object to remove
            
        Returns:
            None
        """
        from django.core.cache import cache
        
        # Invalidate cart total cache before deleting
        cache.delete(f'cart_total_{cart_item.cart.id}')
        
        cart_item.delete()
    
    @staticmethod
    @transaction.atomic
    def merge_carts(session_cart, user_cart):
        """
        Merge session cart into user cart on login.
        
        When a user logs in with items in their session cart,
        this method merges those items into their persistent user cart.
        If an item exists in both carts, quantities are combined.
        
        Args:
            session_cart: Cart object for guest session
            user_cart: Cart object for authenticated user
            
        Returns:
            Cart: The merged user cart
            
        Raises:
            InsufficientStockError: If combined quantities exceed stock
        """
        # Get all items from session cart
        session_items = session_cart.items.all()
        
        for session_item in session_items:
            try:
                # Check if item already exists in user cart
                user_item = CartItem.objects.get(
                    cart=user_cart,
                    product=session_item.product,
                    variant=session_item.variant
                )
                
                # Item exists, combine quantities
                new_quantity = user_item.quantity + session_item.quantity
                
                # Check stock availability
                available_stock = (
                    session_item.variant.stock_quantity 
                    if session_item.variant 
                    else session_item.product.stock_quantity
                )
                
                # Respect both stock limits and maximum quantity of 100
                if new_quantity > 100:
                    user_item.quantity = min(available_stock, 100)
                elif new_quantity > available_stock:
                    user_item.quantity = available_stock
                else:
                    user_item.quantity = new_quantity
                
                user_item.save()
                
            except CartItem.DoesNotExist:
                # Item doesn't exist in user cart, move it over
                session_item.cart = user_cart
                session_item.save()
        
        # Delete the session cart
        session_cart.delete()
        
        return user_cart
    
    @staticmethod
    def calculate_total(cart):
        """
        Calculate cart total with caching.
        
        Calculates the sum of (quantity × unit_price) for all items in the cart.
        Results are cached for 5 minutes to reduce database queries.
        
        Args:
            cart: Cart object to calculate total for
            
        Returns:
            Decimal: Total price for all items in cart
        """
        from django.core.cache import cache
        
        # Try to get from cache
        cache_key = f'cart_total_{cart.id}'
        cached_total = cache.get(cache_key)
        if cached_total is not None:
            return Decimal(cached_total)
        
        # Calculate total
        total = Decimal('0.00')
        for item in cart.items.all():
            total += item.total_price
        
        # Cache for 5 minutes
        cache.set(cache_key, str(total), 60 * 5)
        
        return total
    
    @staticmethod
    def clear_cart(cart):
        """
        Remove all items from cart.
        
        Args:
            cart: Cart object to clear
            
        Returns:
            None
        """
        cart.items.all().delete()



class OrderManager:
    """
    Business logic manager for order creation and management.
    
    Handles:
    - Order creation from cart with transaction safety
    - Unique order number generation
    - Order status updates
    - Order cancellation with stock restoration
    - User order retrieval
    
    This manager ensures atomic order creation with inventory management
    and provides methods for order lifecycle management.
    """
    
    @staticmethod
    @transaction.atomic
    def create_order(user, cart, shipping_info, payment_method, payment_intent_id):
        """
        Create order from cart with transaction safety.
        
        This method performs the following operations atomically:
        1. Validates cart has items
        2. Reserves stock for all items
        3. Creates order with shipping and payment info
        4. Creates order items with product snapshots
        5. Clears the cart
        
        All operations are wrapped in a database transaction to ensure
        atomicity - if any step fails, all changes are rolled back.
        
        Args:
            user: User object placing the order
            cart: Cart object to create order from
            shipping_info: Dictionary containing shipping address fields:
                - shipping_name
                - shipping_address_line1
                - shipping_address_line2 (optional)
                - shipping_city
                - shipping_state
                - shipping_postal_code
                - shipping_country
                - shipping_phone
            payment_method: Payment method ('stripe' or 'paystack')
            payment_intent_id: Payment gateway transaction ID
            
        Returns:
            Order: The created order object
            
        Raises:
            ValidationError: If cart is empty or shipping info is invalid
            InsufficientStockError: If any item has insufficient stock
        """
        # Validate cart has items
        if cart.is_empty:
            raise ValidationError("Cannot create order from empty cart")
        
        # Validate shipping info
        required_fields = [
            'shipping_name', 'shipping_address_line1', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'shipping_phone'
        ]
        for field in required_fields:
            if not shipping_info.get(field):
                raise ValidationError(f"Missing required field: {field}")
        
        # Calculate order totals
        subtotal = Decimal('0.00')
        cart_items = cart.items.select_related('product', 'variant').all()
        
        # Reserve stock for all items first (will raise InsufficientStockError if any fail)
        for cart_item in cart_items:
            # Check availability before reserving
            if not cart_item.is_available:
                raise ValidationError(
                    f"{cart_item.product.name} is no longer available"
                )
            
            if not cart_item.has_sufficient_stock:
                available = (
                    cart_item.variant.stock_quantity 
                    if cart_item.variant 
                    else cart_item.product.stock_quantity
                )
                raise InsufficientStockError(
                    f"Insufficient stock for {cart_item.product.name}. "
                    f"Available: {available}, Requested: {cart_item.quantity}"
                )
            
            # Reserve stock (atomic operation with row-level locking)
            InventoryManager.reserve_stock(
                cart_item.product,
                cart_item.variant,
                cart_item.quantity
            )
            
            # Calculate subtotal
            subtotal += cart_item.total_price
        
        # Calculate shipping and tax (simplified for now)
        # TODO: Implement proper shipping cost calculation based on location
        shipping_cost = Decimal('10.00')  # Flat rate for now
        tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% tax rate, rounded to 2 decimal places
        total = subtotal + shipping_cost + tax
        
        # Generate unique order number
        order_number = OrderManager.generate_order_number()
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            user=user,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            shipping_name=shipping_info['shipping_name'],
            shipping_address_line1=shipping_info['shipping_address_line1'],
            shipping_address_line2=shipping_info.get('shipping_address_line2', ''),
            shipping_city=shipping_info['shipping_city'],
            shipping_state=shipping_info['shipping_state'],
            shipping_postal_code=shipping_info['shipping_postal_code'],
            shipping_country=shipping_info['shipping_country'],
            shipping_phone=shipping_info['shipping_phone'],
            payment_method=payment_method,
            payment_intent_id=payment_intent_id,
            status='pending'
        )
        
        # Create order items with product snapshots
        for cart_item in cart_items:
            # Get unit price
            unit_price = cart_item.unit_price
            
            # Create order item with product snapshot
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_name=cart_item.variant.name if cart_item.variant else '',
                quantity=cart_item.quantity,
                unit_price=unit_price,
                total_price=cart_item.total_price
            )
        
        # Clear the cart
        CartManager.clear_cart(cart)
        
        return order
    
    @staticmethod
    def generate_order_number():
        """
        Generate unique order number in format EYT-YYYY-NNNNNN.
        
        Format:
        - EYT: Prefix for EYTGaming
        - YYYY: Current year
        - NNNNNN: Sequential 6-digit number (padded with zeros)
        
        The sequential number is based on the count of orders created
        in the current year, ensuring uniqueness.
        
        Returns:
            str: Unique order number (e.g., "EYT-2024-000001")
        """
        from django.db import transaction
        
        current_year = datetime.now().year
        
        # Use a transaction to ensure atomicity
        with transaction.atomic():
            # Get count of orders created this year
            year_start = datetime(current_year, 1, 1)
            year_orders_count = Order.objects.filter(
                created_at__gte=year_start
            ).count()
            
            # Generate sequential number (next order number)
            sequential_number = year_orders_count + 1
            
            # Format: EYT-YYYY-NNNNNN
            order_number = f"EYT-{current_year}-{sequential_number:06d}"
            
            # Ensure uniqueness (handle race conditions)
            while Order.objects.filter(order_number=order_number).exists():
                sequential_number += 1
                order_number = f"EYT-{current_year}-{sequential_number:06d}"
        
        return order_number
    
    @staticmethod
    def update_status(order, new_status, tracking_number=None):
        """
        Update order status and optionally set tracking number.
        
        Valid status transitions:
        - pending -> processing
        - processing -> shipped
        - shipped -> delivered
        - pending/processing -> cancelled
        
        Args:
            order: Order object to update
            new_status: New status value (must be in Order.STATUS_CHOICES)
            tracking_number: Optional tracking number (for shipped status)
            
        Returns:
            Order: The updated order object
            
        Raises:
            ValidationError: If status transition is invalid
        """
        # Validate new status
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid status: {new_status}")
        
        # Validate status transitions
        current_status = order.status
        
        # Define valid transitions
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],  # Terminal state
            'cancelled': [],  # Terminal state
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise ValidationError(
                f"Invalid status transition from {current_status} to {new_status}"
            )
        
        # Update order status
        order.status = new_status
        
        # Set tracking number if provided and status is shipped
        if new_status == 'shipped' and tracking_number:
            order.tracking_number = tracking_number
        
        order.save()
        
        # Send email notification based on status change
        from .utils import EmailNotificationService
        
        if new_status == 'processing':
            # Send order confirmation email
            EmailNotificationService.send_order_confirmation(order)
        elif new_status == 'shipped':
            # Send shipping notification email
            EmailNotificationService.send_shipping_notification(order)
        elif new_status == 'delivered':
            # Send delivery confirmation email
            EmailNotificationService.send_delivery_confirmation(order)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order):
        """
        Cancel order and restore inventory.
        
        This method can only cancel orders that meet the following criteria:
        - Order is within 24 hours of creation
        - Order status is 'pending' or 'processing'
        - Order has not been shipped
        
        When an order is cancelled:
        1. Order status is set to 'cancelled'
        2. Stock quantities are restored for all items
        
        Args:
            order: Order object to cancel
            
        Returns:
            Order: The cancelled order object
            
        Raises:
            ValidationError: If order cannot be cancelled
        """
        # Check if order can be cancelled
        if not order.can_be_cancelled:
            if order.status in ['shipped', 'delivered']:
                raise ValidationError(
                    "Cannot cancel order that has been shipped or delivered"
                )
            elif order.status == 'cancelled':
                raise ValidationError("Order is already cancelled")
            else:
                raise ValidationError(
                    "Cannot cancel order after 24 hours of placement"
                )
        
        # Update order status to cancelled
        order.status = 'cancelled'
        order.save()
        
        # Restore stock for all order items
        InventoryManager.restore_stock(order)
        
        # TODO: Process refund if payment was captured
        # This will be implemented in payment integration tasks
        
        # TODO: Send cancellation email to customer
        # This will be implemented in task 17.2
        
        return order
    
    @staticmethod
    def get_user_orders(user, status=None):
        """
        Get all orders for a user, optionally filtered by status.
        
        Returns orders in reverse chronological order (newest first).
        Prefetches related items for efficient querying.
        
        Args:
            user: User object to get orders for
            status: Optional status filter (e.g., 'pending', 'shipped')
            
        Returns:
            QuerySet: Orders for the user, ordered by creation date (newest first)
        """
        orders = Order.objects.filter(user=user).prefetch_related(
            'items',
            'items__product',
            'items__variant'
        ).order_by('-created_at')
        
        if status:
            orders = orders.filter(status=status)
        
        return orders



class PaymentProcessorError(Exception):
    """Base exception for payment processing errors."""
    pass


class PaymentProcessor(ABC):
    """
    Abstract base class for payment processing.
    
    This interface defines the contract that all payment processors must implement.
    It provides methods for:
    - Creating payment intents
    - Confirming payments
    - Refunding payments
    - Verifying webhook signatures
    
    Security Requirements:
    - Never log or store complete credit card numbers (Requirement 2.7)
    - Verify webhook signatures to prevent tampering (Requirement 2.8)
    - Use HTTPS for all payment communications (Requirement 2.2)
    - Handle sensitive card data through payment gateway (Requirement 2.1)
    """
    
    @abstractmethod
    def create_payment_intent(self, amount, currency, metadata=None):
        """
        Create payment intent and return client secret.
        
        This method initializes a payment transaction with the payment gateway.
        The client secret is used by the frontend to complete the payment.
        
        Args:
            amount: Payment amount as Decimal
            currency: Currency code (e.g., 'usd', 'ngn')
            metadata: Optional dictionary of metadata to attach to payment
            
        Returns:
            dict: Payment intent data including client_secret
            
        Raises:
            PaymentProcessorError: If payment intent creation fails
        """
        pass
    
    @abstractmethod
    def confirm_payment(self, payment_intent_id):
        """
        Confirm payment was successful.
        
        This method verifies that a payment has been successfully processed
        by the payment gateway.
        
        Args:
            payment_intent_id: Payment gateway transaction ID
            
        Returns:
            bool: True if payment succeeded, False otherwise
            
        Raises:
            PaymentProcessorError: If payment confirmation fails
        """
        pass
    
    @abstractmethod
    def refund_payment(self, payment_intent_id, amount=None):
        """
        Process refund for a payment.
        
        This method initiates a refund for a previously successful payment.
        If amount is not specified, refunds the full payment amount.
        
        Args:
            payment_intent_id: Payment gateway transaction ID
            amount: Optional refund amount (defaults to full refund)
            
        Returns:
            dict: Refund data including refund_id and status
            
        Raises:
            PaymentProcessorError: If refund processing fails
        """
        pass
    
    @abstractmethod
    def verify_webhook(self, payload, signature):
        """
        Verify webhook signature to prevent tampering.
        
        This method validates that a webhook request actually came from
        the payment gateway and has not been tampered with.
        
        Security: This is critical for preventing fraudulent webhook requests
        that could mark orders as paid without actual payment.
        
        Args:
            payload: Raw webhook payload (bytes or string)
            signature: Signature from webhook headers
            
        Returns:
            dict: Parsed webhook event data if signature is valid
            
        Raises:
            PaymentProcessorError: If signature verification fails
        """
        pass


class StripePaymentProcessor(PaymentProcessor):
    """
    Stripe payment gateway integration.
    
    Implements the PaymentProcessor interface for Stripe payments.
    Uses Stripe's Python SDK for secure payment processing.
    
    Security Features:
    - PCI DSS compliant card input via Stripe Elements (Requirement 2.3)
    - Webhook signature verification (Requirement 2.8)
    - No card data stored on server (Requirement 2.1, 2.7)
    - HTTPS for all communications (Requirement 2.2)
    
    Configuration:
    - STRIPE_SECRET_KEY: API secret key from environment
    - STRIPE_WEBHOOK_SECRET: Webhook signing secret from environment
    """
    
    def __init__(self):
        """Initialize Stripe payment processor with API credentials."""
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY
        
        if not settings.STRIPE_SECRET_KEY:
            logger.error("STRIPE_SECRET_KEY not configured")
            raise ValueError("STRIPE_SECRET_KEY must be configured")
    
    def create_payment_intent(self, amount, currency='usd', metadata=None):
        """
        Create Stripe payment intent.
        
        Stripe amounts are in cents, so we multiply by 100.
        
        Args:
            amount: Payment amount as Decimal (e.g., 99.99)
            currency: Currency code (default: 'usd')
            metadata: Optional metadata dictionary
            
        Returns:
            dict: Payment intent data with client_secret
            
        Raises:
            PaymentProcessorError: If payment intent creation fails
        """
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Create payment intent
            intent = self.stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            
            logger.info(
                f"Stripe payment intent created: {intent.id}",
                extra={'payment_intent_id': intent.id, 'amount': amount}
            )
            
            return {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency,
                'status': intent.status
            }
            
        except stripe.error.StripeError as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Stripe payment intent creation failed: {str(e)}",
                extra={'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to create payment intent: {str(e)}")
    
    def confirm_payment(self, payment_intent_id):
        """
        Confirm Stripe payment was successful.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            bool: True if payment succeeded, False otherwise
            
        Raises:
            PaymentProcessorError: If payment confirmation fails
        """
        try:
            # Retrieve payment intent
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Check if payment succeeded
            is_successful = intent.status == 'succeeded'
            
            if is_successful:
                logger.info(
                    f"Stripe payment confirmed: {payment_intent_id}",
                    extra={'payment_intent_id': payment_intent_id}
                )
            else:
                logger.warning(
                    f"Stripe payment not successful: {payment_intent_id}, status: {intent.status}",
                    extra={'payment_intent_id': payment_intent_id, 'status': intent.status}
                )
            
            return is_successful
            
        except stripe.error.StripeError as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Stripe payment confirmation failed: {str(e)}",
                extra={'payment_intent_id': payment_intent_id, 'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to confirm payment: {str(e)}")
    
    def refund_payment(self, payment_intent_id, amount=None):
        """
        Process Stripe refund.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Optional refund amount in dollars (defaults to full refund)
            
        Returns:
            dict: Refund data including refund_id and status
            
        Raises:
            PaymentProcessorError: If refund processing fails
        """
        try:
            # Prepare refund parameters
            refund_params = {'payment_intent': payment_intent_id}
            
            # If partial refund, convert amount to cents
            if amount is not None:
                refund_params['amount'] = int(amount * 100)
            
            # Create refund
            refund = self.stripe.Refund.create(**refund_params)
            
            logger.info(
                f"Stripe refund created: {refund.id} for payment {payment_intent_id}",
                extra={'refund_id': refund.id, 'payment_intent_id': payment_intent_id}
            )
            
            return {
                'refund_id': refund.id,
                'status': refund.status,
                'amount': Decimal(refund.amount) / 100,  # Convert back to dollars
                'currency': refund.currency
            }
            
        except stripe.error.StripeError as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Stripe refund failed: {str(e)}",
                extra={'payment_intent_id': payment_intent_id, 'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to process refund: {str(e)}")
    
    def verify_webhook(self, payload, signature):
        """
        Verify Stripe webhook signature.
        
        This is critical for security - it ensures the webhook actually
        came from Stripe and hasn't been tampered with.
        
        Args:
            payload: Raw webhook payload (bytes)
            signature: Stripe-Signature header value
            
        Returns:
            dict: Parsed webhook event data
            
        Raises:
            PaymentProcessorError: If signature verification fails
        """
        try:
            # Verify webhook signature and construct event
            event = self.stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            logger.info(
                f"Stripe webhook verified: {event['type']}",
                extra={'event_type': event['type'], 'event_id': event['id']}
            )
            
            return event
            
        except ValueError as e:
            # Invalid payload
            logger.error(
                f"Stripe webhook invalid payload: {str(e)}",
                extra={'error_type': 'invalid_payload'}
            )
            raise PaymentProcessorError("Invalid webhook payload")
            
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(
                f"Stripe webhook signature verification failed: {str(e)}",
                extra={'error_type': 'invalid_signature'}
            )
            raise PaymentProcessorError("Invalid webhook signature")


class PaystackPaymentProcessor(PaymentProcessor):
    """
    Paystack payment gateway integration.
    
    Implements the PaymentProcessor interface for Paystack payments.
    Uses Paystack's REST API for secure payment processing.
    
    Security Features:
    - Secure payment popup (Requirement 2.4)
    - Webhook signature verification (Requirement 2.8)
    - No card data stored on server (Requirement 2.1, 2.7)
    - HTTPS for all communications (Requirement 2.2)
    
    Configuration:
    - PAYSTACK_SECRET_KEY: API secret key from environment
    - PAYSTACK_WEBHOOK_SECRET: Webhook signing secret from environment
    """
    
    def __init__(self):
        """Initialize Paystack payment processor with API credentials."""
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = 'https://api.paystack.co'
        
        if not self.secret_key:
            logger.error("PAYSTACK_SECRET_KEY not configured")
            raise ValueError("PAYSTACK_SECRET_KEY must be configured")
    
    def _make_request(self, method, endpoint, data=None):
        """
        Make authenticated request to Paystack API.
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            endpoint: API endpoint path
            data: Optional request data
            
        Returns:
            dict: Response data
            
        Raises:
            PaymentProcessorError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Paystack API request failed: {str(e)}",
                extra={'endpoint': endpoint, 'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Paystack API request failed: {str(e)}")
    
    def create_payment_intent(self, amount, currency='NGN', metadata=None):
        """
        Create Paystack transaction.
        
        Paystack amounts are in kobo (for NGN) or cents (for other currencies),
        so we multiply by 100.
        
        Args:
            amount: Payment amount as Decimal (e.g., 9999.99)
            currency: Currency code (default: 'NGN')
            metadata: Optional metadata dictionary
            
        Returns:
            dict: Transaction data with authorization_url and reference
            
        Raises:
            PaymentProcessorError: If transaction initialization fails
        """
        try:
            # Convert amount to smallest currency unit (kobo/cents)
            amount_kobo = int(amount * 100)
            
            # Prepare transaction data
            transaction_data = {
                'amount': amount_kobo,
                'currency': currency.upper(),
                'metadata': metadata or {}
            }
            
            # Initialize transaction
            response = self._make_request(
                'POST',
                '/transaction/initialize',
                transaction_data
            )
            
            if not response.get('status'):
                raise PaymentProcessorError(
                    f"Paystack transaction initialization failed: {response.get('message')}"
                )
            
            data = response['data']
            
            logger.info(
                f"Paystack transaction initialized: {data['reference']}",
                extra={'reference': data['reference'], 'amount': amount}
            )
            
            return {
                'id': data['reference'],
                'reference': data['reference'],
                'authorization_url': data['authorization_url'],
                'access_code': data['access_code'],
                'amount': amount,
                'currency': currency
            }
            
        except Exception as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Paystack transaction initialization failed: {str(e)}",
                extra={'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to initialize transaction: {str(e)}")
    
    def confirm_payment(self, payment_intent_id):
        """
        Confirm Paystack payment was successful.
        
        Args:
            payment_intent_id: Paystack transaction reference
            
        Returns:
            bool: True if payment succeeded, False otherwise
            
        Raises:
            PaymentProcessorError: If payment verification fails
        """
        try:
            # Verify transaction
            response = self._make_request(
                'GET',
                f'/transaction/verify/{payment_intent_id}'
            )
            
            if not response.get('status'):
                raise PaymentProcessorError(
                    f"Paystack transaction verification failed: {response.get('message')}"
                )
            
            data = response['data']
            
            # Check if payment succeeded
            is_successful = data['status'] == 'success'
            
            if is_successful:
                logger.info(
                    f"Paystack payment confirmed: {payment_intent_id}",
                    extra={'reference': payment_intent_id}
                )
            else:
                logger.warning(
                    f"Paystack payment not successful: {payment_intent_id}, status: {data['status']}",
                    extra={'reference': payment_intent_id, 'status': data['status']}
                )
            
            return is_successful
            
        except Exception as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Paystack payment verification failed: {str(e)}",
                extra={'reference': payment_intent_id, 'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to verify payment: {str(e)}")
    
    def refund_payment(self, payment_intent_id, amount=None):
        """
        Process Paystack refund.
        
        Args:
            payment_intent_id: Paystack transaction reference
            amount: Optional refund amount in currency units (defaults to full refund)
            
        Returns:
            dict: Refund data including refund_id and status
            
        Raises:
            PaymentProcessorError: If refund processing fails
        """
        try:
            # Prepare refund data
            refund_data = {
                'transaction': payment_intent_id
            }
            
            # If partial refund, convert amount to smallest currency unit
            if amount is not None:
                refund_data['amount'] = int(amount * 100)
            
            # Create refund
            response = self._make_request(
                'POST',
                '/refund',
                refund_data
            )
            
            if not response.get('status'):
                raise PaymentProcessorError(
                    f"Paystack refund failed: {response.get('message')}"
                )
            
            data = response['data']
            
            logger.info(
                f"Paystack refund created: {data['id']} for transaction {payment_intent_id}",
                extra={'refund_id': data['id'], 'reference': payment_intent_id}
            )
            
            return {
                'refund_id': data['id'],
                'status': data['status'],
                'amount': Decimal(data.get('amount', 0)) / 100,  # Convert back to currency units
                'currency': data.get('currency', 'NGN')
            }
            
        except Exception as e:
            # Log error without sensitive data (Requirement 2.5)
            logger.error(
                f"Paystack refund failed: {str(e)}",
                extra={'reference': payment_intent_id, 'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Failed to process refund: {str(e)}")
    
    def verify_webhook(self, payload, signature):
        """
        Verify Paystack webhook signature.
        
        This is critical for security - it ensures the webhook actually
        came from Paystack and hasn't been tampered with.
        
        Paystack uses HMAC SHA512 for webhook signature verification.
        
        Args:
            payload: Raw webhook payload (bytes or string)
            signature: X-Paystack-Signature header value
            
        Returns:
            dict: Parsed webhook event data
            
        Raises:
            PaymentProcessorError: If signature verification fails
        """
        import json as json_module
        
        try:
            # Convert payload to bytes if it's a string
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            # Compute expected signature using HMAC SHA512
            computed_signature = hmac.new(
                settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
                payload,
                hashlib.sha512
            ).hexdigest()
            
            # Compare signatures (constant-time comparison to prevent timing attacks)
            if not hmac.compare_digest(computed_signature, signature):
                logger.error(
                    "Paystack webhook signature verification failed",
                    extra={'error_type': 'invalid_signature'}
                )
                raise PaymentProcessorError("Invalid webhook signature")
            
            # Parse webhook data
            event = json_module.loads(payload.decode('utf-8'))
            
            logger.info(
                f"Paystack webhook verified: {event.get('event')}",
                extra={'event_type': event.get('event')}
            )
            
            return event
            
        except json_module.JSONDecodeError as e:
            # Invalid JSON payload
            logger.error(
                f"Paystack webhook invalid JSON: {str(e)}",
                extra={'error_type': 'invalid_json'}
            )
            raise PaymentProcessorError("Invalid webhook payload")
            
        except PaymentProcessorError:
            # Re-raise PaymentProcessorError without wrapping
            raise
            
        except Exception as e:
            # Other errors
            logger.error(
                f"Paystack webhook verification failed: {str(e)}",
                extra={'error_type': type(e).__name__}
            )
            raise PaymentProcessorError(f"Webhook verification failed: {str(e)}")
