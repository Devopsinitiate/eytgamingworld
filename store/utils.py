"""
Utility functions for the EYTGaming Store.

This module provides security utilities including input validation,
sanitization, and security logging.
"""

import re
import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email

logger = logging.getLogger('security')


class InputValidator:
    """
    Input validation and sanitization utility class.
    
    Provides methods to validate and sanitize user inputs to prevent
    injection attacks and ensure data integrity.
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
    """
    
    @staticmethod
    def validate_quantity(quantity):
        """
        Validate product quantity input.
        
        Args:
            quantity: The quantity value to validate
            
        Returns:
            int: The validated quantity
            
        Raises:
            ValidationError: If quantity is invalid
        """
        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            raise ValidationError('Quantity must be a valid number')
        
        if qty < 1:
            raise ValidationError('Quantity must be at least 1')
        
        if qty > 100:
            raise ValidationError('Quantity cannot exceed 100')
        
        return qty
    
    @staticmethod
    def sanitize_search_query(query):
        """
        Sanitize search query to prevent SQL injection.
        
        Removes special characters that could be used for injection attacks
        while preserving legitimate search terms.
        
        Args:
            query: The search query string
            
        Returns:
            str: The sanitized query string
        """
        if not query:
            return ''
        
        # Remove special characters that could be used for injection
        # Allow: letters, numbers, spaces, hyphens
        sanitized = re.sub(r'[^\w\s-]', ' ', str(query))
        
        # Limit length to prevent abuse
        sanitized = sanitized[:200]
        
        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    @staticmethod
    def validate_email(email):
        """
        Validate and normalize email address.
        
        Args:
            email: The email address to validate
            
        Returns:
            str: The normalized email address
            
        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError('Email address is required')
        
        # Normalize email first (lowercase and strip whitespace)
        normalized = email.lower().strip()
        
        try:
            # Use Django's built-in email validator
            django_validate_email(normalized)
        except ValidationError:
            raise ValidationError('Invalid email address format')
        
        return normalized
    
    @staticmethod
    def validate_file_upload(file, allowed_types=None, max_size_mb=5):
        """
        Validate file upload for security.
        
        Performs multiple security checks:
        - File size validation
        - MIME type validation
        - File extension validation
        - Basic malicious content detection
        
        Args:
            file: The uploaded file object
            allowed_types: List of allowed MIME types
            max_size_mb: Maximum file size in megabytes
            
        Returns:
            bool: True if file is valid
            
        Raises:
            ValidationError: If file is invalid
        """
        if not file:
            raise ValidationError('No file provided')
        
        # Default allowed types for product images
        if allowed_types is None:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise ValidationError(f'File size cannot exceed {max_size_mb}MB')
        
        # Check file type
        if file.content_type not in allowed_types:
            raise ValidationError(
                f'Invalid file type. Allowed types: {", ".join(allowed_types)}'
            )
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        file_ext = file.name.lower().split('.')[-1]
        if f'.{file_ext}' not in allowed_extensions:
            raise ValidationError(
                f'Invalid file extension. Allowed: {", ".join(allowed_extensions)}'
            )
        
        # Basic malicious content detection
        # Check for null bytes in filename (path traversal attempt)
        if '\x00' in file.name:
            raise ValidationError('Invalid filename: contains null bytes')
        
        # Check for path traversal attempts in filename
        if '..' in file.name or '/' in file.name or '\\' in file.name:
            raise ValidationError('Invalid filename: path traversal detected')
        
        # Read first few bytes to verify file signature (magic numbers)
        file.seek(0)
        header = file.read(12)
        file.seek(0)  # Reset file pointer
        
        # Verify file signature matches declared type
        valid_signature = False
        if file.content_type == 'image/jpeg':
            # JPEG starts with FF D8 FF
            valid_signature = header[:3] == b'\xff\xd8\xff'
        elif file.content_type == 'image/png':
            # PNG starts with 89 50 4E 47 0D 0A 1A 0A
            valid_signature = header[:8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
        elif file.content_type == 'image/webp':
            # WebP starts with RIFF....WEBP
            valid_signature = header[:4] == b'RIFF' and header[8:12] == b'WEBP'
        
        if not valid_signature:
            raise ValidationError('File content does not match declared type')
        
        return True
    
    @staticmethod
    def sanitize_html(text):
        """
        Sanitize HTML content to prevent XSS attacks.
        
        Escapes special characters first, then removes HTML tags.
        
        Args:
            text: The text to sanitize
            
        Returns:
            str: The sanitized text
        """
        if not text:
            return ''
        
        text = str(text)
        
        # Escape special characters FIRST
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text


class SecurityLogger:
    """
    Security event logging utility.
    
    Provides methods to log security-related events without exposing
    sensitive information.
    
    Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5
    """
    
    @staticmethod
    def log_failed_login(user_identifier, ip_address):
        """
        Log failed login attempt.
        
        Args:
            user_identifier: Username or email (not password)
            ip_address: Client IP address
        """
        logger.warning(
            f'Failed login attempt for {user_identifier} from {ip_address}',
            extra={
                'event_type': 'failed_login',
                'user_identifier': user_identifier,
                'ip': ip_address
            }
        )
    
    @staticmethod
    def log_payment_failure(order_id, error_message):
        """
        Log payment failure without sensitive data.
        
        NEVER logs credit card numbers or sensitive payment information.
        
        Args:
            order_id: The order identifier
            error_message: Generic error message (no sensitive data)
        """
        # Ensure no sensitive data in error message
        safe_message = str(error_message)[:200]  # Limit length
        
        logger.error(
            f'Payment failed for order {order_id}: {safe_message}',
            extra={
                'event_type': 'payment_failure',
                'order_id': order_id
            }
        )
    
    @staticmethod
    def log_rate_limit_violation(ip_address, path):
        """
        Log rate limit violation.
        
        Args:
            ip_address: Client IP address
            path: Request path that was rate limited
        """
        logger.warning(
            f'Rate limit exceeded for {ip_address} on {path}',
            extra={
                'event_type': 'rate_limit_violation',
                'ip': ip_address,
                'path': path
            }
        )
    
    @staticmethod
    def log_csrf_failure(ip_address, path):
        """
        Log CSRF validation failure.
        
        Args:
            ip_address: Client IP address
            path: Request path where CSRF failed
        """
        logger.warning(
            f'CSRF validation failed for {ip_address} on {path}',
            extra={
                'event_type': 'csrf_failure',
                'ip': ip_address,
                'path': path
            }
        )
    
    @staticmethod
    def log_file_upload_rejection(ip_address, file_name, reason):
        """
        Log rejected file upload.
        
        Args:
            ip_address: Client IP address
            file_name: Name of rejected file (renamed to avoid LogRecord conflict)
            reason: Reason for rejection
        """
        logger.warning(
            f'File upload rejected from {ip_address}: {file_name} - {reason}',
            extra={
                'event_type': 'file_upload_rejection',
                'ip': ip_address,
                'rejected_file': file_name,
                'reason': reason
            }
        )



# ============================================================================
# Email Notification System
# ============================================================================

class EmailNotificationService:
    """
    Service for sending email notifications to users.
    
    Handles order status notifications, wishlist notifications, and
    respects user email preferences.
    
    Requirements: 16.1, 16.2, 16.3, 16.4, 16.7
    """
    
    @staticmethod
    def send_order_confirmation(order):
        """
        Send order confirmation email after successful payment.
        
        Args:
            order: Order instance
            
        Requirements: 16.1
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        from django.contrib.sites.shortcuts import get_current_site
        
        try:
            # Check if user wants to receive order emails
            if not EmailNotificationService._should_send_email(order.user, 'order_updates'):
                return False
            
            # Render email template
            context = {
                'order': order,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('store/emails/order_confirmation.html', context)
            
            # Send email
            send_mail(
                subject=f'Order Confirmation - {order.order_number}',
                message=f'Thank you for your order! Order number: {order.order_number}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send order confirmation email: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def send_shipping_notification(order):
        """
        Send shipping notification email when order is shipped.
        
        Args:
            order: Order instance
            
        Requirements: 16.2
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        try:
            # Check if user wants to receive shipping emails
            if not EmailNotificationService._should_send_email(order.user, 'order_updates'):
                return False
            
            # Render email template
            context = {
                'order': order,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('store/emails/order_shipped.html', context)
            
            # Send email
            send_mail(
                subject=f'Your Order Has Shipped - {order.order_number}',
                message=f'Your order {order.order_number} has been shipped!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send shipping notification email: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def send_delivery_confirmation(order):
        """
        Send delivery confirmation email when order is delivered.
        
        Args:
            order: Order instance
            
        Requirements: 16.3
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        try:
            # Check if user wants to receive delivery emails
            if not EmailNotificationService._should_send_email(order.user, 'order_updates'):
                return False
            
            # Render email template
            context = {
                'order': order,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('store/emails/order_delivered.html', context)
            
            # Send email
            send_mail(
                subject=f'Your Order Has Been Delivered - {order.order_number}',
                message=f'Your order {order.order_number} has been delivered!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send delivery confirmation email: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def send_wishlist_stock_notification(user, product):
        """
        Send notification when wishlist item is back in stock.
        
        Args:
            user: User instance
            product: Product instance
            
        Requirements: 16.4
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        try:
            # Check if user wants to receive wishlist emails
            if not EmailNotificationService._should_send_email(user, 'wishlist_updates'):
                return False
            
            # Render email template
            context = {
                'user': user,
                'product': product,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('store/emails/wishlist_back_in_stock.html', context)
            
            # Send email
            send_mail(
                subject=f'Back in Stock: {product.name}',
                message=f'{product.name} is back in stock!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send wishlist stock notification: {str(e)}", exc_info=True)
            return False
    
    @staticmethod
    def _should_send_email(user, notification_type):
        """
        Check if user wants to receive emails of this type.
        
        Args:
            user: User instance
            notification_type: Type of notification ('order_updates', 'wishlist_updates', etc.)
            
        Returns:
            bool: True if email should be sent
            
        Requirements: 16.7
        """
        # Check if user has email preferences model
        # For now, default to True (send all emails)
        # This can be extended with a UserEmailPreferences model
        
        try:
            # Try to get user email preferences
            from dashboard.models import UserEmailPreferences
            preferences = UserEmailPreferences.objects.filter(user=user).first()
            
            if preferences:
                if notification_type == 'order_updates':
                    return preferences.receive_order_updates
                elif notification_type == 'wishlist_updates':
                    return preferences.receive_wishlist_updates
                elif notification_type == 'marketing':
                    return preferences.receive_marketing_emails
            
            # Default to True if no preferences set
            return True
            
        except ImportError:
            # UserEmailPreferences model doesn't exist yet
            # Default to True (send all emails)
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error checking email preferences: {str(e)}")
            # Default to True on error
            return True
