"""
Unit tests for admin panel inventory tracking features.

Tests the enhanced inventory tracking display in the Django admin panel,
including stock status indicators and low stock warnings.
"""

from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from decimal import Decimal

from store.models import Category, Product, ProductVariant
from store.admin import ProductAdmin, ProductVariantAdmin

User = get_user_model()


class ProductAdminInventoryTrackingTest(TestCase):
    """Test inventory tracking features in ProductAdmin."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = ProductAdmin(Product, self.site)
        
        # Create test user
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create products with different stock levels
        self.product_in_stock = Product.objects.create(
            name='Product In Stock',
            slug='product-in-stock',
            description='Test product',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=50,
            is_active=True
        )
        
        self.product_low_stock = Product.objects.create(
            name='Product Low Stock',
            slug='product-low-stock',
            description='Test product',
            price=Decimal('39.99'),
            category=self.category,
            stock_quantity=5,
            is_active=True
        )
        
        self.product_out_of_stock = Product.objects.create(
            name='Product Out of Stock',
            slug='product-out-of-stock',
            description='Test product',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=0,
            is_active=True
        )
    
    def test_is_in_stock_display_for_in_stock_product(self):
        """Test is_in_stock display method shows correct status for in-stock product."""
        result = self.admin.is_in_stock(self.product_in_stock)
        self.assertIn('In Stock', result)
        self.assertIn('green', result)
        self.assertIn('✓', result)
    
    def test_is_in_stock_display_for_out_of_stock_product(self):
        """Test is_in_stock display method shows correct status for out-of-stock product."""
        result = self.admin.is_in_stock(self.product_out_of_stock)
        self.assertIn('Out of Stock', result)
        self.assertIn('red', result)
        self.assertIn('✗', result)
    
    def test_is_low_stock_display_for_low_stock_product(self):
        """Test is_low_stock display method shows warning for low stock product."""
        result = self.admin.is_low_stock(self.product_low_stock)
        self.assertIn('Low Stock', result)
        self.assertIn('orange', result)
        self.assertIn('⚠', result)
        self.assertIn('5 units', result)
    
    def test_is_low_stock_display_for_ok_stock_product(self):
        """Test is_low_stock display method shows OK for adequate stock."""
        result = self.admin.is_low_stock(self.product_in_stock)
        self.assertIn('OK', result)
        self.assertIn('green', result)
        self.assertIn('✓', result)
        self.assertIn('50 units', result)
    
    def test_is_low_stock_display_for_out_of_stock_product(self):
        """Test is_low_stock display method shows out of stock for zero stock."""
        result = self.admin.is_low_stock(self.product_out_of_stock)
        self.assertIn('Out of Stock', result)
        self.assertIn('red', result)
        self.assertIn('✗', result)
    
    def test_stock_quantity_displayed_in_list_display(self):
        """Test that stock_quantity is included in list_display."""
        self.assertIn('stock_quantity', self.admin.list_display)
    
    def test_stock_status_displayed_in_list_display(self):
        """Test that is_in_stock is included in list_display."""
        self.assertIn('is_in_stock', self.admin.list_display)
    
    def test_low_stock_warning_displayed_in_list_display(self):
        """Test that is_low_stock is included in list_display."""
        self.assertIn('is_low_stock', self.admin.list_display)


class ProductVariantAdminInventoryTrackingTest(TestCase):
    """Test inventory tracking features in ProductVariantAdmin."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = ProductVariantAdmin(ProductVariant, self.site)
        
        # Create test category and product
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test product',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=100
        )
        
        # Create variants with different stock levels
        self.variant_in_stock = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='TEST-L',
            stock_quantity=50
        )
        
        self.variant_low_stock = ProductVariant.objects.create(
            product=self.product,
            name='Size: Medium',
            sku='TEST-M',
            stock_quantity=3
        )
        
        self.variant_out_of_stock = ProductVariant.objects.create(
            product=self.product,
            name='Size: Small',
            sku='TEST-S',
            stock_quantity=0
        )
    
    def test_is_in_stock_display_for_in_stock_variant(self):
        """Test is_in_stock display method shows correct status for in-stock variant."""
        result = self.admin.is_in_stock(self.variant_in_stock)
        self.assertIn('In Stock', result)
        self.assertIn('green', result)
        self.assertIn('✓', result)
    
    def test_is_in_stock_display_for_out_of_stock_variant(self):
        """Test is_in_stock display method shows correct status for out-of-stock variant."""
        result = self.admin.is_in_stock(self.variant_out_of_stock)
        self.assertIn('Out of Stock', result)
        self.assertIn('red', result)
        self.assertIn('✗', result)
    
    def test_is_low_stock_display_for_low_stock_variant(self):
        """Test is_low_stock display method shows warning for low stock variant."""
        result = self.admin.is_low_stock(self.variant_low_stock)
        self.assertIn('Low Stock', result)
        self.assertIn('orange', result)
        self.assertIn('⚠', result)
        self.assertIn('3 units', result)
    
    def test_is_low_stock_display_for_ok_stock_variant(self):
        """Test is_low_stock display method shows OK for adequate stock."""
        result = self.admin.is_low_stock(self.variant_in_stock)
        self.assertIn('OK', result)
        self.assertIn('green', result)
        self.assertIn('✓', result)
        self.assertIn('50 units', result)
    
    def test_stock_quantity_displayed_in_list_display(self):
        """Test that stock_quantity is included in list_display."""
        self.assertIn('stock_quantity', self.admin.list_display)
    
    def test_stock_status_displayed_in_list_display(self):
        """Test that is_in_stock is included in list_display."""
        self.assertIn('is_in_stock', self.admin.list_display)
    
    def test_low_stock_warning_displayed_in_list_display(self):
        """Test that is_low_stock is included in list_display."""
        self.assertIn('is_low_stock', self.admin.list_display)

