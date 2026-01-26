"""
Payment views for handling checkout and payment management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
import stripe
import json
import logging

from .models import Payment, PaymentMethod
from .services import StripeService, WebhookHandler
from security.utils import log_audit_action

logger = logging.getLogger(__name__)


@login_required
def payment_methods_list(request):
    """List user's saved payment methods"""
    payment_methods = PaymentMethod.objects.filter(
        user=request.user,
        is_active=True
    )
    
    context = {
        'payment_methods': payment_methods,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'payments/payment_methods.html', context)


@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def add_payment_method(request):
    """Add a new payment method"""
    if request.method == 'POST':
        try:
            payment_method_id = request.POST.get('payment_method_id')
            set_as_default = request.POST.get('set_as_default') == 'true'
            
            if not payment_method_id:
                return JsonResponse({'success': False, 'error': 'Payment method ID is required'}, status=400)
            
            payment_method = StripeService.add_payment_method(
                user=request.user,
                payment_method_id=payment_method_id,
                set_as_default=set_as_default
            )
            
            if payment_method:
                log_audit_action(
                    user=request.user,
                    action='create',
                    description='Added new payment method',
                    severity='low',
                    request=request
                )
                messages.success(request, 'Payment method added successfully')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Failed to add payment method'}, status=400)
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # GET request - show add payment method form
    setup_intent = StripeService.create_setup_intent(request.user)
    
    context = {
        'client_secret': setup_intent.client_secret if setup_intent else None,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'payments/add_payment_method.html', context)


@login_required
@require_POST
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def remove_payment_method(request, method_id):
    """Remove a payment method"""
    payment_method = get_object_or_404(
        PaymentMethod,
        id=method_id,
        user=request.user
    )
    
    if StripeService.remove_payment_method(payment_method):
        log_audit_action(
            user=request.user,
            action='delete',
            description='Removed payment method',
            severity='low',
            request=request
        )
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': 'Payment method removed successfully'})
        
        messages.success(request, 'Payment method removed successfully')
    else:
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Failed to remove payment method'}, status=400)
        
        messages.error(request, 'Failed to remove payment method')
    
    return redirect('payments:payment_methods')


@login_required
@require_POST
def set_default_payment_method(request, method_id):
    """Set a payment method as default"""
    payment_method = get_object_or_404(
        PaymentMethod,
        id=method_id,
        user=request.user
    )
    
    # Remove default from other methods
    PaymentMethod.objects.filter(
        user=request.user,
        is_default=True
    ).update(is_default=False)
    
    # Set this one as default
    payment_method.is_default = True
    payment_method.save()
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'message': 'Default payment method updated'})
    
    messages.success(request, 'Default payment method updated')
    return redirect('payments:payment_methods')


@login_required
@ratelimit(key='user', rate='20/h', method='POST', block=True)
def create_payment_intent(request):
    """Create a payment intent for checkout"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        payment_type = data.get('payment_type', 'other')
        description = data.get('description', '')
        metadata = data.get('metadata', {})
        
        if not amount:
            return JsonResponse({'error': 'Amount required'}, status=400)
        
        payment, intent = StripeService.create_payment_intent(
            user=request.user,
            amount=amount,
            payment_type=payment_type,
            description=description,
            metadata=metadata
        )
        
        log_audit_action(
            user=request.user,
            action='payment',
            description=f'Created payment intent for ${amount}',
            severity='medium',
            content_object=payment,
            request=request
        )
        
        return JsonResponse({
            'client_secret': intent.client_secret,
            'payment_id': str(payment.id)
        })
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    # Confirm payment if not already confirmed
    if payment.status == 'pending':
        StripeService.confirm_payment(payment)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/success.html', context)


@login_required
def payment_cancel(request):
    """Payment canceled page"""
    return render(request, 'payments/cancel.html')


@login_required
def payment_history(request):
    """View payment history"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        payments = payments.filter(status=status_filter)
    
    # Filter by payment type if provided
    type_filter = request.GET.get('type')
    if type_filter and type_filter != 'all':
        payments = payments.filter(payment_type=type_filter)
    
    # Pagination - 25 payments per page
    paginator = Paginator(payments, 25)
    page = request.GET.get('page', 1)
    
    # Validate and sanitize page number
    try:
        page_num = int(page)
        # Handle negative and zero page numbers
        if page_num <= 0:
            page_num = 1
    except (ValueError, TypeError):
        # If page is not an integer, default to 1
        page_num = 1
    
    try:
        payments_page = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        payments_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver first page instead of last page
        payments_page = paginator.page(1)
    
    context = {
        'payments': payments_page,
        'page_obj': payments_page,
        'status_filter': status_filter or 'all',
        'type_filter': type_filter or 'all',
    }
    
    return render(request, 'payments/history.html', context)


@login_required
def payment_detail(request, payment_id):
    """View payment details"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/detail.html', context)


@login_required
@require_POST
@ratelimit(key='user', rate='5/h', method='POST', block=True)
def request_refund(request, payment_id):
    """Request a refund for a payment"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if not payment.is_refundable:
        messages.error(request, 'This payment is not eligible for refund')
        return redirect('payments:detail', payment_id=payment_id)
    
    reason = request.POST.get('reason', 'Customer requested refund')
    
    if StripeService.refund_payment(payment, reason=reason):
        log_audit_action(
            user=request.user,
            action='payment',
            description=f'Requested refund for payment ${payment.amount}',
            severity='medium',
            content_object=payment,
            request=request
        )
        messages.success(request, 'Refund processed successfully')
    else:
        messages.error(request, 'Failed to process refund')
    
    return redirect('payments:detail', payment_id=payment_id)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        return HttpResponse(status=400)
    
    # Handle the event
    success = WebhookHandler.handle_event(event)
    
    if success:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=500)


@login_required
def checkout(request):
    """Generic checkout page"""
    # Get payment details from session or query params
    amount = request.GET.get('amount')
    payment_type = request.GET.get('type', 'other')
    description = request.GET.get('description', '')
    
    if not amount:
        messages.error(request, 'Invalid payment amount')
        return redirect('dashboard:home')
    
    context = {
        'amount': amount,
        'payment_type': payment_type,
        'description': description,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    
    return render(request, 'payments/checkout.html', context)


def rate_limit_exceeded(request, exception=None):
    """Custom view for rate limit exceeded"""
    logger.warning(f"Rate limit exceeded for user {request.user.id if request.user.is_authenticated else 'anonymous'}")
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': False,
            'error': 'Rate limit exceeded. Please try again later.',
            'retry_after': 3600  # 1 hour in seconds
        }, status=429)
    
    # Regular request
    messages.error(request, 'Too many requests. Please try again later.')
    return render(request, 'payments/rate_limit.html', status=429)
