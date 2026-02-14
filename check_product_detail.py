import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Product

# Check if products exist
products = Product.objects.filter(is_active=True)
print(f"Total active products: {products.count()}")

if products.exists():
    for product in products:
        print(f"\nProduct: {product.name}")
        print(f"  Slug: {product.slug}")
        print(f"  Active: {product.is_active}")
        print(f"  Price: {product.price}")
        print(f"  Images: {product.images.count()}")
        print(f"  Category: {product.category}")
        print(f"  URL: /store/product/{product.slug}/")
        
        # Check if product has description
        if hasattr(product, 'description'):
            print(f"  Description length: {len(product.description) if product.description else 0}")
else:
    print("No active products found!")

