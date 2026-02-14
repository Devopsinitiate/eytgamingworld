"""
Unit tests for store models.

Tests the Product, Category, ProductVariant, and ProductImage models
including field validation, soft delete, and business logic.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from store.models import Category, Product, ProductVariant, ProductImage
from django.core.files.uploadedfile import SimpleUploadedFile


class CategoryModelTestCase(TestCase):
    """Test Category model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent_category = Category.objects.create(
            name='Apparel',
            description='Clothing and accessories'
        )
    
    def test_category_creation(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Jerseys',
            description='Team jerseys'
        )
        self.assertEqual(category.name, 'Jerseys')
        self.assertEqual(category.slug, 'jerseys')
        self.assertIsNotNone(category.id)
        self.assertIsNotNone(category.created_at)
    
    def test_category_slug_auto_generation(self):
        """Test that slug is auto-generated from name."""
        category = Category.objects.create(name='Gaming Hoodies')
        self.assertEqual(category.slug, 'gaming-hoodies')
    
    def test_category_slug_uniqueness(self):
        """Test that slug must be unique."""
        Category.objects.create(name='Accessories', slug='accessories')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Accessories 2', slug='accessories')
    
    def test_category_hierarchy(self):
        """Test parent-child category relationships."""
        child_category = Category.objects.create(
            name='Jerseys',
            parent=self.parent_category
        )
        self.assertEqual(child_category.parent, self.parent_category)
        self.assertIn(child_category, self.parent_category.children.all())
    
    def test_category_ordering(self):
        """Test category ordering by display_order and name."""
        # Clear any existing categories from setUp
        Category.objects.all().delete()
        
        cat1 = Category.objects.create(name='Hoodies', display_order=2)
        cat2 = Category.objects.create(name='Jerseys', display_order=1)
        cat3 = Category.objects.create(name='Accessories', display_order=1)
        
        categories = list(Category.objects.all())
        # Should be ordered by display_order first, then name
        self.assertEqual(categories[0].name, 'Accessories')
        self.assertEqual(categories[1].name, 'Jerseys')
        self.assertEqual(categories[2].name, 'Hoodies')
    
    def test_category_str_representation(self):
        """Test string representation of category."""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(str(category), 'Test Category')


class ProductModelTestCase(TestCase):
    """Test Product model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.category = Category.objects.create(
            name='Jerseys',
            description='Team jerseys'
        )
    
    def test_product_creation(self):
        """Test creating a product."""
        product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=100
        )
        self.assertEqual(product.name, 'EYT Gaming Jersey')
        self.assertEqual(product.price, Decimal('49.99'))
        self.assertEqual(product.stock_quantity, 100)
        self.assertTrue(product.is_active)
        self.assertIsNotNone(product.id)
    
    def test_product_slug_auto_generation(self):
        """Test that slug is auto-generated from name."""
        product = Product.objects.create(
            name='Gaming Hoodie Pro',
            description='Premium hoodie',
            price=Decimal('59.99'),
            category=self.category
        )
        self.assertEqual(product.slug, 'gaming-hoodie-pro')
    
    def test_product_slug_uniqueness(self):
        """Test that slug must be unique."""
        Product.objects.create(
            name='Jersey',
            slug='jersey',
            description='Test',
            price=Decimal('49.99'),
            category=self.category
        )
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Jersey 2',
                slug='jersey',
                description='Test',
                price=Decimal('49.99'),
                category=self.category
            )
    
    def test_product_price_validation(self):
        """Test that price must be positive."""
        product = Product(
            name='Test Product',
            description='Test',
            price=Decimal('-10.00'),
            category=self.category
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_stock_quantity_validation(self):
        """Test that stock quantity cannot be negative."""
        product = Product(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=-5
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_soft_delete(self):
        """Test soft delete functionality."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category
        )
        product_id = product.id
        
        # Soft delete
        product.delete()
        
        # Product should still exist in database
        product = Product.objects.get(id=product_id)
        self.assertFalse(product.is_active)
    
    def test_product_hard_delete(self):
        """Test hard delete functionality."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category
        )
        product_id = product.id
        
        # Hard delete
        product.hard_delete()
        
        # Product should not exist in database
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=product_id)
    
    def test_product_is_in_stock_property(self):
        """Test is_in_stock property."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=10
        )
        self.assertTrue(product.is_in_stock)
        
        product.stock_quantity = 0
        product.save()
        self.assertFalse(product.is_in_stock)
    
    def test_product_is_low_stock_property(self):
        """Test is_low_stock property."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=5
        )
        self.assertTrue(product.is_low_stock)
        
        product.stock_quantity = 15
        product.save()
        self.assertFalse(product.is_low_stock)
        
        product.stock_quantity = 0
        product.save()
        self.assertFalse(product.is_low_stock)  # Not low stock, it's out of stock
    
    def test_product_str_representation(self):
        """Test string representation of product."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category
        )
        self.assertEqual(str(product), 'Test Product')
    
    def test_product_category_protection(self):
        """Test that category cannot be deleted if products exist."""
        product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('49.99'),
            category=self.category
        )
        
        # Attempting to delete category should raise error
        with self.assertRaises(Exception):
            self.category.delete()


class ProductVariantModelTestCase(TestCase):
    """Test ProductVariant model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category
        )
    
    def test_variant_creation(self):
        """Test creating a product variant."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=50
        )
        self.assertEqual(variant.name, 'Size: Large')
        self.assertEqual(variant.sku, 'EYT-JERSEY-L')
        self.assertEqual(variant.price_adjustment, Decimal('5.00'))
        self.assertTrue(variant.is_available)
    
    def test_variant_sku_uniqueness(self):
        """Test that SKU must be unique."""
        ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            stock_quantity=50
        )
        
        with self.assertRaises(IntegrityError):
            ProductVariant.objects.create(
                product=self.product,
                name='Size: XL',
                sku='EYT-JERSEY-L',
                stock_quantity=50
            )
    
    def test_variant_final_price_calculation(self):
        """Test final price calculation with adjustment."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=50
        )
        self.assertEqual(variant.final_price, Decimal('54.99'))
        
        # Test with negative adjustment (discount)
        variant.price_adjustment = Decimal('-5.00')
        variant.save()
        self.assertEqual(variant.final_price, Decimal('44.99'))
    
    def test_variant_is_in_stock_property(self):
        """Test is_in_stock property."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            stock_quantity=10
        )
        self.assertTrue(variant.is_in_stock)
        
        variant.stock_quantity = 0
        variant.save()
        self.assertFalse(variant.is_in_stock)
    
    def test_variant_is_low_stock_property(self):
        """Test is_low_stock property."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            stock_quantity=5
        )
        self.assertTrue(variant.is_low_stock)
        
        variant.stock_quantity = 15
        variant.save()
        self.assertFalse(variant.is_low_stock)
    
    def test_variant_str_representation(self):
        """Test string representation of variant."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            stock_quantity=50
        )
        self.assertEqual(str(variant), 'EYT Gaming Jersey - Size: Large')
    
    def test_variant_cascade_delete(self):
        """Test that variants are deleted when product is hard deleted."""
        variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            stock_quantity=50
        )
        variant_id = variant.id
        
        # Hard delete product
        self.product.hard_delete()
        
        # Variant should also be deleted
        with self.assertRaises(ProductVariant.DoesNotExist):
            ProductVariant.objects.get(id=variant_id)


class ProductImageModelTestCase(TestCase):
    """Test ProductImage model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category
        )
        
        # Create a simple test image
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'fake image content',
            content_type='image/jpeg'
        )
    
    def test_image_creation(self):
        """Test creating a product image."""
        image = ProductImage.objects.create(
            product=self.product,
            image=self.test_image,
            alt_text='EYT Gaming Jersey Front View',
            display_order=1,
            is_primary=True
        )
        self.assertEqual(image.alt_text, 'EYT Gaming Jersey Front View')
        self.assertEqual(image.display_order, 1)
        self.assertTrue(image.is_primary)
    
    def test_image_primary_uniqueness(self):
        """Test that only one image can be primary per product."""
        image1 = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('img1.jpg', b'content1', 'image/jpeg'),
            alt_text='Image 1',
            is_primary=True
        )
        
        image2 = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('img2.jpg', b'content2', 'image/jpeg'),
            alt_text='Image 2',
            is_primary=True
        )
        
        # Refresh image1 from database
        image1.refresh_from_db()
        
        # image1 should no longer be primary
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)
    
    def test_image_ordering(self):
        """Test image ordering by display_order."""
        img1 = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('img1.jpg', b'content1', 'image/jpeg'),
            alt_text='Image 1',
            display_order=2
        )
        img2 = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('img2.jpg', b'content2', 'image/jpeg'),
            alt_text='Image 2',
            display_order=1,
            is_primary=True
        )
        img3 = ProductImage.objects.create(
            product=self.product,
            image=SimpleUploadedFile('img3.jpg', b'content3', 'image/jpeg'),
            alt_text='Image 3',
            display_order=1
        )
        
        images = list(ProductImage.objects.filter(product=self.product))
        # Should be ordered by display_order, then is_primary, then created_at
        self.assertEqual(images[0], img2)  # display_order=1, is_primary=True
        self.assertEqual(images[1], img3)  # display_order=1, is_primary=False
        self.assertEqual(images[2], img1)  # display_order=2
    
    def test_image_str_representation(self):
        """Test string representation of image."""
        image = ProductImage.objects.create(
            product=self.product,
            image=self.test_image,
            alt_text='Test Image',
            display_order=1
        )
        self.assertEqual(str(image), 'EYT Gaming Jersey - Image 1')
    
    def test_image_cascade_delete(self):
        """Test that images are deleted when product is hard deleted."""
        image = ProductImage.objects.create(
            product=self.product,
            image=self.test_image,
            alt_text='Test Image'
        )
        image_id = image.id
        
        # Hard delete product
        self.product.hard_delete()
        
        # Image should also be deleted
        with self.assertRaises(ProductImage.DoesNotExist):
            ProductImage.objects.get(id=image_id)


class CartModelTestCase(TestCase):
    """Test Cart model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=100
        )
    
    def test_cart_creation_for_authenticated_user(self):
        """Test creating a cart for an authenticated user."""
        from store.models import Cart
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertIsNone(cart.session_key)
        self.assertIsNotNone(cart.id)
        self.assertIsNotNone(cart.created_at)
        self.assertIsNotNone(cart.updated_at)
    
    def test_cart_creation_for_guest_user(self):
        """Test creating a cart for a guest user with session key."""
        from store.models import Cart
        cart = Cart.objects.create(session_key='test_session_key_12345')
        self.assertIsNone(cart.user)
        self.assertEqual(cart.session_key, 'test_session_key_12345')
        self.assertIsNotNone(cart.id)
    
    def test_cart_str_representation_authenticated(self):
        """Test string representation for authenticated user cart."""
        from store.models import Cart
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(str(cart), 'Cart for testuser')
    
    def test_cart_str_representation_guest(self):
        """Test string representation for guest user cart."""
        from store.models import Cart
        cart = Cart.objects.create(session_key='test_session_key_12345')
        self.assertIn('Guest Cart', str(cart))
        self.assertIn('test_ses', str(cart))
    
    def test_cart_item_count_property(self):
        """Test item_count property."""
        from store.models import Cart, CartItem
        cart = Cart.objects.create(user=self.user)
        
        # Empty cart
        self.assertEqual(cart.item_count, 0)
        
        # Add items
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        product2 = Product.objects.create(
            name='Hoodie',
            description='Test',
            price=Decimal('59.99'),
            category=self.category
        )
        CartItem.objects.create(cart=cart, product=product2, quantity=3)
        
        # Should return total quantity
        self.assertEqual(cart.item_count, 5)
    
    def test_cart_is_empty_property(self):
        """Test is_empty property."""
        from store.models import Cart, CartItem
        cart = Cart.objects.create(user=self.user)
        
        # Empty cart
        self.assertTrue(cart.is_empty)
        
        # Add item
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.assertFalse(cart.is_empty)
    
    def test_cart_cascade_delete_with_user(self):
        """Test that cart is deleted when user is deleted."""
        from store.models import Cart
        cart = Cart.objects.create(user=self.user)
        cart_id = cart.id
        
        # Delete user
        self.user.delete()
        
        # Cart should also be deleted
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(id=cart_id)
    
    def test_cart_indexes(self):
        """Test that cart has proper indexes for performance."""
        from store.models import Cart
        # This test verifies the model has the expected indexes defined
        indexes = [index.name for index in Cart._meta.indexes]
        self.assertTrue(any('user' in idx for idx in indexes))
        self.assertTrue(any('session' in idx for idx in indexes))


class CartItemModelTestCase(TestCase):
    """Test CartItem model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.auth import get_user_model
        from store.models import Cart
        
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=100
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=50
        )
        self.cart = Cart.objects.create(user=self.user)
    
    def test_cart_item_creation_without_variant(self):
        """Test creating a cart item without a variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.cart, self.cart)
        self.assertEqual(cart_item.product, self.product)
        self.assertIsNone(cart_item.variant)
        self.assertEqual(cart_item.quantity, 2)
        self.assertIsNotNone(cart_item.added_at)
    
    def test_cart_item_creation_with_variant(self):
        """Test creating a cart item with a variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=3
        )
        self.assertEqual(cart_item.variant, self.variant)
        self.assertEqual(cart_item.quantity, 3)
    
    def test_cart_item_quantity_validation(self):
        """Test that quantity must be at least 1."""
        from store.models import CartItem
        cart_item = CartItem(
            cart=self.cart,
            product=self.product,
            quantity=0
        )
        with self.assertRaises(ValidationError):
            cart_item.full_clean()
        
        cart_item.quantity = -1
        with self.assertRaises(ValidationError):
            cart_item.full_clean()
    
    def test_cart_item_unique_constraint(self):
        """Test unique constraint on cart, product, and variant."""
        from store.models import CartItem
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=2
        )
        
        # Attempting to create duplicate should raise error
        with self.assertRaises(IntegrityError):
            CartItem.objects.create(
                cart=self.cart,
                product=self.product,
                variant=self.variant,
                quantity=3
            )
    
    def test_cart_item_unit_price_without_variant(self):
        """Test unit_price property without variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        self.assertEqual(cart_item.unit_price, Decimal('49.99'))
    
    def test_cart_item_unit_price_with_variant(self):
        """Test unit_price property with variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=1
        )
        # Product price (49.99) + variant adjustment (5.00) = 54.99
        self.assertEqual(cart_item.unit_price, Decimal('54.99'))
    
    def test_cart_item_total_price_calculation(self):
        """Test total_price property calculation."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=3
        )
        # 49.99 * 3 = 149.97
        self.assertEqual(cart_item.total_price, Decimal('149.97'))
        
        # With variant
        cart_item_variant = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=2
        )
        # 54.99 * 2 = 109.98
        self.assertEqual(cart_item_variant.total_price, Decimal('109.98'))
    
    def test_cart_item_is_available_property(self):
        """Test is_available property."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        
        # Product is active
        self.assertTrue(cart_item.is_available)
        
        # Deactivate product
        self.product.is_active = False
        self.product.save()
        self.assertFalse(cart_item.is_available)
        
        # Reactivate product
        self.product.is_active = True
        self.product.save()
        
        # Test with variant
        cart_item_variant = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=1
        )
        self.assertTrue(cart_item_variant.is_available)
        
        # Deactivate variant
        self.variant.is_available = False
        self.variant.save()
        self.assertFalse(cart_item_variant.is_available)
    
    def test_cart_item_has_sufficient_stock_property(self):
        """Test has_sufficient_stock property."""
        from store.models import CartItem
        
        # Without variant
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=50
        )
        self.assertTrue(cart_item.has_sufficient_stock)
        
        cart_item.quantity = 150
        cart_item.save()
        self.assertFalse(cart_item.has_sufficient_stock)
        
        # With variant
        cart_item_variant = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=30
        )
        self.assertTrue(cart_item_variant.has_sufficient_stock)
        
        cart_item_variant.quantity = 60
        cart_item_variant.save()
        self.assertFalse(cart_item_variant.has_sufficient_stock)
    
    def test_cart_item_str_representation_without_variant(self):
        """Test string representation without variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        self.assertEqual(str(cart_item), 'EYT Gaming Jersey (x2)')
    
    def test_cart_item_str_representation_with_variant(self):
        """Test string representation with variant."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=3
        )
        self.assertEqual(str(cart_item), 'EYT Gaming Jersey - Size: Large (x3)')
    
    def test_cart_item_cascade_delete_with_cart(self):
        """Test that cart items are deleted when cart is deleted."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        cart_item_id = cart_item.id
        
        # Delete cart
        self.cart.delete()
        
        # Cart item should also be deleted
        with self.assertRaises(CartItem.DoesNotExist):
            CartItem.objects.get(id=cart_item_id)
    
    def test_cart_item_cascade_delete_with_product(self):
        """Test that cart items are deleted when product is hard deleted."""
        from store.models import CartItem
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        cart_item_id = cart_item.id
        
        # Hard delete product
        self.product.hard_delete()
        
        # Cart item should also be deleted
        with self.assertRaises(CartItem.DoesNotExist):
            CartItem.objects.get(id=cart_item_id)


class OrderModelTestCase(TestCase):
    """Test Order model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.auth import get_user_model
        from store.models import Order
        
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=100
        )
    
    def test_order_creation(self):
        """Test creating an order."""
        from store.models import Order
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        self.assertEqual(order.order_number, 'EYT-2024-001234')
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.subtotal, Decimal('49.99'))
        self.assertEqual(order.total, Decimal('59.49'))
        self.assertEqual(order.status, 'pending')
        self.assertIsNone(order.paid_at)
        self.assertIsNotNone(order.id)
        self.assertIsNotNone(order.created_at)
    
    def test_order_number_uniqueness(self):
        """Test that order number must be unique."""
        from store.models import Order
        Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        with self.assertRaises(IntegrityError):
            Order.objects.create(
                order_number='EYT-2024-001234',
                user=self.user,
                subtotal=Decimal('49.99'),
                shipping_cost=Decimal('5.00'),
                tax=Decimal('4.50'),
                total=Decimal('59.49'),
                shipping_name='Test User',
                shipping_address_line1='123 Test St',
                shipping_city='Test City',
                shipping_state='Test State',
                shipping_postal_code='12345',
                shipping_country='Test Country',
                shipping_phone='1234567890',
                payment_method='stripe',
                payment_intent_id='pi_test_456'
            )
    
    def test_order_status_choices(self):
        """Test order status choices."""
        from store.models import Order
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Test all valid status choices
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        for status in valid_statuses:
            order.status = status
            order.save()
            order.refresh_from_db()
            self.assertEqual(order.status, status)
    
    def test_order_payment_method_choices(self):
        """Test payment method choices."""
        from store.models import Order
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Test valid payment methods
        order.payment_method = 'paystack'
        order.save()
        order.refresh_from_db()
        self.assertEqual(order.payment_method, 'paystack')
    
    def test_order_is_paid_property(self):
        """Test is_paid property."""
        from store.models import Order
        from django.utils import timezone
        
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Not paid initially
        self.assertFalse(order.is_paid)
        
        # Mark as paid
        order.paid_at = timezone.now()
        order.save()
        self.assertTrue(order.is_paid)
    
    def test_order_can_be_cancelled_property(self):
        """Test can_be_cancelled property."""
        from store.models import Order
        from django.utils import timezone
        from datetime import timedelta
        
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123',
            status='pending'
        )
        
        # Can be cancelled when pending and within 24 hours
        self.assertTrue(order.can_be_cancelled)
        
        # Cannot be cancelled when shipped
        order.status = 'shipped'
        order.save()
        self.assertFalse(order.can_be_cancelled)
        
        # Cannot be cancelled when delivered
        order.status = 'delivered'
        order.save()
        self.assertFalse(order.can_be_cancelled)
        
        # Cannot be cancelled when already cancelled
        order.status = 'cancelled'
        order.save()
        self.assertFalse(order.can_be_cancelled)
        
        # Test time-based cancellation (simulate old order)
        order.status = 'pending'
        order.save()
        # Manually set created_at to more than 24 hours ago
        old_time = timezone.now() - timedelta(hours=25)
        Order.objects.filter(id=order.id).update(created_at=old_time)
        order.refresh_from_db()
        self.assertFalse(order.can_be_cancelled)
    
    def test_order_item_count_property(self):
        """Test item_count property."""
        from store.models import Order, OrderItem
        
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Empty order
        self.assertEqual(order.item_count, 0)
        
        # Add items
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=2,
            unit_price=Decimal('49.99'),
            total_price=Decimal('99.98')
        )
        
        product2 = Product.objects.create(
            name='Hoodie',
            description='Test',
            price=Decimal('59.99'),
            category=self.category
        )
        OrderItem.objects.create(
            order=order,
            product=product2,
            product_name='Hoodie',
            quantity=3,
            unit_price=Decimal('59.99'),
            total_price=Decimal('179.97')
        )
        
        # Should return total quantity
        self.assertEqual(order.item_count, 5)
    
    def test_order_str_representation(self):
        """Test string representation of order."""
        from store.models import Order
        order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        self.assertEqual(str(order), 'Order EYT-2024-001234 - testuser')
    
    def test_order_indexes(self):
        """Test that order has proper indexes for performance."""
        from store.models import Order
        # This test verifies the model has the expected indexes defined
        indexes = [index.name for index in Order._meta.indexes]
        self.assertTrue(any('user' in idx for idx in indexes))
        self.assertTrue(any('order_number' in idx or 'order_n' in idx for idx in indexes))
        self.assertTrue(any('status' in idx for idx in indexes))
    
    def test_order_user_protection(self):
        """Test that user cannot be deleted if orders exist."""
        from store.models import Order
        Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
        
        # Attempting to delete user should raise error
        with self.assertRaises(Exception):
            self.user.delete()


class OrderItemModelTestCase(TestCase):
    """Test OrderItem model functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        from django.contrib.auth import get_user_model
        from store.models import Order
        
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Jerseys')
        self.product = Product.objects.create(
            name='EYT Gaming Jersey',
            description='Official team jersey',
            price=Decimal('49.99'),
            category=self.category,
            stock_quantity=100
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            name='Size: Large',
            sku='EYT-JERSEY-L',
            price_adjustment=Decimal('5.00'),
            stock_quantity=50
        )
        self.order = Order.objects.create(
            order_number='EYT-2024-001234',
            user=self.user,
            subtotal=Decimal('49.99'),
            shipping_cost=Decimal('5.00'),
            tax=Decimal('4.50'),
            total=Decimal('59.49'),
            shipping_name='Test User',
            shipping_address_line1='123 Test St',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_postal_code='12345',
            shipping_country='Test Country',
            shipping_phone='1234567890',
            payment_method='stripe',
            payment_intent_id='pi_test_123'
        )
    
    def test_order_item_creation_without_variant(self):
        """Test creating an order item without a variant."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=2,
            unit_price=Decimal('49.99'),
            total_price=Decimal('99.98')
        )
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.product, self.product)
        self.assertIsNone(order_item.variant)
        self.assertEqual(order_item.product_name, 'EYT Gaming Jersey')
        self.assertEqual(order_item.quantity, 2)
        self.assertEqual(order_item.unit_price, Decimal('49.99'))
        self.assertEqual(order_item.total_price, Decimal('99.98'))
        self.assertIsNotNone(order_item.created_at)
    
    def test_order_item_creation_with_variant(self):
        """Test creating an order item with a variant."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            variant=self.variant,
            product_name='EYT Gaming Jersey',
            variant_name='Size: Large',
            quantity=3,
            unit_price=Decimal('54.99'),
            total_price=Decimal('164.97')
        )
        self.assertEqual(order_item.variant, self.variant)
        self.assertEqual(order_item.variant_name, 'Size: Large')
        self.assertEqual(order_item.quantity, 3)
    
    def test_order_item_auto_calculate_total_price(self):
        """Test that total_price is auto-calculated if not provided."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=3,
            unit_price=Decimal('49.99')
            # total_price not provided
        )
        # Should be auto-calculated: 49.99 * 3 = 149.97
        self.assertEqual(order_item.total_price, Decimal('149.97'))
    
    def test_order_item_quantity_validation(self):
        """Test that quantity must be at least 1."""
        from store.models import OrderItem
        order_item = OrderItem(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=0,
            unit_price=Decimal('49.99')
        )
        with self.assertRaises(ValidationError):
            order_item.full_clean()
    
    def test_order_item_price_validation(self):
        """Test that prices cannot be negative."""
        from store.models import OrderItem
        order_item = OrderItem(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=1,
            unit_price=Decimal('-49.99')
        )
        with self.assertRaises(ValidationError):
            order_item.full_clean()
    
    def test_order_item_product_snapshot(self):
        """Test that product snapshots preserve order history."""
        from store.models import OrderItem
        
        # Create order item with current product details
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=1,
            unit_price=Decimal('49.99'),
            total_price=Decimal('49.99')
        )
        
        # Change product name
        self.product.name = 'Updated Jersey Name'
        self.product.save()
        
        # Order item should still have original name
        order_item.refresh_from_db()
        self.assertEqual(order_item.product_name, 'EYT Gaming Jersey')
        self.assertNotEqual(order_item.product_name, self.product.name)
    
    def test_order_item_str_representation_without_variant(self):
        """Test string representation without variant."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=2,
            unit_price=Decimal('49.99'),
            total_price=Decimal('99.98')
        )
        self.assertEqual(str(order_item), 'EYT Gaming Jersey (x2)')
    
    def test_order_item_str_representation_with_variant(self):
        """Test string representation with variant."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            variant=self.variant,
            product_name='EYT Gaming Jersey',
            variant_name='Size: Large',
            quantity=3,
            unit_price=Decimal('54.99'),
            total_price=Decimal('164.97')
        )
        self.assertEqual(str(order_item), 'EYT Gaming Jersey - Size: Large (x3)')
    
    def test_order_item_cascade_delete_with_order(self):
        """Test that order items are deleted when order is deleted."""
        from store.models import OrderItem
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=1,
            unit_price=Decimal('49.99'),
            total_price=Decimal('49.99')
        )
        order_item_id = order_item.id
        
        # Delete order
        self.order.delete()
        
        # Order item should also be deleted
        with self.assertRaises(OrderItem.DoesNotExist):
            OrderItem.objects.get(id=order_item_id)
    
    def test_order_item_product_protection(self):
        """Test that product cannot be deleted if order items exist."""
        from store.models import OrderItem
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='EYT Gaming Jersey',
            quantity=1,
            unit_price=Decimal('49.99'),
            total_price=Decimal('49.99')
        )
        
        # Attempting to hard delete product should raise error
        with self.assertRaises(Exception):
            self.product.hard_delete()
    
    def test_order_item_indexes(self):
        """Test that order item has proper indexes for performance."""
        from store.models import OrderItem
        # This test verifies the model has the expected indexes defined
        indexes = [index.name for index in OrderItem._meta.indexes]
        self.assertTrue(any('order' in idx for idx in indexes))
        self.assertTrue(any('product' in idx for idx in indexes))
