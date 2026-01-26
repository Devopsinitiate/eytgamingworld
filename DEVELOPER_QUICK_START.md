# Developer Quick Start Guide

## Getting Started with Phase 2 Features

This guide will help you quickly integrate the new payment and notification systems into your features.

## Table of Contents
1. [Setup](#setup)
2. [Processing Payments](#processing-payments)
3. [Sending Notifications](#sending-notifications)
4. [Adding Audit Logging](#adding-audit-logging)
5. [Common Patterns](#common-patterns)

---

## Setup

### 1. Install Required Packages

```bash
pip install stripe
```

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# Stripe Test Keys (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLIC_KEY=pk_test_51xxxxx
STRIPE_SECRET_KEY=sk_test_51xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@eytgaming.com
```

### 3. Run Migrations

```bash
python manage.py migrate
```

---

## Processing Payments

### Basic Payment Flow

```python
from payments.services import StripeService
from payments.models import Payment
from notifications.models import Notification

def process_tournament_payment(request, tournament):
    """Process payment for tournament registration"""
    
    # Step 1: Create payment intent
    payment, intent = StripeService.create_payment_intent(
        user=request.user,
        amount=tournament.entry_fee,
        payment_type='tournament_fee',
        description=f'Registration for {tournament.name}',
        metadata={
            'tournament_id': str(tournament.id),
            'tournament_name': tournament.name
        }
    )
    
    # Step 2: Return client secret to frontend
    return JsonResponse({
        'client_secret': intent.client_secret,
        'payment_id': str(payment.id)
    })
```

### Handle Payment Success

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Payment)
def handle_tournament_payment_success(sender, instance, **kwargs):
    """Auto-register user when payment succeeds"""
    
    if instance.status == 'succeeded' and instance.payment_type == 'tournament_fee':
        tournament_id = instance.metadata.get('tournament_id')
        
        if tournament_id:
            tournament = Tournament.objects.get(id=tournament_id)
            
            # Create participant
            Participant.objects.get_or_create(
                tournament=tournament,
                user=instance.user,
                defaults={'payment': instance}
            )
            
            # Send confirmation notification
            Notification.create_notification(
                user=instance.user,
                title='Registration Confirmed!',
                message=f'You are registered for {tournament.name}',
                notification_type='tournament',
                priority='high',
                content_object=tournament,
                action_url=f'/tournaments/{tournament.id}/',
                delivery_methods=['in_app', 'email']
            )
```

---

## Sending Notifications

### Simple Notification

```python
from notifications.models import Notification

# Send a simple notification
Notification.create_notification(
    user=user,
    title='Welcome to EYTGaming!',
    message='Your account has been created successfully',
    notification_type='system',
    priority='normal'
)
```

### Notification with Action

```python
# Notification that links to a specific page
Notification.create_notification(
    user=user,
    title='New Match Scheduled',
    message=f'Your match in {tournament.name} starts at {match.start_time}',
    notification_type='match',
    priority='high',
    content_object=match,
    action_url=f'/tournaments/{tournament.id}/matches/{match.id}/',
    delivery_methods=['in_app', 'email', 'push']
)
```

### Using Notification Templates

```python
from notifications.models import NotificationTemplate

# Create a reusable template
template = NotificationTemplate.objects.create(
    name='match_reminder',
    notification_type='match',
    title_template='Match Starting Soon: {tournament_name}',
    message_template='Your match in {tournament_name} starts in {time_until}. Get ready!',
    default_priority='high',
    default_delivery_methods=['in_app', 'push']
)

# Use the template
template.create_notification(
    user=user,
    context={
        'tournament_name': tournament.name,
        'time_until': '15 minutes'
    }
)
```

### Bulk Notifications

```python
# Send notification to all tournament participants
participants = tournament.participants.all()

for participant in participants:
    Notification.create_notification(
        user=participant.user,
        title='Tournament Update',
        message=f'{tournament.name} schedule has been updated',
        notification_type='tournament',
        content_object=tournament,
        action_url=f'/tournaments/{tournament.id}/'
    )
```

---

## Adding Audit Logging

### Basic Audit Logging

```python
from security.utils import log_audit_action

# Log a user action
log_audit_action(
    user=request.user,
    action='create',
    description='Created new tournament',
    severity='low',
    content_object=tournament,
    request=request
)
```

### Using Decorators

```python
from security.utils import audit_action

@audit_action('tournament_create', 'medium')
def create_tournament(request):
    # Your view logic
    tournament = Tournament.objects.create(...)
    return redirect('tournament_detail', tournament.id)
```

### Logging Security Events

```python
from security.utils import log_security_event

# Log a security event
log_security_event(
    event_type='suspicious_activity',
    request=request,
    description='Multiple failed login attempts',
    risk_level='high',
    user=user
)
```

---

## Common Patterns

### Pattern 1: Tournament Registration with Payment

```python
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from payments.services import StripeService
from security.utils import log_audit_action

@login_required
def register_for_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Check if already registered
    if Participant.objects.filter(tournament=tournament, user=request.user).exists():
        messages.warning(request, 'You are already registered')
        return redirect('tournament_detail', tournament_id)
    
    if request.method == 'POST':
        # Create payment intent
        payment, intent = StripeService.create_payment_intent(
            user=request.user,
            amount=tournament.entry_fee,
            payment_type='tournament_fee',
            description=f'Registration for {tournament.name}',
            metadata={'tournament_id': str(tournament.id)}
        )
        
        # Log action
        log_audit_action(
            user=request.user,
            action='tournament_join',
            description=f'Started registration for {tournament.name}',
            content_object=tournament,
            request=request
        )
        
        # Redirect to checkout
        return render(request, 'tournaments/checkout.html', {
            'tournament': tournament,
            'payment': payment,
            'client_secret': intent.client_secret,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY
        })
    
    return render(request, 'tournaments/register.html', {
        'tournament': tournament
    })
```

### Pattern 2: Coaching Session Booking

```python
@login_required
def book_coaching_session(request, session_id):
    session = get_object_or_404(CoachingSession, id=session_id)
    
    if request.method == 'POST':
        # Create payment
        payment, intent = StripeService.create_payment_intent(
            user=request.user,
            amount=session.price,
            payment_type='coaching_session',
            description=f'Coaching with {session.coach.get_display_name()}',
            metadata={'session_id': str(session.id)}
        )
        
        # Notify both parties
        Notification.create_notification(
            user=request.user,
            title='Booking Pending',
            message='Complete payment to confirm your session',
            notification_type='coaching',
            action_url=f'/payments/checkout/?payment_id={payment.id}'
        )
        
        Notification.create_notification(
            user=session.coach,
            title='New Booking Request',
            message=f'{request.user.get_display_name()} is booking your session',
            notification_type='coaching'
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'payment_id': str(payment.id)
        })
    
    return render(request, 'coaching/book.html', {'session': session})
```

### Pattern 3: Refund Processing

```python
@login_required
def cancel_tournament_registration(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    participant = get_object_or_404(
        Participant,
        tournament=tournament,
        user=request.user
    )
    
    if participant.payment and participant.payment.is_refundable:
        # Process refund
        success = StripeService.refund_payment(
            payment=participant.payment,
            reason='Tournament registration canceled by user'
        )
        
        if success:
            # Remove participant
            participant.delete()
            
            # Notify user
            Notification.create_notification(
                user=request.user,
                title='Registration Canceled',
                message=f'Your registration for {tournament.name} has been canceled and refunded',
                notification_type='tournament',
                priority='normal',
                delivery_methods=['in_app', 'email']
            )
            
            # Log action
            log_audit_action(
                user=request.user,
                action='tournament_leave',
                description=f'Canceled registration and refunded for {tournament.name}',
                severity='medium',
                request=request
            )
            
            messages.success(request, 'Registration canceled and refunded')
        else:
            messages.error(request, 'Failed to process refund')
    else:
        messages.error(request, 'This registration is not eligible for refund')
    
    return redirect('tournament_detail', tournament_id)
```

### Pattern 4: Team Payment Split

```python
def process_team_tournament_payment(request, tournament, team):
    """Split payment among team members"""
    
    # Calculate per-person amount
    per_person = tournament.entry_fee / team.members.count()
    
    # Create payment for current user
    payment, intent = StripeService.create_payment_intent(
        user=request.user,
        amount=per_person,
        payment_type='tournament_fee',
        description=f'Team registration for {tournament.name}',
        metadata={
            'tournament_id': str(tournament.id),
            'team_id': str(team.id),
            'split_payment': True
        }
    )
    
    # Notify team members
    for member in team.members.exclude(id=request.user.id):
        Notification.create_notification(
            user=member,
            title='Team Tournament Payment',
            message=f'{request.user.get_display_name()} paid for team registration',
            notification_type='team',
            content_object=team
        )
    
    return intent.client_secret
```

---

## Frontend Integration

### Basic Checkout Form

```html
<!-- templates/payments/checkout.html -->
{% load static %}

<form id="payment-form">
    <div id="card-element"></div>
    <div id="card-errors" role="alert"></div>
    <button type="submit">Pay ${{ amount }}</button>
</form>

<script src="https://js.stripe.com/v3/"></script>
<script>
    const stripe = Stripe('{{ stripe_public_key }}');
    const elements = stripe.elements();
    const cardElement = elements.create('card');
    cardElement.mount('#card-element');
    
    const form = document.getElementById('payment-form');
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        // Create payment intent
        const response = await fetch('/payments/create-intent/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({
                amount: '{{ amount }}',
                payment_type: '{{ payment_type }}',
                description: '{{ description }}',
                metadata: {{ metadata|safe }}
            })
        });
        
        const {client_secret, payment_id} = await response.json();
        
        // Confirm payment
        const {error, paymentIntent} = await stripe.confirmCardPayment(
            client_secret,
            {
                payment_method: {
                    card: cardElement,
                    billing_details: {
                        name: '{{ user.get_full_name }}',
                        email: '{{ user.email }}'
                    }
                }
            }
        );
        
        if (error) {
            document.getElementById('card-errors').textContent = error.message;
        } else {
            window.location.href = `/payments/success/${payment_id}/`;
        }
    });
</script>
```

### Notification Dropdown

```html
<!-- templates/components/notification_dropdown.html -->
<div class="notification-dropdown">
    <button id="notification-bell">
        <i class="fas fa-bell"></i>
        <span class="badge" id="notification-count">0</span>
    </button>
    
    <div class="dropdown-menu" id="notification-menu">
        <div class="notification-list" id="notification-list">
            <!-- Notifications loaded via AJAX -->
        </div>
        <a href="{% url 'notifications:list' %}" class="view-all">View All</a>
    </div>
</div>

<script>
    // Load notifications
    async function loadNotifications() {
        const response = await fetch('/notifications/recent/', {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const data = await response.json();
        
        // Update count
        document.getElementById('notification-count').textContent = data.unread_count;
        
        // Render notifications
        const list = document.getElementById('notification-list');
        list.innerHTML = data.notifications.map(n => `
            <div class="notification-item ${n.read ? '' : 'unread'}">
                <a href="/notifications/${n.id}/">
                    <strong>${n.title}</strong>
                    <p>${n.message}</p>
                    <small>${new Date(n.created_at).toLocaleString()}</small>
                </a>
            </div>
        `).join('');
    }
    
    // Load on page load
    loadNotifications();
    
    // Poll every 30 seconds
    setInterval(loadNotifications, 30000);
</script>
```

---

## Testing

### Test Payment with Stripe Test Cards

```python
# Test successful payment
# Card: 4242 4242 4242 4242
# Any future expiry, any CVC

# Test declined payment
# Card: 4000 0000 0000 0002

# Test insufficient funds
# Card: 4000 0000 0000 9995
```

### Test Notifications

```python
from django.test import TestCase
from notifications.models import Notification

class NotificationTestCase(TestCase):
    def test_create_notification(self):
        notification = Notification.create_notification(
            user=self.user,
            title='Test',
            message='Test message',
            notification_type='system'
        )
        
        self.assertFalse(notification.read)
        self.assertEqual(notification.user, self.user)
```

---

## Troubleshooting

### Payment Not Processing
1. Check Stripe keys in `.env`
2. Verify webhook is configured
3. Check browser console for errors
4. Review Django logs

### Notifications Not Sending
1. Check email settings
2. Verify notification preferences
3. Check delivery_methods list
4. Review logs for errors

### Webhook Not Working
1. Verify webhook URL is publicly accessible
2. Check webhook secret matches
3. Review Stripe dashboard logs
4. Ensure CSRF exemption on webhook endpoint

---

## Best Practices

1. **Always use metadata** - Store relevant IDs in payment metadata
2. **Handle webhooks** - Don't rely solely on client-side confirmation
3. **Log everything** - Use audit logging for all important actions
4. **Test thoroughly** - Use Stripe test cards before going live
5. **Notify users** - Keep users informed of payment status
6. **Handle errors gracefully** - Show user-friendly error messages
7. **Secure endpoints** - Always require login for payment operations
8. **Validate amounts** - Never trust client-side amount calculations

---

## Need Help?

- Review `QUICK_REFERENCE_NEW_MODULES.md` for detailed API reference
- Check `PHASE_2_STRIPE_INTEGRATION_COMPLETE.md` for implementation details
- Review Stripe documentation: https://stripe.com/docs
- Check Django logs in `logs/django.log`

---

Happy coding! 🚀
