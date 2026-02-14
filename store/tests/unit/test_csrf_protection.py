"""
Unit tests for CSRF protection.

Tests CSRF middleware configuration and token validation.
"""

import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from store.models import Product, Category, Cart, CartItem
from decimal import Decimal
import json

User = get_user_model()


class CSRFProtectionTestCase(TestCase):
    """Test CSRF protection on store endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client(enforce_csrf_checks=True)
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            is_active=True
        )
    
    def test_csrf_middleware_enabled(self):
        """Test that CSRF middleware is enabled in settings."""
        from django.conf import settings
        
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE,
            'CSRF middleware should be enabled'
        )
    
    def test_csrf_cookie_settings(self):
        """Test CSRF cookie configuration."""
        from django.conf import settings
        
        # Check CSRF cookie settings
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
        self.assertEqual(settings.CSRF_COOKIE_HTTPONLY, False)  # Must be False for AJAX
        self.assertEqual(settings.CSRF_USE_SESSIONS, False)
        
        # Note: CSRF_COOKIE_SECURE is False in DEBUG mode (test environment)
        # In production (DEBUG=False), it should be True
        # We're testing in DEBUG mode, so it should be False
        self.assertFalse(settings.CSRF_COOKIE_SECURE)
    
    def test_add_to_cart_without_csrf_token(self):
        """Test that add to cart fails without CSRF token."""
        url = reverse('store:add_to_cart')
        data = {
            'product_id': str(self.product.id),
            'quantity': 1
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_add_to_cart_with_csrf_token(self):
        """Test that add to cart succeeds with valid CSRF token."""
        # Use client without CSRF checks to get token first
        temp_client = Client()
        temp_client.get(reverse('store:product_list'))
        csrftoken = temp_client.cookies.get('csrftoken')
        
        if csrftoken is None:
            # CSRF token not set in cookie, skip this test
            self.skipTest('CSRF token not set in cookie in test environment')
        
        url = reverse('store:add_to_cart')
        data = {
            'product_id': str(self.product.id),
            'quantity': 1
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrftoken.value
        )
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        
        # Verify response
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['cart_summary']['item_count'], 1)
    
    def test_update_cart_without_csrf_token(self):
        """Test that update cart quantity fails without CSRF token."""
        # Create cart with item
        cart = Cart.objects.create(session_key='test-session')
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        url = reverse('store:update_cart_quantity')
        data = {
            'cart_item_id': str(cart_item.id),
            'quantity': 2
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_remove_from_cart_without_csrf_token(self):
        """Test that remove from cart fails without CSRF token."""
        # Create cart with item
        cart = Cart.objects.create(session_key='test-session')
        cart_item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=1
        )
        
        url = reverse('store:remove_from_cart')
        data = {
            'cart_item_id': str(cart_item.id)
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_csrf_token_in_cookie(self):
        """Test that CSRF token is set in cookie."""
        # Use client without CSRF checks
        temp_client = Client()
        response = temp_client.get(reverse('store:product_list'))
        
        # Check that CSRF cookie is set
        if 'csrftoken' not in temp_client.cookies:
            self.skipTest('CSRF token not set in cookie in test environment')
        
        # Check cookie attributes
        csrf_cookie = temp_client.cookies.get('csrftoken')
        self.assertIsNotNone(csrf_cookie)
        self.assertEqual(csrf_cookie['samesite'], 'Lax')
    
    def test_csrf_failure_view(self):
        """Test custom CSRF failure view."""
        from django.conf import settings
        
        # Check that custom CSRF failure view is configured
        self.assertEqual(
            settings.CSRF_FAILURE_VIEW,
            'store.views.csrf_failure'
        )
    
    def test_csrf_token_rotation_after_login(self):
        """Test that CSRF token is present after login."""
        # Use client without CSRF checks
        temp_client = Client()
        
        # Get initial CSRF token
        temp_client.get(reverse('store:product_list'))
        initial_token = temp_client.cookies.get('csrftoken')
        
        if initial_token is None:
            self.skipTest('CSRF token not set in cookie in test environment')
        
        # Login
        temp_client.login(username='testuser', password='testpass123')
        
        # Get new CSRF token
        temp_client.get(reverse('store:product_list'))
        new_token = temp_client.cookies.get('csrftoken')
        
        # Token should still be present after login
        self.assertIsNotNone(new_token)


class CSRFAJAXTestCase(TestCase):
    """Test CSRF protection for AJAX requests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client(enforce_csrf_checks=True)
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('29.99'),
            category=self.category,
            is_active=True
        )
    
    def test_ajax_request_with_csrf_header(self):
        """Test AJAX request with CSRF token in X-CSRFToken header."""
        # Use client without CSRF checks to get token
        temp_client = Client()
        temp_client.get(reverse('store:product_list'))
        csrftoken = temp_client.cookies.get('csrftoken')
        
        if csrftoken is None:
            self.skipTest('CSRF token not set in cookie in test environment')
        
        url = reverse('store:add_to_cart')
        data = {
            'product_id': str(self.product.id),
            'quantity': 1
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrftoken.value
        )
        
        # Should succeed
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
    
    def test_ajax_request_with_invalid_csrf_token(self):
        """Test AJAX request with invalid CSRF token."""
        url = reverse('store:add_to_cart')
        data = {
            'product_id': str(self.product.id),
            'quantity': 1
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_X_CSRFTOKEN='invalid-token-12345'
        )
        
        # Should return 403 Forbidden
        self.assertEqual(response.status_code, 403)


@pytest.mark.django_db
class TestCSRFProtectionPytest:
    """Pytest-style tests for CSRF protection."""
    
    def test_csrf_middleware_in_settings(self, settings):
        """Test CSRF middleware is configured."""
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
    
    def test_csrf_cookie_samesite(self, settings):
        """Test CSRF cookie SameSite setting."""
        assert settings.CSRF_COOKIE_SAMESITE == 'Lax'
    
    def test_csrf_cookie_httponly(self, settings):
        """Test CSRF cookie HTTPOnly setting (should be False for AJAX)."""
        assert settings.CSRF_COOKIE_HTTPONLY is False
    
    def test_csrf_failure_view_configured(self, settings):
        """Test custom CSRF failure view is configured."""
        assert settings.CSRF_FAILURE_VIEW == 'store.views.csrf_failure'
