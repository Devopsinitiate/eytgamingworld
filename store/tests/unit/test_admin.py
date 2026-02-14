"""
Unit tests for admin interface functionality.

Tests admin forms, validation, bulk actions, and image upload validation.
"""

import os
import tempfile
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from PIL import Image
import io

from store.models import Category, Product, ProductVariant, ProductImage
from store.admin import (
    ProductAdmin,
    ProductVariantAdmin,
    ProductImageAdmin,
    ProductForm,
    ProductVariantForm,
    ProductImageForm
)

User = get_user_model()


class MockRequest:
    """Mock request object for testing admin actions."""
    pass


class ProductFormTest(TestCase):
    """Test ProductForm validation."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
    
    def test_valid_product_form(self):
        """Test that valid product data passes validation."""
        form_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('29.99'),
            'category': self.category.id,
            'stock_quantity': 10,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_negative_price_validation(self):
        """Test that negative price is rejected."""
        form_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('-10.00'),
            'category': self.category.id,
            'stock_quantity': 10,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
    
    def test_zero_price_validation(self):
        """Test that zero price is rejected."""
        form_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('0.00'),
            'category': self.category.id,
            'stock_quantity': 10,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
    
    def test_negative_stock_validation(self):
        """Test that negative stock is rejected."""
        form_data = {
            'name': 'Test Product',
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('29.99'),
            'category': self.category.id,
            'stock_quantity': -5,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('stock_quantity', form.errors)
    
    def test_empty_name_validation(self):
        """Test that empty product name is rejected."""
        form_data = {
            'name': '   ',
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('29.99'),
            'category': self.category.id,
            'stock_quantity': 10,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_long_name_validation(self):
        """Test that product name exceeding 200 characters is rejected."""
        form_data = {
            'name': 'A' * 201,
            'slug': 'test-product',
            'description': 'Test description',
            'price': Decimal('29.99'),
            'category': self.category.id,
            'stock_quantity': 10,
            'is_active': True
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class ProductVariantFormTest(TestCase):
    """Test ProductVariantForm validation."""
    
    def setUp(self):
        """Set up test data."""
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
            stock_quantity=10
        )
    
    def test_valid_variant_form(self):
        """Test that valid variant data passes validation."""
        form_data = {
            'product': self.product.id,
            'name': 'Size: Large',
            'sku': 'TEST-L',
            'price_adjustment': Decimal('5.00'),
            'stock_quantity': 5,
            'is_available': True
        }
        form = ProductVariantForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_sku_uppercase_normalization(self):
        """Test that SKU is normalized to uppercase."""
        form_data = {
            'product': self.product.id,
            'name': 'Size: Large',
            'sku': 'test-l',
            'price_adjustment': Decimal('5.00'),
            'stock_quantity': 5,
            'is_available': True
        }
        form = ProductVariantForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['sku'], 'TEST-L')
    
    def test_duplicate_sku_validation(self):
        """Test that duplicate SKU is rejected."""
        # Create existing variant
        ProductVariant.objects.create(
            product=self.product,
            name='Size: Medium',
            sku='TEST-M',
            stock_quantity=5
        )
        
        # Try to create another variant with same SKU
        form_data = {
            'product': self.product.id,
            'name': 'Size: Large',
            'sku': 'test-m',  # Will be normalized to TEST-M
            'price_adjustment': Decimal('5.00'),
            'stock_quantity': 5,
            'is_available': True
        }
        form = ProductVariantForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('sku', form.errors)
    
    def test_negative_stock_validation(self):
        """Test that negative stock is rejected."""
        form_data = {
            'product': self.product.id,
            'name': 'Size: Large',
            'sku': 'TEST-L',
            'price_adjustment': Decimal('5.00'),
            'stock_quantity': -5,
            'is_available': True
        }
        form = ProductVariantForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('stock_quantity', form.errors)


class ProductImageFormTest(TestCase):
    """Test ProductImageForm validation including file type and size."""
    
    def setUp(self):
        """Set up test data."""
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
            stock_quantity=10
        )
    
    def create_test_image(self, format='JPEG', size=(100, 100), file_size_mb=1):
        """Helper to create test image file."""
        image = Image.new('RGB', size, color='red')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        
        # Adjust file size if needed
        content = image_io.getvalue()
        if file_size_mb > 1:
            # Pad with zeros to reach desired size
            target_size = int(file_size_mb * 1024 * 1024)
            content = content + b'\x00' * (target_size - len(content))
        
        filename = f'test.{format.lower()}'
        if format == 'JPEG':
            filename = 'test.jpg'
        
        uploaded_file = SimpleUploadedFile(
            filename,
            content,
            content_type=f'image/{format.lower()}'
        )
        
        return uploaded_file
    
    def test_valid_jpeg_image(self):
        """Test that valid JPEG image passes validation."""
        image_file = self.create_test_image(format='JPEG')
        
        form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        form = ProductImageForm(data=form_data, files={'image': image_file})
        self.assertTrue(form.is_valid())
    
    def test_valid_png_image(self):
        """Test that valid PNG image passes validation."""
        image_file = self.create_test_image(format='PNG')
        
        form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        form = ProductImageForm(data=form_data, files={'image': image_file})
        self.assertTrue(form.is_valid())
    
    def test_valid_webp_image(self):
        """Test that valid WebP image passes validation."""
        image_file = self.create_test_image(format='WEBP')
        
        form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        form = ProductImageForm(data=form_data, files={'image': image_file})
        self.assertTrue(form.is_valid())
    
    def test_invalid_file_type(self):
        """Test that invalid file type is rejected."""
        # Create a text file pretending to be an image
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        form = ProductImageForm(data=form_data, files={'image': invalid_file})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
    
    def test_file_size_exceeds_limit(self):
        """Test that file size exceeding 5MB is rejected."""
        # Create a large image (6MB)
        large_image = self.create_test_image(format='JPEG', file_size_mb=6)
        
        form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        form = ProductImageForm(data=form_data, files={'image': large_image})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
        self.assertIn('5MB', str(form.errors['image']))


class ProductAdminTest(TestCase):
    """Test ProductAdmin bulk actions and functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = ProductAdmin(Product, self.site)
        self.factory = RequestFactory()
        
        # Create superuser
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            description='Description 1',
            price=Decimal('29.99'),
            category=self.category,
            stock_quantity=10,
            is_active=True
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            description='Description 2',
            price=Decimal('39.99'),
            category=self.category,
            stock_quantity=5,
            is_active=False
        )
    
    def _create_request_with_messages(self):
        """Create a request with message middleware support."""
        from django.contrib.messages.storage.fallback import FallbackStorage
        request = self.factory.get('/')
        request.user = self.user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        return request
    
    def test_mark_as_active_action(self):
        """Test bulk action to mark products as active."""
        request = self._create_request_with_messages()
        
        queryset = Product.objects.filter(id=self.product2.id)
        self.admin.mark_as_active(request, queryset)
        
        self.product2.refresh_from_db()
        self.assertTrue(self.product2.is_active)
    
    def test_mark_as_inactive_action(self):
        """Test bulk action to mark products as inactive (soft delete)."""
        request = self._create_request_with_messages()
        
        queryset = Product.objects.filter(id=self.product1.id)
        self.admin.mark_as_inactive(request, queryset)
        
        self.product1.refresh_from_db()
        self.assertFalse(self.product1.is_active)
    
    def test_duplicate_products_action(self):
        """Test bulk action to duplicate products."""
        request = self._create_request_with_messages()
        
        initial_count = Product.objects.count()
        queryset = Product.objects.filter(id=self.product1.id)
        self.admin.duplicate_products(request, queryset)
        
        # Should have one more product
        self.assertEqual(Product.objects.count(), initial_count + 1)
        
        # Check the duplicated product
        duplicated = Product.objects.filter(name='Product 1 (Copy)').first()
        self.assertIsNotNone(duplicated)
        self.assertNotEqual(duplicated.id, self.product1.id)
        self.assertNotEqual(duplicated.slug, self.product1.slug)
    
    def test_export_to_csv_action(self):
        """Test bulk action to export products to CSV."""
        request = self._create_request_with_messages()
        
        queryset = Product.objects.all()
        response = self.admin.export_to_csv(request, queryset)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Check CSV content
        content = response.content.decode('utf-8')
        self.assertIn('Product 1', content)
        self.assertIn('Product 2', content)


class ProductImageAdminTest(TestCase):
    """Test ProductImageAdmin functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = ProductImageAdmin(ProductImage, self.site)
        self.factory = RequestFactory()
        
        # Create superuser
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='password123'
        )
        
        # Create test data
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
            stock_quantity=10
        )
        
        # Create test images
        image_file = SimpleUploadedFile(
            'test.jpg',
            b'fake image content',
            content_type='image/jpeg'
        )
        self.image1 = ProductImage.objects.create(
            product=self.product,
            image=image_file,
            alt_text='Image 1',
            display_order=0,
            is_primary=True
        )
        
        image_file2 = SimpleUploadedFile(
            'test2.jpg',
            b'fake image content 2',
            content_type='image/jpeg'
        )
        self.image2 = ProductImage.objects.create(
            product=self.product,
            image=image_file2,
            alt_text='Image 2',
            display_order=1,
            is_primary=False
        )
    
    def _create_request_with_messages(self):
        """Create a request with message middleware support."""
        from django.contrib.messages.storage.fallback import FallbackStorage
        request = self.factory.get('/')
        request.user = self.user
        setattr(request, 'session', {})
        setattr(request, '_messages', FallbackStorage(request))
        return request
    
    def test_set_as_primary_action_single_image(self):
        """Test setting a single image as primary."""
        request = self._create_request_with_messages()
        
        queryset = ProductImage.objects.filter(id=self.image2.id)
        self.admin.set_as_primary(request, queryset)
        
        self.image1.refresh_from_db()
        self.image2.refresh_from_db()
        
        self.assertFalse(self.image1.is_primary)
        self.assertTrue(self.image2.is_primary)
    
    def test_set_as_primary_action_multiple_images(self):
        """Test that setting multiple images as primary fails."""
        request = self._create_request_with_messages()
        
        queryset = ProductImage.objects.all()
        # This should not change anything
        self.admin.set_as_primary(request, queryset)
        
        self.image1.refresh_from_db()
        self.image2.refresh_from_db()
        
        # Should remain unchanged
        self.assertTrue(self.image1.is_primary)
        self.assertFalse(self.image2.is_primary)


class AdminValidationIntegrationTest(TestCase):
    """Integration tests for admin validation."""
    
    def setUp(self):
        """Set up test data."""
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
            stock_quantity=10
        )
    
    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Helper to create test image file."""
        image = Image.new('RGB', size, color='red')
        image_io = io.BytesIO()
        image.save(image_io, format=format)
        image_io.seek(0)
        
        filename = f'test.{format.lower()}'
        if format == 'JPEG':
            filename = 'test.jpg'
        
        uploaded_file = SimpleUploadedFile(
            filename,
            image_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
        
        return uploaded_file
    
    def test_product_with_variants_and_images(self):
        """Test creating product with variants and images through forms."""
        # Create variant
        variant_form_data = {
            'product': self.product.id,
            'name': 'Size: Large',
            'sku': 'TEST-L',
            'price_adjustment': Decimal('5.00'),
            'stock_quantity': 5,
            'is_available': True
        }
        variant_form = ProductVariantForm(data=variant_form_data)
        self.assertTrue(variant_form.is_valid())
        variant = variant_form.save()
        
        # Verify final price calculation
        self.assertEqual(variant.final_price, Decimal('34.99'))
        
        # Create image with proper test image
        image_file = self.create_test_image(format='JPEG')
        image_form_data = {
            'product': self.product.id,
            'alt_text': 'Test image',
            'display_order': 0,
            'is_primary': True
        }
        image_form = ProductImageForm(data=image_form_data, files={'image': image_file})
        self.assertTrue(image_form.is_valid(), f"Form errors: {image_form.errors}")
        image = image_form.save()
        
        # Verify relationships
        self.assertEqual(self.product.variants.count(), 1)
        self.assertEqual(self.product.images.count(), 1)
        self.assertTrue(image.is_primary)
