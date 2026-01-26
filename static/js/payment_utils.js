/**
 * Payment Utilities - Shared JavaScript utilities for payment pages
 * Provides reusable functions for loading states, error handling, success messages,
 * modals, form validation, and common payment operations
 * 
 * Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 9.3
 */

// ============================================================================
// CSRF Token Utilities
// ============================================================================

/**
 * Get CSRF token from cookies
 * @param {string} name - Cookie name (default: 'csrftoken')
 * @returns {string|null} CSRF token value or null if not found
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

/**
 * Get CSRF token for AJAX requests
 * @returns {string} CSRF token value
 */
function getCSRFToken() {
    return getCookie('csrftoken') || '';
}

// ============================================================================
// Loading State Helpers
// ============================================================================

/**
 * Set loading state on a button
 * @param {HTMLElement} button - Button element
 * @param {boolean} isLoading - Whether to show loading state
 * @param {string} loadingText - Text to display while loading (default: 'Processing...')
 */
function setButtonLoading(button, isLoading, loadingText = 'Processing...') {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> ${loadingText}`;
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

/**
 * Set loading state on a form
 * @param {HTMLFormElement} form - Form element
 * @param {boolean} isLoading - Whether to show loading state
 */
function setFormLoading(form, isLoading) {
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, select, textarea, button');
    inputs.forEach(input => {
        input.disabled = isLoading;
    });
}

/**
 * Show/hide loading spinner
 * @param {string} spinnerId - ID of spinner element
 * @param {boolean} show - Whether to show the spinner
 */
function toggleSpinner(spinnerId, show) {
    const spinner = document.getElementById(spinnerId);
    if (spinner) {
        if (show) {
            spinner.classList.remove('hidden');
        } else {
            spinner.classList.add('hidden');
        }
    }
}

/**
 * Set loading state for payment form with Stripe element
 * @param {Object} options - Configuration object
 * @param {HTMLElement} options.submitBtn - Submit button element
 * @param {HTMLElement} options.spinner - Spinner element
 * @param {HTMLElement} options.btnText - Button text element
 * @param {Object} options.cardElement - Stripe card element (optional)
 * @param {boolean} options.isLoading - Whether to show loading state
 * @param {string} options.loadingText - Text to display while loading
 * @param {string} options.defaultText - Text to display when not loading
 */
function setPaymentFormLoading(options) {
    const {
        submitBtn,
        spinner,
        btnText,
        cardElement,
        isLoading,
        loadingText = 'Processing...',
        defaultText = 'Submit'
    } = options;
    
    if (isLoading) {
        if (submitBtn) submitBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');
        if (btnText) btnText.textContent = loadingText;
        if (cardElement) cardElement.update({ disabled: true });
    } else {
        if (submitBtn) submitBtn.disabled = false;
        if (spinner) spinner.classList.add('hidden');
        if (btnText) btnText.textContent = defaultText;
        if (cardElement) cardElement.update({ disabled: false });
    }
}

// ============================================================================
// Error Display Helpers
// ============================================================================

/**
 * Display error message in a specific element
 * @param {string} elementId - ID of error display element
 * @param {string} message - Error message to display
 * @param {boolean} scroll - Whether to scroll to error (default: true)
 */
function showError(elementId, message, scroll = true) {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        
        if (scroll) {
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

/**
 * Clear error message from a specific element
 * @param {string} elementId - ID of error display element
 */
function clearError(elementId) {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.textContent = '';
        errorDiv.classList.add('hidden');
    }
}

/**
 * Display inline error for a form field
 * @param {HTMLElement} field - Form field element
 * @param {string} message - Error message
 */
function showFieldError(field, message) {
    if (!field) return;
    
    // Add error styling to field
    field.classList.add('border-red-400', 'focus:border-red-400');
    
    // Create or update error message element
    let errorElement = field.parentElement.querySelector('.field-error');
    if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.className = 'field-error text-red-400 text-sm mt-1';
        field.parentElement.appendChild(errorElement);
    }
    errorElement.textContent = message;
}

/**
 * Clear inline error for a form field
 * @param {HTMLElement} field - Form field element
 */
function clearFieldError(field) {
    if (!field) return;
    
    // Remove error styling
    field.classList.remove('border-red-400', 'focus:border-red-400');
    
    // Remove error message element
    const errorElement = field.parentElement.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

/**
 * Display error toast notification
 * @param {string} message - Error message
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showErrorToast(message, duration = 3000) {
    showToast(message, 'error', duration);
}

// ============================================================================
// Success Message Helpers
// ============================================================================

/**
 * Display success message in a specific element
 * @param {string} elementId - ID of success display element
 * @param {string} message - Success message to display
 */
function showSuccess(elementId, message) {
    const successDiv = document.getElementById(elementId);
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.remove('hidden');
    }
}

/**
 * Clear success message from a specific element
 * @param {string} elementId - ID of success display element
 */
function clearSuccess(elementId) {
    const successDiv = document.getElementById(elementId);
    if (successDiv) {
        successDiv.textContent = '';
        successDiv.classList.add('hidden');
    }
}

/**
 * Display success toast notification
 * @param {string} message - Success message
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showSuccessToast(message, duration = 3000) {
    showToast(message, 'success', duration);
}

/**
 * Display toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast ('success', 'error', 'info', 'warning')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    
    // Set background color based on type
    const bgColors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    const bgColor = bgColors[type] || bgColors.info;
    
    toast.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${bgColor} text-white`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after duration
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

// ============================================================================
// Modal Helpers
// ============================================================================

/**
 * Open a modal
 * @param {string} modalId - ID of modal element
 * @param {string} overlayId - ID of overlay element (optional)
 */
function openModal(modalId, overlayId = null) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
    
    if (overlayId) {
        const overlay = document.getElementById(overlayId);
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }
}

/**
 * Close a modal
 * @param {string} modalId - ID of modal element
 * @param {string} overlayId - ID of overlay element (optional)
 */
function closeModal(modalId, overlayId = null) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    
    if (overlayId) {
        const overlay = document.getElementById(overlayId);
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
}

/**
 * Setup modal with open/close handlers
 * @param {Object} options - Configuration object
 * @param {string} options.modalId - ID of modal element
 * @param {string} options.overlayId - ID of overlay element
 * @param {string} options.closeButtonId - ID of close button
 * @param {Function} options.onOpen - Callback when modal opens
 * @param {Function} options.onClose - Callback when modal closes
 */
function setupModal(options) {
    const {
        modalId,
        overlayId,
        closeButtonId,
        onOpen,
        onClose
    } = options;
    
    const modal = document.getElementById(modalId);
    const overlay = overlayId ? document.getElementById(overlayId) : null;
    const closeButton = closeButtonId ? document.getElementById(closeButtonId) : null;
    
    if (!modal) return;
    
    // Close button handler
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            closeModal(modalId, overlayId);
            if (onClose) onClose();
        });
    }
    
    // Overlay click handler
    if (overlay) {
        overlay.addEventListener('click', () => {
            closeModal(modalId, overlayId);
            if (onClose) onClose();
        });
    }
    
    // Escape key handler
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal(modalId, overlayId);
            if (onClose) onClose();
        }
    });
    
    return {
        open: () => {
            openModal(modalId, overlayId);
            if (onOpen) onOpen();
        },
        close: () => {
            closeModal(modalId, overlayId);
            if (onClose) onClose();
        }
    };
}

// ============================================================================
// Form Validation Helpers
// ============================================================================

/**
 * Validate required field
 * @param {HTMLElement} field - Form field element
 * @param {string} errorMessage - Error message to display
 * @returns {boolean} True if valid, false otherwise
 */
function validateRequired(field, errorMessage = 'This field is required') {
    if (!field) return false;
    
    const value = field.value.trim();
    if (!value) {
        showFieldError(field, errorMessage);
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate email format
 * @param {HTMLElement} field - Email field element
 * @param {string} errorMessage - Error message to display
 * @returns {boolean} True if valid, false otherwise
 */
function validateEmail(field, errorMessage = 'Please enter a valid email address') {
    if (!field) return false;
    
    const value = field.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailRegex.test(value)) {
        showFieldError(field, errorMessage);
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate minimum length
 * @param {HTMLElement} field - Form field element
 * @param {number} minLength - Minimum length required
 * @param {string} errorMessage - Error message to display
 * @returns {boolean} True if valid, false otherwise
 */
function validateMinLength(field, minLength, errorMessage = null) {
    if (!field) return false;
    
    const value = field.value.trim();
    if (value.length < minLength) {
        const message = errorMessage || `Must be at least ${minLength} characters`;
        showFieldError(field, message);
        return false;
    }
    
    clearFieldError(field);
    return true;
}

/**
 * Validate form with multiple fields
 * @param {Array} validations - Array of validation objects
 * @returns {boolean} True if all validations pass, false otherwise
 * 
 * Example:
 * validateForm([
 *   { field: emailField, validator: validateEmail },
 *   { field: nameField, validator: validateRequired }
 * ])
 */
function validateForm(validations) {
    let isValid = true;
    
    validations.forEach(({ field, validator, ...args }) => {
        if (!validator(field, ...Object.values(args))) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Clear all field errors in a form
 * @param {HTMLFormElement} form - Form element
 */
function clearFormErrors(form) {
    if (!form) return;
    
    const fields = form.querySelectorAll('input, select, textarea');
    fields.forEach(field => clearFieldError(field));
}

// ============================================================================
// Stripe Helpers
// ============================================================================

/**
 * Create Stripe card element with EYT Gaming styling
 * @param {Object} stripe - Stripe instance
 * @param {Object} customStyle - Custom style overrides (optional)
 * @returns {Object} Stripe card element
 */
function createStyledCardElement(stripe, customStyle = {}) {
    const elements = stripe.elements();
    
    const defaultStyle = {
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
    
    const style = { ...defaultStyle, ...customStyle };
    return elements.create('card', { style });
}

/**
 * Setup Stripe card element with error handling
 * @param {Object} cardElement - Stripe card element
 * @param {string} mountElementId - ID of element to mount card to
 * @param {string} errorElementId - ID of element to display errors
 */
function setupCardElement(cardElement, mountElementId, errorElementId) {
    // Mount card element
    cardElement.mount(`#${mountElementId}`);
    
    // Handle real-time validation errors
    cardElement.on('change', function(event) {
        if (event.error) {
            showError(errorElementId, event.error.message, false);
        } else {
            clearError(errorElementId);
        }
    });
}

// ============================================================================
// AJAX Helpers
// ============================================================================

/**
 * Make AJAX request with error handling
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @returns {Promise} Response data or throws error
 */
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `Request failed with status ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Request error:', error);
        throw error;
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format currency amount
 * @param {number} amount - Amount in cents
 * @param {string} currency - Currency code (default: 'USD')
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount / 100);
}

/**
 * Debounce function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Redirect with delay
 * @param {string} url - URL to redirect to
 * @param {number} delay - Delay in milliseconds (default: 1500)
 */
function redirectWithDelay(url, delay = 1500) {
    setTimeout(() => {
        window.location.href = url;
    }, delay);
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCookie,
        getCSRFToken,
        setButtonLoading,
        setFormLoading,
        toggleSpinner,
        setPaymentFormLoading,
        showError,
        clearError,
        showFieldError,
        clearFieldError,
        showErrorToast,
        showSuccess,
        clearSuccess,
        showSuccessToast,
        showToast,
        openModal,
        closeModal,
        setupModal,
        validateRequired,
        validateEmail,
        validateMinLength,
        validateForm,
        clearFormErrors,
        createStyledCardElement,
        setupCardElement,
        makeRequest,
        formatCurrency,
        debounce,
        redirectWithDelay
    };
}
