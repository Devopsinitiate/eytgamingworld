# Design Document: EYTGaming Secure E-commerce Store

## Overview

The EYTGaming Secure E-commerce Store is a Django-based e-commerce platform that provides a secure, performant, and accessible shopping experience for the EYTGaming community. The system integrates with the existing Django project structure, leveraging the current User model, authentication system, and design aesthetic.

### Key Design Principles

1. **Security First**: All design decisions prioritize security, from payment processing to data validation
2. **Progressive Enhancement**: Core functionality works without JavaScript, enhanced with JS for better UX
3. **Responsive Design**: Mobile-first approach ensuring optimal experience on all devices
4. **Performance**: Optimized database queries, caching, and lazy loading for fast page loads
5. **Accessibility**: WCAG 2.1 AA compliant with semantic HTML and ARIA labels
6. **Integration**: Seamless integration with existing EYTGaming platform and authentication

### Technology Stack

- **Backend**: Django 4.x with PostgreSQL database
- **Frontend**: Tailwind CSS, vanilla JavaScript (no framework dependencies)
- **Payment Processing**: Stripe and Paystack SDKs
- **Session Management**: Django sessions with database backend
- **Security**: Django's built-in security features + custom middleware
- **Icons**: Material Symbols
- **Fonts**: Space Grotesk

## Architecture

### System Architecture

The store follows Django's MVT (Model-View-Template) architecture with additional security layers:

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  (Browser with Tailwind CSS, JavaScript, Session Storage)   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────────┐
│                    Security Middleware                       │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │  CSRF    │  Rate    │  Input   │  Session             │ │
│  │  Token   │  Limiter │  Validator│  Security           │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Django Views Layer                      │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │ Product  │  Cart    │ Checkout │  Order               │ │
│  │ Views    │  Views   │  Views   │  Views               │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Business Logic Layer                      │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │ Cart     │ Order    │ Inventory│  Payment             │ │
│  │ Manager  │ Manager  │ Manager  │  Processor           │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Data Access Layer                       │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐ │
│  │ Product  │  Cart    │  Order   │  Review              │ │
│  │ Models   │  Models  │  Models  │  Models              │ │
│  └──────────┴──────────┴──────────┴──────────────────────┘ │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   PostgreSQL Database                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌──────────────────┬──────────────────┬─────────────────┐  │
│  │  Stripe API      │  Paystack API    │  Email Service  │  │
│  └──────────────────┴──────────────────┴─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```


### Security Architecture

The security architecture implements defense-in-depth with multiple layers:

**Layer 1: Network Security**
- HTTPS enforcement for all connections
- Secure cookie flags (HTTPOnly, Secure, SameSite)
- HSTS headers for HTTPS enforcement

**Layer 2: Application Security**
- CSRF protection on all state-changing operations
- Rate limiting on API endpoints and checkout
- Input validation and sanitization
- SQL injection prevention via Django ORM
- XSS prevention via template auto-escaping

**Layer 3: Authentication & Authorization**
- Integration with existing User model
- Session-based authentication
- Permission checks on admin operations
- Account lockout after failed attempts

**Layer 4: Payment Security**
- PCI DSS compliance via Stripe/Paystack
- No card data stored on server
- Webhook signature verification
- Secure payment token handling

**Layer 5: Data Security**
- Encrypted database connections
- Secure password hashing (Django's PBKDF2)
- Audit logging for security events
- Regular security log review

### Payment Flow Architecture

```
User Checkout Flow:
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Cart    │────▶│ Checkout │────▶│ Payment  │────▶│  Order   │
│  Review  │     │  Form    │     │ Gateway  │     │ Confirm  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                 │
                       │                 │
                       ▼                 ▼
                 ┌──────────┐     ┌──────────┐
                 │  Django  │     │  Stripe/ │
                 │  Backend │◀────│ Paystack │
                 └──────────┘     └──────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ Database │
                 │  Order   │
                 └──────────┘
```

**Stripe Flow**:
1. User enters shipping info
2. Frontend loads Stripe Elements (PCI compliant card input)
3. User enters card details (never touches our server)
4. Stripe.js creates payment token
5. Token sent to Django backend
6. Backend creates Stripe PaymentIntent
7. Payment confirmed via webhook
8. Order created and user notified

**Paystack Flow**:
1. User enters shipping info
2. Backend initializes Paystack transaction
3. User redirected to Paystack popup
4. User completes payment on Paystack
5. Paystack webhook confirms payment
6. Order created and user notified

## Components and Interfaces

### 1. Product Management Components

**Product Model**
```python
class Product(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=200)
    slug = SlugField(unique=True)
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    category = ForeignKey(Category)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**ProductVariant Model**
```python
class ProductVariant(models.Model):
    id = UUIDField(primary_key=True)
    product = ForeignKey(Product)
    name = CharField(max_length=100)  # e.g., "Size: Large"
    sku = CharField(max_length=100, unique=True)
    price_adjustment = DecimalField(default=0)
    stock_quantity = IntegerField(default=0)
    is_available = BooleanField(default=True)
```

**ProductImage Model**
```python
class ProductImage(models.Model):
    id = UUIDField(primary_key=True)
    product = ForeignKey(Product)
    image = ImageField(upload_to='products/')
    alt_text = CharField(max_length=200)
    display_order = IntegerField(default=0)
    is_primary = BooleanField(default=False)
```

**Category Model**
```python
class Category(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField(max_length=100)
    slug = SlugField(unique=True)
    description = TextField(blank=True)
    parent = ForeignKey('self', null=True, blank=True)
    display_order = IntegerField(default=0)
```


### 2. Shopping Cart Components

**Cart Model (Persistent)**
```python
class Cart(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User, null=True, blank=True)
    session_key = CharField(max_length=40, null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            Index(fields=['user']),
            Index(fields=['session_key']),
        ]
```

**CartItem Model**
```python
class CartItem(models.Model):
    id = UUIDField(primary_key=True)
    cart = ForeignKey(Cart)
    product = ForeignKey(Product)
    variant = ForeignKey(ProductVariant, null=True, blank=True)
    quantity = IntegerField(validators=[MinValueValidator(1)])
    added_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'product', 'variant']
```

**CartManager Class**
```python
class CartManager:
    def get_or_create_cart(user, session_key):
        """Get existing cart or create new one"""
        
    def add_item(cart, product, variant, quantity):
        """Add item to cart with stock validation"""
        
    def update_quantity(cart_item, quantity):
        """Update item quantity with validation"""
        
    def remove_item(cart_item):
        """Remove item from cart"""
        
    def merge_carts(session_cart, user_cart):
        """Merge session cart into user cart on login"""
        
    def calculate_total(cart):
        """Calculate cart total with tax"""
        
    def clear_cart(cart):
        """Remove all items from cart"""
```

### 3. Order Management Components

**Order Model**
```python
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = UUIDField(primary_key=True)
    order_number = CharField(max_length=20, unique=True)
    user = ForeignKey(User)
    
    # Pricing
    subtotal = DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = DecimalField(max_digits=10, decimal_places=2)
    tax = DecimalField(max_digits=10, decimal_places=2)
    total = DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping
    shipping_name = CharField(max_length=200)
    shipping_address_line1 = CharField(max_length=200)
    shipping_address_line2 = CharField(max_length=200, blank=True)
    shipping_city = CharField(max_length=100)
    shipping_state = CharField(max_length=100)
    shipping_postal_code = CharField(max_length=20)
    shipping_country = CharField(max_length=100)
    shipping_phone = CharField(max_length=20)
    
    # Status
    status = CharField(max_length=20, choices=STATUS_CHOICES)
    tracking_number = CharField(max_length=100, blank=True)
    
    # Payment
    payment_method = CharField(max_length=20)  # 'stripe' or 'paystack'
    payment_intent_id = CharField(max_length=200)
    paid_at = DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            Index(fields=['user', '-created_at']),
            Index(fields=['order_number']),
            Index(fields=['status']),
        ]
```

**OrderItem Model**
```python
class OrderItem(models.Model):
    id = UUIDField(primary_key=True)
    order = ForeignKey(Order)
    product = ForeignKey(Product)
    variant = ForeignKey(ProductVariant, null=True, blank=True)
    product_name = CharField(max_length=200)  # Snapshot
    variant_name = CharField(max_length=100, blank=True)  # Snapshot
    quantity = IntegerField()
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    total_price = DecimalField(max_digits=10, decimal_places=2)
```

**OrderManager Class**
```python
class OrderManager:
    def create_order(user, cart, shipping_info, payment_method):
        """Create order from cart with transaction safety"""
        
    def generate_order_number():
        """Generate unique order number (e.g., EYT-2024-001234)"""
        
    def update_status(order, new_status):
        """Update order status and send notification"""
        
    def cancel_order(order):
        """Cancel order and restore inventory"""
        
    def get_user_orders(user):
        """Get all orders for a user"""
```


### 4. Payment Processing Components

**PaymentProcessor Interface**
```python
class PaymentProcessor(ABC):
    @abstractmethod
    def create_payment_intent(amount, currency, metadata):
        """Create payment intent and return client secret"""
        
    @abstractmethod
    def confirm_payment(payment_intent_id):
        """Confirm payment was successful"""
        
    @abstractmethod
    def refund_payment(payment_intent_id, amount):
        """Process refund"""
        
    @abstractmethod
    def verify_webhook(payload, signature):
        """Verify webhook signature"""
```

**StripePaymentProcessor**
```python
class StripePaymentProcessor(PaymentProcessor):
    def __init__(api_key):
        self.stripe = stripe
        self.stripe.api_key = api_key
        
    def create_payment_intent(amount, currency, metadata):
        return self.stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            metadata=metadata,
            automatic_payment_methods={'enabled': True}
        )
        
    def confirm_payment(payment_intent_id):
        intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent.status == 'succeeded'
        
    def verify_webhook(payload, signature):
        return self.stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
```

**PaystackPaymentProcessor**
```python
class PaystackPaymentProcessor(PaymentProcessor):
    def __init__(api_key):
        self.api_key = api_key
        self.base_url = 'https://api.paystack.co'
        
    def create_payment_intent(amount, currency, metadata):
        response = requests.post(
            f'{self.base_url}/transaction/initialize',
            headers={'Authorization': f'Bearer {self.api_key}'},
            json={
                'amount': int(amount * 100),  # Convert to kobo
                'currency': currency,
                'metadata': metadata
            }
        )
        return response.json()
        
    def verify_webhook(payload, signature):
        computed_hash = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()
        return computed_hash == signature
```

### 5. Wishlist Components

**Wishlist Model**
```python
class Wishlist(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user']
```

**WishlistItem Model**
```python
class WishlistItem(models.Model):
    id = UUIDField(primary_key=True)
    wishlist = ForeignKey(Wishlist)
    product = ForeignKey(Product)
    added_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['wishlist', 'product']
```

### 6. Review Components

**ProductReview Model**
```python
class ProductReview(models.Model):
    id = UUIDField(primary_key=True)
    product = ForeignKey(Product)
    user = ForeignKey(User)
    order = ForeignKey(Order)  # Must have purchased
    rating = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = CharField(max_length=200, blank=True)
    comment = TextField(blank=True)
    is_verified_purchase = BooleanField(default=True)
    is_published = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user', 'order']
        indexes = [
            Index(fields=['product', '-created_at']),
            Index(fields=['is_published']),
        ]
```

### 7. Security Components

**RateLimitMiddleware**
```python
class RateLimitMiddleware:
    def __init__(get_response):
        self.get_response = get_response
        self.cache = caches['default']
        
    def __call__(request):
        if self.is_rate_limited(request):
            return HttpResponse('Too Many Requests', status=429)
        return self.get_response(request)
        
    def is_rate_limited(request):
        """Check if request exceeds rate limit"""
        key = f'rate_limit:{request.META["REMOTE_ADDR"]}:{request.path}'
        count = self.cache.get(key, 0)
        
        if count >= self.get_limit(request.path):
            return True
            
        self.cache.set(key, count + 1, timeout=60)
        return False
        
    def get_limit(path):
        """Get rate limit for path"""
        if '/checkout/' in path:
            return 10  # 10 per minute
        return 100  # 100 per minute default
```

**InputValidator**
```python
class InputValidator:
    @staticmethod
    def validate_quantity(quantity):
        """Validate product quantity"""
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            raise ValidationError('Invalid quantity')
        return quantity
        
    @staticmethod
    def sanitize_search_query(query):
        """Sanitize search input"""
        # Remove special characters that could be used for injection
        return re.sub(r'[^\w\s-]', '', query)[:200]
        
    @staticmethod
    def validate_email(email):
        """Validate and normalize email"""
        try:
            validated = validate_email(email)
            return validated.email
        except EmailNotValidError:
            raise ValidationError('Invalid email address')
```


**SecurityLogger**
```python
class SecurityLogger:
    @staticmethod
    def log_failed_login(user_email, ip_address):
        """Log failed login attempt"""
        logger.warning(
            f'Failed login attempt for {user_email} from {ip_address}',
            extra={'event_type': 'failed_login', 'ip': ip_address}
        )
        
    @staticmethod
    def log_payment_failure(order_id, error_message):
        """Log payment failure without sensitive data"""
        logger.error(
            f'Payment failed for order {order_id}',
            extra={'event_type': 'payment_failure', 'order_id': order_id}
        )
        
    @staticmethod
    def log_rate_limit_violation(ip_address, path):
        """Log rate limit violation"""
        logger.warning(
            f'Rate limit exceeded for {ip_address} on {path}',
            extra={'event_type': 'rate_limit', 'ip': ip_address}
        )
```

### 8. Inventory Management Components

**InventoryManager**
```python
class InventoryManager:
    @staticmethod
    def check_availability(product, variant, quantity):
        """Check if product/variant has sufficient stock"""
        if variant:
            return variant.stock_quantity >= quantity
        return product.stock_quantity >= quantity
        
    @staticmethod
    def reserve_stock(product, variant, quantity):
        """Reserve stock for order (atomic operation)"""
        with transaction.atomic():
            if variant:
                variant = ProductVariant.objects.select_for_update().get(id=variant.id)
                if variant.stock_quantity < quantity:
                    raise InsufficientStockError()
                variant.stock_quantity -= quantity
                variant.save()
            else:
                product = Product.objects.select_for_update().get(id=product.id)
                if product.stock_quantity < quantity:
                    raise InsufficientStockError()
                product.stock_quantity -= quantity
                product.save()
                
    @staticmethod
    def restore_stock(order):
        """Restore stock when order is cancelled"""
        with transaction.atomic():
            for item in order.items.all():
                if item.variant:
                    variant = ProductVariant.objects.select_for_update().get(id=item.variant.id)
                    variant.stock_quantity += item.quantity
                    variant.save()
                else:
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock_quantity += item.quantity
                    product.save()
```

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   User      │         │  Category   │         │   Product   │
│  (existing) │         │             │         │             │
└──────┬──────┘         └──────┬──────┘         └──────┬──────┘
       │                       │                       │
       │                       │                       │
       │                       └───────────────────────┘
       │                                               │
       │                                               │
       ├───────────────────────────────────────────────┤
       │                                               │
       │                                               │
┌──────▼──────┐         ┌─────────────┐         ┌─────▼───────┐
│   Cart      │────────▶│  CartItem   │────────▶│ProductVariant│
└──────┬──────┘         └─────────────┘         └─────────────┘
       │
       │
┌──────▼──────┐         ┌─────────────┐         ┌─────────────┐
│  Wishlist   │────────▶│WishlistItem │────────▶│   Product   │
└─────────────┘         └─────────────┘         └─────────────┘
       │
       │
┌──────▼──────┐         ┌─────────────┐         ┌─────────────┐
│   Order     │────────▶│  OrderItem  │────────▶│   Product   │
└──────┬──────┘         └─────────────┘         └─────────────┘
       │
       │
┌──────▼──────┐
│ProductReview│
└─────────────┘
```

### Database Indexes

**Critical Indexes for Performance**:
- `Product`: (is_active, category_id), (slug), (created_at DESC)
- `ProductVariant`: (product_id, is_available), (sku)
- `Cart`: (user_id), (session_key), (updated_at)
- `CartItem`: (cart_id, product_id, variant_id)
- `Order`: (user_id, created_at DESC), (order_number), (status)
- `OrderItem`: (order_id)
- `ProductReview`: (product_id, is_published, created_at DESC)

### Data Validation Rules

**Product Validation**:
- Name: 1-200 characters, required
- Price: Positive decimal, max 10 digits
- Stock: Non-negative integer
- Images: JPEG/PNG/WebP, max 5MB

**Cart Validation**:
- Quantity: 1-100 per item
- Total items: Max 50 items per cart
- Cart expiry: 30 days for authenticated users

**Order Validation**:
- Shipping address: All fields required
- Phone: Valid format
- Email: Valid format
- Total: Must match calculated total


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication and Authorization Enforcement

*For any* user attempting to access protected resources (checkout, admin panel, wishlist), the system should verify authentication status and appropriate permissions before granting access.

**Validates: Requirements 1.1, 1.6, 11.6, 13.1**

### Property 2: Input Validation and Sanitization

*For any* user input (form data, search queries, file uploads), the system should validate format, sanitize content, and reject invalid data before processing or storage.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 3: CSRF Protection

*For any* state-changing HTTP request (POST, PUT, DELETE), the system should require a valid CSRF token that matches the user's session.

**Validates: Requirements 4.1, 4.2**

### Property 4: Payment Security

*For any* payment transaction, the system should never log or store complete credit card numbers, and should verify webhook signatures before processing payment confirmations.

**Validates: Requirements 2.5, 2.7, 2.8**

### Property 5: Order Creation After Payment

*For any* successful payment, the system should create an order record, decrement inventory, clear the cart, and send confirmation email.

**Validates: Requirements 2.6, 8.6, 10.2**

### Property 6: Search and Filter Accuracy

*For any* search query or filter combination (category, price range, sorting), all returned products should match the specified criteria and be ordered according to the sort parameter.

**Validates: Requirements 6.3, 6.4, 17.1, 17.2, 17.3, 17.4, 17.5**

### Property 7: Cart Total Calculation

*For any* shopping cart with items, the calculated total should equal the sum of (quantity × unit_price) for all items, plus shipping and tax.

**Validates: Requirements 7.4**

### Property 8: Inventory Stock Management

*For any* order completion, the system should atomically decrement stock quantities, and for any order cancellation, the system should restore stock quantities.

**Validates: Requirements 10.1, 10.2, 10.6, 10.7**

### Property 9: Review Permission Enforcement

*For any* user attempting to submit a product review, the system should verify the user has purchased that product before allowing review submission.

**Validates: Requirements 12.2, 12.6**

### Property 10: Average Rating Calculation

*For any* product with reviews, the displayed average rating should equal the sum of all review ratings divided by the review count, rounded to one decimal place.

**Validates: Requirements 12.7**

### Property 11: Product Soft Delete

*For any* product deletion request, the system should mark the product as inactive rather than removing the database record, preserving order history integrity.

**Validates: Requirements 13.5**

### Property 12: Email Notification on Status Change

*For any* order status change (placed, shipped, delivered), the system should send an email notification to the customer with relevant order details.

**Validates: Requirements 9.3, 16.1, 16.2, 16.3, 16.4**

### Property 13: Unique Order Number Generation

*For any* two orders created in the system, they should have different order numbers following the format EYT-YYYY-NNNNNN.

**Validates: Requirements 9.4**

### Property 14: Rate Limiting Enforcement

*For any* IP address making requests to an endpoint, when the request count exceeds the configured limit within the time window, subsequent requests should receive a 429 status code.

**Validates: Requirements 5.1**

### Property 15: Accessibility Compliance

*For any* image element in the system, it should have a descriptive alt attribute, and for any interactive element, it should have appropriate ARIA labels when semantic HTML is insufficient.

**Validates: Requirements 14.5, 14.7**

### Property 16: Email Notification Preferences

*For any* user with email notifications disabled, the system should not send marketing or promotional emails, but should still send transactional emails (order confirmations, shipping updates).

**Validates: Requirements 16.7**

### Property 17: Shipping Address Validation

*For any* checkout submission, all required shipping address fields (name, address line 1, city, state, postal code, country, phone) should be present and properly formatted.

**Validates: Requirements 8.2**

### Property 18: Security Event Logging

*For any* security-relevant event (failed login, payment failure, rate limit violation, CSRF failure), the system should create a log entry with timestamp, event type, and relevant non-sensitive metadata.

**Validates: Requirements 19.1, 19.2**


## Error Handling

### Error Handling Strategy

The store implements comprehensive error handling at multiple levels:

**1. Input Validation Errors**
- Return 400 Bad Request with specific field errors
- Display user-friendly error messages in forms
- Preserve valid form data on validation failure
- Example: "Quantity must be between 1 and 100"

**2. Authentication Errors**
- Return 401 Unauthorized for missing authentication
- Return 403 Forbidden for insufficient permissions
- Redirect to login page with return URL
- Display clear error messages

**3. Payment Errors**
- Catch payment gateway exceptions
- Log errors without sensitive data
- Display user-friendly error messages
- Allow retry without re-entering information
- Example: "Payment failed. Please try again or use a different payment method."

**4. Inventory Errors**
- Catch insufficient stock exceptions
- Display "Out of Stock" or "Only X remaining" messages
- Prevent checkout when items unavailable
- Notify user to update cart

**5. Database Errors**
- Use database transactions for critical operations
- Rollback on failure
- Log errors with context
- Display generic error message to user
- Example: "An error occurred. Please try again."

**6. External Service Errors**
- Implement retry logic with exponential backoff
- Use circuit breaker pattern for payment gateways
- Fallback to alternative payment method if one fails
- Log service failures

**7. Rate Limiting Errors**
- Return 429 Too Many Requests
- Include Retry-After header
- Display "Too many requests. Please try again in X seconds."

### Error Response Format

**API Errors (JSON)**:
```json
{
  "error": {
    "code": "INVALID_QUANTITY",
    "message": "Quantity must be between 1 and 100",
    "field": "quantity",
    "details": {}
  }
}
```

**Form Errors (HTML)**:
- Display errors above form
- Highlight invalid fields in red
- Preserve valid input values
- Provide specific guidance for correction

### Critical Error Scenarios

**Scenario 1: Payment Succeeds but Order Creation Fails**
- Solution: Use database transaction wrapping payment confirmation
- Rollback payment if order creation fails
- Log critical error for manual review
- Notify admin immediately

**Scenario 2: Concurrent Stock Depletion**
- Solution: Use SELECT FOR UPDATE in transactions
- Prevent race conditions
- Return "Out of Stock" to later request
- Ensure no overselling

**Scenario 3: Webhook Replay Attack**
- Solution: Store processed webhook IDs
- Check for duplicate webhooks
- Verify webhook signature
- Ignore duplicate events

**Scenario 4: Session Expiry During Checkout**
- Solution: Preserve cart in database
- Redirect to login with return URL
- Restore cart after authentication
- Resume checkout process

## Testing Strategy

### Testing Approach

The EYTGaming Store uses a dual testing approach combining unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
**Property Tests**: Verify universal properties across all inputs

Both testing approaches are complementary and necessary for comprehensive coverage. Unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Library**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Each test references its design document property
- Tag format: `# Feature: eytgaming-store, Property {number}: {property_text}`

**Example Property Test**:
```python
from hypothesis import given, strategies as st
import pytest

# Feature: eytgaming-store, Property 7: Cart Total Calculation
@given(
    items=st.lists(
        st.tuples(
            st.decimals(min_value=0.01, max_value=1000, places=2),  # price
            st.integers(min_value=1, max_value=100)  # quantity
        ),
        min_size=1,
        max_size=50
    )
)
def test_cart_total_calculation(items):
    """
    Property 7: For any shopping cart with items, the calculated total
    should equal the sum of (quantity × unit_price) for all items.
    """
    cart = Cart.objects.create()
    expected_total = Decimal('0.00')
    
    for price, quantity in items:
        product = Product.objects.create(price=price)
        CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        expected_total += price * quantity
    
    calculated_total = CartManager.calculate_total(cart)
    assert calculated_total == expected_total
```

### Test Coverage Requirements

**Unit Test Coverage**:
- Models: 90%+ coverage
- Views: 85%+ coverage
- Business logic: 95%+ coverage
- Utilities: 90%+ coverage

**Property Test Coverage**:
- All 18 correctness properties must have property tests
- Each property test must run minimum 100 iterations
- Property tests must use randomized input generation

### Test Organization

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_cart_manager.py
│   ├── test_order_manager.py
│   ├── test_payment_processor.py
│   └── test_inventory_manager.py
├── property/
│   ├── test_authentication_properties.py
│   ├── test_input_validation_properties.py
│   ├── test_cart_properties.py
│   ├── test_order_properties.py
│   ├── test_inventory_properties.py
│   └── test_security_properties.py
├── integration/
│   ├── test_checkout_flow.py
│   ├── test_payment_flow.py
│   └── test_order_flow.py
└── fixtures/
    ├── products.json
    ├── users.json
    └── categories.json
```

### Key Test Scenarios

**Authentication Tests**:
- Login with valid credentials
- Login with invalid credentials
- Account lockout after 5 failed attempts
- Session expiry and cart preservation
- Permission checks for admin access

**Input Validation Tests**:
- SQL injection attempts in search
- XSS attempts in reviews
- Invalid file uploads
- Quantity validation (negative, zero, huge)
- Email format validation

**CSRF Tests**:
- Form submission without token
- Form submission with invalid token
- AJAX requests with token in header

**Payment Tests**:
- Successful Stripe payment
- Successful Paystack payment
- Failed payment handling
- Webhook signature verification
- Duplicate webhook handling

**Cart Tests**:
- Add item to cart
- Update quantity
- Remove item
- Cart merging on login
- Total calculation with tax

**Order Tests**:
- Order creation from cart
- Order number uniqueness
- Status change notifications
- Order cancellation within 24 hours
- Order history display

**Inventory Tests**:
- Stock verification on add to cart
- Stock decrement on order
- Stock restoration on cancellation
- Concurrent purchase prevention
- Out of stock handling

**Review Tests**:
- Review submission by purchaser
- Review rejection by non-purchaser
- Rating calculation
- Review content sanitization

**Security Tests**:
- Rate limiting enforcement
- Failed login logging
- Payment error logging (no sensitive data)
- CSRF failure logging

### Integration Testing

**Checkout Flow Integration Test**:
1. User adds products to cart
2. User proceeds to checkout
3. User enters shipping information
4. User selects payment method
5. Payment is processed
6. Order is created
7. Inventory is decremented
8. Cart is cleared
9. Confirmation email is sent
10. User is redirected to confirmation page

**Payment Flow Integration Test**:
1. Create order with test payment
2. Simulate webhook from payment gateway
3. Verify webhook signature
4. Confirm order status updated
5. Verify email sent
6. Verify inventory decremented

### Performance Testing

**Load Testing Scenarios**:
- 100 concurrent users browsing products
- 50 concurrent users adding to cart
- 20 concurrent users checking out
- Measure response times and database query counts

**Performance Targets**:
- Product list page: < 500ms
- Product detail page: < 300ms
- Add to cart: < 200ms
- Checkout page: < 400ms
- Payment processing: < 2s

### Security Testing

**Security Test Checklist**:
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Authentication enforcement
- [ ] Authorization checks
- [ ] Secure session management
- [ ] Payment security (no card data stored)
- [ ] Webhook signature verification
- [ ] Input validation
- [ ] File upload validation
- [ ] Security logging

### Continuous Integration

**CI Pipeline**:
1. Run unit tests
2. Run property tests
3. Run integration tests
4. Check code coverage (minimum 85%)
5. Run security linters (bandit, safety)
6. Run code quality checks (pylint, flake8)
7. Build and deploy to staging

**Pre-deployment Checklist**:
- [ ] All tests passing
- [ ] Code coverage meets minimum
- [ ] Security scan clean
- [ ] Performance tests passing
- [ ] Manual QA on staging
- [ ] Database migrations tested
- [ ] Payment gateway tested in sandbox
- [ ] Email notifications tested
- [ ] Accessibility audit passed
