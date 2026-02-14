import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Product, ProductImage

print("\n=== PRODUCT CHECK ===\n")

products = Product.objects.all()
print(f"Total products: {products.count()}")

for product in products:
    print(f"\nProduct: {product.name}")
    print(f"  Slug: {product.slug}")
    print(f"  Is Active: {product.is_active}")
    print(f"  Stock: {product.stock_quantity}")
    print(f"  Category: {product.category.name if product.category else 'None'}")
    print(f"  Images: {product.images.count()}")
    
    if product.images.exists():
        for img in product.images.all():
            print(f"    - Image: {img.image.name}")
            print(f"      Is Primary: {img.is_primary}")
            print(f"      Display Order: {img.display_order}")

# Check what the view would return
print("\n=== VIEW QUERY CHECK ===\n")
active_products = Product.objects.filter(is_active=True)
print(f"Active products (what view returns): {active_products.count()}")

for product in active_products:
    print(f"  - {product.name} (slug: {product.slug})")
