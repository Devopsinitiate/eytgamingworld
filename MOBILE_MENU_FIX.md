# Mobile Menu JavaScript Error Fix

## Issue
Console error when clicking mobile menu button on tournament pages:
```
Uncaught ReferenceError: toggleMobileMenu is not defined
at HTMLButtonElement.onclick (tournaments/:433:67)
```

## Root Cause
The mobile menu button in `base.html` was using an event listener approach, but some pages or cached versions might have inline `onclick="toggleMobileMenu()"` handlers that expected a global function to exist.

## Solution Applied
Added a global `toggleMobileMenu()` function to `base.html` that:
1. Toggles the mobile menu visibility
2. Updates the aria-expanded attribute
3. Works with both inline onclick handlers and event listeners

## Files Modified
- `templates/base.html` - Added global toggleMobileMenu function

## Changes Made

### templates/base.html
```javascript
// Global mobile menu toggle function (for inline onclick handlers)
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
    
    if (mobileMenuButton) {
        const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
        mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
    }
}

// Mobile menu toggle for base.html
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            toggleMobileMenu();
        });
    }
});
```

## Testing
1. Navigate to any tournament page
2. Click the mobile menu button (hamburger icon) on mobile view
3. Verify the menu opens/closes without console errors
4. Check that the menu works on all pages that extend base.html

## Status
✅ Fixed - The toggleMobileMenu function is now globally available and works with both inline onclick handlers and event listeners.
