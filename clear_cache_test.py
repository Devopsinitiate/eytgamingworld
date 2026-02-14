import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache

print("Clearing all cache...")
cache.clear()
print("Cache cleared successfully!")

# Test the product list view query
from store.models import Product, ProductImage
from django.db.models import Prefetch

print("\n=== Testing Product List Query ===\n")

products = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
    Prefetch(
        'images',
        queryset=ProductImage.objects.filter(is_primary=True).order_by('-is_primary', 'display_order'),
        to_attr='primary_images'
    )
)

print(f"Found {products.count()} active product(s)")

for product in products:
    print(f"\nProduct: {product.name}")
    print(f"  Category: {product.category.name}")
    print(f"  Primary Images: {len(product.primary_images)}")
    
    if product.primary_images:
        for img in product.primary_images:
            print(f"    - {img.image.url}")
    else:
        print("    - No primary images found")
        print(f"    - Total images: {product.images.count()}")
