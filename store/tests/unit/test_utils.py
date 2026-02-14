"""
Unit tests for store utility functions.

Tests the InputValidator and SecurityLogger classes to ensure
proper validation, sanitization, and security logging.
"""

import io
from django.test import TestCase
from django.core.exceptions import ValidationError
from store.utils import InputValidator, SecurityLogger


class InputValidatorQuantityTests(TestCase):
    """Test quantity validation."""
    
    def test_valid_quantity(self):
        """Test validation of valid quantity values."""
        self.assertEqual(InputValidator.validate_quantity(1), 1)
        self.assertEqual(InputValidator.validate_quantity(50), 50)
        self.assertEqual(InputValidator.validate_quantity(100), 100)
    
    def test_quantity_below_minimum(self):
        """Test that quantities below 1 are rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_quantity(0)
        self.assertIn('at least 1', str(cm.exception))
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(-5)
    
    def test_quantity_above_maximum(self):
        """Test that quantities above 100 are rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_quantity(101)
        self.assertIn('cannot exceed 100', str(cm.exception))
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(1000)
    
    def test_quantity_non_integer(self):
        """Test that non-integer quantities are rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_quantity('abc')
        self.assertIn('valid number', str(cm.exception))
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity(None)
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_quantity([])
    
    def test_quantity_string_integer(self):
        """Test that string integers are converted properly."""
        self.assertEqual(InputValidator.validate_quantity('5'), 5)
        self.assertEqual(InputValidator.validate_quantity('99'), 99)


class InputValidatorSearchQueryTests(TestCase):
    """Test search query sanitization."""
    
    def test_sanitize_normal_query(self):
        """Test sanitization of normal search queries."""
        result = InputValidator.sanitize_search_query('gaming hoodie')
        self.assertEqual(result, 'gaming hoodie')
        
        result = InputValidator.sanitize_search_query('EYT-Gaming Jersey')
        self.assertEqual(result, 'EYT-Gaming Jersey')
    
    def test_sanitize_sql_injection_attempts(self):
        """Test that SQL injection attempts are sanitized."""
        # Single quote injection
        result = InputValidator.sanitize_search_query("'; DROP TABLE products; --")
        self.assertNotIn("'", result)
        self.assertNotIn(';', result)
        # Note: Double-dash (--) becomes a single dash after sanitization
        
        # OR 1=1 injection
        result = InputValidator.sanitize_search_query("hoodie' OR '1'='1")
        self.assertNotIn("'", result)
        self.assertNotIn('=', result)
        
        # UNION injection - special characters removed but alphanumeric preserved
        result = InputValidator.sanitize_search_query("hoodie UNION SELECT * FROM users")
        # Should remove special characters but keep alphanumeric
        self.assertIn('hoodie', result)
        self.assertIn('UNION', result)
        self.assertNotIn('*', result)  # Special character removed
    
    def test_sanitize_special_characters(self):
        """Test that special characters are removed."""
        result = InputValidator.sanitize_search_query('test<script>alert(1)</script>')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn('(', result)
        self.assertNotIn(')', result)
    
    def test_sanitize_empty_query(self):
        """Test sanitization of empty queries."""
        self.assertEqual(InputValidator.sanitize_search_query(''), '')
        self.assertEqual(InputValidator.sanitize_search_query(None), '')
    
    def test_sanitize_long_query(self):
        """Test that queries are limited to 200 characters."""
        long_query = 'a' * 300
        result = InputValidator.sanitize_search_query(long_query)
        self.assertEqual(len(result), 200)
    
    def test_sanitize_excessive_whitespace(self):
        """Test that excessive whitespace is normalized."""
        result = InputValidator.sanitize_search_query('gaming    hoodie   jersey')
        self.assertEqual(result, 'gaming hoodie jersey')


class InputValidatorEmailTests(TestCase):
    """Test email validation."""
    
    def test_valid_email(self):
        """Test validation of valid email addresses."""
        result = InputValidator.validate_email('user@example.com')
        self.assertEqual(result, 'user@example.com')
        
        result = InputValidator.validate_email('test.user+tag@domain.co.uk')
        self.assertEqual(result, 'test.user+tag@domain.co.uk')
    
    def test_email_normalization(self):
        """Test that emails are normalized to lowercase."""
        result = InputValidator.validate_email('USER@EXAMPLE.COM')
        self.assertEqual(result, 'user@example.com')
        
        result = InputValidator.validate_email('  Test@Example.Com  ')
        self.assertEqual(result, 'test@example.com')
    
    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_email('invalid-email')
        self.assertIn('Invalid email', str(cm.exception))
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email('user@')
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email('@example.com')
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email('user @example.com')
    
    def test_empty_email(self):
        """Test that empty emails are rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_email('')
        self.assertIn('required', str(cm.exception))
        
        with self.assertRaises(ValidationError):
            InputValidator.validate_email(None)


class InputValidatorFileUploadTests(TestCase):
    """Test file upload validation."""
    
    def create_mock_file(self, name, content, content_type, size=None):
        """Helper to create a mock uploaded file."""
        file = io.BytesIO(content)
        file.name = name
        file.content_type = content_type
        file.size = size if size is not None else len(content)
        file.seek(0)
        return file
    
    def test_valid_jpeg_upload(self):
        """Test validation of valid JPEG file."""
        # JPEG magic number: FF D8 FF
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        file = self.create_mock_file('test.jpg', jpeg_content, 'image/jpeg')
        
        result = InputValidator.validate_file_upload(file)
        self.assertTrue(result)
    
    def test_valid_png_upload(self):
        """Test validation of valid PNG file."""
        # PNG magic number: 89 50 4E 47 0D 0A 1A 0A
        png_content = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\x00' * 100
        file = self.create_mock_file('test.png', png_content, 'image/png')
        
        result = InputValidator.validate_file_upload(file)
        self.assertTrue(result)
    
    def test_valid_webp_upload(self):
        """Test validation of valid WebP file."""
        # WebP magic number: RIFF....WEBP
        webp_content = b'RIFF\x00\x00\x00\x00WEBP' + b'\x00' * 100
        file = self.create_mock_file('test.webp', webp_content, 'image/webp')
        
        result = InputValidator.validate_file_upload(file)
        self.assertTrue(result)
    
    def test_file_too_large(self):
        """Test that files exceeding size limit are rejected."""
        # Create a file larger than 5MB
        large_content = b'\xff\xd8\xff\xe0' + b'\x00' * (6 * 1024 * 1024)
        file = self.create_mock_file('large.jpg', large_content, 'image/jpeg')
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('cannot exceed', str(cm.exception))
    
    def test_invalid_file_type(self):
        """Test that invalid file types are rejected."""
        file = self.create_mock_file('test.pdf', b'PDF content', 'application/pdf')
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('Invalid file type', str(cm.exception))
    
    def test_invalid_file_extension(self):
        """Test that invalid file extensions are rejected."""
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        file = self.create_mock_file('test.exe', jpeg_content, 'image/jpeg')
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('Invalid file extension', str(cm.exception))
    
    def test_mismatched_content_type(self):
        """Test that files with mismatched content are rejected."""
        # Claim it's a JPEG but provide PNG content
        png_content = b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\x00' * 100
        file = self.create_mock_file('test.jpg', png_content, 'image/jpeg')
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('does not match declared type', str(cm.exception))
    
    def test_path_traversal_in_filename(self):
        """Test that path traversal attempts are rejected."""
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        
        # Test various path traversal attempts
        file = self.create_mock_file('../../../etc/passwd.jpg', jpeg_content, 'image/jpeg')
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('path traversal', str(cm.exception))
        
        file = self.create_mock_file('..\\..\\test.jpg', jpeg_content, 'image/jpeg')
        with self.assertRaises(ValidationError):
            InputValidator.validate_file_upload(file)
        
        file = self.create_mock_file('/etc/passwd.jpg', jpeg_content, 'image/jpeg')
        with self.assertRaises(ValidationError):
            InputValidator.validate_file_upload(file)
    
    def test_null_byte_in_filename(self):
        """Test that null bytes in filename are rejected."""
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        file = self.create_mock_file('test\x00.jpg', jpeg_content, 'image/jpeg')
        
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(file)
        self.assertIn('null bytes', str(cm.exception))
    
    def test_no_file_provided(self):
        """Test that missing file is rejected."""
        with self.assertRaises(ValidationError) as cm:
            InputValidator.validate_file_upload(None)
        self.assertIn('No file provided', str(cm.exception))


class InputValidatorHTMLSanitizationTests(TestCase):
    """Test HTML sanitization."""
    
    def test_sanitize_normal_text(self):
        """Test that normal text is preserved."""
        result = InputValidator.sanitize_html('This is a normal review')
        self.assertEqual(result, 'This is a normal review')
    
    def test_sanitize_html_tags(self):
        """Test that HTML tags are escaped."""
        result = InputValidator.sanitize_html('<script>alert("XSS")</script>')
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('&lt;/script&gt;', result)
    
    def test_sanitize_xss_attempts(self):
        """Test that XSS attempts are neutralized."""
        # Script tag
        result = InputValidator.sanitize_html('<script>alert(1)</script>')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        
        # Image with onerror
        result = InputValidator.sanitize_html('<img src=x onerror=alert(1)>')
        self.assertNotIn('<img', result)
        self.assertIn('&lt;img', result)
        
        # Link with javascript
        result = InputValidator.sanitize_html('<a href="javascript:alert(1)">Click</a>')
        self.assertNotIn('<a', result)
        self.assertIn('&lt;a', result)
    
    def test_sanitize_special_characters(self):
        """Test that special characters are escaped."""
        result = InputValidator.sanitize_html('Test & "quotes" and \'apostrophes\'')
        self.assertIn('&amp;', result)
        self.assertIn('&quot;', result)
        self.assertIn('&#x27;', result)
    
    def test_sanitize_empty_text(self):
        """Test sanitization of empty text."""
        self.assertEqual(InputValidator.sanitize_html(''), '')
        self.assertEqual(InputValidator.sanitize_html(None), '')
    
    def test_sanitize_preserves_content(self):
        """Test that legitimate content is preserved after escaping."""
        text = 'Great product! 5/5 stars'
        result = InputValidator.sanitize_html(text)
        self.assertEqual(result, text)


class SecurityLoggerTests(TestCase):
    """Test security logging functionality."""
    
    def test_log_failed_login(self):
        """Test that failed login attempts are logged."""
        # This test verifies the method runs without error
        # In production, you'd verify the log output
        SecurityLogger.log_failed_login('user@example.com', '192.168.1.1')
    
    def test_log_payment_failure(self):
        """Test that payment failures are logged without sensitive data."""
        SecurityLogger.log_payment_failure('ORDER-123', 'Payment declined')
    
    def test_log_rate_limit_violation(self):
        """Test that rate limit violations are logged."""
        SecurityLogger.log_rate_limit_violation('192.168.1.1', '/checkout/')
    
    def test_log_csrf_failure(self):
        """Test that CSRF failures are logged."""
        SecurityLogger.log_csrf_failure('192.168.1.1', '/cart/add/')
    
    def test_log_file_upload_rejection(self):
        """Test that file upload rejections are logged."""
        SecurityLogger.log_file_upload_rejection(
            '192.168.1.1',
            'malicious.exe',
            'Invalid file type'
        )
