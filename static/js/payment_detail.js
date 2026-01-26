/**
 * Payment Detail Page JavaScript
 * Handles refund modal and refund request functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const refundModal = document.getElementById('refund-modal');
    const requestRefundBtn = document.getElementById('request-refund-btn');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelRefundBtn = document.getElementById('cancel-refund-btn');
    const refundForm = document.getElementById('refund-form');
    const refundReasonInput = document.getElementById('refund-reason');
    const confirmRefundBtn = document.getElementById('confirm-refund-btn');
    const refundSpinner = document.getElementById('refund-spinner');
    const refundBtnText = document.getElementById('refund-btn-text');

    // Open refund modal
    if (requestRefundBtn) {
        requestRefundBtn.addEventListener('click', function() {
            openRefundModal();
        });
    }

    // Close modal handlers
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            closeRefundModal();
        });
    }

    if (cancelRefundBtn) {
        cancelRefundBtn.addEventListener('click', function() {
            closeRefundModal();
        });
    }

    // Close modal when clicking outside
    if (refundModal) {
        refundModal.addEventListener('click', function(e) {
            if (e.target === refundModal) {
                closeRefundModal();
            }
        });
    }

    // Close modal on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && refundModal && refundModal.classList.contains('active')) {
            closeRefundModal();
        }
    });

    // Handle refund form submission
    if (refundForm) {
        refundForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleRefundSubmit();
        });
    }

    // Validate reason input
    if (refundReasonInput) {
        refundReasonInput.addEventListener('input', function() {
            validateReasonInput();
        });
    }

    /**
     * Open the refund modal
     */
    function openRefundModal() {
        if (refundModal) {
            refundModal.classList.add('active');
            // Focus on the reason input
            if (refundReasonInput) {
                setTimeout(() => {
                    refundReasonInput.focus();
                }, 100);
            }
        }
    }

    /**
     * Close the refund modal
     */
    function closeRefundModal() {
        if (refundModal) {
            refundModal.classList.remove('active');
            // Reset form
            if (refundForm) {
                refundForm.reset();
            }
            // Reset loading state
            setLoadingState(false);
        }
    }

    /**
     * Validate the reason input
     */
    function validateReasonInput() {
        if (!refundReasonInput || !confirmRefundBtn) return;

        const reason = refundReasonInput.value.trim();
        const isValid = reason.length >= 10;

        // Enable/disable submit button based on validation
        confirmRefundBtn.disabled = !isValid;
    }

    /**
     * Handle refund form submission
     */
    async function handleRefundSubmit() {
        // Validate reason
        const reason = refundReasonInput.value.trim();
        if (reason.length < 10) {
            showError('Please provide a reason with at least 10 characters');
            return;
        }

        // Set loading state
        setLoadingState(true);

        try {
            // Get form data
            const formData = new FormData(refundForm);
            const formAction = refundForm.action;

            // Submit the form via fetch
            const response = await fetch(formAction, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                // Success - reload the page to show updated payment status
                showSuccess('Refund processed successfully. Reloading...');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Error response
                const data = await response.json().catch(() => ({}));
                showError(data.error || 'Failed to process refund. Please try again.');
                setLoadingState(false);
            }
        } catch (error) {
            console.error('Refund request error:', error);
            showError('Network error. Please check your connection and try again.');
            setLoadingState(false);
        }
    }

    /**
     * Set loading state for the refund button
     */
    function setLoadingState(loading) {
        if (!confirmRefundBtn || !refundSpinner || !refundBtnText) return;

        if (loading) {
            confirmRefundBtn.disabled = true;
            refundSpinner.classList.remove('hidden');
            refundBtnText.textContent = 'Processing...';
            if (cancelRefundBtn) {
                cancelRefundBtn.disabled = true;
            }
        } else {
            confirmRefundBtn.disabled = false;
            refundSpinner.classList.add('hidden');
            refundBtnText.textContent = 'Confirm Refund';
            if (cancelRefundBtn) {
                cancelRefundBtn.disabled = false;
            }
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        // Create or update error message element
        let errorDiv = refundForm.querySelector('.error-message');
        
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message mb-4 p-4 bg-red-900/20 border border-red-800 text-red-200 rounded-lg flex items-center gap-3';
            errorDiv.innerHTML = `
                <span class="material-symbols-outlined">error</span>
                <span class="error-text"></span>
            `;
            refundForm.insertBefore(errorDiv, refundForm.firstChild);
        }

        const errorText = errorDiv.querySelector('.error-text');
        if (errorText) {
            errorText.textContent = message;
        }

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv && errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    /**
     * Show success message
     */
    function showSuccess(message) {
        // Create or update success message element
        let successDiv = refundForm.querySelector('.success-message');
        
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.className = 'success-message mb-4 p-4 bg-green-900/20 border border-green-800 text-green-200 rounded-lg flex items-center gap-3';
            successDiv.innerHTML = `
                <span class="material-symbols-outlined">check_circle</span>
                <span class="success-text"></span>
            `;
            refundForm.insertBefore(successDiv, refundForm.firstChild);
        }

        const successText = successDiv.querySelector('.success-text');
        if (successText) {
            successText.textContent = message;
        }
    }
});
