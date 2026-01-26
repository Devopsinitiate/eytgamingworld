/**
 * Accessibility JavaScript
 * Requirements: 15.1 - Keyboard navigation and focus management
 */

/**
 * Focus Trap for Modals
 * Traps keyboard focus within a modal dialog
 */
class FocusTrap {
    constructor(element) {
        this.element = element;
        this.focusableElements = null;
        this.firstFocusableElement = null;
        this.lastFocusableElement = null;
        this.previouslyFocusedElement = null;
    }

    /**
     * Get all focusable elements within the container
     */
    getFocusableElements() {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'textarea:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(', ');

        return this.element.querySelectorAll(focusableSelectors);
    }

    /**
     * Activate the focus trap
     */
    activate() {
        // Store the currently focused element
        this.previouslyFocusedElement = document.activeElement;

        // Get all focusable elements
        this.focusableElements = this.getFocusableElements();
        
        if (this.focusableElements.length === 0) {
            return;
        }

        this.firstFocusableElement = this.focusableElements[0];
        this.lastFocusableElement = this.focusableElements[this.focusableElements.length - 1];

        // Add event listener for tab key
        this.element.addEventListener('keydown', this.handleKeyDown.bind(this));

        // Focus the first element
        this.firstFocusableElement.focus();

        // Add modal-open class to body
        document.body.classList.add('modal-open');
    }

    /**
     * Deactivate the focus trap
     */
    deactivate() {
        // Remove event listener
        this.element.removeEventListener('keydown', this.handleKeyDown.bind(this));

        // Restore focus to previously focused element
        if (this.previouslyFocusedElement) {
            this.previouslyFocusedElement.focus();
        }

        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
    }

    /**
     * Handle keyboard navigation within the trap
     */
    handleKeyDown(event) {
        const isTabPressed = event.key === 'Tab';
        const isEscapePressed = event.key === 'Escape';

        // Handle Escape key to close modal
        if (isEscapePressed) {
            this.deactivate();
            // Trigger close event
            const closeEvent = new CustomEvent('modal:close');
            this.element.dispatchEvent(closeEvent);
            return;
        }

        if (!isTabPressed) {
            return;
        }

        // If shift + tab (going backwards)
        if (event.shiftKey) {
            if (document.activeElement === this.firstFocusableElement) {
                this.lastFocusableElement.focus();
                event.preventDefault();
            }
        } else {
            // If tab (going forward)
            if (document.activeElement === this.lastFocusableElement) {
                this.firstFocusableElement.focus();
                event.preventDefault();
            }
        }
    }
}

/**
 * Initialize focus traps for all modals
 */
function initializeFocusTraps() {
    const modals = document.querySelectorAll('[role="dialog"], .modal-container');
    
    modals.forEach(modal => {
        const focusTrap = new FocusTrap(modal);
        
        // Store focus trap instance on the element
        modal.focusTrap = focusTrap;
        
        // Activate when modal is shown
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'class') {
                    const isVisible = !modal.classList.contains('hidden') && 
                                    modal.style.display !== 'none';
                    
                    if (isVisible) {
                        focusTrap.activate();
                    } else {
                        focusTrap.deactivate();
                    }
                }
            });
        });
        
        observer.observe(modal, { attributes: true });
    });
}

/**
 * Keyboard Navigation Helpers
 */

/**
 * Add keyboard navigation to custom dropdowns
 */
function initializeDropdownKeyboardNav() {
    const dropdowns = document.querySelectorAll('[role="menu"]');
    
    dropdowns.forEach(dropdown => {
        const items = dropdown.querySelectorAll('[role="menuitem"]');
        let currentIndex = -1;
        
        dropdown.addEventListener('keydown', (event) => {
            switch (event.key) {
                case 'ArrowDown':
                    event.preventDefault();
                    currentIndex = (currentIndex + 1) % items.length;
                    items[currentIndex].focus();
                    break;
                    
                case 'ArrowUp':
                    event.preventDefault();
                    currentIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
                    items[currentIndex].focus();
                    break;
                    
                case 'Home':
                    event.preventDefault();
                    currentIndex = 0;
                    items[currentIndex].focus();
                    break;
                    
                case 'End':
                    event.preventDefault();
                    currentIndex = items.length - 1;
                    items[currentIndex].focus();
                    break;
                    
                case 'Escape':
                    event.preventDefault();
                    // Close dropdown
                    dropdown.classList.add('hidden');
                    break;
            }
        });
    });
}

/**
 * Add keyboard navigation to tabs
 */
function initializeTabKeyboardNav() {
    const tabLists = document.querySelectorAll('[role="tablist"]');
    
    tabLists.forEach(tabList => {
        const tabs = tabList.querySelectorAll('[role="tab"]');
        let currentIndex = 0;
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('keydown', (event) => {
                switch (event.key) {
                    case 'ArrowLeft':
                        event.preventDefault();
                        currentIndex = index === 0 ? tabs.length - 1 : index - 1;
                        tabs[currentIndex].focus();
                        tabs[currentIndex].click();
                        break;
                        
                    case 'ArrowRight':
                        event.preventDefault();
                        currentIndex = (index + 1) % tabs.length;
                        tabs[currentIndex].focus();
                        tabs[currentIndex].click();
                        break;
                        
                    case 'Home':
                        event.preventDefault();
                        tabs[0].focus();
                        tabs[0].click();
                        break;
                        
                    case 'End':
                        event.preventDefault();
                        tabs[tabs.length - 1].focus();
                        tabs[tabs.length - 1].click();
                        break;
                }
            });
        });
    });
}

/**
 * Ensure logical tab order
 * Automatically set tabindex for elements that should be in tab order
 */
function ensureLogicalTabOrder() {
    // Interactive elements that should be in tab order
    const interactiveElements = document.querySelectorAll(
        'button, a[href], input, select, textarea, [role="button"], [role="link"]'
    );
    
    interactiveElements.forEach(element => {
        // Skip if already has tabindex
        if (element.hasAttribute('tabindex')) {
            return;
        }
        
        // Skip if disabled
        if (element.disabled || element.getAttribute('aria-disabled') === 'true') {
            element.setAttribute('tabindex', '-1');
            return;
        }
        
        // Ensure element is in tab order
        if (!element.hasAttribute('tabindex')) {
            element.setAttribute('tabindex', '0');
        }
    });
}

/**
 * Initialize all accessibility features
 */
function initializeAccessibility() {
    // Initialize focus traps
    initializeFocusTraps();
    
    // Initialize keyboard navigation
    initializeDropdownKeyboardNav();
    initializeTabKeyboardNav();
    
    // Ensure logical tab order
    ensureLogicalTabOrder();
    
    console.log('Accessibility features initialized');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAccessibility);
} else {
    initializeAccessibility();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        FocusTrap,
        initializeFocusTraps,
        initializeDropdownKeyboardNav,
        initializeTabKeyboardNav,
        ensureLogicalTabOrder
    };
}
