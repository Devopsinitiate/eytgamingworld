"""
Unit tests for CartManager business logic.

Tests cart operations including:
- Cart creation and retrieval
- Adding items with stock validation
- Updating quantities
- Removing items
- Merging carts on login
- Total calculation
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from store.models import Cart, CartItem, Product, ProductVariant, Category
from store.managers import CartManager, InsufficientStockError

User = get_user_model()


@pytest.mark.django_db
class TestCartManagerGetOrCreateCart:
    """Tests for get_or_create_cart method."""
    
    def test_get_or_create_cart_for_authenticated_user(self):
        """Test creating cart for authenticated user."""
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        
        cart = CartManager.get_or_create_cart(user=user)
        
        assert cart is not None
        assert cart.user == user
        assert cart.session_key is None
    
    def test_get_existing_cart_for_authenticated_user(self):
        """Test retrieving existing cart for authenticated user."""
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        existing_cart = Cart.objects.create(user=user)
        
        cart = CartManager.get_or_create_cart(user=user)
        
        assert cart.id == existing_cart.id
    
    def test_get_or_create_cart_for_guest_user(self):
        """Test creating cart for guest user with session key."""
        session_key = 'test_session_key_12345'
        
        cart = CartManager.get_or_create_cart(session_key=session_key)
        
        assert cart is not None
        assert cart.user is None
        assert cart.session_key == session_key
    
    def test_get_existing_cart_for_guest_user(self):
        """Test retrieving existing cart for guest user."""
        session_key = 'test_session_key_12345'
        existing_cart = Cart.objects.create(session_key=session_key)
        
        cart = CartManager.get_or_create_cart(session_key=session_key)
        
        assert cart.id == existing_cart.id
    
    def test_get_or_create_cart_without_user_or_session_raises_error(self):
        """Test that providing neither user nor session_key raises ValueError."""
        with pytest.raises(ValueError, match="Either user or session_key must be provided"):
            CartManager.get_or_create_cart()


@pytest.mark.django_db
class TestCartManagerAddItem:
    """Tests for add_item method."""
    
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
        self.cart = Cart.objects.create(user=self.user)
    
    def test_add_item_to_empty_cart(self):
        """Test adding item to empty cart."""
        cart_item = CartManager.add_item(self.cart, self.product, quantity=2)
        
        assert cart_item is not None
        assert cart_item.cart == self.cart
        assert cart_item.product == self.product
        assert cart_item.quantity == 2
    
    def test_add_item_increases_quantity_if_exists(self):
        """Test adding same item increases quantity."""
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        
        cart_item = CartManager.add_item(self.cart, self.product, quantity=3)
        
        assert cart_item.quantity == 5
        assert CartItem.objects.filter(cart=self.cart, product=self.product).count() == 1
    
    def test_add_item_with_variant(self):
        """Test adding item with variant."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5
        )
        
        cart_item = CartManager.add_item(self.cart, self.product, variant=variant, quantity=2)
        
        assert cart_item.variant == variant
        assert cart_item.quantity == 2
    
    def test_add_item_validates_quantity_minimum(self):
        """Test that quantity must be at least 1."""
        with pytest.raises(ValidationError, match="Quantity must be between 1 and 100"):
            CartManager.add_item(self.cart, self.product, quantity=0)
    
    def test_add_item_validates_quantity_maximum(self):
        """Test that quantity cannot exceed 100."""
        with pytest.raises(ValidationError, match="Quantity must be between 1 and 100"):
            CartManager.add_item(self.cart, self.product, quantity=101)
    
    def test_add_item_checks_stock_availability(self):
        """Test that adding more than available stock raises error."""
        with pytest.raises(InsufficientStockError, match="Only 10 units available"):
            CartManager.add_item(self.cart, self.product, quantity=15)
    
    def test_add_item_checks_stock_with_existing_cart_item(self):
        """Test stock validation considers existing cart quantity."""
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=8)
        
        with pytest.raises(InsufficientStockError, match="You already have 8 in your cart"):
            CartManager.add_item(self.cart, self.product, quantity=5)
    
    def test_add_item_rejects_inactive_product(self):
        """Test that inactive products cannot be added."""
        self.product.is_active = False
        self.product.save()
        
        with pytest.raises(ValidationError, match="This product is no longer available"):
            CartManager.add_item(self.cart, self.product, quantity=1)
    
    def test_add_item_rejects_unavailable_variant(self):
        """Test that unavailable variants cannot be added."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=5,
            is_available=False
        )
        
        with pytest.raises(ValidationError, match="This product variant is not available"):
            CartManager.add_item(self.cart, self.product, variant=variant, quantity=1)


@pytest.mark.django_db
class TestCartManagerUpdateQuantity:
    """Tests for update_quantity method."""
    
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
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
    
    def test_update_quantity_success(self):
        """Test updating quantity to valid value."""
        updated_item = CartManager.update_quantity(self.cart_item, 5)
        
        assert updated_item.quantity == 5
    
    def test_update_quantity_validates_minimum(self):
        """Test that quantity must be at least 1."""
        with pytest.raises(ValidationError, match="Quantity must be between 1 and 100"):
            CartManager.update_quantity(self.cart_item, 0)
    
    def test_update_quantity_validates_maximum(self):
        """Test that quantity cannot exceed 100."""
        with pytest.raises(ValidationError, match="Quantity must be between 1 and 100"):
            CartManager.update_quantity(self.cart_item, 101)
    
    def test_update_quantity_checks_stock(self):
        """Test that updating quantity checks stock availability."""
        with pytest.raises(InsufficientStockError, match="Only 10 units available"):
            CartManager.update_quantity(self.cart_item, 15)


@pytest.mark.django_db
class TestCartManagerRemoveItem:
    """Tests for remove_item method."""
    
    def test_remove_item_deletes_cart_item(self):
        """Test removing item from cart."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=2)
        
        CartManager.remove_item(cart_item)
        
        assert not CartItem.objects.filter(id=cart_item.id).exists()


@pytest.mark.django_db
class TestCartManagerMergeCarts:
    """Tests for merge_carts method."""
    
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
            price=Decimal('39.99'),
            category=self.category,
            stock_quantity=15
        )
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        self.user_cart = Cart.objects.create(user=self.user)
        self.session_cart = Cart.objects.create(session_key='test_session_123')
    
    def test_merge_carts_moves_unique_items(self):
        """Test merging carts moves items that don't exist in user cart."""
        CartItem.objects.create(cart=self.session_cart, product=self.product1, quantity=2)
        
        merged_cart = CartManager.merge_carts(self.session_cart, self.user_cart)
        
        assert merged_cart == self.user_cart
        assert CartItem.objects.filter(cart=self.user_cart, product=self.product1).exists()
        assert not Cart.objects.filter(id=self.session_cart.id).exists()
    
    def test_merge_carts_combines_quantities_for_duplicate_items(self):
        """Test merging carts combines quantities for items in both carts."""
        CartItem.objects.create(cart=self.user_cart, product=self.product1, quantity=3)
        CartItem.objects.create(cart=self.session_cart, product=self.product1, quantity=2)
        
        merged_cart = CartManager.merge_carts(self.session_cart, self.user_cart)
        
        cart_item = CartItem.objects.get(cart=self.user_cart, product=self.product1)
        assert cart_item.quantity == 5
    
    def test_merge_carts_respects_stock_limits(self):
        """Test merging carts doesn't exceed available stock."""
        self.product1.stock_quantity = 8
        self.product1.save()
        
        CartItem.objects.create(cart=self.user_cart, product=self.product1, quantity=5)
        CartItem.objects.create(cart=self.session_cart, product=self.product1, quantity=10)
        
        merged_cart = CartManager.merge_carts(self.session_cart, self.user_cart)
        
        cart_item = CartItem.objects.get(cart=self.user_cart, product=self.product1)
        assert cart_item.quantity == 8  # Limited to available stock
    
    def test_merge_carts_respects_maximum_quantity(self):
        """Test merging carts doesn't exceed maximum quantity of 100."""
        # Increase stock to allow testing the 100 quantity limit
        self.product1.stock_quantity = 150
        self.product1.save()
        
        CartItem.objects.create(cart=self.user_cart, product=self.product1, quantity=60)
        CartItem.objects.create(cart=self.session_cart, product=self.product1, quantity=50)
        
        merged_cart = CartManager.merge_carts(self.session_cart, self.user_cart)
        
        cart_item = CartItem.objects.get(cart=self.user_cart, product=self.product1)
        assert cart_item.quantity == 100  # Limited to maximum
    
    def test_merge_carts_handles_multiple_items(self):
        """Test merging carts with multiple different items."""
        CartItem.objects.create(cart=self.user_cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.session_cart, product=self.product1, quantity=3)
        CartItem.objects.create(cart=self.session_cart, product=self.product2, quantity=1)
        
        merged_cart = CartManager.merge_carts(self.session_cart, self.user_cart)
        
        assert CartItem.objects.filter(cart=self.user_cart).count() == 2
        item1 = CartItem.objects.get(cart=self.user_cart, product=self.product1)
        item2 = CartItem.objects.get(cart=self.user_cart, product=self.product2)
        assert item1.quantity == 5
        assert item2.quantity == 1


@pytest.mark.django_db
class TestCartManagerCalculateTotal:
    """Tests for calculate_total method."""
    
    def test_calculate_total_empty_cart(self):
        """Test calculating total for empty cart."""
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        
        total = CartManager.calculate_total(cart)
        
        assert total == Decimal('0.00')
    
    def test_calculate_total_single_item(self):
        """Test calculating total for cart with single item."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        
        total = CartManager.calculate_total(cart)
        
        assert total == Decimal('59.98')
    
    def test_calculate_total_multiple_items(self):
        """Test calculating total for cart with multiple items."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Test description',
            price=Decimal('49.99'),
            category=category,
            stock_quantity=10
        )
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product1, quantity=2)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)
        
        total = CartManager.calculate_total(cart)
        
        assert total == Decimal('109.97')
    
    def test_calculate_total_with_variant(self):
        """Test calculating total with product variant price adjustment."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        variant = ProductVariant.objects.create(
            product=product,
            name='Size: Large',
            sku='TEST-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=5
        )
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=2)
        
        total = CartManager.calculate_total(cart)
        
        # (29.99 + 5.00) * 2 = 69.98
        assert total == Decimal('69.98')


@pytest.mark.django_db
class TestCartManagerClearCart:
    """Tests for clear_cart method."""
    
    def test_clear_cart_removes_all_items(self):
        """Test clearing cart removes all items."""
        category = Category.objects.create(name='Test Category', slug='test-category')
        product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Test description',
            price=Decimal('29.99'),
            category=category,
            stock_quantity=10
        )
        product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Test description',
            price=Decimal('39.99'),
            category=category,
            stock_quantity=10
        )
        user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='testpass123'
        )
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product1, quantity=2)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)
        
        CartManager.clear_cart(cart)
        
        assert CartItem.objects.filter(cart=cart).count() == 0
        assert cart.is_empty
