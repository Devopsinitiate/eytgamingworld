#!/usr/bin/env python
"""Test if products display on frontend"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from store.models import Product, Category, ProductImage
from django.test import Client

print("\n" + "="*70)
print("PRODUCT DISPLAY TEST")
print("="*70)

# Check products in database
products = Product.objects.filter(is_active=True)
print(f"\n1. Active products in database: {products.count()}")

if products.count() > 0:
    for p in products:
        print(f"\n   Product: {p.name}")
        print(f"   - Slug: {p.slug}")
        print(f"   - Price: ${p.price}")
        print(f"   - Stock: {p.stock_quantity}")
        print(f"   - Category: {p.category.name}")
        print(f"   - Images: {p.images.count()}")
        print(f"   - Active: {p.is_active}")

# Test the view
print("\n2. Testing product list view...")
client = Client()
response = client.get('/store/')

print(f"   Status Code: {response.status_code}")

if response.status_code == 200:
    print("   ✅ Page loads successfully!")
    
    # Check if products are in context
    if hasattr(response, 'context') and response.context:
        if 'products' in response.context:
            context_products = response.context['products']
            if hasattr(context_products, 'object_list'):
                product_count = len(context_products.object_list)
            else:
                product_count = len(context_products)
            print(f"   Products in page context: {product_count}")
            
            if product_count > 0:
                print("   ✅ Products are being passed to template!")
            else:
                print("   ❌ No products in template context!")
        else:
            print("   ❌ 'products' not in context!")
    
    # Check if product appears in HTML
    html_content = response.content.decode('utf-8')
    if 'EYT GAMER ARMY' in html_content:
        print("   ✅ Product name found in HTML!")
    else:
        print("   ❌ Product name NOT found in HTML!")
        print("   This might be a template issue.")
else:
    print(f"   ❌ Page failed to load! Status: {response.status_code}")

print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

print("""
If products aren't showing:

1. Clear cache:
   python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared!')"

2. Check the URL you're visiting:
   - http://localhost:8000/store/ (product list)
   - http://localhost:8000/store/products/ (also product list)

3. Check browser console for JavaScript errors

4. Verify template exists:
   - templates/store/product_list.html

5. Try accessing product directly:
   - http://localhost:8000/store/product/eyt-gamer-army/
""")

print("="*70 + "\n")
