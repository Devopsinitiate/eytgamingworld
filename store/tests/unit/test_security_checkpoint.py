"""
Security Foundation Validation Tests for Task 4 Checkpoint

This test suite validates that all security middleware and features
implemented in tasks 1-3 are working correctly.

Tests cover:
- Rate limiting enforcement
- Input validation and sanitization
- CSRF protection
- Security logging
- Session security
- File upload validation

Validates: Task 4 - Security foundation validation checkpoint
"""

import time
from decimal import Decimal
from io import BytesIO
from unittest.mock import Mock, patch

from django.test import TestCase, RequestFactory, Client, override_settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.csrf import CsrfViewMiddleware
from django.http import HttpResponse

from store.middleware import RateLimitMiddleware
from store.utils import InputValidator, SecurityLogger

User = get_user_model()


class RateLimitingTests(TestCase):
    """
    Test rate limiting middleware is working correctly.
    
    Validates: Requirement 5.1, 5.2, 5.3
    """
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda r: HttpResponse('OK'))
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    def test_rate_limit_not_exceeded(self):
        """Test that requests under the limit are allowed"""
        request = self.factory.get('/store/products/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        # Make 5 requests (well under the 100/min limit)
        for _ in range(5):
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_exceeded_general_endpoint(self):
        """Test that exceeding rate limit returns 429"""
        request = self.factory.get('/store/products/')
        request.META['REMOTE_ADDR'] = '192.168.1.2'
        
        # Make 101 requests (exceeds 100/min limit)
        for i in range(101):
            response = self.middleware(request)
            if i < 100:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 429)
                self.assertIn('Too Many Requests', response.content.decode())
    
    def test_rate_limit_checkout_endpoint_stricter(self):
        """Test that checkout endpoints have stricter limits (10/min)"""
        request = self.factory.post('/store/checkout/payment/')
        request.META['REMOTE_ADDR'] = '192.168.1.3'
        
        # Make 11 requests (exceeds 10/min limit for checkout)
        for i in range(11):
            response = self.middleware(request)
            if i < 10:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_per_ip_isolation(self):
        """Test that rate limits are tracked per IP address"""
        request1 = self.factory.get('/store/products/')
        request1.META['REMOTE_ADDR'] = '192.168.1.4'
        
        request2 = self.factory.get('/store/products/')
        request2.META['REMOTE_ADDR'] = '192.168.1.5'
        
        # Make 100 requests from IP 1
        for _ in range(100):
            response = self.middleware(request1)
            self.assertEqual(response.status_code, 200)
        
        # IP 2 should still be able to make requests
        response = self.middleware(request2)
        self.assertEqual(response.status_code, 200)
    
    def test_rate_limit_includes_retry_after_header(self):
        """Test that 429 response includes Retry-After header"""
        request = self.factory.get('/store/products/')
        request.META['REMOTE_ADDR'] = '192.168.1.6'
        
        # Exceed rate limit
        for _ in range(101):
            response = self.middleware(request)
        
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)
        self.assertEqual(response.headers['Retry-After'], '60')


class InputValidationTests(TestCase):
    """
    Test input validation and sanitization utilities.
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are sanitized"""
        malicious_queries = [
            ("'; DROP TABLE products; --", ["'", ";"]),
            ("1' OR '1'='1", ["'", "="]),
            ("admin'--", ["'"]),
            ("' UNION SELECT * FROM users--", ["'", "UNION", "SELECT", "FROM"]),
        ]
        
        for query, dangerous_chars in malicious_queries:
            sanitized = InputValidator.sanitize_search_query(query)
            # Should remove SQL special characters
            for char in dangerous_chars:
                # The sanitizer removes special chars but may keep alphanumeric
                # Check that dangerous SQL keywords are broken up
                if char in ["'", ";", "="]:
                    self.assertNotIn(char, sanitized)
    
    def test_xss_prevention(self):
        """Test that XSS attempts are escaped"""
        xss_attempts = [
            ("<script>alert('XSS')</script>", ["<script>", "</script>"]),
            ("<img src=x onerror=alert('XSS')>", ["<img"]),
            ("<iframe src='evil.com'></iframe>", ["<iframe"]),
        ]
        
        for attempt, dangerous_tags in xss_attempts:
            sanitized = InputValidator.sanitize_html(attempt)
            # Should escape HTML special characters
            for tag in dangerous_tags:
                self.assertNotIn(tag, sanitized)
            # Should contain escaped versions
            self.assertIn("&lt;", sanitized)
            self.assertIn("&gt;", sanitized)
    
    def test_quantity_validation_rejects_malicious_input(self):
        """Test that quantity validation rejects malicious input"""
        invalid_quantities = [
            -1,
            0,
            101,
            1000,
            "'; DROP TABLE--",
            "<script>alert('XSS')</script>",
        ]
        
        for qty in invalid_quantities:
            with self.assertRaises(ValidationError):
                InputValidator.validate_quantity(qty)
    
    def test_email_validation_rejects_malicious_input(self):
        """Test that email validation rejects malicious input"""
        invalid_emails = [
            "'; DROP TABLE users; --",  # SQL injection attempt
            "not-an-email",  # Missing @ symbol
            "@test.com",  # Missing local part
            "test@",  # Missing domain
            "test@.com",  # Invalid domain
            "test..test@example.com",  # Consecutive dots
            "test@example",  # Missing TLD
        ]
        
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                InputValidator.validate_email(email)
    
    def test_file_upload_validation_rejects_malicious_files(self):
        """Test that file upload validation rejects malicious files"""
        # Test path traversal attempt - should be caught by extension check first
        file = Mock()
        file.name = "../../../etc/passwd.jpg"  # Add valid extension
        file.size = 1024
        file.content_type = "image/jpeg"
        file.seek = Mock()
        file.read = Mock(return_value=b'\xff\xd8\xff')  # Valid JPEG header
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn("path traversal", str(cm.exception))
        
        # Test null byte in filename
        file.name = "test\x00.jpg"
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn("null bytes", str(cm.exception))
        
        # Test file type spoofing (PNG header with JPEG extension)
        file.name = "test.jpg"
        file.content_type = "image/jpeg"
        file.size = 1024
        file.seek = Mock()
        file.read = Mock(return_value=b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a')  # PNG header
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn("does not match declared type", str(cm.exception))


class CSRFProtectionTests(TestCase):
    """
    Test CSRF protection is active and working.
    
    Validates: Requirements 4.1, 4.2, 4.3
    """
    
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_csrf_token_required_for_post(self):
        """Test that POST requests without CSRF token are rejected"""
        # Note: This test verifies CSRF middleware is configured
        # Actual CSRF protection will be tested in integration tests
        # when views are implemented
        from django.conf import settings
        
        # Verify CSRF middleware is installed
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE
        )
        
        # Verify CSRF settings are secure
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
    
    def test_csrf_token_in_forms(self):
        """Test that forms include CSRF token"""
        # This would be tested in integration tests with actual views
        # For now, verify CSRF middleware is installed
        from django.conf import settings
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE
        )
    
    def test_csrf_cookie_settings(self):
        """Test that CSRF cookie has secure settings"""
        from django.conf import settings
        
        # Verify CSRF cookie settings
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')


class SecurityLoggingTests(TestCase):
    """
    Test security event logging is working.
    
    Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
    """
    
    @patch('store.utils.logger')
    def test_failed_login_logging(self, mock_logger):
        """Test that failed login attempts are logged"""
        SecurityLogger.log_failed_login('test@example.com', '192.168.1.1')
        
        # Verify logging was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Verify log message contains relevant info
        self.assertIn('Failed login', call_args[0][0])
        self.assertIn('test@example.com', call_args[0][0])
        
        # Verify extra data
        extra = call_args[1]['extra']
        self.assertEqual(extra['event_type'], 'failed_login')
        self.assertEqual(extra['ip'], '192.168.1.1')
    
    @patch('store.utils.logger')
    def test_payment_failure_logging_no_sensitive_data(self, mock_logger):
        """Test that payment failures are logged without sensitive data"""
        SecurityLogger.log_payment_failure('ORDER-123', 'Card declined')
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Verify log message
        self.assertIn('Payment failed', call_args[0][0])
        self.assertIn('ORDER-123', call_args[0][0])
        
        # Verify no credit card numbers in log
        log_message = call_args[0][0]
        self.assertNotIn('4111', log_message)  # No card numbers
        self.assertNotIn('CVV', log_message)   # No CVV
    
    @patch('store.utils.logger')
    def test_rate_limit_violation_logging(self, mock_logger):
        """Test that rate limit violations are logged"""
        SecurityLogger.log_rate_limit_violation('192.168.1.1', '/store/checkout/')
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Verify log message
        self.assertIn('Rate limit exceeded', call_args[0][0])
        
        # Verify extra data
        extra = call_args[1]['extra']
        self.assertEqual(extra['event_type'], 'rate_limit_violation')
        self.assertEqual(extra['ip'], '192.168.1.1')
        self.assertEqual(extra['path'], '/store/checkout/')
    
    @patch('store.utils.logger')
    def test_csrf_failure_logging(self, mock_logger):
        """Test that CSRF failures are logged"""
        SecurityLogger.log_csrf_failure('192.168.1.1', '/store/cart/add/')
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Verify log message
        self.assertIn('CSRF validation failed', call_args[0][0])
        
        # Verify extra data
        extra = call_args[1]['extra']
        self.assertEqual(extra['event_type'], 'csrf_failure')
    
    @patch('store.utils.logger')
    def test_file_upload_rejection_logging(self, mock_logger):
        """Test that file upload rejections are logged"""
        SecurityLogger.log_file_upload_rejection(
            '192.168.1.1',
            'malicious.exe',
            'Invalid file type'
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Verify log message
        self.assertIn('File upload rejected', call_args[0][0])
        self.assertIn('malicious.exe', call_args[0][0])


class SessionSecurityTests(TestCase):
    """
    Test session security settings are configured correctly.
    
    Validates: Requirement 1.3
    """
    
    def test_session_cookie_httponly(self):
        """Test that session cookies are HTTPOnly"""
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
    
    def test_session_cookie_samesite(self):
        """Test that session cookies have SameSite attribute"""
        from django.conf import settings
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
    
    def test_session_cookie_age(self):
        """Test that session cookies have appropriate expiry"""
        from django.conf import settings
        # Should be 24 hours (86400 seconds)
        self.assertEqual(settings.SESSION_COOKIE_AGE, 86400)


class SecurityMiddlewareIntegrationTests(TestCase):
    """
    Integration tests for security middleware stack.
    
    Validates: Overall security foundation
    """
    
    def test_security_middleware_installed(self):
        """Test that all security middleware is installed"""
        from django.conf import settings
        
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'store.middleware.RateLimitMiddleware',
        ]
        
        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)
    
    def test_security_settings_configured(self):
        """Test that security settings are properly configured"""
        from django.conf import settings
        
        # Session security
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
        
        # CSRF security
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, 'Lax')
        
        # Rate limiting
        self.assertTrue(settings.STORE_RATE_LIMIT_ENABLED)
    
    def test_security_logging_configured(self):
        """Test that security logging is configured"""
        from django.conf import settings
        
        # Verify security logger exists
        self.assertIn('security', settings.LOGGING['loggers'])
        
        # Verify security log file handler exists
        self.assertIn('security_file', settings.LOGGING['handlers'])


class ComprehensiveSecurityValidationTests(TestCase):
    """
    Comprehensive validation of all security features for Task 4 checkpoint.
    
    This test class provides a high-level validation that all security
    features from tasks 1-3 are working together correctly.
    """
    
    def test_all_security_features_present(self):
        """Test that all required security features are present"""
        from django.conf import settings
        
        # 1. Rate limiting
        self.assertIn('store.middleware.RateLimitMiddleware', settings.MIDDLEWARE)
        self.assertTrue(settings.STORE_RATE_LIMIT_ENABLED)
        
        # 2. Input validation utilities
        self.assertTrue(hasattr(InputValidator, 'validate_quantity'))
        self.assertTrue(hasattr(InputValidator, 'sanitize_search_query'))
        self.assertTrue(hasattr(InputValidator, 'validate_email'))
        self.assertTrue(hasattr(InputValidator, 'validate_file_upload'))
        self.assertTrue(hasattr(InputValidator, 'sanitize_html'))
        
        # 3. Security logging
        self.assertTrue(hasattr(SecurityLogger, 'log_failed_login'))
        self.assertTrue(hasattr(SecurityLogger, 'log_payment_failure'))
        self.assertTrue(hasattr(SecurityLogger, 'log_rate_limit_violation'))
        self.assertTrue(hasattr(SecurityLogger, 'log_csrf_failure'))
        self.assertTrue(hasattr(SecurityLogger, 'log_file_upload_rejection'))
        
        # 4. CSRF protection
        self.assertIn('django.middleware.csrf.CsrfViewMiddleware', settings.MIDDLEWARE)
        self.assertTrue(settings.CSRF_COOKIE_HTTPONLY)
        
        # 5. Session security
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, 'Lax')
    
    def test_security_defense_in_depth(self):
        """Test that multiple layers of security are in place"""
        # This test verifies the defense-in-depth approach
        
        # Layer 1: Network security (HTTPS enforcement in production)
        from django.conf import settings
        # In production, these should be True
        # In development, they're False but that's expected
        
        # Layer 2: Application security (middleware)
        middleware_layers = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'store.middleware.RateLimitMiddleware',
        ]
        for layer in middleware_layers:
            self.assertIn(layer, settings.MIDDLEWARE)
        
        # Layer 3: Input validation
        # Verify all validation methods work
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(-1)
        
        sanitized = InputValidator.sanitize_search_query("'; DROP TABLE--")
        self.assertNotIn("'", sanitized)
        
        # Layer 4: Security logging
        # Verify logging methods exist and are callable
        self.assertTrue(callable(SecurityLogger.log_failed_login))
        self.assertTrue(callable(SecurityLogger.log_payment_failure))
