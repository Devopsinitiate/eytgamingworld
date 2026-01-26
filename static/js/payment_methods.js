/**
 * Payment Methods Management JavaScript
 * Handles remove confirmation, set default, and AJAX operations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Modal elements
    const removeModal = document.getElementById('removeModal');
    const removeModalOverlay = document.getElementById('removeModalOverlay');
    const confirmRemoveBtn = document.getElementById('confirmRemove');
    const cancelRemoveBtn = document.getElementById('cancelRemove');
    
    let methodToRemove = null;
    
    // Remove button click handlers
    document.querySelectorAll('.remove-method-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            methodToRemove = this.dataset.methodId;
            openRemoveModal();
        });
    });
    
    // Set default button click handlers
    document.querySelectorAll('.set-default-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const methodId = this.dataset.methodId;
            setDefaultPaymentMethod(methodId, this);
        });
    });
    
    // Modal controls
    if (cancelRemoveBtn) {
        cancelRemoveBtn.addEventListener('click', closeRemoveModal);
    }
    
    if (removeModalOverlay) {
        removeModalOverlay.addEventListener('click', closeRemoveModal);
    }
    
    if (confirmRemoveBtn) {
        confirmRemoveBtn.addEventListener('click', function() {
            if (methodToRemove) {
                removePaymentMethod(methodToRemove);
            }
        });
    }
    
    // Open remove confirmation modal
    function openRemoveModal() {
        if (removeModal && removeModalOverlay) {
            removeModal.classList.remove('hidden');
            removeModalOverlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }
    
    // Close remove confirmation modal
    function closeRemoveModal() {
        if (removeModal && removeModalOverlay) {
            removeModal.classList.add('hidden');
            removeModalOverlay.classList.add('hidden');
            document.body.style.overflow = '';
            methodToRemove = null;
        }
    }
    
    // Remove payment method via AJAX
    async function removePaymentMethod(methodId) {
        const button = confirmRemoveBtn;
        
        // Show loading state
        setLoadingState(button, true);
        
        try {
            const response = await fetch(`/payments/methods/${methodId}/remove/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            });
            
            if (response.ok) {
                // Success - remove the card from UI
                const card = document.querySelector(`[data-method-id="${methodId}"]`).closest('.payment-method-card');
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        card.remove();
                        checkEmptyState();
                        showSuccessMessage('Payment method removed successfully');
                    }, 300);
                }
                closeRemoveModal();
            } else {
                showErrorMessage('Failed to remove payment method. Please try again.');
            }
        } catch (error) {
            console.error('Error removing payment method:', error);
            showErrorMessage('An error occurred. Please try again.');
        } finally {
            setLoadingState(button, false);
        }
    }
    
    // Set default payment method via AJAX
    async function setDefaultPaymentMethod(methodId, button) {
        // Show loading state
        setLoadingState(button, true);
        
        try {
            const response = await fetch(`/payments/methods/${methodId}/set-default/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            });
            
            if (response.ok) {
                // Success - update UI
                updateDefaultBadges(methodId);
                showSuccessMessage('Default payment method updated');
            } else {
                showErrorMessage('Failed to set default payment method. Please try again.');
            }
        } catch (error) {
            console.error('Error setting default payment method:', error);
            showErrorMessage('An error occurred. Please try again.');
        } finally {
            setLoadingState(button, false);
        }
    }
    
    // Update default badges in UI
    function updateDefaultBadges(newDefaultId) {
        // Remove all default badges
        document.querySelectorAll('.default-badge').forEach(badge => {
            badge.remove();
        });
        
        // Hide all "Set as Default" buttons
        document.querySelectorAll('.set-default-btn').forEach(btn => {
            btn.classList.remove('hidden');
        });
        
        // Add default badge to new default method
        const newDefaultCard = document.querySelector(`[data-method-id="${newDefaultId}"]`).closest('.payment-method-card');
        if (newDefaultCard) {
            const cardHeader = newDefaultCard.querySelector('.card-header');
            const badge = document.createElement('span');
            badge.className = 'default-badge px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded-full';
            badge.textContent = 'Default';
            cardHeader.appendChild(badge);
            
            // Hide "Set as Default" button for this card
            const setDefaultBtn = newDefaultCard.querySelector('.set-default-btn');
            if (setDefaultBtn) {
                setDefaultBtn.classList.add('hidden');
            }
        }
    }
    
    // Check if payment methods list is empty and show empty state
    function checkEmptyState() {
        const methodsList = document.getElementById('paymentMethodsList');
        const emptyState = document.getElementById('emptyState');
        const cards = methodsList?.querySelectorAll('.payment-method-card');
        
        if (cards && cards.length === 0) {
            if (methodsList) methodsList.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
        }
    }
    
    // Set loading state on button
    function setLoadingState(button, isLoading) {
        if (!button) return;
        
        if (isLoading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = '<span class="inline-block animate-spin mr-2">⏳</span> Processing...';
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || button.textContent;
        }
    }
    
    // Show success message
    function showSuccessMessage(message) {
        showMessage(message, 'success');
    }
    
    // Show error message
    function showErrorMessage(message) {
        showMessage(message, 'error');
    }
    
    // Show message toast
    function showMessage(message, type) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-0 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(400px)';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    }
});
