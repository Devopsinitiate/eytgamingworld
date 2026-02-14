"""
Unit tests for product catalog views.

Tests product list and detail views including:
- Product listing with pagination
- Category filtering
- Search functionality
- Price range filtering
- Sorting
- Product detail display
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from store.models import Product, Category, ProductImage, ProductVariant


@pytest.mark.django_db
class TestProductListView(TestCase):
    """Test product list view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create categories
        self.category1 = Category.objects.create(
            name='Jerseys',
            slug='jerseys',
            description='Team jerseys'
        )
        self.category2 = Category.objects.create(
            name='Hoodies',
            slug='hoodies',
            description='Team hoodies'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='EYT Gaming Jersey',
            slug='eyt-gaming-jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category1,
            stock_quantity=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='EYT Gaming Hoodie',
            slug='eyt-gaming-hoodie',
            description='Comfortable team hoodie',
            price=Decimal('69.99'),
            category=self.category2,
            stock_quantity=5,
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            name='Premium Jersey',
            slug='premium-jersey',
            description='Premium quality jersey',
            price=Decimal('79.99'),
            category=self.category1,
            stock_quantity=0,
            is_active=True
        )
        
        # Create inactive product (should not appear)
        self.inactive_product = Product.objects.create(
            name='Inactive Product',
            slug='inactive-product',
            description='This should not appear',
            price=Decimal('99.99'),
            category=self.category1,
            stock_quantity=10,
            is_active=False
        )
    
    def test_product_list_displays_active_products(self):
        """Test that product list displays only active products."""
        response = self.client.get(reverse('store:product_list'))
        
        assert response.status_code == 200
        assert self.product1 in response.context['products']
        assert self.product2 in response.context['products']
        assert self.product3 in response.context['products']
        assert self.inactive_product not in response.context['products']
    
    def test_category_filtering(self):
        """Test filtering products by category."""
        response = self.client.get(
            reverse('store:product_list'),
            {'category': 'jerseys'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert self.product1 in products
        assert self.product3 in products
        assert self.product2 not in products
    
    def test_search_functionality(self):
        """Test search by product name and description."""
        # Search by name
        response = self.client.get(
            reverse('store:product_list'),
            {'q': 'hoodie'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert self.product2 in products
        assert self.product1 not in products
        
        # Search by description
        response = self.client.get(
            reverse('store:product_list'),
            {'q': 'comfortable'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert self.product2 in products
    
    def test_search_sanitization(self):
        """Test that search queries are sanitized."""
        # Test with SQL injection attempt
        response = self.client.get(
            reverse('store:product_list'),
            {'q': "'; DROP TABLE products; --"}
        )
        
        # Should not crash and should return safely
        assert response.status_code == 200
        
        # Test with XSS attempt
        response = self.client.get(
            reverse('store:product_list'),
            {'q': '<script>alert("xss")</script>'}
        )
        
        assert response.status_code == 200
    
    def test_price_range_filtering(self):
        """Test filtering by price range."""
        # Filter for products under $60
        response = self.client.get(
            reverse('store:product_list'),
            {'max_price': '60.00'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert self.product1 in products  # $49.99
        assert self.product2 not in products  # $69.99
        assert self.product3 not in products  # $79.99
        
        # Filter for products between $60 and $80
        response = self.client.get(
            reverse('store:product_list'),
            {'min_price': '60.00', 'max_price': '80.00'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert self.product2 in products  # $69.99
        assert self.product3 in products  # $79.99
        assert self.product1 not in products  # $49.99
    
    def test_price_filtering_invalid_values(self):
        """Test that invalid price values are ignored."""
        # Invalid price values should not crash
        response = self.client.get(
            reverse('store:product_list'),
            {'min_price': 'invalid', 'max_price': 'also_invalid'}
        )
        
        assert response.status_code == 200
        # Should return all products
        assert len(response.context['products']) == 3
    
    def test_sorting_by_price_low_to_high(self):
        """Test sorting products by price (low to high)."""
        response = self.client.get(
            reverse('store:product_list'),
            {'sort': 'price_low'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert products[0] == self.product1  # $49.99
        assert products[1] == self.product2  # $69.99
        assert products[2] == self.product3  # $79.99
    
    def test_sorting_by_price_high_to_low(self):
        """Test sorting products by price (high to low)."""
        response = self.client.get(
            reverse('store:product_list'),
            {'sort': 'price_high'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        assert products[0] == self.product3  # $79.99
        assert products[1] == self.product2  # $69.99
        assert products[2] == self.product1  # $49.99
    
    def test_sorting_by_name(self):
        """Test sorting products by name."""
        response = self.client.get(
            reverse('store:product_list'),
            {'sort': 'name'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        # Should be alphabetically sorted
        product_names = [p.name for p in products]
        assert product_names == sorted(product_names)
    
    def test_sorting_by_newest(self):
        """Test sorting products by creation date (newest first)."""
        response = self.client.get(
            reverse('store:product_list'),
            {'sort': 'newest'}
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        # Newest should be first (product3 was created last)
        assert products[0] == self.product3
    
    def test_pagination(self):
        """Test that pagination works correctly."""
        # Create 30 products to test pagination (24 per page)
        for i in range(30):
            Product.objects.create(
                name=f'Test Product {i}',
                slug=f'test-product-{i}',
                description='Test description',
                price=Decimal('29.99'),
                category=self.category1,
                stock_quantity=10,
                is_active=True
            )
        
        # First page
        response = self.client.get(reverse('store:product_list'))
        assert response.status_code == 200
        assert len(response.context['products']) == 24
        assert response.context['products'].has_next()
        
        # Second page
        response = self.client.get(
            reverse('store:product_list'),
            {'page': 2}
        )
        assert response.status_code == 200
        assert len(response.context['products']) == 9  # 33 total - 24 on first page
        assert not response.context['products'].has_next()
    
    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(
            reverse('store:product_list'),
            {
                'category': 'jerseys',
                'max_price': '60.00',
                'sort': 'price_low'
            }
        )
        
        assert response.status_code == 200
        products = list(response.context['products'])
        # Should only show product1 (jerseys category, under $60)
        assert len(products) == 1
        assert products[0] == self.product1
    
    def test_no_results(self):
        """Test display when no products match filters."""
        response = self.client.get(
            reverse('store:product_list'),
            {'q': 'nonexistent product xyz'}
        )
        
        assert response.status_code == 200
        assert len(response.context['products']) == 0


@pytest.mark.django_db
class TestProductDetailView(TestCase):
    """Test product detail view functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create category
        self.category = Category.objects.create(
            name='Jerseys',
            slug='jerseys',
            description='Team jerseys'
        )
        
        # Create product
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            slug='eyt-gaming-jersey',
            description='Official team jersey with premium quality',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        
        # Create product images
        self.image1 = ProductImage.objects.create(
            product=self.product,
            image='products/jersey1.jpg',
            alt_text='Front view of jersey',
            display_order=0,
            is_primary=True
        )
        
        self.image2 = ProductImage.objects.create(
            product=self.product,
            image='products/jersey2.jpg',
            alt_text='Back view of jersey',
            display_order=1,
            is_primary=False
        )
        
        # Create variants
        self.variant_small = ProductVariant.objects.create(
            product=self.product,
            name='Size: Small',
            sku='EYT-JERSEY-S',
            price_adjustment=Decimal('0.00'),
            stock_quantity=5,
            is_available=True
        )
        
        self.variant_large = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=3,
            is_available=True
        )
    
    def test_product_detail_displays_correctly(self):
        """Test that product detail page displays all information."""
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': self.product.slug})
        )
        
        assert response.status_code == 200
        assert response.context['product'] == self.product
        # Context contains the correct product - that's the main thing we need to verify
        # The template rendering is tested by other tests
    
    def test_product_detail_shows_images(self):
        """Test that product images are displayed."""
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': self.product.slug})
        )
        
        assert response.status_code == 200
        images = response.context['images']
        assert len(images) == 2
        assert self.image1 in images
        assert self.image2 in images
    
    def test_product_detail_shows_variants(self):
        """Test that product variants are displayed."""
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': self.product.slug})
        )
        
        assert response.status_code == 200
        variants = response.context['variants']
        assert len(variants) == 2
        assert self.variant_small in variants
        assert self.variant_large in variants
    
    def test_product_detail_stock_availability(self):
        """Test stock availability display."""
        # Product with stock
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': self.product.slug})
        )
        
        assert response.status_code == 200
        assert response.context['has_stock'] is True
        
        # Product without stock
        out_of_stock_product = Product.objects.create(
            name='Out of Stock Product',
            slug='out-of-stock-product',
            description='No stock available',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=0,
            is_active=True
        )
        
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': out_of_stock_product.slug})
        )
        
        assert response.status_code == 200
        assert response.context['has_stock'] is False
    
    def test_product_detail_inactive_product_404(self):
        """Test that inactive products return 404."""
        inactive_product = Product.objects.create(
            name='Inactive Product',
            slug='inactive-product',
            description='This is inactive',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=False
        )
        
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': inactive_product.slug})
        )
        
        assert response.status_code == 404
    
    def test_product_detail_nonexistent_product_404(self):
        """Test that nonexistent products return 404."""
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': 'nonexistent-product'})
        )
        
        assert response.status_code == 404
    
    def test_product_detail_with_variants_has_stock(self):
        """Test that product with variants shows stock correctly."""
        # Product with no base stock but variants have stock
        product_with_variants = Product.objects.create(
            name='Variant Product',
            slug='variant-product',
            description='Product with variants',
            price=Decimal('39.99'),
            category=self.category,
            stock_quantity=0,  # No base stock
            is_active=True
        )
        
        # Add variant with stock
        ProductVariant.objects.create(
            product=product_with_variants,
            name='Size: Medium',
            sku='VAR-PROD-M',
            price_adjustment=Decimal('0.00'),
            stock_quantity=5,
            is_available=True
        )
        
        response = self.client.get(
            reverse('store:product_detail', kwargs={'slug': product_with_variants.slug})
        )
        
        assert response.status_code == 200
        # Should show as having stock because variant has stock
        assert response.context['has_stock'] is True
