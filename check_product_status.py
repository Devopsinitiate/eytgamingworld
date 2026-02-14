"""
Diagnostic script to check why products aren't displaying on the frontend.
Run this with: python manage.py shell < check_product_status.py
"""

from store.models import Product, Category, ProductImage

print("\n" + "="*60)
print("PRODUCT DISPLAY DIAGNOSTIC")
print("="*60 + "\n")

# Check all products
all_products = Product.objects.all()
print(f"Total products in database: {all_products.count()}")

if all_products.count() == 0:
    print("\n❌ NO PRODUCTS FOUND IN DATABASE")
    print("   Please add a product via the admin panel first.")
else:
    print("\nProduct Details:")
    print("-" * 60)
    
    for product in all_products:
        print(f"\nProduct: {product.name}")
        print(f"  - ID: {product.id}")
        print(f"  - Slug: {product.slug}")
        print(f"  - Price: ${product.price}")
        print(f"  - Stock: {product.stock_quantity}")
        print(f"  - Category: {product.category.name if product.category else 'None'}")
        print(f"  - Is Active: {'✅ YES' if product.is_active else '❌ NO (This is why it\'s not showing!)'}")
        print(f"  - Has Images: {product.images.count()} image(s)")
        print(f"  - Created: {product.created_at}")
        
        # Check if product should display
        issues = []
        if not product.is_active:
            issues.append("❌ Product is NOT ACTIVE (is_active=False)")
        if not product.category:
            issues.append("⚠️  Product has no category")
        if product.stock_quantity == 0:
            issues.append("⚠️  Product is out of stock (will show but can't be purchased)")
        if product.images.count() == 0:
            issues.append("⚠️  Product has no images")
        
        if issues:
            print("\n  Issues preventing display:")
            for issue in issues:
                print(f"    {issue}")
        else:
            print("\n  ✅ Product should display on frontend!")

# Check categories
print("\n" + "="*60)
print("CATEGORIES")
print("="*60)
categories = Category.objects.all()
print(f"\nTotal categories: {categories.count()}")
for cat in categories:
    product_count = Product.objects.filter(category=cat, is_active=True).count()
    print(f"  - {cat.name} (slug: {cat.slug}): {product_count} active product(s)")

# Check for common issues
print("\n" + "="*60)
print("COMMON ISSUES & SOLUTIONS")
print("="*60)

inactive_products = Product.objects.filter(is_active=False)
if inactive_products.count() > 0:
    print(f"\n❌ Found {inactive_products.count()} INACTIVE product(s):")
    for p in inactive_products:
        print(f"   - {p.name}")
    print("\n   SOLUTION: In admin, edit the product and check the 'Is active' checkbox")

products_no_category = Product.objects.filter(category__isnull=True)
if products_no_category.count() > 0:
    print(f"\n⚠️  Found {products_no_category.count()} product(s) without category:")
    for p in products_no_category:
        print(f"   - {p.name}")
    print("\n   SOLUTION: In admin, edit the product and assign a category")

products_no_images = Product.objects.filter(is_active=True).exclude(
    id__in=ProductImage.objects.values_list('product_id', flat=True)
)
if products_no_images.count() > 0:
    print(f"\n⚠️  Found {products_no_images.count()} active product(s) without images:")
    for p in products_no_images:
        print(f"   - {p.name}")
    print("\n   SOLUTION: In admin, add at least one image to the product")

# Final recommendations
print("\n" + "="*60)
print("QUICK FIX CHECKLIST")
print("="*60)
print("""
To make a product display on the frontend, ensure:

1. ✅ Product 'Is active' checkbox is CHECKED
2. ✅ Product has a Category assigned
3. ✅ Product has at least one image (recommended)
4. ✅ Product has stock_quantity > 0 (to allow purchases)
5. ✅ Product has a valid price

To fix in Django admin:
1. Go to /admin/store/product/
2. Click on your product
3. Check the 'Is active' checkbox
4. Assign a category
5. Add images in the 'Product images' section
6. Save the product

Then refresh your frontend page!
""")

print("="*60)
print("END OF DIAGNOSTIC")
print("="*60 + "\n")
