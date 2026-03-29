/**
 * Performance Optimizations for Manage Participant Page
 * 
 * This module implements:
 * 1. Debounced search input (300ms delay)
 * 2. Viewport-based neon glow effect limiting using Intersection Observer
 * 3. Lazy loading support for participant avatars
 */

// ==========================================
// DEBOUNCED SEARCH (Requirement 10.4)
// ==========================================

/**
 * Debounce function - delays execution until after wait time has elapsed
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
 * Search functionality with debouncing
 * Filters table rows based on search term with 300ms delay
 */
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    // Search function that filters table rows
    const performSearch = (searchTerm) => {
        const rows = document.querySelectorAll('tbody tr');
        const lowerSearchTerm = searchTerm.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(lowerSearchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    };

    // Create debounced version with 300ms delay (Requirement 10.4)
    const debouncedSearch = debounce(performSearch, 300);

    // Attach debounced search to input event
    searchInput.addEventListener('input', function(e) {
        debouncedSearch(e.target.value);
    });
}

// ==========================================
// VIEWPORT-BASED GLOW EFFECTS (Requirement 10.5)
// ==========================================

/**
 * Manages neon glow effects based on viewport visibility
 * Uses Intersection Observer API to disable glows for off-screen elements
 */
function initializeViewportGlowOptimization() {
    // Elements that have glow effects
    const glowSelectors = [
        '.gaming-stat-card',
        '.gaming-table tbody tr',
        '.gaming-seed-badge',
        '.gaming-status-dot.checked-in',
        '.gaming-status-dot.pending',
        '.gaming-status-dot.confirmed',
        '.gaming-status-dot.disqualified',
        '.gaming-btn-primary',
        '.gaming-btn-ghost',
        '.gaming-btn-action'
    ];

    // Create a single observer for all glow elements
    const observerOptions = {
        root: null, // viewport
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0 // Trigger as soon as any part is visible
    };

    const glowObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Element is in viewport - enable glow
                entry.target.classList.add('glow-enabled');
                entry.target.classList.remove('glow-disabled');
            } else {
                // Element is out of viewport - disable glow
                entry.target.classList.add('glow-disabled');
                entry.target.classList.remove('glow-enabled');
            }
        });
    }, observerOptions);

    // Observe all elements with glow effects
    glowSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            glowObserver.observe(element);
        });
    });

    // Return observer for cleanup if needed
    return glowObserver;
}

// ==========================================
// LAZY LOADING SUPPORT (Requirement 10.3)
// ==========================================

/**
 * Initializes lazy loading for participant avatars
 * Adds loading="lazy" attribute and placeholder styling
 */
function initializeLazyLoading() {
    const avatarImages = document.querySelectorAll('tbody img[src]');
    
    avatarImages.forEach(img => {
        // Add lazy loading attribute if not already present
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }

        // Add placeholder class while loading
        img.classList.add('avatar-loading');

        // Remove placeholder class when loaded
        img.addEventListener('load', function() {
            this.classList.remove('avatar-loading');
            this.classList.add('avatar-loaded');
        });

        // Handle loading errors
        img.addEventListener('error', function() {
            this.classList.remove('avatar-loading');
            this.classList.add('avatar-error');
        });
    });
}

// ==========================================
// INITIALIZATION
// ==========================================

/**
 * Initialize all performance optimizations when DOM is ready
 */
function initializePerformanceOptimizations() {
    // Initialize debounced search
    initializeSearch();

    // Initialize viewport-based glow optimization
    initializeViewportGlowOptimization();

    // Initialize lazy loading for avatars
    initializeLazyLoading();

    console.log('Performance optimizations initialized');
}

// Run when DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePerformanceOptimizations);
} else {
    // DOM is already loaded
    initializePerformanceOptimizations();
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        initializeSearch,
        initializeViewportGlowOptimization,
        initializeLazyLoading,
        initializePerformanceOptimizations
    };
}
