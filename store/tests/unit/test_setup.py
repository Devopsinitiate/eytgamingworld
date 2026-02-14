"""
Unit tests to verify store app setup and configuration.
"""

from django.test import TestCase, RequestFactory
from django.conf import settings
from django.core.exceptions import ValidationError
from store.middleware import RateLimitMiddleware
from store.utils import InputValidator, SecurityLogger


class StoreSetupTestCase(TestCase):
    """Test that the store app is properly configured."""
    
    def test_store_app_installed(self):
        """Test that store app is in INSTALLED_APPS."""
        self.assertIn('store.apps.StoreConfig', settings.INSTALLED_APPS)
    
    def test_rate_limit_middleware_installed(self):
        """Test that rate limit middleware is configured."""
        self.assertIn('store.middleware.RateLimitMiddleware', settings.MIDDLEWARE)
    
    def test_security_settings_configured(self):
        """Test that security settings are properly configured."""
        # Session security
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
        
        # CSRF security
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
    
    def test_store_specific_settings_exist(self):
        """Test that store-specific settings are configured."""
        self.assertTrue(hasattr(settings, 'CART_SESSION_ID'))
        self.assertTrue(hasattr(settings, 'CART_EXPIRY_DAYS'))
        self.assertTrue(hasattr(settings, 'ORDER_NUMBER_PREFIX'))
        self.assertTrue(hasattr(settings, 'LOW_STOCK_THRESHOLD'))


class InputValidatorTestCase(TestCase):
    """Test input validation utilities."""
    
    def test_validate_quantity_valid(self):
        """Test quantity validation with valid input."""
        self.assertEqual(InputValidator.validate_quantity(1), 1)
        self.assertEqual(InputValidator.validate_quantity(50), 50)
        self.assertEqual(InputValidator.validate_quantity(100), 100)
    
    def test_validate_quantity_invalid_type(self):
        """Test quantity validation with invalid type."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity('invalid')
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(None)
    
    def test_validate_quantity_out_of_range(self):
        """Test quantity validation with out of range values."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(0)
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(-1)
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(101)
    
    def test_sanitize_search_query(self):
        """Test search query sanitization."""
        # Normal query
        self.assertEqual(
            InputValidator.sanitize_search_query('gaming hoodie'),
            'gaming hoodie'
        )
        
        # Query with special characters (SQL injection attempt)
        # Special chars replaced with spaces, hyphens kept, then normalized
        result = InputValidator.sanitize_search_query("'; DROP TABLE products; --")
        # Should remove quotes and semicolons but keep hyphens
        self.assertIn('DROP TABLE products', result)
        self.assertNotIn("'", result)
        self.assertNotIn(";", result)
        
        # Query with HTML/JavaScript
        self.assertEqual(
            InputValidator.sanitize_search_query('<script>alert("xss")</script>'),
            'script alert xss script'
        )
        
        # Empty query
        self.assertEqual(InputValidator.sanitize_search_query(''), '')
        self.assertEqual(InputValidator.sanitize_search_query(None), '')
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        self.assertEqual(
            InputValidator.validate_email('user@example.com'),
            'user@example.com'
        )
        
        # Test normalization (lowercase)
        self.assertEqual(
            InputValidator.validate_email('USER@EXAMPLE.COM'),
            'user@example.com'
        )
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        with self.assertRaises(ValidationError):
            InputValidator.validate_email('invalid-email')
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email('')
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email(None)
    
    def test_sanitize_html(self):
        """Test HTML sanitization."""
        # Remove HTML tags by escaping
        self.assertEqual(
            InputValidator.sanitize_html('<p>Hello <b>World</b></p>'),
            '&lt;p&gt;Hello &lt;b&gt;World&lt;/b&gt;&lt;/p&gt;'
        )
        
        # Escape special characters
        self.assertEqual(
            InputValidator.sanitize_html('5 < 10 & 10 > 5'),
            '5 &lt; 10 &amp; 10 &gt; 5'
        )
        
        # XSS attempt - all tags escaped
        self.assertEqual(
            InputValidator.sanitize_html('<script>alert("xss")</script>'),
            '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
        )
        
        # Empty input
        self.assertEqual(InputValidator.sanitize_html(''), '')
        self.assertEqual(InputValidator.sanitize_html(None), '')


class RateLimitMiddlewareTestCase(TestCase):
    """Test rate limiting middleware."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda r: None)
    
    def test_get_client_ip(self):
        """Test IP address extraction."""
        # Direct connection
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = self.middleware.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Behind proxy
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 192.168.1.1'
        ip = self.middleware.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')
    
    def test_get_limit(self):
        """Test rate limit determination."""
        # Checkout endpoint (stricter limit)
        limit = self.middleware.get_limit('/store/checkout/')
        self.assertEqual(limit, 10)
        
        limit = self.middleware.get_limit('/store/payment/')
        self.assertEqual(limit, 10)
        
        # General endpoint
        limit = self.middleware.get_limit('/store/products/')
        self.assertEqual(limit, 100)
        
        limit = self.middleware.get_limit('/store/cart/')
        self.assertEqual(limit, 100)


class SecurityLoggerTestCase(TestCase):
    """Test security logging utilities."""
    
    def test_log_methods_exist(self):
        """Test that all logging methods exist and are callable."""
        self.assertTrue(callable(SecurityLogger.log_failed_login))
        self.assertTrue(callable(SecurityLogger.log_payment_failure))
        self.assertTrue(callable(SecurityLogger.log_rate_limit_violation))
        self.assertTrue(callable(SecurityLogger.log_csrf_failure))
        self.assertTrue(callable(SecurityLogger.log_file_upload_rejection))
    
    def test_log_failed_login(self):
        """Test failed login logging (should not raise exception)."""
        try:
            SecurityLogger.log_failed_login('user@example.com', '192.168.1.1')
        except Exception as e:
            self.fail(f'log_failed_login raised exception: {e}')
    
    def test_log_payment_failure(self):
        """Test payment failure logging (should not raise exception)."""
        try:
            SecurityLogger.log_payment_failure('EYT-2024-001234', 'Payment declined')
        except Exception as e:
            self.fail(f'log_payment_failure raised exception: {e}')
    
    def test_log_rate_limit_violation(self):
        """Test rate limit violation logging (should not raise exception)."""
        try:
            SecurityLogger.log_rate_limit_violation('192.168.1.1', '/store/checkout/')
        except Exception as e:
            self.fail(f'log_rate_limit_violation raised exception: {e}')
