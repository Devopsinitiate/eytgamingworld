"""
Views for the EYTGaming Store.

This module will contain views for:
- Product catalog and detail pages
- Shopping cart
- Checkout process
- Order management
- Wishlist
- Product reviews
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import cache_page
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch
from django.urls import reverse
from django.core.cache import cache
from decimal import Decimal, InvalidOperation
import json

from .models import Product, ProductVariant, Cart, CartItem, Category, ProductImage, Order, OrderItem
from .managers import CartManager, InsufficientStockError
from .utils import InputValidator


# ============================================================================
# Product Catalog Views
# ============================================================================

@require_http_methods(["GET"])
def product_list(request):
    """
    Display product catalog with filtering, search, and sorting.
    
    Supports:
    - Category filtering
    - Search by name, description, tags
    - Price range filtering
    - Sorting (price, name, newest)
    - Pagination (24 products per page)
    
    Requirements: 6.1, 6.3, 6.4, 6.7, 17.1, 17.2, 17.3, 17.4, 17.5, 20.5
    """
    # Build cache key from query parameters
    cache_key_parts = ['product_list']
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    page = request.GET.get('page', 1)
    
    if category_slug:
        cache_key_parts.append(f'cat_{category_slug}')
    if search_query:
        cache_key_parts.append(f'q_{search_query[:50]}')  # Limit search query length in cache key
    if min_price:
        cache_key_parts.append(f'min_{min_price}')
    if max_price:
        cache_key_parts.append(f'max_{max_price}')
    cache_key_parts.append(f'sort_{sort_by}')
    cache_key_parts.append(f'page_{page}')
    
    cache_key = '_'.join(cache_key_parts)
    
    # Try to get from cache
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'store/product_list.html', cached_context)
    
    # Start with active products only
    products = Product.objects.filter(is_active=True)
    
    # Category filtering
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)
    
    # Search functionality with sanitization
    if search_query:
        # Sanitize search query to prevent SQL injection
        sanitized_query = InputValidator.sanitize_search_query(search_query)
        
        if sanitized_query:
            # Search in product name and description
            products = products.filter(
                Q(name__icontains=sanitized_query) |
                Q(description__icontains=sanitized_query)
            )
    
    # Price range filtering
    if min_price:
        try:
            min_price_decimal = Decimal(min_price)
            if min_price_decimal >= 0:
                products = products.filter(price__gte=min_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            pass  # Ignore invalid price values
    
    if max_price:
        try:
            max_price_decimal = Decimal(max_price)
            if max_price_decimal >= 0:
                products = products.filter(price__lte=max_price_decimal)
        except (ValueError, TypeError, InvalidOperation):
            pass  # Ignore invalid price values
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price', 'name')
    elif sort_by == 'price_high':
        products = products.order_by('-price', 'name')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at', 'name')
    else:
        # Default to newest
        products = products.order_by('-created_at', 'name')
    
    # Optimize queries with select_related and prefetch_related
    products = products.select_related('category').prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.filter(is_primary=True).order_by('-is_primary', 'display_order'),
            to_attr='primary_images'
        )
    )
    
    # Pagination (24 products per page)
    paginator = Paginator(products, 24)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    # Get all categories for filter UI (cache categories separately)
    categories_cache_key = 'product_categories_tree'
    categories = cache.get(categories_cache_key)
    if not categories:
        categories = Category.objects.filter(parent=None).prefetch_related('children')
        cache.set(categories_cache_key, categories, 60 * 15)  # Cache for 15 minutes
    
    # Build context
    context = {
        'products': products_page,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'total_products': paginator.count,
    }
    
    # Cache the context for 5 minutes
    cache.set(cache_key, context, 60 * 5)
    
    return render(request, 'store/product_list.html', context)


@require_http_methods(["GET"])
def product_detail(request, slug):
    """
    Display detailed product information.
    
    Shows:
    - Full product description
    - All product images
    - Available variants (sizes, colors)
    - Stock availability
    - Add to cart functionality
    
    Requirements: 6.7
    """
    # Try to get from cache
    cache_key = f'product_detail_{slug}'
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'store/product_detail.html', cached_context)
    
    # Get product with related data
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related(
            'images',
            'variants'
        ),
        slug=slug,
        is_active=True
    )
    
    # Get all images ordered by display order
    images = product.images.all().order_by('display_order', '-is_primary')
    
    # Get available variants
    variants = product.variants.filter(is_available=True).order_by('name')
    
    # Check stock availability
    has_stock = product.is_in_stock or any(v.is_in_stock for v in variants)
    
    context = {
        'product': product,
        'images': images,
        'variants': variants,
        'has_stock': has_stock,
    }
    
    # Cache for 10 minutes
    cache.set(cache_key, context, 60 * 10)
    
    return render(request, 'store/product_detail.html', context)


# ============================================================================
# Cart Views
# ============================================================================

@require_http_methods(["GET"])
def cart_view(request):
    """
    Display the shopping cart.
    
    Shows all items in the cart with quantities, prices, and total.
    Supports both authenticated users and guest sessions.
    
    Requirements: 7.4, 7.5, 7.6
    """
    # Get or create cart
    if request.user.is_authenticated:
        cart = CartManager.get_or_create_cart(user=request.user)
    else:
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        cart = CartManager.get_or_create_cart(session_key=request.session.session_key)
    
    # Get cart items with related data
    cart_items = cart.items.select_related(
        'product', 
        'product__category',
        'variant'
    ).prefetch_related('product__images')
    
    # Calculate totals
    subtotal = CartManager.calculate_total(cart)
    
    # Check availability for each item
    unavailable_items = []
    for item in cart_items:
        if not item.is_available or not item.has_sufficient_stock:
            unavailable_items.append(item)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'unavailable_items': unavailable_items,
        'item_count': cart.item_count,
    }
    
    return render(request, 'store/cart.html', context)


@csrf_protect
@require_POST
def add_to_cart(request):
    """
    AJAX endpoint to add item to cart.
    
    Validates stock availability and adds item to cart.
    Returns JSON response with success/error status.
    
    Requirements: 7.1, 7.2, 7.3
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)
        
        # Validate inputs
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Product ID is required'
            }, status=400)
        
        # Validate quantity
        try:
            quantity = InputValidator.validate_quantity(quantity)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        # Get product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get variant if specified
        variant = None
        if variant_id:
            variant = get_object_or_404(
                ProductVariant, 
                id=variant_id, 
                product=product,
                is_available=True
            )
        
        # Get or create cart
        if request.user.is_authenticated:
            cart = CartManager.get_or_create_cart(user=request.user)
        else:
            # Ensure session exists
            if not request.session.session_key:
                request.session.create()
            cart = CartManager.get_or_create_cart(session_key=request.session.session_key)
        
        # Add item to cart
        cart_item = CartManager.add_item(cart, product, variant, quantity)
        
        # Calculate new totals
        subtotal = CartManager.calculate_total(cart)
        item_count = cart.item_count
        
        return JsonResponse({
            'success': True,
            'message': 'Item added to cart',
            'cart_item': {
                'id': str(cart_item.id),
                'product_name': product.name,
                'variant_name': variant.name if variant else None,
                'quantity': cart_item.quantity,
                'unit_price': str(cart_item.unit_price),
                'total_price': str(cart_item.total_price),
            },
            'cart_summary': {
                'item_count': item_count,
                'subtotal': str(subtotal),
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product variant not found'
        }, status=404)
    
    except InsufficientStockError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding to cart: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@csrf_protect
@require_POST
def update_cart_quantity(request):
    """
    AJAX endpoint to update cart item quantity.
    
    Validates stock availability and updates quantity.
    Returns JSON response with success/error status.
    
    Requirements: 7.4
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        quantity = data.get('quantity')
        
        # Validate inputs
        if not cart_item_id:
            return JsonResponse({
                'success': False,
                'error': 'Cart item ID is required'
            }, status=400)
        
        # Validate quantity
        try:
            quantity = InputValidator.validate_quantity(quantity)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        # Get cart item
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        
        # Verify cart ownership
        if cart_item.cart.user:
            # Cart belongs to a user - check if it's the current user
            if not request.user.is_authenticated or cart_item.cart.user != request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=403)
        else:
            # Cart belongs to a guest - check session key
            if not request.session.session_key or cart_item.cart.session_key != request.session.session_key:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=403)
        
        # Update quantity
        cart_item = CartManager.update_quantity(cart_item, quantity)
        
        # Calculate new totals
        cart = cart_item.cart
        subtotal = CartManager.calculate_total(cart)
        item_count = cart.item_count
        
        return JsonResponse({
            'success': True,
            'message': 'Quantity updated',
            'cart_item': {
                'id': str(cart_item.id),
                'quantity': cart_item.quantity,
                'unit_price': str(cart_item.unit_price),
                'total_price': str(cart_item.total_price),
            },
            'cart_summary': {
                'item_count': item_count,
                'subtotal': str(subtotal),
            }
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        }, status=404)
    
    except InsufficientStockError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating cart quantity: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@csrf_protect
@require_POST
def remove_from_cart(request):
    """
    AJAX endpoint to remove item from cart.
    
    Removes the specified item and returns updated cart totals.
    Returns JSON response with success/error status.
    
    Requirements: 7.6
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        cart_item_id = data.get('cart_item_id')
        
        # Validate inputs
        if not cart_item_id:
            return JsonResponse({
                'success': False,
                'error': 'Cart item ID is required'
            }, status=400)
        
        # Get cart item
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        
        # Verify cart ownership
        if cart_item.cart.user:
            # Cart belongs to a user - check if it's the current user
            if not request.user.is_authenticated or cart_item.cart.user != request.user:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=403)
        else:
            # Cart belongs to a guest - check session key
            if not request.session.session_key or cart_item.cart.session_key != request.session.session_key:
                return JsonResponse({
                    'success': False,
                    'error': 'Unauthorized'
                }, status=403)
        
        # Get cart before deleting item
        cart = cart_item.cart
        
        # Remove item
        CartManager.remove_item(cart_item)
        
        # Calculate new totals
        subtotal = CartManager.calculate_total(cart)
        item_count = cart.item_count
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_summary': {
                'item_count': item_count,
                'subtotal': str(subtotal),
            }
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart item not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing from cart: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


# ============================================================================
# Checkout Views
# ============================================================================

@login_required
@require_http_methods(["GET"])
def checkout_initiate(request):
    """
    Initiate checkout process (requires authentication).
    
    Displays cart summary and prompts user to proceed to shipping information.
    Validates that cart has items before allowing checkout.
    
    Requirements: 8.1, 8.4
    """
    # Get user's cart
    cart = CartManager.get_or_create_cart(user=request.user)
    
    # Check if cart is empty
    if cart.is_empty:
        return redirect('store:cart')
    
    # Get cart items with related data
    cart_items = cart.items.select_related(
        'product',
        'product__category',
        'variant'
    ).prefetch_related('product__images')
    
    # Check availability for each item
    unavailable_items = []
    for item in cart_items:
        if not item.is_available or not item.has_sufficient_stock:
            unavailable_items.append(item)
    
    # If any items are unavailable, redirect back to cart
    if unavailable_items:
        return redirect('store:cart')
    
    # Calculate totals
    subtotal = CartManager.calculate_total(cart)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'item_count': cart.item_count,
    }
    
    return render(request, 'store/checkout_initiate.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def checkout_shipping(request):
    """
    Shipping information form view.
    
    Displays form for entering shipping address and contact information.
    Validates all required fields and stores in session for order creation.
    
    Requirements: 8.2, 8.8
    """
    # Get user's cart
    cart = CartManager.get_or_create_cart(user=request.user)
    
    # Check if cart is empty
    if cart.is_empty:
        return redirect('store:cart')
    
    if request.method == 'POST':
        # Get shipping information from form
        shipping_info = {
            'shipping_name': request.POST.get('shipping_name', '').strip(),
            'shipping_address_line1': request.POST.get('shipping_address_line1', '').strip(),
            'shipping_address_line2': request.POST.get('shipping_address_line2', '').strip(),
            'shipping_city': request.POST.get('shipping_city', '').strip(),
            'shipping_state': request.POST.get('shipping_state', '').strip(),
            'shipping_postal_code': request.POST.get('shipping_postal_code', '').strip(),
            'shipping_country': request.POST.get('shipping_country', '').strip(),
            'shipping_phone': request.POST.get('shipping_phone', '').strip(),
        }
        
        # Validate required fields
        errors = {}
        required_fields = [
            'shipping_name', 'shipping_address_line1', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'shipping_phone'
        ]
        
        for field in required_fields:
            if not shipping_info.get(field):
                field_label = field.replace('shipping_', '').replace('_', ' ').title()
                errors[field] = f'{field_label} is required'
        
        # Validate phone number format (basic validation)
        phone = shipping_info.get('shipping_phone', '')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            errors['shipping_phone'] = 'Please enter a valid phone number'
        
        # Validate postal code (basic validation)
        postal_code = shipping_info.get('shipping_postal_code', '')
        if postal_code and len(postal_code) < 3:
            errors['shipping_postal_code'] = 'Please enter a valid postal code'
        
        if not errors:
            # Store shipping info in session
            request.session['shipping_info'] = shipping_info
            
            # Calculate shipping cost based on country
            shipping_cost = calculate_shipping_cost(shipping_info['shipping_country'])
            request.session['shipping_cost'] = str(shipping_cost)
            
            # Redirect to payment method selection
            return redirect('store:checkout_payment')
        
        # If there are errors, re-render form with errors
        context = {
            'shipping_info': shipping_info,
            'errors': errors,
        }
        return render(request, 'store/checkout_shipping.html', context)
    
    # GET request - display form
    # Pre-fill with session data if available
    shipping_info = request.session.get('shipping_info', {})
    
    context = {
        'shipping_info': shipping_info,
    }
    
    return render(request, 'store/checkout_shipping.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def checkout_payment(request):
    """
    Payment method selection view.
    
    Displays available payment methods (Stripe and Paystack).
    Shows order summary with items, prices, shipping, and total.
    
    Requirements: 8.3, 8.4
    """
    # Get user's cart
    cart = CartManager.get_or_create_cart(user=request.user)
    
    # Check if cart is empty
    if cart.is_empty:
        return redirect('store:cart')
    
    # Check if shipping info is in session
    shipping_info = request.session.get('shipping_info')
    if not shipping_info:
        return redirect('store:checkout_shipping')
    
    # Get cart items
    cart_items = cart.items.select_related(
        'product',
        'variant'
    ).prefetch_related('product__images')
    
    # Calculate totals
    subtotal = CartManager.calculate_total(cart)
    shipping_cost = Decimal(request.session.get('shipping_cost', '10.00'))
    tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% tax
    total = subtotal + shipping_cost + tax
    
    if request.method == 'POST':
        # Get selected payment method
        payment_method = request.POST.get('payment_method')
        
        if payment_method not in ['stripe', 'paystack']:
            context = {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'tax': tax,
                'total': total,
                'shipping_info': shipping_info,
                'error': 'Please select a valid payment method',
            }
            return render(request, 'store/checkout_payment.html', context)
        
        # Store payment method in session
        request.session['payment_method'] = payment_method
        
        # Redirect to payment processing
        # This will be implemented in tasks 13.4 and 13.5
        # For now, redirect to a placeholder confirmation
        return redirect('store:checkout_confirm')
    
    # GET request - display payment method selection
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'total': total,
        'shipping_info': shipping_info,
    }
    
    return render(request, 'store/checkout_payment.html', context)


@login_required
@require_http_methods(["GET"])
def checkout_confirm(request):
    """
    Order confirmation view.
    
    Displays order confirmation after successful payment.
    Shows order details, shipping information, and order number.
    
    Requirements: 8.4, 8.6
    """
    # Get order number from session (set after payment processing)
    order_number = request.session.get('order_number')
    
    if not order_number:
        # No order in session, redirect to cart
        return redirect('store:cart')
    
    # Get the order with optimized queries
    try:
        order = Order.objects.select_related('user').prefetch_related(
            Prefetch(
                'items',
                queryset=OrderItem.objects.select_related('product', 'variant')
            )
        ).get(order_number=order_number, user=request.user)
    except Order.DoesNotExist:
        # Order not found, redirect to cart
        return redirect('store:cart')
    
    # Clear checkout session data
    for key in ['shipping_info', 'shipping_cost', 'payment_method', 'order_number']:
        request.session.pop(key, None)
    
    context = {
        'order': order,
    }
    
    return render(request, 'store/checkout_confirm.html', context)


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_shipping_cost(country):
    """
    Calculate shipping cost based on country.
    
    This is a simplified implementation. In production, this would
    integrate with a shipping API or use a more complex calculation.
    
    Args:
        country: Country name or code
        
    Returns:
        Decimal: Shipping cost
        
    Requirements: 8.8
    """
    # Simplified shipping cost calculation
    # In production, this would be more sophisticated
    
    country = country.upper().strip()
    
    # Domestic shipping (Nigeria)
    if country in ['NIGERIA', 'NG', 'NGA']:
        return Decimal('5.00')
    
    # Regional shipping (West Africa)
    west_africa = ['GHANA', 'GH', 'BENIN', 'BJ', 'TOGO', 'TG', 'SENEGAL', 'SN']
    if country in west_africa:
        return Decimal('15.00')
    
    # International shipping
    return Decimal('25.00')


# ============================================================================
# CSRF Protection Views
# ============================================================================

def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view.
    
    Provides user-friendly error message when CSRF validation fails.
    Logs the failure for security monitoring.
    
    Requirements: 4.3
    """
    import logging
    logger = logging.getLogger('security')
    
    # Log CSRF failure
    logger.warning(
        f'CSRF validation failed: {reason}',
        extra={
            'event_type': 'csrf_failure',
            'ip': request.META.get('REMOTE_ADDR'),
            'path': request.path,
            'reason': reason,
        }
    )
    
    # Return user-friendly error page
    context = {
        'reason': reason,
        'message': 'Your request could not be processed due to a security check failure. This usually happens when your session has expired or cookies are disabled.',
    }
    
    return render(request, 'store/csrf_failure.html', context, status=403)


# ============================================================================
# Stripe Payment Integration Views
# ============================================================================

@login_required
@csrf_protect
@require_POST
def stripe_create_payment_intent(request):
    """
    Create Stripe payment intent.
    
    Creates a payment intent for the current cart and returns client secret
    for Stripe Elements to complete the payment.
    
    Requirements: 2.2, 2.3, 2.6
    """
    try:
        from .managers import StripePaymentProcessor, PaymentProcessorError
        from django.conf import settings
        
        # Get user's cart
        cart = CartManager.get_or_create_cart(user=request.user)
        
        # Check if cart is empty
        if cart.is_empty:
            return JsonResponse({
                'success': False,
                'error': 'Cart is empty'
            }, status=400)
        
        # Get shipping info from session
        shipping_info = request.session.get('shipping_info')
        if not shipping_info:
            return JsonResponse({
                'success': False,
                'error': 'Shipping information required'
            }, status=400)
        
        # Calculate totals
        subtotal = CartManager.calculate_total(cart)
        shipping_cost = Decimal(request.session.get('shipping_cost', '10.00'))
        tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        total = subtotal + shipping_cost + tax
        
        # Initialize Stripe processor
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe_key:
            return JsonResponse({
                'success': False,
                'error': 'Payment processor not configured'
            }, status=500)
        
        processor = StripePaymentProcessor(stripe_key)
        
        # Create payment intent
        metadata = {
            'user_id': str(request.user.id),
            'cart_id': str(cart.id),
            'order_type': 'store_purchase'
        }
        
        payment_intent = processor.create_payment_intent(
            amount=total,
            currency='usd',
            metadata=metadata
        )
        
        # Store payment intent ID in session
        request.session['stripe_payment_intent_id'] = payment_intent['id']
        
        return JsonResponse({
            'success': True,
            'client_secret': payment_intent['client_secret'],
            'amount': str(total)
        })
        
    except PaymentProcessorError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Stripe payment intent creation failed: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'Payment processing error. Please try again.'
        }, status=500)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@csrf_protect
@require_POST
def stripe_confirm_payment(request):
    """
    Confirm Stripe payment and create order.
    
    Called after Stripe Elements confirms payment on client side.
    Creates the order and clears the cart.
    
    Requirements: 2.6, 8.6, 10.2
    """
    try:
        from .managers import StripePaymentProcessor, OrderManager, InventoryManager, PaymentProcessorError
        from django.conf import settings
        from django.db import transaction
        
        # Parse request data
        data = json.loads(request.body)
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return JsonResponse({
                'success': False,
                'error': 'Payment intent ID required'
            }, status=400)
        
        # Verify payment intent ID matches session
        session_intent_id = request.session.get('stripe_payment_intent_id')
        if payment_intent_id != session_intent_id:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment intent'
            }, status=400)
        
        # Initialize Stripe processor
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        if not stripe_key:
            return JsonResponse({
                'success': False,
                'error': 'Payment processor not configured'
            }, status=500)
        
        processor = StripePaymentProcessor(stripe_key)
        
        # Confirm payment succeeded
        if not processor.confirm_payment(payment_intent_id):
            return JsonResponse({
                'success': False,
                'error': 'Payment not confirmed'
            }, status=400)
        
        # Get user's cart
        cart = CartManager.get_or_create_cart(user=request.user)
        
        # Get shipping info from session
        shipping_info = request.session.get('shipping_info')
        if not shipping_info:
            return JsonResponse({
                'success': False,
                'error': 'Shipping information required'
            }, status=400)
        
        # Create order with transaction safety
        with transaction.atomic():
            # Calculate totals
            subtotal = CartManager.calculate_total(cart)
            shipping_cost = Decimal(request.session.get('shipping_cost', '10.00'))
            tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
            total = subtotal + shipping_cost + tax
            
            # Create order
            order = OrderManager.create_order(
                user=request.user,
                cart=cart,
                shipping_info=shipping_info,
                payment_method='stripe',
                payment_intent_id=payment_intent_id,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                total=total
            )
            
            # Reserve inventory
            for item in cart.items.all():
                InventoryManager.reserve_stock(
                    item.product,
                    item.variant,
                    item.quantity
                )
            
            # Clear cart
            CartManager.clear_cart(cart)
            
            # Store order number in session for confirmation page
            request.session['order_number'] = order.order_number
            
            # Clear payment intent from session
            request.session.pop('stripe_payment_intent_id', None)
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'redirect_url': reverse('store:checkout_confirm')
        })
        
    except PaymentProcessorError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Stripe payment confirmation failed: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'Payment confirmation failed. Please contact support.'
        }, status=500)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error confirming payment: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@require_POST
@csrf_exempt  # Stripe webhooks don't include CSRF token
def stripe_webhook(request):
    """
    Handle Stripe webhook events.
    
    Processes webhook events from Stripe for payment confirmations,
    refunds, and other payment-related events.
    
    Requirements: 2.8
    """
    try:
        from .managers import StripePaymentProcessor, OrderManager
        from django.conf import settings
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get webhook payload and signature
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning('Stripe webhook received without signature')
            return JsonResponse({'error': 'No signature'}, status=400)
        
        # Initialize Stripe processor
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        
        if not stripe_key or not webhook_secret:
            logger.error('Stripe not configured')
            return JsonResponse({'error': 'Not configured'}, status=500)
        
        processor = StripePaymentProcessor(stripe_key)
        
        # Verify webhook signature
        try:
            event = processor.verify_webhook(payload, sig_header, webhook_secret)
        except Exception as e:
            logger.warning(f'Stripe webhook signature verification failed: {str(e)}')
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Handle the event
        event_type = event.get('type')
        
        if event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            logger.info(f'Payment succeeded: {payment_intent["id"]}')
            
            # Update order status if needed
            # This is a backup in case the client-side confirmation fails
            try:
                order = Order.objects.get(payment_intent_id=payment_intent['id'])
                if order.status == 'pending':
                    OrderManager.update_status(order, 'processing')
            except Order.DoesNotExist:
                logger.warning(f'Order not found for payment intent: {payment_intent["id"]}')
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.warning(f'Payment failed: {payment_intent["id"]}')
            
            # Log payment failure
            from .utils import SecurityLogger
            SecurityLogger.log_payment_failure(
                payment_intent.get('id', 'unknown'),
                'Payment intent failed'
            )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Stripe webhook error: {str(e)}", exc_info=True)
        
        return JsonResponse({'error': 'Webhook processing failed'}, status=500)


# ============================================================================
# Paystack Payment Integration Views
# ============================================================================

@login_required
@csrf_protect
@require_POST
def paystack_initialize(request):
    """
    Initialize Paystack transaction.
    
    Creates a Paystack transaction and returns the reference and public key
    for the Paystack popup to complete the payment.
    
    Requirements: 2.2, 2.4, 2.6
    """
    try:
        from .managers import PaystackPaymentProcessor, PaymentProcessorError
        from django.conf import settings
        
        # Get user's cart
        cart = CartManager.get_or_create_cart(user=request.user)
        
        # Check if cart is empty
        if cart.is_empty:
            return JsonResponse({
                'success': False,
                'error': 'Cart is empty'
            }, status=400)
        
        # Get shipping info from session
        shipping_info = request.session.get('shipping_info')
        if not shipping_info:
            return JsonResponse({
                'success': False,
                'error': 'Shipping information required'
            }, status=400)
        
        # Calculate totals
        subtotal = CartManager.calculate_total(cart)
        shipping_cost = Decimal(request.session.get('shipping_cost', '10.00'))
        tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
        total = subtotal + shipping_cost + tax
        
        # Initialize Paystack processor
        paystack_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        if not paystack_key:
            return JsonResponse({
                'success': False,
                'error': 'Payment processor not configured'
            }, status=500)
        
        processor = PaystackPaymentProcessor()
        
        # Create payment intent
        metadata = {
            'user_id': str(request.user.id),
            'cart_id': str(cart.id),
            'order_type': 'store_purchase'
        }
        
        payment_intent = processor.create_payment_intent(
            amount=total,
            currency='NGN',  # Paystack primarily uses NGN
            metadata=metadata
        )
        
        # Store payment reference in session
        request.session['paystack_reference'] = payment_intent['reference']
        
        return JsonResponse({
            'success': True,
            'reference': payment_intent['reference'],
            'public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
            'amount': int(total * 100),  # Convert to kobo
            'currency': 'NGN'
        })
        
    except PaymentProcessorError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Paystack transaction initialization failed: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'Payment processing error. Please try again.'
        }, status=500)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error initializing Paystack: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@csrf_protect
@require_POST
def paystack_verify(request):
    """
    Verify Paystack payment and create order.
    
    Called after Paystack popup confirms payment on client side.
    Creates the order and clears the cart.
    
    Requirements: 2.6, 8.6, 10.2
    """
    try:
        from .managers import PaystackPaymentProcessor, OrderManager, InventoryManager, PaymentProcessorError
        from django.conf import settings
        from django.db import transaction
        from django.urls import reverse
        
        # Parse request data
        data = json.loads(request.body)
        reference = data.get('reference')
        
        if not reference:
            return JsonResponse({
                'success': False,
                'error': 'Payment reference required'
            }, status=400)
        
        # Verify reference matches session
        session_reference = request.session.get('paystack_reference')
        if reference != session_reference:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment reference'
            }, status=400)
        
        # Initialize Paystack processor
        paystack_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        if not paystack_key:
            return JsonResponse({
                'success': False,
                'error': 'Payment processor not configured'
            }, status=500)
        
        processor = PaystackPaymentProcessor()
        
        # Confirm payment succeeded
        if not processor.confirm_payment(reference):
            return JsonResponse({
                'success': False,
                'error': 'Payment not confirmed'
            }, status=400)
        
        # Get user's cart
        cart = CartManager.get_or_create_cart(user=request.user)
        
        # Get shipping info from session
        shipping_info = request.session.get('shipping_info')
        if not shipping_info:
            return JsonResponse({
                'success': False,
                'error': 'Shipping information required'
            }, status=400)
        
        # Create order with transaction safety
        with transaction.atomic():
            order = OrderManager.create_order(
                user=request.user,
                cart=cart,
                shipping_info=shipping_info,
                payment_method='paystack',
                payment_intent_id=reference
            )
            
            # Store order number in session for confirmation page
            request.session['order_number'] = order.order_number
            
            # Clear payment reference from session
            request.session.pop('paystack_reference', None)
        
        return JsonResponse({
            'success': True,
            'order_number': order.order_number,
            'redirect_url': reverse('store:checkout_confirm')
        })
        
    except PaymentProcessorError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Paystack payment verification failed: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'Payment verification failed. Please contact support.'
        }, status=500)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error verifying Paystack payment: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@require_POST
@csrf_exempt  # Paystack webhooks don't include CSRF token
def paystack_webhook(request):
    """
    Handle Paystack webhook events.
    
    Processes webhook events from Paystack for payment confirmations,
    refunds, and other payment-related events.
    
    Requirements: 2.8
    """
    try:
        from .managers import PaystackPaymentProcessor, OrderManager
        from django.conf import settings
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get webhook payload and signature
        payload = request.body
        sig_header = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        
        if not sig_header:
            logger.warning('Paystack webhook received without signature')
            return JsonResponse({'error': 'No signature'}, status=400)
        
        # Initialize Paystack processor
        paystack_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        
        if not paystack_key:
            logger.error('Paystack not configured')
            return JsonResponse({'error': 'Not configured'}, status=500)
        
        processor = PaystackPaymentProcessor()
        
        # Verify webhook signature
        try:
            event = processor.verify_webhook(payload, sig_header)
        except Exception as e:
            logger.warning(f'Paystack webhook signature verification failed: {str(e)}')
            return JsonResponse({'error': 'Invalid signature'}, status=400)
        
        # Handle the event
        event_type = event.get('event')
        
        if event_type == 'charge.success':
            data = event.get('data', {})
            reference = data.get('reference')
            logger.info(f'Payment succeeded: {reference}')
            
            # Update order status if needed
            # This is a backup in case the client-side verification fails
            try:
                order = Order.objects.get(payment_intent_id=reference)
                if order.status == 'pending':
                    OrderManager.update_status(order, 'processing')
            except Order.DoesNotExist:
                logger.warning(f'Order not found for reference: {reference}')
        
        elif event_type == 'charge.failed':
            data = event.get('data', {})
            reference = data.get('reference')
            logger.warning(f'Payment failed: {reference}')
            
            # Log payment failure
            from .utils import SecurityLogger
            SecurityLogger.log_payment_failure(
                reference or 'unknown',
                'Paystack charge failed'
            )
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Paystack webhook error: {str(e)}", exc_info=True)
        
        return JsonResponse({'error': 'Webhook processing failed'}, status=500)



# ============================================================================
# Wishlist Views
# ============================================================================

@login_required
@require_http_methods(["GET"])
def wishlist_view(request):
    """
    Display user's wishlist.
    
    Shows all products saved to the wishlist with their current
    availability and pricing information.
    
    Requirements: 11.3, 11.4
    """
    # Get or create wishlist for user
    from .models import Wishlist
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Get wishlist items with optimized queries
    wishlist_items = wishlist.items.select_related(
        'product',
        'product__category'
    ).prefetch_related(
        Prefetch(
            'product__images',
            queryset=ProductImage.objects.filter(is_primary=True).order_by('-is_primary', 'display_order')
        )
    )
    
    context = {
        'wishlist': wishlist,
        'wishlist_items': wishlist_items,
        'item_count': wishlist.item_count,
    }
    
    return render(request, 'store/wishlist.html', context)


@login_required
@csrf_protect
@require_POST
def add_to_wishlist(request):
    """
    AJAX endpoint to add product to wishlist.
    
    Adds a product to the user's wishlist. If the product is already
    in the wishlist, returns an appropriate message.
    
    Requirements: 11.1, 11.2, 11.6
    """
    try:
        from .models import Wishlist, WishlistItem
        
        # Parse request data
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        # Validate inputs
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Product ID is required'
            }, status=400)
        
        # Get product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get or create wishlist
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        # Check if product already in wishlist
        wishlist_item, item_created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )
        
        if item_created:
            message = 'Product added to wishlist'
        else:
            message = 'Product already in wishlist'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'item_count': wishlist.item_count,
            'in_wishlist': True
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error adding to wishlist: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@login_required
@csrf_protect
@require_POST
def remove_from_wishlist(request):
    """
    AJAX endpoint to remove product from wishlist.
    
    Removes a product from the user's wishlist.
    
    Requirements: 11.2, 11.4
    """
    try:
        from .models import WishlistItem
        
        # Parse request data
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        # Validate inputs
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Product ID is required'
            }, status=400)
        
        # Get wishlist item
        wishlist_item = get_object_or_404(
            WishlistItem,
            wishlist__user=request.user,
            product_id=product_id
        )
        
        # Remove item
        wishlist_item.delete()
        
        # Get updated item count
        from .models import Wishlist
        wishlist = Wishlist.objects.get(user=request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Product removed from wishlist',
            'item_count': wishlist.item_count,
            'in_wishlist': False
        })
        
    except WishlistItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not in wishlist'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing from wishlist: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)



# ============================================================================
# Product Review Views
# ============================================================================

@login_required
@csrf_protect
@require_POST
def submit_review(request, product_slug):
    """
    Submit a product review.
    
    Allows users who have purchased a product to submit a rating and
    optional text review. Validates that the user has purchased the product
    and prevents duplicate reviews for the same order.
    
    Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
    """
    try:
        from .models import ProductReview, OrderItem
        
        # Get product
        product = get_object_or_404(Product, slug=product_slug, is_active=True)
        
        # Parse request data
        data = json.loads(request.body)
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        order_id = data.get('order_id')
        
        # Validate rating
        if not rating:
            return JsonResponse({
                'success': False,
                'error': 'Rating is required'
            }, status=400)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }, status=400)
        
        # Validate order_id if provided
        order = None
        if order_id:
            try:
                order = Order.objects.select_related('user').get(
                    id=order_id,
                    user=request.user,
                    status__in=['delivered', 'processing', 'shipped']
                )
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Order not found'
                }, status=404)
        else:
            # Find an order where user purchased this product (optimized query)
            from .models import OrderItem
            order_items = OrderItem.objects.filter(
                order__user=request.user,
                product=product,
                order__status__in=['delivered', 'processing', 'shipped']
            ).select_related('order', 'product').order_by('-order__created_at')
            
            if not order_items.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'You must purchase this product before reviewing it'
                }, status=403)
            
            order = order_items.first().order
        
        # Check if user already reviewed this product for this order
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user,
            order=order
        ).first()
        
        if existing_review:
            return JsonResponse({
                'success': False,
                'error': 'You have already reviewed this product for this order'
            }, status=400)
        
        # Create review (comment will be sanitized in model's save method)
        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            order=order,
            rating=rating,
            comment=comment
        )
        
        # Get updated average rating
        avg_rating = product.average_rating
        review_count = product.review_count
        
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully',
            'review': {
                'id': str(review.id),
                'rating': review.rating,
                'comment': review.comment,
                'user': request.user.username,
                'created_at': review.created_at.isoformat(),
            },
            'product_stats': {
                'average_rating': avg_rating,
                'review_count': review_count,
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error submitting review: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@require_http_methods(["GET"])
def product_reviews(request, product_slug):
    """
    Get product reviews with pagination.
    
    Returns paginated list of reviews for a product, ordered by most recent.
    Can be used for AJAX loading of reviews.
    
    Requirements: 12.5
    """
    try:
        # Get product
        product = get_object_or_404(Product, slug=product_slug, is_active=True)
        
        # Get reviews with optimized user data query
        reviews = product.reviews.select_related('user', 'order').order_by('-created_at')
        
        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(reviews, 10)  # 10 reviews per page
        
        try:
            reviews_page = paginator.page(page)
        except PageNotAnInteger:
            reviews_page = paginator.page(1)
        except EmptyPage:
            reviews_page = paginator.page(paginator.num_pages)
        
        # Build response data
        reviews_data = []
        for review in reviews_page:
            reviews_data.append({
                'id': str(review.id),
                'rating': review.rating,
                'comment': review.comment,
                'user': review.user.username,
                'created_at': review.created_at.strftime('%B %d, %Y'),
            })
        
        return JsonResponse({
            'success': True,
            'reviews': reviews_data,
            'pagination': {
                'current_page': reviews_page.number,
                'total_pages': paginator.num_pages,
                'total_reviews': paginator.count,
                'has_next': reviews_page.has_next(),
                'has_previous': reviews_page.has_previous(),
            },
            'product_stats': {
                'average_rating': product.average_rating,
                'review_count': product.review_count,
            }
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching reviews: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


# ============================================================================
# Newsletter Views
# ============================================================================

@csrf_protect
@require_POST
def newsletter_subscribe(request):
    """
    AJAX endpoint to subscribe to newsletter.
    
    Validates email format and adds subscriber to the newsletter list.
    Handles duplicate subscriptions gracefully.
    
    Requirements: 18.1, 18.2, 18.3, 18.4
    """
    try:
        from .models import NewsletterSubscriber
        
        # Parse request data
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        # Validate email
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required'
            }, status=400)
        
        # Validate email format
        try:
            email = InputValidator.validate_email(email)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        # Check if email already subscribed
        existing_subscriber = NewsletterSubscriber.objects.filter(email=email).first()
        
        if existing_subscriber:
            if existing_subscriber.is_active:
                return JsonResponse({
                    'success': True,
                    'message': 'You are already subscribed to our newsletter',
                    'already_subscribed': True
                })
            else:
                # Reactivate subscription
                existing_subscriber.is_active = True
                existing_subscriber.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Welcome back! Your subscription has been reactivated',
                    'reactivated': True
                })
        
        # Create new subscriber
        subscriber = NewsletterSubscriber.objects.create(email=email)
        
        # TODO: Send confirmation email (will be implemented with email system)
        # For now, just return success
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for subscribing! You will receive updates about new products and promotions',
            'new_subscription': True
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data'
        }, status=400)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error subscribing to newsletter: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


@require_http_methods(["GET"])
def newsletter_unsubscribe(request, token):
    """
    Unsubscribe from newsletter using unique token.
    
    Provides one-click unsubscribe functionality via email link.
    
    Requirements: 18.5, 18.6
    """
    try:
        from .models import NewsletterSubscriber
        
        # Get subscriber by token
        subscriber = get_object_or_404(
            NewsletterSubscriber,
            unsubscribe_token=token
        )
        
        # Check if already unsubscribed
        if not subscriber.is_active:
            context = {
                'message': 'You have already unsubscribed from our newsletter.',
                'email': subscriber.email,
                'already_unsubscribed': True
            }
            return render(request, 'store/newsletter_unsubscribe.html', context)
        
        # Unsubscribe
        subscriber.is_active = False
        subscriber.save()
        
        context = {
            'message': 'You have been successfully unsubscribed from our newsletter.',
            'email': subscriber.email,
            'success': True
        }
        
        return render(request, 'store/newsletter_unsubscribe.html', context)
        
    except NewsletterSubscriber.DoesNotExist:
        context = {
            'message': 'Invalid unsubscribe link.',
            'error': True
        }
        return render(request, 'store/newsletter_unsubscribe.html', context, status=404)
    
    except Exception as e:
        # Log unexpected errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error unsubscribing from newsletter: {str(e)}", exc_info=True)
        
        context = {
            'message': 'An error occurred. Please try again or contact support.',
            'error': True
        }
        return render(request, 'store/newsletter_unsubscribe.html', context, status=500)
