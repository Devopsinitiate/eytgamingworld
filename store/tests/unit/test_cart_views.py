"""
Unit tests for cart views.

Tests cart display, add to cart, update quantity, and remove from cart functionality.
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from store.models import Product, Category, Cart, CartItem, ProductVariant
from store.managers import CartManager

User = get_user_model()


class CartViewTests(TestCase):
    """Test cart display view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
    
    def test_cart_view_empty_guest(self):
        """Test cart view for guest user with empty cart."""
        response = self.client.get(reverse('store:cart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your cart is empty')
    
    def test_cart_view_empty_authenticated(self):
        """Test cart view for authenticated user with empty cart."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('store:cart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your cart is empty')
    
    def test_cart_view_with_items(self):
        """Test cart view with items in cart."""
        # Add item to cart BEFORE logging in
        cart = CartManager.get_or_create_cart(user=self.user)
        CartManager.add_item(cart, self.product, quantity=2)
        
        # Login after creating cart
        self.client.login(username='testuser', password='testpass123')
        
        # Get the cart view
        response = self.client.get(reverse('store:cart'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, '2 item')
        # Check for price display
        self.assertIn('29.99', response.content.decode())


class AddToCartTests(TestCase):
    """Test add to cart AJAX endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
    
    def test_add_to_cart_success(self):
        """Test successfully adding item to cart."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:add_to_cart'),
            data=json.dumps({
                'product_id': str(self.product.id),
                'quantity': 2
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_item']['quantity'], 2)
        self.assertEqual(data['cart_summary']['item_count'], 2)
    
    def test_add_to_cart_invalid_quantity(self):
        """Test adding item with invalid quantity."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:add_to_cart'),
            data=json.dumps({
                'product_id': str(self.product.id),
                'quantity': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_add_to_cart_insufficient_stock(self):
        """Test adding more items than available stock."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:add_to_cart'),
            data=json.dumps({
                'product_id': str(self.product.id),
                'quantity': 20  # More than stock_quantity of 10
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('available', data['error'].lower())
    
    def test_add_to_cart_missing_product_id(self):
        """Test adding item without product ID."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:add_to_cart'),
            data=json.dumps({
                'quantity': 1
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])


class UpdateCartQuantityTests(TestCase):
    """Test update cart quantity AJAX endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        
        # Create cart with item
        self.cart = CartManager.get_or_create_cart(user=self.user)
        self.cart_item = CartManager.add_item(self.cart, self.product, quantity=2)
    
    def test_update_quantity_success(self):
        """Test successfully updating quantity."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:update_cart_quantity'),
            data=json.dumps({
                'cart_item_id': str(self.cart_item.id),
                'quantity': 5
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_item']['quantity'], 5)
    
    def test_update_quantity_invalid(self):
        """Test updating with invalid quantity."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:update_cart_quantity'),
            data=json.dumps({
                'cart_item_id': str(self.cart_item.id),
                'quantity': 0
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_update_quantity_unauthorized(self):
        """Test updating another user's cart item."""
        # Create another user and login
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Login as other user (this creates a new session)
        self.client.login(username='otheruser', password='testpass123')
        
        # Ensure the other user has a session
        if not self.client.session.session_key:
            self.client.session.create()
        
        response = self.client.post(
            reverse('store:update_cart_quantity'),
            data=json.dumps({
                'cart_item_id': str(self.cart_item.id),
                'quantity': 5
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])


class RemoveFromCartTests(TestCase):
    """Test remove from cart AJAX endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        
        # Create cart with item
        self.cart = CartManager.get_or_create_cart(user=self.user)
        self.cart_item = CartManager.add_item(self.cart, self.product, quantity=2)
    
    def test_remove_from_cart_success(self):
        """Test successfully removing item from cart."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:remove_from_cart'),
            data=json.dumps({
                'cart_item_id': str(self.cart_item.id)
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_summary']['item_count'], 0)
        
        # Verify item was deleted
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())
    
    def test_remove_from_cart_unauthorized(self):
        """Test removing another user's cart item."""
        # Create another user and login
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Login as other user (this creates a new session)
        self.client.login(username='otheruser', password='testpass123')
        
        # Ensure the other user has a session
        if not self.client.session.session_key:
            self.client.session.create()
        
        response = self.client.post(
            reverse('store:remove_from_cart'),
            data=json.dumps({
                'cart_item_id': str(self.cart_item.id)
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
        
        # Verify item was not deleted
        self.assertTrue(CartItem.objects.filter(id=self.cart_item.id).exists())
    
    def test_remove_from_cart_missing_id(self):
        """Test removing item without cart_item_id."""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('store:remove_from_cart'),
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
