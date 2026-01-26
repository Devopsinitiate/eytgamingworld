/**
 * Add Payment Method JavaScript for Stripe SetupIntent
 * Handles saving payment methods without charging
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
    const form = document.getElementById('add-payment-method-form');
    const stripePublicKey = form.dataset.stripeKey;
    
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
    const form = document.getElementById('add-payment-method-form');
    
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        await handleFormSubmission();
    });
    
    // Cancel button handler
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            window.location.href = '/payments/methods/';
        });
    }
}

/**
 * Handle form submission and payment method saving
 */
async function handleFormSubmission() {
    setLoading(true);
    clearError();
    
    try {
        // Get client secret from form
        const form = document.getElementById('add-payment-method-form');
        const clientSecret = form.dataset.clientSecret;
        
        if (!clientSecret) {
            throw new Error('Setup intent not initialized. Please refresh the page.');
        }
        
        // Get set as default checkbox value
        const setAsDefault = document.getElementById('set-as-default').checked;
        
        // Confirm setup intent with Stripe
        const { setupIntent, error } = await stripe.confirmCardSetup(
            clientSecret,
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
            // Save payment method to database
            await savePaymentMethod(setupIntent.payment_method, setAsDefault);
        }
        
    } catch (error) {
        console.error('Payment method error:', error);
        showError(error.message || 'An unexpected error occurred. Please try again.');
        setLoading(false);
    }
}

/**
 * Save payment method to database via AJAX
 */
async function savePaymentMethod(paymentMethodId, setAsDefault) {
    const csrfToken = getCookie('csrftoken');
    
    if (!csrfToken) {
        console.error('CSRF token not found. Debugging info:');
        console.error('- Form input:', document.querySelector('input[name="csrfmiddlewaretoken"]'));
        console.error('- Meta tag:', document.querySelector('meta[name="csrf-token"]'));
        console.error('- Cookies:', document.cookie);
        throw new Error('CSRF token not found. Please refresh the page and try again.');
    }
    
    console.log('CSRF token found:', csrfToken.substring(0, 10) + '...');
    
    const response = await fetch('/payments/methods/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
            payment_method_id: paymentMethodId,
            set_as_default: setAsDefault ? 'true' : 'false'
        }),
        credentials: 'same-origin'
    });
    
    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Server returned an invalid response. Please try again.');
    }
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || 'Failed to save payment method');
    }
    
    if (data.success) {
        handleSuccess();
    } else {
        throw new Error(data.error || 'Failed to save payment method');
    }
}

/**
 * Handle successful payment method save
 */
function handleSuccess() {
    // Show success message briefly
    showSuccess('Payment method saved successfully! Redirecting...');
    
    // Redirect to payment methods list after short delay
    setTimeout(() => {
        window.location.href = '/payments/methods/';
    }, 1500);
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
    const submitBtn = document.getElementById('submit-btn');
    const spinner = document.getElementById('loading-spinner');
    const btnText = document.getElementById('btn-text');
    const cancelBtn = document.getElementById('cancel-btn');
    const setAsDefaultCheckbox = document.getElementById('set-as-default');
    
    if (isLoading) {
        submitBtn.disabled = true;
        cancelBtn.disabled = true;
        setAsDefaultCheckbox.disabled = true;
        spinner.classList.remove('hidden');
        btnText.textContent = 'Saving...';
        cardElement.update({ disabled: true });
    } else {
        submitBtn.disabled = false;
        cancelBtn.disabled = false;
        setAsDefaultCheckbox.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = 'Save Payment Method';
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
 * Get CSRF token from form, meta tag, or cookies
 */
function getCookie(name) {
    // First try to get from form's hidden input (most reliable)
    const form = document.getElementById('add-payment-method-form');
    if (form) {
        const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput && csrfInput.value) {
            return csrfInput.value;
        }
    }
    
    // Try to get from meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.getAttribute('content')) {
        return metaTag.getAttribute('content');
    }
    
    // Fallback to cookie
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
