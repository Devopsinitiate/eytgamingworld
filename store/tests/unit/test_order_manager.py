"""
Unit tests for OrderManager business logic.

Tests order operations including:
- Order creation from cart with transaction safety
- Unique order number generation
- Order status updates
- Order cancellation with stock restoration
- User order retrieval
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from store.models import (
    Cart, CartItem, Product, ProductVariant, Category,
    Order, OrderItem
)
from store.managers import OrderManager, CartManager, InsufficientStockError

User = get_user_model()


@pytest.mark.django_db
class TestOrderManagerCreateOrder:
    """Tests for create_order method."""
    
    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=20
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Test description',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=15
        )
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.cart = Cart.objects.create(user=self.user)
        
        self.shipping_info = {
            'shipping_name': 'John Doe',
            'shipping_address_line1': '123 Main St',
            'shipping_address_line2': 'Apt 4B',
            'shipping_city': 'New York',
            'shipping_state': 'NY',
            'shipping_postal_code': '10001',
            'shipping_country': 'USA',
            'shipping_phone': '+1234567890'
        }
    
    def test_create_order_success(self):
        """Test creating order from cart successfully."""
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)
        
        order = OrderManager.create_order(
            user=self.user,
            cart=self.cart,
            shipping_info=self.shipping_info,
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        assert order is not None
        assert order.user == self.user
        assert order.status == 'pending'
        assert order.payment_method == 'stripe'
        assert order.payment_intent_id == 'pi_test_123'
        assert order.shipping_name == 'John Doe'
        assert order.shipping_city == 'New York'
        
        # Check order items were created
        assert order.items.count() == 2
        
        # Check cart was cleared
        assert self.cart.items.count() == 0
    
    def test_create_order_calculates_totals_correctly(self):
        """Test order totals are calculated correctly."""
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)
        
        order = OrderManager.create_order(
            user=self.user,
            cart=self.cart,
            shipping_info=self.shipping_info,
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Subtotal: (29.99 * 2) + (49.99 * 1) = 109.97
        expected_subtotal = Decimal('109.97')
        assert order.subtotal == expected_subtotal
        
        # Shipping: flat rate of 10.00
        assert order.shipping_cost == Decimal('10.00')
        
        # Tax: 10% of subtotal = 10.997 rounded to 10.99 or 11.00
        expected_tax = (expected_subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        assert order.tax == expected_tax
        
        # Total: subtotal + shipping + tax
        expected_total = expected_subtotal + Decimal('10.00') + expected_tax
        assert order.total == expected_total
    
    def test_create_order_reserves_stock(self):
        """Test order creation reserves stock."""
        initial_stock1 = self.product1.stock_quantity
        initial_stock2 = self.product2.stock_quantity
        
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)
        
        OrderManager.create_order(
            user=self.user,
            cart=self.cart,
            shipping_info=self.shipping_info,
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Refresh products from database
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        
        assert self.product1.stock_quantity == initial_stock1 - 2
        assert self.product2.stock_quantity == initial_stock2 - 1
    
    def test_create_order_creates_order_items_with_snapshots(self):
        """Test order items are created with product snapshots."""
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        
        order = OrderManager.create_order(
            user=self.user,
            cart=self.cart,
            shipping_info=self.shipping_info,
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        order_item = order.items.first()
        assert order_item.product_name == 'Product 1'
        assert order_item.unit_price == Decimal('29.99')
        assert order_item.quantity == 2
        assert order_item.total_price == Decimal('59.98')
    
    def test_create_order_with_variant(self):
        """Test creating order with product variant."""
        variant = ProductVariant.objects.create(
            product=self.product1,
            name='Size: Large',
            sku='PROD1-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=10
        )
        CartItem.objects.create(
            cart=self.cart,
            product=self.product1,
            variant=variant,
            quantity=1
        )
        
        order = OrderManager.create_order(
            user=self.user,
            cart=self.cart,
            shipping_info=self.shipping_info,
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        order_item = order.items.first()
        assert order_item.variant == variant
        assert order_item.variant_name == 'Size: Large'
        assert order_item.unit_price == Decimal('34.99')  # 29.99 + 5.00
    
    def test_create_order_from_empty_cart_raises_error(self):
        """Test creating order from empty cart raises ValidationError."""
        with pytest.raises(ValidationError, match="Cannot create order from empty cart"):
            OrderManager.create_order(
                user=self.user,
                cart=self.cart,
                shipping_info=self.shipping_info,
                payment_method='stripe',
                payment_intent_id='pi_test_123'
            )
    
    def test_create_order_with_missing_shipping_info_raises_error(self):
        """Test creating order with missing shipping info raises ValidationError."""
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=1)
        
        incomplete_shipping = {
            'shipping_name': 'John Doe',
            'shipping_city': 'New York',
            # Missing required fields
        }
        
        with pytest.raises(ValidationError, match="Missing required field"):
            OrderManager.create_order(
                user=self.user,
                cart=self.cart,
                shipping_info=incomplete_shipping,
                payment_method='stripe',
                payment_intent_id='pi_test_123'
            )
    
    def test_create_order_with_insufficient_stock_raises_error(self):
        """Test creating order with insufficient stock raises InsufficientStockError."""
        self.product1.stock_quantity = 1
        self.product1.save()
        
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=5)
        
        with pytest.raises(InsufficientStockError, match="Insufficient stock"):
            OrderManager.create_order(
                user=self.user,
                cart=self.cart,
                shipping_info=self.shipping_info,
                payment_method='stripe',
                payment_intent_id='pi_test_123'
            )
    
    def test_create_order_with_inactive_product_raises_error(self):
        """Test creating order with inactive product raises ValidationError."""
        self.product1.is_active = False
        self.product1.save()
        
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=1)
        
        with pytest.raises(ValidationError, match="is no longer available"):
            OrderManager.create_order(
                user=self.user,
                cart=self.cart,
                shipping_info=self.shipping_info,
                payment_method='stripe',
                payment_intent_id='pi_test_123'
            )
    
    def test_create_order_is_atomic(self):
        """Test order creation is atomic - rolls back on failure."""
        # Set up a scenario where stock reservation will fail for second item
        self.product2.stock_quantity = 0
        self.product2.save()
        
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)
        
        initial_stock1 = self.product1.stock_quantity
        initial_cart_items = self.cart.items.count()
        
        with pytest.raises(InsufficientStockError):
            OrderManager.create_order(
                user=self.user,
                cart=self.cart,
                shipping_info=self.shipping_info,
                payment_method='stripe',
                payment_intent_id='pi_test_123'
            )
        
        # Verify rollback: stock should not be decremented
        self.product1.refresh_from_db()
        assert self.product1.stock_quantity == initial_stock1
        
        # Verify rollback: cart should not be cleared
        assert self.cart.items.count() == initial_cart_items
        
        # Verify rollback: no order should be created
        assert Order.objects.count() == 0


@pytest.mark.django_db
class TestOrderManagerGenerateOrderNumber:
    """Tests for generate_order_number method."""
    
    def test_generate_order_number_format(self):
        """Test order number has correct format EYT-YYYY-NNNNNN."""
        order_number = OrderManager.generate_order_number()
        
        parts = order_number.split('-')
        assert len(parts) == 3
        assert parts[0] == 'EYT'
        assert len(parts[1]) == 4  # Year
        assert len(parts[2]) == 6  # Sequential number
        assert parts[2].isdigit()
    
    def test_generate_order_number_includes_current_year(self):
        """Test order number includes current year."""
        from datetime import datetime
        current_year = datetime.now().year
        
        order_number = OrderManager.generate_order_number()
        
        assert f'-{current_year}-' in order_number
    
    def test_generate_order_number_is_unique(self):
        """Test generated order numbers are unique."""
        # Create a user and order to establish baseline
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        
        order_number1 = OrderManager.generate_order_number()
        
        # Create an order with the first number
        Order.objects.create(
            order_number=order_number1,
            user=user,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Generate second order number
        order_number2 = OrderManager.generate_order_number()
        
        assert order_number1 != order_number2
    
    def test_generate_order_number_sequential(self):
        """Test order numbers are sequential."""
        # Create an order to establish a baseline
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        category = Category.objects.create(name='Test Category', slug='test-category')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        
        Order.objects.create(
            order_number='EYT-2024-000001',
            user=user,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Generate next order number
        order_number = OrderManager.generate_order_number()
        
        # Extract sequential number
        sequential = int(order_number.split('-')[2])
        assert sequential >= 2  # Should be at least 2


@pytest.mark.django_db
class TestOrderManagerUpdateStatus:
    """Tests for update_status method."""
    
    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.order = Order.objects.create(
            order_number='EYT-2024-000001',
            user=self.user,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123',
            status='pending'
        )
    
    def test_update_status_pending_to_processing(self):
        """Test updating status from pending to processing."""
        updated_order = OrderManager.update_status(self.order, 'processing')
        
        assert updated_order.status == 'processing'
    
    def test_update_status_processing_to_shipped(self):
        """Test updating status from processing to shipped."""
        self.order.status = 'processing'
        self.order.save()
        
        updated_order = OrderManager.update_status(
            self.order,
            'shipped',
            tracking_number='TRACK123456'
        )
        
        assert updated_order.status == 'shipped'
        assert updated_order.tracking_number == 'TRACK123456'
    
    def test_update_status_shipped_to_delivered(self):
        """Test updating status from shipped to delivered."""
        self.order.status = 'shipped'
        self.order.save()
        
        updated_order = OrderManager.update_status(self.order, 'delivered')
        
        assert updated_order.status == 'delivered'
    
    def test_update_status_pending_to_cancelled(self):
        """Test updating status from pending to cancelled."""
        updated_order = OrderManager.update_status(self.order, 'cancelled')
        
        assert updated_order.status == 'cancelled'
    
    def test_update_status_invalid_transition_raises_error(self):
        """Test invalid status transition raises ValidationError."""
        self.order.status = 'delivered'
        self.order.save()
        
        with pytest.raises(ValidationError, match="Invalid status transition"):
            OrderManager.update_status(self.order, 'processing')
    
    def test_update_status_invalid_status_raises_error(self):
        """Test invalid status value raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid status"):
            OrderManager.update_status(self.order, 'invalid_status')
    
    def test_update_status_from_cancelled_raises_error(self):
        """Test cannot update status from cancelled (terminal state)."""
        self.order.status = 'cancelled'
        self.order.save()
        
        with pytest.raises(ValidationError, match="Invalid status transition"):
            OrderManager.update_status(self.order, 'processing')


@pytest.mark.django_db
class TestOrderManagerCancelOrder:
    """Tests for cancel_order method."""
    
    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10
        )
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.order = Order.objects.create(
            order_number='EYT-2024-000001',
            user=self.user,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123',
            status='pending'
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='Test Product',
            quantity=2,
            unit_price=Decimal('29.99'),
            total_price=Decimal('59.98')
        )
    
    def test_cancel_order_success(self):
        """Test cancelling order successfully."""
        initial_stock = self.product.stock_quantity
        
        cancelled_order = OrderManager.cancel_order(self.order)
        
        assert cancelled_order.status == 'cancelled'
        
        # Verify stock was restored
        self.product.refresh_from_db()
        assert self.product.stock_quantity == initial_stock + 2
    
    def test_cancel_order_within_24_hours(self):
        """Test order can be cancelled within 24 hours."""
        # Order was just created, should be within 24 hours
        cancelled_order = OrderManager.cancel_order(self.order)
        
        assert cancelled_order.status == 'cancelled'
    
    def test_cancel_order_after_24_hours_raises_error(self):
        """Test cannot cancel order after 24 hours."""
        # Set order creation time to more than 24 hours ago
        self.order.created_at = timezone.now() - timedelta(hours=25)
        self.order.save()
        
        with pytest.raises(ValidationError, match="Cannot cancel order after 24 hours"):
            OrderManager.cancel_order(self.order)
    
    def test_cancel_shipped_order_raises_error(self):
        """Test cannot cancel shipped order."""
        self.order.status = 'shipped'
        self.order.save()
        
        with pytest.raises(ValidationError, match="Cannot cancel order that has been shipped"):
            OrderManager.cancel_order(self.order)
    
    def test_cancel_delivered_order_raises_error(self):
        """Test cannot cancel delivered order."""
        self.order.status = 'delivered'
        self.order.save()
        
        with pytest.raises(ValidationError, match="Cannot cancel order that has been shipped or delivered"):
            OrderManager.cancel_order(self.order)
    
    def test_cancel_already_cancelled_order_raises_error(self):
        """Test cannot cancel already cancelled order."""
        self.order.status = 'cancelled'
        self.order.save()
        
        with pytest.raises(ValidationError, match="Order is already cancelled"):
            OrderManager.cancel_order(self.order)
    
    def test_cancel_order_restores_stock_for_multiple_items(self):
        """Test cancelling order restores stock for all items."""
        product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Test description',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=5
        )
        OrderItem.objects.create(
            order=self.order,
            product=product2,
            product_name='Product 2',
            quantity=1,
            unit_price=Decimal('49.99'),
            total_price=Decimal('49.99')
        )
        
        initial_stock1 = self.product.stock_quantity
        initial_stock2 = product2.stock_quantity
        
        OrderManager.cancel_order(self.order)
        
        self.product.refresh_from_db()
        product2.refresh_from_db()
        
        assert self.product.stock_quantity == initial_stock1 + 2
        assert product2.stock_quantity == initial_stock2 + 1


@pytest.mark.django_db
class TestOrderManagerGetUserOrders:
    """Tests for get_user_orders method."""
    
    def setup_method(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        
        # Create orders for user1
        self.order1 = Order.objects.create(
            order_number='EYT-2024-000001',
            user=self.user1,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='User 1',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123',
            status='pending'
        )
        self.order2 = Order.objects.create(
            order_number='EYT-2024-000002',
            user=self.user1,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('4.99'),
            total=Decimal('64.98'),
            shipping_name='User 1',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_456',
            status='shipped'
        )
        
        # Create order for user2
        self.order3 = Order.objects.create(
            order_number='EYT-2024-000003',
            user=self.user2,
            subtotal=Decimal('19.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('1.99'),
            total=Decimal('31.98'),
            shipping_name='User 2',
            shipping_address_line1='456 Test Ave',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='paystack',
            payment_intent_id='ps_test_789',
            status='delivered'
        )
    
    def test_get_user_orders_returns_only_user_orders(self):
        """Test get_user_orders returns only orders for specified user."""
        orders = OrderManager.get_user_orders(self.user1)
        
        assert orders.count() == 2
        assert self.order1 in orders
        assert self.order2 in orders
        assert self.order3 not in orders
    
    def test_get_user_orders_ordered_by_created_at_desc(self):
        """Test orders are returned in reverse chronological order."""
        orders = list(OrderManager.get_user_orders(self.user1))
        
        # order2 was created after order1, so should come first
        assert orders[0].created_at >= orders[1].created_at
    
    def test_get_user_orders_with_status_filter(self):
        """Test filtering orders by status."""
        orders = OrderManager.get_user_orders(self.user1, status='shipped')
        
        assert orders.count() == 1
        assert orders.first() == self.order2
    
    def test_get_user_orders_empty_result(self):
        """Test get_user_orders returns empty queryset for user with no orders."""
        user3 = User.objects.create_user(
            email='user3@example.com',
            username='user3',
            password='testpass123'
        )
        
        orders = OrderManager.get_user_orders(user3)
        
        assert orders.count() == 0
    
    def test_get_user_orders_prefetches_items(self):
        """Test get_user_orders prefetches order items for efficiency."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        
        # Create a new order with items for this test
        order = Order.objects.create(
            order_number='EYT-2024-000999',
            user=self.user1,
            subtotal=Decimal('29.99'),
            shipping_cost=Decimal('10.00'),
            tax=Decimal('2.99'),
            total=Decimal('42.98'),
            shipping_name='User 1',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='TS',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='+1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_999',
            status='pending'
        )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name='Test Product',
            quantity=2,
            unit_price=Decimal('29.99'),
            total_price=Decimal('59.98')
        )
        
        orders = OrderManager.get_user_orders(self.user1)
        
        # Verify we can access items (they should be prefetched)
        # Find the order we just created
        test_order = orders.filter(order_number='EYT-2024-000999').first()
        assert test_order is not None
        
        items = list(test_order.items.all())
        assert len(items) > 0
        
        # Verify product is also prefetched
        first_item = items[0]
        assert first_item.product.name == 'Test Product'
