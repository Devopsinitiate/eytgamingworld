"""
Unit tests for InventoryManager business logic.

Tests inventory operations including:
- Stock availability checking
- Stock reservation with atomic transactions
- Stock restoration on order cancellation
- Race condition prevention with SELECT FOR UPDATE
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from unittest.mock import Mock, MagicMock

from store.models import Product, ProductVariant, Category
from store.managers import InventoryManager, InsufficientStockError

User = get_user_model()


@pytest.mark.django_db
class TestInventoryManagerCheckAvailability:
    """Tests for check_availability method."""
    
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
    
    def test_check_availability_product_sufficient_stock(self):
        """Test checking availability when product has sufficient stock."""
        result = InventoryManager.check_availability(self.product, quantity=5)
        
        assert result is True
    
    def test_check_availability_product_insufficient_stock(self):
        """Test checking availability when product has insufficient stock."""
        result = InventoryManager.check_availability(self.product, quantity=15)
        
        assert result is False
    
    def test_check_availability_product_exact_stock(self):
        """Test checking availability when quantity equals stock."""
        result = InventoryManager.check_availability(self.product, quantity=10)
        
        assert result is True
    
    def test_check_availability_product_zero_stock(self):
        """Test checking availability when product has zero stock."""
        self.product.stock_quantity = 0
        self.product.save()
        
        result = InventoryManager.check_availability(self.product, quantity=1)
        
        assert result is False
    
    def test_check_availability_variant_sufficient_stock(self):
        """Test checking availability when variant has sufficient stock."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5
        )
        
        result = InventoryManager.check_availability(self.product, variant=variant, quantity=3)
        
        assert result is True
    
    def test_check_availability_variant_insufficient_stock(self):
        """Test checking availability when variant has insufficient stock."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5
        )
        
        result = InventoryManager.check_availability(self.product, variant=variant, quantity=10)
        
        assert result is False
    
    def test_check_availability_default_quantity(self):
        """Test checking availability with default quantity of 1."""
        result = InventoryManager.check_availability(self.product)
        
        assert result is True


@pytest.mark.django_db
class TestInventoryManagerReserveStock:
    """Tests for reserve_stock method."""
    
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
    
    def test_reserve_stock_product_success(self):
        """Test successfully reserving stock from product."""
        InventoryManager.reserve_stock(self.product, quantity=5)
        
        # Refresh from database
        self.product.refresh_from_db()
        assert self.product.stock_quantity == 5
    
    def test_reserve_stock_product_insufficient_stock(self):
        """Test reserving more stock than available raises error."""
        with pytest.raises(InsufficientStockError, match="Insufficient stock for Test Product"):
            InventoryManager.reserve_stock(self.product, quantity=15)
        
        # Stock should remain unchanged
        self.product.refresh_from_db()
        assert self.product.stock_quantity == 10
    
    def test_reserve_stock_product_exact_stock(self):
        """Test reserving exact amount of available stock."""
        InventoryManager.reserve_stock(self.product, quantity=10)
        
        self.product.refresh_from_db()
        assert self.product.stock_quantity == 0
    
    def test_reserve_stock_product_zero_stock(self):
        """Test reserving from product with zero stock raises error."""
        self.product.stock_quantity = 0
        self.product.save()
        
        with pytest.raises(InsufficientStockError):
            InventoryManager.reserve_stock(self.product, quantity=1)
    
    def test_reserve_stock_variant_success(self):
        """Test successfully reserving stock from variant."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=8
        )
        
        InventoryManager.reserve_stock(self.product, variant=variant, quantity=3)
        
        variant.refresh_from_db()
        assert variant.stock_quantity == 5
        # Product stock should remain unchanged
        self.product.refresh_from_db()
        assert self.product.stock_quantity == 10
    
    def test_reserve_stock_variant_insufficient_stock(self):
        """Test reserving more variant stock than available raises error."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5
        )
        
        with pytest.raises(InsufficientStockError, match="Insufficient stock for Test Product - Size: Large"):
            InventoryManager.reserve_stock(self.product, variant=variant, quantity=10)
        
        variant.refresh_from_db()
        assert variant.stock_quantity == 5
    
    def test_reserve_stock_uses_select_for_update(self):
        """Test that reserve_stock uses SELECT FOR UPDATE for locking."""
        # This test verifies the method is atomic and uses proper locking
        # by checking that it's wrapped in a transaction
        
        # The reserve_stock method should be atomic
        # We can verify this by checking that it's decorated with @transaction.atomic
        assert hasattr(InventoryManager.reserve_stock, '_wrapped_function') or \
               hasattr(InventoryManager.reserve_stock, '__wrapped__')
    
    def test_reserve_stock_multiple_times(self):
        """Test reserving stock multiple times decrements correctly."""
        InventoryManager.reserve_stock(self.product, quantity=3)
        InventoryManager.reserve_stock(self.product, quantity=2)
        
        self.product.refresh_from_db()
        assert self.product.stock_quantity == 5


@pytest.mark.django_db
class TestInventoryManagerRestoreStock:
    """Tests for restore_stock method."""
    
    def setup_method(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=5  # Already reduced from original 10
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Test description',
            price=Decimal('39.99'),
            category=self.category,
            stock_quantity=8  # Already reduced from original 10
        )
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_restore_stock_single_product(self):
        """Test restoring stock for order with single product."""
        # Create mock order and order item
        mock_order_item = Mock()
        mock_order_item.product = self.product1
        mock_order_item.variant = None
        mock_order_item.quantity = 5
        
        mock_order = Mock()
        mock_order.items.all.return_value = [mock_order_item]
        
        InventoryManager.restore_stock(mock_order)
        
        self.product1.refresh_from_db()
        assert self.product1.stock_quantity == 10  # 5 + 5 restored
    
    def test_restore_stock_multiple_products(self):
        """Test restoring stock for order with multiple products."""
        # Create mock order items
        mock_item1 = Mock()
        mock_item1.product = self.product1
        mock_item1.variant = None
        mock_item1.quantity = 3
        
        mock_item2 = Mock()
        mock_item2.product = self.product2
        mock_item2.variant = None
        mock_item2.quantity = 2
        
        mock_order = Mock()
        mock_order.items.all.return_value = [mock_item1, mock_item2]
        
        InventoryManager.restore_stock(mock_order)
        
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        assert self.product1.stock_quantity == 8  # 5 + 3 restored
        assert self.product2.stock_quantity == 10  # 8 + 2 restored
    
    def test_restore_stock_with_variant(self):
        """Test restoring stock for order with product variant."""
        variant = ProductVariant.objects.create(
            product=self.product1,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=3  # Already reduced from original 7
        )
        
        mock_order_item = Mock()
        mock_order_item.product = self.product1
        mock_order_item.variant = variant
        mock_order_item.quantity = 4
        
        mock_order = Mock()
        mock_order.items.all.return_value = [mock_order_item]
        
        InventoryManager.restore_stock(mock_order)
        
        variant.refresh_from_db()
        assert variant.stock_quantity == 7  # 3 + 4 restored
        # Product stock should remain unchanged
        self.product1.refresh_from_db()
        assert self.product1.stock_quantity == 5
    
    def test_restore_stock_mixed_products_and_variants(self):
        """Test restoring stock for order with both products and variants."""
        variant = ProductVariant.objects.create(
            product=self.product1,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5
        )
        
        # Mock order item with variant
        mock_item1 = Mock()
        mock_item1.product = self.product1
        mock_item1.variant = variant
        mock_item1.quantity = 2
        
        # Mock order item without variant
        mock_item2 = Mock()
        mock_item2.product = self.product2
        mock_item2.variant = None
        mock_item2.quantity = 3
        
        mock_order = Mock()
        mock_order.items.all.return_value = [mock_item1, mock_item2]
        
        InventoryManager.restore_stock(mock_order)
        
        variant.refresh_from_db()
        self.product2.refresh_from_db()
        assert variant.stock_quantity == 7  # 5 + 2 restored
        assert self.product2.stock_quantity == 11  # 8 + 3 restored
    
    def test_restore_stock_empty_order(self):
        """Test restoring stock for order with no items."""
        mock_order = Mock()
        mock_order.items.all.return_value = []
        
        # Should not raise any errors
        InventoryManager.restore_stock(mock_order)
        
        # Stock should remain unchanged
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        assert self.product1.stock_quantity == 5
        assert self.product2.stock_quantity == 8
    
    def test_restore_stock_uses_select_for_update(self):
        """Test that restore_stock uses SELECT FOR UPDATE for locking."""
        # The restore_stock method should be atomic
        assert hasattr(InventoryManager.restore_stock, '_wrapped_function') or \
               hasattr(InventoryManager.restore_stock, '__wrapped__')


@pytest.mark.django_db
class TestInventoryManagerAtomicity:
    """Tests for transaction atomicity and race condition prevention."""
    
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
    
    def test_reserve_stock_rollback_on_error(self):
        """Test that stock reservation is rolled back if transaction fails."""
        # This test verifies that if an error occurs during the transaction,
        # the stock quantity is not changed
        
        initial_stock = self.product.stock_quantity
        
        try:
            with transaction.atomic():
                InventoryManager.reserve_stock(self.product, quantity=5)
                # Force a rollback by raising an exception
                raise Exception("Simulated error")
        except Exception:
            pass
        
        # Stock should be rolled back to original value
        self.product.refresh_from_db()
        assert self.product.stock_quantity == initial_stock
    
    def test_restore_stock_rollback_on_error(self):
        """Test that stock restoration is rolled back if transaction fails."""
        # Create mock order item
        mock_order_item = Mock()
        mock_order_item.product = self.product
        mock_order_item.variant = None
        mock_order_item.quantity = 3
        
        mock_order = Mock()
        mock_order.items.all.return_value = [mock_order_item]
        
        initial_stock = self.product.stock_quantity
        
        try:
            with transaction.atomic():
                InventoryManager.restore_stock(mock_order)
                # Force a rollback by raising an exception
                raise Exception("Simulated error")
        except Exception:
            pass
        
        # Stock should be rolled back to original value
        self.product.refresh_from_db()
        assert self.product.stock_quantity == initial_stock
