"""
Payment models for EYTGaming platform.
Handles Stripe integration, invoices, and payment tracking.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Payment(models.Model):
    """
    Track all payments in the system.
    Integrates with Stripe for payment processing.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('tournament_fee', 'Tournament Registration Fee'),
        ('coaching_session', 'Coaching Session'),
        ('package_purchase', 'Package Purchase'),
        ('venue_booking', 'Venue Booking'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payments')
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe Integration
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    # Related Objects (generic tracking)
    related_model = models.CharField(max_length=100, blank=True, 
                                     help_text="Model name (e.g., 'Tournament', 'CoachingSession')")
    related_object_id = models.CharField(max_length=100, blank=True,
                                         help_text="UUID of related object")
    
    # Metadata
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Refund Information
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    refund_reason = models.TextField(blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_type', '-created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"{self.user.email} - {self.payment_type} - ${self.amount} - {self.status}"
    
    def mark_succeeded(self):
        """Mark payment as succeeded"""
        self.status = 'succeeded'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, reason=''):
        """Mark payment as failed"""
        self.status = 'failed'
        self.metadata['failure_reason'] = reason
        self.save()
    
    def process_refund(self, amount=None, reason=''):
        """Process a refund"""
        refund_amount = amount or self.amount
        self.refund_amount = refund_amount
        self.refund_reason = reason
        self.refunded_at = timezone.now()
        self.status = 'refunded'
        self.save()
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded"""
        return (
            self.status == 'succeeded' and 
            self.refund_amount == 0 and
            self.stripe_charge_id
        )


class Invoice(models.Model):
    """
    Generate invoices for payments.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Billing Information
    bill_to_name = models.CharField(max_length=200)
    bill_to_email = models.EmailField()
    bill_to_address = models.TextField(blank=True)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.bill_to_name}"


class StripeWebhookEvent(models.Model):
    """
    Log all Stripe webhook events for debugging and verification.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Stripe Event Details
    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100, db_index=True)
    
    # Payload
    payload = models.JSONField(help_text="Full webhook payload from Stripe")
    
    # Processing
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stripe_webhook_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['processed', '-created_at']),
        ]
        verbose_name = 'Stripe Webhook Event'
        verbose_name_plural = 'Stripe Webhook Events'
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"
    
    def mark_processed(self):
        """Mark event as processed"""
        self.processed = True
        self.processed_at = timezone.now()
        self.save()
    
    def mark_error(self, error_message):
        """Mark event as failed with error"""
        self.error_message = error_message
        self.save()


class PaymentMethod(models.Model):
    """
    Store user payment methods (cards, etc.)
    """
    
    METHOD_TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Method Details
    method_type = models.CharField(max_length=20, choices=METHOD_TYPE_CHOICES, default='card')
    is_default = models.BooleanField(default=False)
    
    # Stripe
    stripe_payment_method_id = models.CharField(max_length=255, blank=True)
    
    # Card Info (last 4 digits only for display)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        if self.card_last4:
            return f"{self.card_brand} ending in {self.card_last4}"
        return f"{self.method_type} - {self.user.email}"
