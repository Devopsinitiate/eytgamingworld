# EYTGaming Store App

## Overview

The EYTGaming Store is a secure e-commerce platform for selling official merchandise to the EYTGaming esports community. The store prioritizes security, performance, and accessibility while maintaining the aggressive esports aesthetic with dark themes and bold red accents.

## Features

- **Product Catalog**: Browse and search products with filtering and sorting
- **Shopping Cart**: Add products to cart with session and database persistence
- **Secure Checkout**: Multi-step checkout with Stripe and Paystack integration
- **Order Management**: Track orders and view order history
- **Wishlist**: Save products for later purchase
- **Product Reviews**: Read and write reviews for purchased products
- **Inventory Management**: Real-time stock tracking with overselling prevention
- **Admin Panel**: Comprehensive admin interface for managing products and orders

## Security Features

- **Rate Limiting**: Prevents abuse and DDoS attacks
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Input Validation**: All user inputs validated and sanitized
- **Payment Security**: PCI DSS compliant via Stripe/Paystack (no card data stored)
- **Session Security**: Secure session management with HTTPOnly and Secure flags
- **HTTPS Enforcement**: All connections encrypted in production
- **Security Logging**: Comprehensive logging of security events

## Directory Structure

```
store/
├── __init__.py
├── apps.py              # App configuration
├── models.py            # Database models
├── views.py             # View functions and classes
├── urls.py              # URL routing
├── admin.py             # Django admin configuration
├── middleware.py        # Rate limiting and security middleware
├── utils.py             # Utility functions (validation, logging)
├── signals.py           # Django signals
├── migrations/          # Database migrations
└── tests/               # Test suite
    ├── unit/            # Unit tests
    ├── property/        # Property-based tests (Hypothesis)
    └── integration/     # Integration tests
```

## Configuration

The store app is configured in `config/settings.py` with the following settings:

### Security Settings
- `STORE_RATE_LIMIT_ENABLED`: Enable/disable rate limiting
- `SESSION_COOKIE_HTTPONLY`: Prevent JavaScript access to session cookies
- `CSRF_COOKIE_HTTPONLY`: Prevent JavaScript access to CSRF tokens
- `SECURE_SSL_REDIRECT`: Force HTTPS in production

### Business Settings
- `CART_SESSION_ID`: Session key for cart storage
- `CART_EXPIRY_DAYS`: Days to keep cart for authenticated users
- `ORDER_NUMBER_PREFIX`: Prefix for order numbers (EYT)
- `LOW_STOCK_THRESHOLD`: Stock level for low stock warnings

### Payment Settings
- `STRIPE_PUBLIC_KEY`: Stripe publishable key
- `STRIPE_SECRET_KEY`: Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret
- `PAYSTACK_PUBLIC_KEY`: Paystack public key
- `PAYSTACK_SECRET_KEY`: Paystack secret key
- `PAYSTACK_WEBHOOK_SECRET`: Paystack webhook secret

## Middleware

### RateLimitMiddleware

Implements rate limiting to prevent abuse:
- General endpoints: 100 requests per minute per IP
- Checkout endpoints: 10 requests per minute per IP

## Utilities

### InputValidator

Provides input validation and sanitization:
- `validate_quantity()`: Validate product quantities (1-100)
- `sanitize_search_query()`: Sanitize search inputs to prevent SQL injection
- `validate_email()`: Validate and normalize email addresses
- `validate_file_upload()`: Validate file uploads (type, size)
- `sanitize_html()`: Remove HTML tags and escape special characters

### SecurityLogger

Provides security event logging:
- `log_failed_login()`: Log failed login attempts
- `log_payment_failure()`: Log payment failures (no sensitive data)
- `log_rate_limit_violation()`: Log rate limit violations
- `log_csrf_failure()`: Log CSRF validation failures
- `log_file_upload_rejection()`: Log rejected file uploads

## Testing

The store app uses a dual testing approach:

### Unit Tests
Located in `tests/unit/`, these tests verify specific examples and edge cases.

### Property-Based Tests
Located in `tests/property/`, these tests use Hypothesis to verify universal properties across randomized inputs.

### Integration Tests
Located in `tests/integration/`, these tests verify end-to-end workflows.

Run tests with:
```bash
# All tests
python manage.py test store

# Unit tests only
python manage.py test store.tests.unit

# Property tests only
python manage.py test store.tests.property

# Integration tests only
python manage.py test store.tests.integration
```

## Development Status

This app is currently under development. See `.kiro/specs/eytgaming-store/tasks.md` for implementation progress.

## Requirements

See `.kiro/specs/eytgaming-store/requirements.md` for detailed requirements.

## Design

See `.kiro/specs/eytgaming-store/design.md` for detailed design specifications.
