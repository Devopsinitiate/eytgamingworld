/**
 * Gaming Ripple Effect
 * Creates a ripple animation effect on button clicks for gaming-styled buttons
 */

(function() {
    'use strict';

    /**
     * Creates a ripple effect at the click position
     * @param {MouseEvent} event - The click event
     */
    function createRipple(event) {
        const button = event.currentTarget;
        
        // Remove any existing ripple elements
        const existingRipple = button.querySelector('.ripple-effect');
        if (existingRipple) {
            existingRipple.remove();
        }

        // Create ripple element
        const ripple = document.createElement('span');
        ripple.classList.add('ripple-effect');

        // Calculate ripple position relative to button
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        // Set ripple size and position
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        // Add ripple to button
        button.appendChild(ripple);

        // Remove ripple after animation completes
        ripple.addEventListener('animationend', function() {
            ripple.remove();
        });
    }

    /**
     * Initialize ripple effect on all gaming buttons
     */
    function initRippleEffect() {
        // Select all gaming buttons that should have ripple effect
        const buttons = document.querySelectorAll(
            '.gaming-btn-primary, .gaming-btn-ghost, .gaming-btn-action, ' +
            'button[class*="gaming-btn"], button[onclick*="assign"], ' +
            'button[onclick*="show"], button[type="submit"]'
        );

        buttons.forEach(button => {
            // Ensure button has position relative for ripple positioning
            if (getComputedStyle(button).position === 'static') {
                button.style.position = 'relative';
            }

            // Ensure button has overflow hidden to contain ripple
            button.style.overflow = 'hidden';

            // Add click event listener
            button.addEventListener('click', createRipple);
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRippleEffect);
    } else {
        initRippleEffect();
    }

    // Re-initialize for dynamically added buttons
    // This is useful if buttons are added after page load
    window.reinitRippleEffect = initRippleEffect;

})();
