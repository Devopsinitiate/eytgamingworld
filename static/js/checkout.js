/**
 * Checkout page JavaScript for Stripe payment processing
 * Handles payment intent creation and card payment confirmation
 */

// Initialize Stripe with public key from template
let stripe;
let elements;
let cardElement;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeStripe();
    setupFormHandlers();
});

/**
 * Initialize Stripe.js and create Card Element
 */
function initializeStripe() {
    // Get Stripe public key from data attribute
    const stripePublicKey = document.getElementById('checkout-form').dataset.stripeKey;
    
    if (!stripePublicKey) {
        showError('Stripe configuration error. Please contact support.');
        return;
    }
    
    // Initialize Stripe
    stripe = Stripe(stripePublicKey);
    elements = stripe.elements();
    
    // Create card element with custom styling
    const style = {
        base: {
            color: '#ffffff',
            fontFamily: '"Spline Sans", sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#9da6b9'
            }
        },
        invalid: {
            color: '#f87171',
            iconColor: '#f87171'
        }
    };
    
    cardElement = elements.create('card', { style: style });
    cardElement.mount('#card-element');
    
    // Handle real-time validation errors
    cardElement.on('change', function(event) {
        const displayError = document.getElementById('card-errors');
        if (event.error) {
            displayError.textContent = event.error.message;
            displayError.classList.remove('hidden');
        } else {
            displayError.textContent = '';
            displayError.classList.add('hidden');
        }
    });
}

/**
 * Setup form submission handlers
 */
function setupFormHandlers() {
    const form = document.getElementById('checkout-form');
    
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        await handleFormSubmission();
    });
    
    // Cancel button handler
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            window.location.href = cancelBtn.dataset.cancelUrl;
        });
    }
}

/**
 * Handle form submission and payment processing
 */
async function handleFormSubmission() {
    setLoading(true);
    clearError();
    
    try {
        // Get payment details from form
        const amount = document.getElementById('checkout-form').dataset.amount;
        const paymentType = document.getElementById('checkout-form').dataset.paymentType;
        const description = document.getElementById('checkout-form').dataset.description;
        
        // Create payment intent
        const intentResponse = await createPaymentIntent(amount, paymentType, description);
        
        if (!intentResponse.client_secret) {
            throw new Error('Failed to create payment intent');
        }
        
        // Confirm payment with Stripe
        const { error, paymentIntent } = await stripe.confirmCardPayment(
            intentResponse.client_secret,
            {
                payment_method: {
                    card: cardElement
                }
            }
        );
        
        if (error) {
            showError(error.message);
            setLoading(false);
        } else {
            // Payment successful
            handlePaymentSuccess(intentResponse.payment_id);
        }
        
    } catch (error) {
        console.error('Payment error:', error);
        showError(error.message || 'An unexpected error occurred. Please try again.');
        setLoading(false);
    }
}

/**
 * Create payment intent via AJAX
 */
async function createPaymentIntent(amount, paymentType, description) {
    const response = await fetch('/payments/create-intent/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            amount: amount,
            payment_type: paymentType,
            description: description
        })
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create payment intent');
    }
    
    return await response.json();
}

/**
 * Handle successful payment
 */
function handlePaymentSuccess(paymentId) {
    // Show success message briefly
    showSuccess('Payment successful! Redirecting...');
    
    // Redirect to success page after short delay
    setTimeout(() => {
        window.location.href = `/payments/success/${paymentId}/`;
    }, 1500);
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('loading-spinner');
    const btnText = document.getElementById('btn-text');
    
    if (isLoading) {
        submitBtn.disabled = true;
        spinner.classList.remove('hidden');
        btnText.textContent = 'Processing...';
        cardElement.update({ disabled: true });
    } else {
        submitBtn.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = 'Pay Now';
        cardElement.update({ disabled: false });
    }
}

/**
 * Display error message
 */
function showError(message) {
    const errorDiv = document.getElementById('payment-errors');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    
    // Scroll to error
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Clear error message
 */
function clearError() {
    const errorDiv = document.getElementById('payment-errors');
    errorDiv.textContent = '';
    errorDiv.classList.add('hidden');
}

/**
 * Display success message
 */
function showSuccess(message) {
    const successDiv = document.getElementById('payment-success');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.remove('hidden');
    }
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
