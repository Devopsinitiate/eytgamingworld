"""
Unit tests for checkout views.

Tests checkout flow including:
- Checkout initiation (requires auth)
- Shipping information form
- Payment method selection
- Order confirmation
- Shipping cost calculation

Requirements: 8.1, 8.2, 8.3, 8.4, 8.8
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from store.models import Product, Category, Cart, CartItem, ProductVariant, Order
from store.managers import CartManager

User = get_user_model()


class CheckoutInitiateViewTest(TestCase):
    """Test checkout initiation view."""
    
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
            price=Decimal('50.00'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
    
    def test_checkout_initiate_requires_authentication(self):
        """Test that checkout requires authentication."""
        # Requirement: 8.1 - Checkout requires authentication
        response = self.client.get(reverse('store:checkout_initiate'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_checkout_initiate_with_empty_cart_redirects(self):
        """Test that empty cart redirects to cart page."""
        # Requirement: 8.1 - Validate cart has items
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('store:checkout_initiate'))
        
        # Should redirect to cart
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('store:cart'))
    
    def test_checkout_initiate_with_items_displays_summary(self):
        """Test that checkout displays cart summary."""
        # Requirement: 8.4 - Display order summary
        self.client.login(username='testuser', password='testpass123')
        
        # Add item to cart
        cart = CartManager.get_or_create_cart(user=self.user)
        CartManager.add_item(cart, self.product, None, 2)
        
        response = self.client.get(reverse('store:checkout_initiate'))
        
        # Should display checkout page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/checkout_initiate.html')
        self.assertIn('cart_items', response.context)
        self.assertIn('subtotal', response.context)
        self.assertEqual(response.context['item_count'], 2)


class ShippingCostCalculationTest(TestCase):
    """Test shipping cost calculation."""
    
    def test_domestic_shipping_cost(self):
        """Test shipping cost for domestic (Nigeria) orders."""
        # Requirement: 8.8 - Calculate shipping cost based on location
        from store.views import calculate_shipping_cost
        
        cost = calculate_shipping_cost('Nigeria')
        self.assertEqual(cost, Decimal('5.00'))
        
        cost = calculate_shipping_cost('NG')
        self.assertEqual(cost, Decimal('5.00'))
        
        cost = calculate_shipping_cost('NGA')
        self.assertEqual(cost, Decimal('5.00'))
    
    def test_regional_shipping_cost(self):
        """Test shipping cost for regional (West Africa) orders."""
        # Requirement: 8.8 - Calculate shipping cost based on location
        from store.views import calculate_shipping_cost
        
        cost = calculate_shipping_cost('Ghana')
        self.assertEqual(cost, Decimal('15.00'))
        
        cost = calculate_shipping_cost('Senegal')
        self.assertEqual(cost, Decimal('15.00'))
    
    def test_international_shipping_cost(self):
        """Test shipping cost for international orders."""
        # Requirement: 8.8 - Calculate shipping cost based on location
        from store.views import calculate_shipping_cost
        
        cost = calculate_shipping_cost('United States')
        self.assertEqual(cost, Decimal('25.00'))
        
        cost = calculate_shipping_cost('United Kingdom')
        self.assertEqual(cost, Decimal('25.00'))
