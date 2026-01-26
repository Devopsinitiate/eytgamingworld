# Quick Reference Guide - New Modules

## Security Module

### Logging Audit Actions

```python
from security.models import AuditLog
from security.utils import log_audit_action

# Method 1: Direct model usage
AuditLog.log_action(
    user=request.user,
    action='create',
    description='Created new tournament',
    severity='low',
    content_object=tournament,
    ip_address='192.168.1.1',
    request_path='/tournaments/create/',
    request_method='POST'
)

# Method 2: Using utility function
log_audit_action(
    user=request.user,
    action='payment',
    description='Processed tournament payment',
    severity='medium',
    content_object=payment,
    request=request
)
```

### Logging Security Events

```python
from security.models import SecurityEvent
from security.utils import log_security_event

# Log a security event
log_security_event(
    event_type='failed_login',
    request=request,
    description='Failed login attempt for user@example.com',
    risk_level='medium',
    user=None
)
```

### Using Security Decorators

```python
from security.utils import audit_action, log_view_access

@audit_action('tournament_create', 'medium')
def create_tournament(request):
    # Your view logic
    pass

@log_view_access
def view_tournament(request, tournament_id):
    # Your view logic
    pass
```

---

## Payment Module

### Creating a Payment

```python
from payments.models import Payment
from decimal import Decimal

payment = Payment.objects.create(
    user=request.user,
    amount=Decimal('50.00'),
    currency='USD',
    payment_type='tournament_fee',
    description='Registration for Summer Championship',
    metadata={'tournament_id': str(tournament.id)}
)
```

### Processing Payment with Stripe

```python
# After Stripe payment intent succeeds
payment.stripe_payment_intent_id = 'pi_xxxxx'
payment.stripe_charge_id = 'ch_xxxxx'
payment.stripe_customer_id = 'cus_xxxxx'
payment.platform_fee = Decimal('5.00')
payment.stripe_fee = Decimal('1.75')
payment.mark_completed()
```

### Creating an Invoice

```python
from payments.models import Invoice
from datetime import date, timedelta

invoice = Invoice.objects.create(
    user=request.user,
    amount=Decimal('100.00'),
    currency='USD',
    issue_date=date.today(),
    due_date=date.today() + timedelta(days=30),
    description='Coaching package - 5 sessions',
    line_items=[
        {'description': 'Coaching Session', 'quantity': 5, 'price': 20.00},
    ]
)
```

### Handling Stripe Webhooks

```python
from payments.models import StripeWebhookEvent

# In your webhook view
webhook_event = StripeWebhookEvent.objects.create(
    stripe_event_id=event.id,
    event_type=event.type,
    payload=event.to_dict()
)

try:
    # Process the event
    if event.type == 'payment_intent.succeeded':
        # Handle successful payment
        pass
    
    webhook_event.mark_processed()
except Exception as e:
    webhook_event.mark_failed(str(e))
```

---

## Notification Module

### Creating Notifications

```python
from notifications.models import Notification

# Simple notification
Notification.create_notification(
    user=user,
    title='Tournament Starting Soon',
    message='Your tournament starts in 30 minutes!',
    notification_type='tournament',
    priority='high',
    action_url='/tournaments/123/',
    delivery_methods=['in_app', 'email']
)

# Notification with related object
Notification.create_notification(
    user=user,
    title='Payment Received',
    message=f'Payment of ${payment.amount} received',
    notification_type='payment',
    priority='normal',
    content_object=payment,
    action_url=f'/payments/{payment.id}/',
    delivery_methods=['in_app', 'email']
)
```

### Using Notification Templates

```python
from notifications.models import NotificationTemplate

# Create a template
template = NotificationTemplate.objects.create(
    name='tournament_reminder',
    notification_type='tournament',
    title_template='Tournament {tournament_name} starts in {time}',
    message_template='Your tournament {tournament_name} starts at {start_time}. Good luck!',
    default_priority='high',
    default_delivery_methods=['in_app', 'email', 'push']
)

# Use the template
template.create_notification(
    user=user,
    context={
        'tournament_name': 'Summer Championship',
        'time': '30 minutes',
        'start_time': '3:00 PM'
    }
)
```

### Managing User Preferences

```python
from notifications.models import NotificationPreference

# Get or create preferences
prefs, created = NotificationPreference.objects.get_or_create(user=user)

# Update preferences
prefs.email_tournament_updates = True
prefs.push_enabled = True
prefs.quiet_hours_enabled = True
prefs.quiet_hours_start = time(22, 0)  # 10 PM
prefs.quiet_hours_end = time(8, 0)     # 8 AM
prefs.save()

# Check if notification should be sent
if prefs.should_send_notification('tournament', 'email'):
    # Send notification
    pass
```

### Marking Notifications as Read

```python
# Single notification
notification = Notification.objects.get(id=notification_id)
notification.mark_as_read()

# Bulk mark as read
Notification.objects.filter(
    user=request.user,
    read=False
).update(read=True)
```

---

## User Model Enhancements

### Email Verification

```python
# Verify user email
user.verify_email()

# Check if verified
if user.is_verified:
    # Allow access
    pass
```

### Account Locking

```python
# Lock account
user.lock_account("Suspicious activity detected")

# Unlock account
user.unlock_account()

# Check if locked
if user.account_locked:
    return HttpResponse("Account is locked")
```

### Failed Login Tracking

```python
# In your login view
from django.contrib.auth import authenticate

user = authenticate(email=email, password=password)

if user is None:
    # Get user by email
    try:
        user = User.objects.get(email=email)
        user.record_failed_login()  # Auto-locks after 5 attempts
    except User.DoesNotExist:
        pass
else:
    user.reset_failed_logins()
    # Continue with login
```

### Profile Completeness

```python
# Check if profile is complete
if not user.check_profile_completeness():
    # Redirect to profile completion
    return redirect('complete_profile')
```

### Stripe Customer

```python
# Store Stripe customer ID
user.stripe_customer_id = 'cus_xxxxx'
user.save()

# Use in payment processing
if user.stripe_customer_id:
    # Use existing customer
    pass
else:
    # Create new Stripe customer
    pass
```

---

## Common Integration Patterns

### Tournament Registration with Payment

```python
from payments.models import Payment
from notifications.models import Notification
from security.utils import log_audit_action

def register_for_tournament(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    
    # Create payment
    payment = Payment.objects.create(
        user=request.user,
        amount=tournament.entry_fee,
        payment_type='tournament_fee',
        description=f'Registration for {tournament.name}',
        metadata={'tournament_id': str(tournament.id)}
    )
    
    # Log the action
    log_audit_action(
        user=request.user,
        action='tournament_join',
        description=f'Registered for {tournament.name}',
        severity='low',
        content_object=tournament,
        request=request
    )
    
    # Send notification
    Notification.create_notification(
        user=request.user,
        title='Registration Confirmed',
        message=f'You are registered for {tournament.name}',
        notification_type='tournament',
        content_object=tournament,
        action_url=f'/tournaments/{tournament.id}/'
    )
    
    return payment
```

### Coaching Session Booking

```python
def book_coaching_session(request, session_id):
    session = CoachingSession.objects.get(id=session_id)
    
    # Create payment
    payment = Payment.objects.create(
        user=request.user,
        amount=session.price,
        payment_type='coaching_session',
        description=f'Coaching with {session.coach.get_display_name()}',
        metadata={'session_id': str(session.id)}
    )
    
    # Log action
    log_audit_action(
        user=request.user,
        action='coaching_book',
        description=f'Booked session with {session.coach.get_display_name()}',
        content_object=session,
        request=request
    )
    
    # Notify user
    Notification.create_notification(
        user=request.user,
        title='Session Booked',
        message=f'Your coaching session is confirmed for {session.scheduled_time}',
        notification_type='coaching',
        priority='normal',
        delivery_methods=['in_app', 'email']
    )
    
    # Notify coach
    Notification.create_notification(
        user=session.coach,
        title='New Booking',
        message=f'{request.user.get_display_name()} booked a session',
        notification_type='coaching',
        priority='normal'
    )
    
    return payment
```

### Security Alert on Suspicious Activity

```python
from security.utils import log_security_event

def check_and_alert_suspicious_activity(request, user):
    # Check for suspicious patterns
    recent_failures = SecurityEvent.objects.filter(
        event_type='failed_login',
        ip_address=get_client_ip(request),
        created_at__gte=timezone.now() - timedelta(minutes=15)
    ).count()
    
    if recent_failures >= 3:
        # Log security event
        log_security_event(
            event_type='suspicious_activity',
            request=request,
            description=f'Multiple failed login attempts from {get_client_ip(request)}',
            risk_level='high',
            user=user
        )
        
        # Send notification to user
        Notification.create_notification(
            user=user,
            title='Security Alert',
            message='Multiple failed login attempts detected on your account',
            notification_type='security',
            priority='urgent',
            delivery_methods=['in_app', 'email']
        )
```

---

## Admin Usage

### Viewing Audit Logs
1. Go to Django Admin
2. Navigate to Security → Audit Logs
3. Filter by user, action, severity, or date
4. View detailed information about each action

### Managing Security Events
1. Go to Security → Security Events
2. Filter by event type, risk level, or resolved status
3. Click on an event to view details
4. Mark as resolved and add resolution notes

### Monitoring Payments
1. Go to Payments → Payments
2. View all payments with status indicators
3. Filter by status, type, or date
4. Click to view full payment details including fees

### Managing Notifications
1. Go to Notifications → Notifications
2. View all notifications sent to users
3. Filter by type, priority, or read status
4. Bulk mark as read/unread

---

## Environment Variables Needed

Add these to your `.env` file:

```env
# Stripe
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@eytgaming.com

# Security
RATE_LIMIT_ENABLED=True
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCK_DURATION=3600  # seconds
```

---

## Testing Examples

### Test Payment Creation

```python
from django.test import TestCase
from payments.models import Payment
from core.models import User
from decimal import Decimal

class PaymentTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
    
    def test_create_payment(self):
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            payment_type='tournament_fee'
        )
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.amount, Decimal('50.00'))
    
    def test_payment_net_amount(self):
        payment = Payment.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            platform_fee=Decimal('10.00'),
            stripe_fee=Decimal('3.20')
        )
        self.assertEqual(payment.net_amount, Decimal('86.80'))
```

### Test Notification Creation

```python
def test_create_notification(self):
    notification = Notification.create_notification(
        user=self.user,
        title='Test Notification',
        message='This is a test',
        notification_type='system'
    )
    self.assertFalse(notification.read)
    self.assertEqual(notification.user, self.user)
    
    notification.mark_as_read()
    self.assertTrue(notification.read)
    self.assertIsNotNone(notification.read_at)
```

---

## Troubleshooting

### Notifications Not Sending
- Check `NotificationPreference` for the user
- Verify email settings in `.env`
- Check notification delivery_methods list
- Look for errors in logs

### Payments Not Processing
- Verify Stripe keys are correct
- Check webhook endpoint is accessible
- Review `StripeWebhookEvent` for errors
- Ensure payment status is updating

### Audit Logs Not Appearing
- Verify middleware is installed
- Check signal handlers are connected
- Ensure `security` app is in INSTALLED_APPS
- Review database for entries

### Account Locking Issues
- Check `failed_login_attempts` count
- Verify `MAX_LOGIN_ATTEMPTS` setting
- Use `unlock_account()` method to reset
- Check `account_locked` field

---

This quick reference should help you integrate and use the new modules effectively!
