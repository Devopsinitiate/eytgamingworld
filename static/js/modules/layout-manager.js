/**
 * Layout Manager for Tournament Detail Page
 * Handles component positioning, breadcrumb alignment, and responsive layout
 */

class LayoutManager {
    constructor(config = {}) {
        this.config = {
            debug: false,
            breakpoints: {
                mobile: 768,
                tablet: 1024,
                desktop: 1200
            },
            spacing: {
                xs: '0.25rem',
                sm: '0.5rem',
                md: '1rem',
                lg: '1.5rem',
                xl: '2rem'
            },
            ...config
        };
        
        this.components = new Set();
        this.alignmentRules = new Map();
        this.resizeObserver = null;
        this.mediaQueries = new Map();
        
        this.init();
    }
    
    init() {
        this.log('LayoutManager initialized');
        
        // Set up responsive layout handling
        this.setupResponsiveLayout();
        
        // Set up resize observer for dynamic adjustments
        this.setupResizeObserver();
        
        // Initialize alignment rules
        this.setupAlignmentRules();
        
        // Auto-fix existing breadcrumbs
        this.alignBreadcrumbs();
    }
    
    /**
     * Fix breadcrumb navigation alignment
     * Addresses Requirements 3.1, 3.2, 3.3, 3.4, 3.5
     */
    alignBreadcrumbs() {
        const breadcrumbs = document.querySelectorAll('.breadcrumbs, nav[aria-label*="Breadcrumb"]');
        
        breadcrumbs.forEach(breadcrumb => {
            this.fixBreadcrumbLayout(breadcrumb);
            this.components.add(breadcrumb);
        });
        
        this.log(`Aligned ${breadcrumbs.length} breadcrumb components`);
    }
    
    /**
     * Fix individual breadcrumb layout
     */
    fixBreadcrumbLayout(breadcrumb) {
        const ol = breadcrumb.querySelector('ol, ul');
        if (!ol) return;
        
        // Apply CSS Grid and Flexbox alignment strategies
        this.applyBreadcrumbStyles(breadcrumb, ol);
        
        // Fix separator spacing and vertical alignment
        this.fixSeparatorAlignment(ol);
        
        // Handle responsive layout
        this.applyResponsiveBreadcrumbLayout(breadcrumb);
        
        // Ensure proper wrapping behavior
        this.setupBreadcrumbWrapping(ol);
    }
    
    /**
     * Apply breadcrumb styles using CSS Grid and Flexbox
     */
    applyBreadcrumbStyles(breadcrumb, ol) {
        // Apply styles to the breadcrumb container
        const breadcrumbStyles = {
            display: 'block',
            width: '100%',
            overflow: 'hidden',
            boxSizing: 'border-box'
        };
        
        Object.assign(breadcrumb.style, breadcrumbStyles);
        
        // Apply flexbox layout to the list with explicit gap handling
        const listStyles = {
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            margin: '0',
            padding: '0',
            listStyle: 'none',
            lineHeight: '1.5',
            boxSizing: 'border-box'
        };
        
        // Use margin-based spacing instead of gap for better browser support
        Object.assign(ol.style, listStyles);
        
        // Style list items with consistent spacing
        const listItems = ol.querySelectorAll('li');
        listItems.forEach((li, index) => {
            const itemStyles = {
                display: 'flex',
                alignItems: 'center',
                margin: '0',
                padding: '0',
                whiteSpace: 'nowrap',
                boxSizing: 'border-box'
            };
            
            // Add right margin for spacing (except last item)
            if (index < listItems.length - 1) {
                itemStyles.marginRight = '8px'; // Explicit 8px spacing
            }
            
            Object.assign(li.style, itemStyles);
        });
    }
    
    /**
     * Fix separator spacing and vertical alignment
     */
    fixSeparatorAlignment(ol) {
        const separators = ol.querySelectorAll('li[aria-hidden="true"] span, li span.text-gray-400');
        
        separators.forEach(separator => {
            const separatorStyles = {
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '1rem',
                height: '1.5rem', // Match line height
                color: '#9ca3af', // text-gray-400
                fontSize: '0.875rem',
                lineHeight: '1.5', // Match parent line height
                userSelect: 'none',
                flexShrink: '0',
                textAlign: 'center'
            };
            
            Object.assign(separator.style, separatorStyles);
            
            // Ensure separator parent is properly aligned
            const parentLi = separator.closest('li');
            if (parentLi) {
                const parentStyles = {
                    display: 'flex',
                    alignItems: 'center',
                    height: '1.5rem', // Consistent height
                    lineHeight: '1.5',
                    flexShrink: '0'
                };
                Object.assign(parentLi.style, parentStyles);
            }
        });
        
        // Also fix links to have consistent height
        const links = ol.querySelectorAll('a');
        links.forEach(link => {
            const linkStyles = {
                display: 'inline-flex',
                alignItems: 'center',
                height: '1.5rem', // Match separator height
                lineHeight: '1.5',
                textDecoration: 'none',
                color: 'inherit'
            };
            Object.assign(link.style, linkStyles);
        });
        
        // Fix current page spans
        const currentSpans = ol.querySelectorAll('span[aria-current="page"]');
        currentSpans.forEach(span => {
            const spanStyles = {
                display: 'inline-flex',
                alignItems: 'center',
                height: '1.5rem',
                lineHeight: '1.5'
            };
            Object.assign(span.style, spanStyles);
        });
    }
    
    /**
     * Apply responsive breadcrumb layout
     */
    applyResponsiveBreadcrumbLayout(breadcrumb) {
        const currentViewport = this.getCurrentViewport();
        
        // Mobile-specific adjustments
        if (currentViewport === 'mobile') {
            this.applyMobileBreadcrumbLayout(breadcrumb);
        }
        // Tablet-specific adjustments
        else if (currentViewport === 'tablet') {
            this.applyTabletBreadcrumbLayout(breadcrumb);
        }
        // Desktop-specific adjustments
        else {
            this.applyDesktopBreadcrumbLayout(breadcrumb);
        }
    }
    
    /**
     * Mobile breadcrumb layout (< 768px)
     */
    applyMobileBreadcrumbLayout(breadcrumb) {
        const mobileStyles = {
            padding: '0.75rem 1rem',
            fontSize: '0.875rem',
            boxSizing: 'border-box'
        };
        
        Object.assign(breadcrumb.style, mobileStyles);
        
        const ol = breadcrumb.querySelector('ol, ul');
        if (ol) {
            // Adjust spacing for mobile - use smaller margins
            const listItems = ol.querySelectorAll('li');
            listItems.forEach((li, index) => {
                if (index < listItems.length - 1) {
                    li.style.marginRight = '6px'; // Smaller gap on mobile
                }
            });
            
            // Make links more touch-friendly
            const links = ol.querySelectorAll('a');
            links.forEach(link => {
                const linkStyles = {
                    minHeight: '44px', // Touch-friendly minimum
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '0.5rem 0.25rem',
                    borderRadius: '0.25rem',
                    transition: 'all 0.2s ease',
                    boxSizing: 'border-box'
                };
                
                Object.assign(link.style, linkStyles);
            });
            
            // Adjust separators for mobile
            const separators = ol.querySelectorAll('li[aria-hidden="true"] span');
            separators.forEach(separator => {
                separator.style.fontSize = '0.75rem';
                separator.style.width = '0.75rem';
            });
        }
    }
    
    /**
     * Tablet breadcrumb layout (768px - 1024px)
     */
    applyTabletBreadcrumbLayout(breadcrumb) {
        const tabletStyles = {
            padding: '1rem 1.5rem',
            fontSize: '0.875rem',
            boxSizing: 'border-box'
        };
        
        Object.assign(breadcrumb.style, tabletStyles);
        
        const ol = breadcrumb.querySelector('ol, ul');
        if (ol) {
            // Standard spacing for tablet
            const listItems = ol.querySelectorAll('li');
            listItems.forEach((li, index) => {
                if (index < listItems.length - 1) {
                    li.style.marginRight = '8px'; // Standard 8px gap
                }
            });
        }
    }
    
    /**
     * Desktop breadcrumb layout (> 1024px)
     */
    applyDesktopBreadcrumbLayout(breadcrumb) {
        const desktopStyles = {
            padding: '1.5rem 2rem',
            fontSize: '1rem',
            boxSizing: 'border-box'
        };
        
        Object.assign(breadcrumb.style, desktopStyles);
        
        const ol = breadcrumb.querySelector('ol, ul');
        if (ol) {
            // Standard spacing for desktop
            const listItems = ol.querySelectorAll('li');
            listItems.forEach((li, index) => {
                if (index < listItems.length - 1) {
                    li.style.marginRight = '8px'; // Standard 8px gap
                }
            });
        }
    }
    
    /**
     * Setup breadcrumb wrapping behavior
     */
    setupBreadcrumbWrapping(ol) {
        // Ensure proper wrapping without breaking layout
        const wrappingStyles = {
            flexWrap: 'wrap',
            alignItems: 'center',
            alignContent: 'flex-start', // Align wrapped rows to start
            boxSizing: 'border-box'
        };
        
        Object.assign(ol.style, wrappingStyles);
        
        // Add CSS class for additional styling
        ol.classList.add('breadcrumb-list');
        
        // Inject CSS for better wrapping behavior
        this.injectBreadcrumbCSS();
        
        // Force layout recalculation
        ol.offsetHeight; // Trigger reflow
    }
    
    /**
     * Inject CSS for breadcrumb styling
     */
    injectBreadcrumbCSS() {
        const styleId = 'layout-manager-breadcrumb-styles';
        
        // Don't inject if already exists
        if (document.getElementById(styleId)) {
            return;
        }
        
        const css = `
            .breadcrumb-list {
                /* Ensure consistent alignment across all items */
                align-items: center !important;
                
                /* Handle text overflow gracefully */
                word-break: break-word;
                overflow-wrap: break-word;
                
                /* Force consistent line height */
                line-height: 1.5 !important;
            }
            
            .breadcrumb-list li {
                /* Ensure all list items align properly */
                display: flex !important;
                align-items: center !important;
                
                /* Prevent awkward breaks */
                min-width: 0;
                
                /* Consistent height for alignment */
                height: 1.5rem;
                line-height: 1.5;
                box-sizing: border-box;
            }
            
            .breadcrumb-list li a,
            .breadcrumb-list li span {
                /* Consistent vertical alignment */
                display: inline-flex !important;
                align-items: center !important;
                
                /* Consistent height */
                height: 1.5rem;
                line-height: 1.5;
                
                /* Prevent text from breaking layout */
                max-width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
                box-sizing: border-box;
            }
            
            /* Mobile-specific breadcrumb improvements */
            @media (max-width: 767px) {
                .breadcrumb-list li {
                    margin-right: 6px !important;
                }
                
                .breadcrumb-list li:last-child {
                    margin-right: 0 !important;
                }
                
                .breadcrumb-list li a {
                    min-height: 44px;
                    padding: 0.5rem 0.25rem;
                    height: auto;
                }
                
                /* Allow longer breadcrumb items to wrap on mobile */
                .breadcrumb-list li:last-child span {
                    white-space: normal;
                    word-break: break-word;
                    line-height: 1.4;
                    height: auto;
                }
                
                .breadcrumb-list li[aria-hidden="true"] span {
                    font-size: 0.75rem;
                    width: 0.75rem;
                }
            }
            
            /* Tablet-specific improvements */
            @media (min-width: 768px) and (max-width: 1023px) {
                .breadcrumb-list li {
                    margin-right: 8px !important;
                }
                
                .breadcrumb-list li:last-child {
                    margin-right: 0 !important;
                }
            }
            
            /* Desktop-specific improvements */
            @media (min-width: 1024px) {
                .breadcrumb-list li {
                    margin-right: 8px !important;
                }
                
                .breadcrumb-list li:last-child {
                    margin-right: 0 !important;
                }
            }
            
            /* Focus and hover states for accessibility */
            .breadcrumb-list li a:focus-visible {
                outline: 2px solid #3b82f6;
                outline-offset: 2px;
                border-radius: 0.25rem;
            }
            
            .breadcrumb-list li a:hover {
                color: #d1d5db !important;
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 0.25rem;
            }
            
            /* Separator improvements */
            .breadcrumb-list li[aria-hidden="true"] {
                flex-shrink: 0;
                margin-right: 8px !important;
            }
            
            .breadcrumb-list li[aria-hidden="true"] span {
                width: 1rem;
                height: 1.5rem;
                text-align: center;
                user-select: none;
                pointer-events: none;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
        `;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = css;
        document.head.appendChild(style);
        
        this.log('Breadcrumb CSS injected');
    }
    
    /**
     * Setup responsive layout handling with media queries
     */
    setupResponsiveLayout() {
        // Check if matchMedia is available (not available in JSDOM)
        if (typeof window.matchMedia !== 'function') {
            this.log('matchMedia not available, skipping responsive setup');
            return;
        }
        
        // Create media query listeners
        const mobileQuery = window.matchMedia(`(max-width: ${this.config.breakpoints.mobile - 1}px)`);
        const tabletQuery = window.matchMedia(`(min-width: ${this.config.breakpoints.mobile}px) and (max-width: ${this.config.breakpoints.tablet - 1}px)`);
        const desktopQuery = window.matchMedia(`(min-width: ${this.config.breakpoints.tablet}px)`);
        
        // Store queries for later use
        this.mediaQueries.set('mobile', mobileQuery);
        this.mediaQueries.set('tablet', tabletQuery);
        this.mediaQueries.set('desktop', desktopQuery);
        
        // Add listeners
        mobileQuery.addListener(() => this.handleViewportChange());
        tabletQuery.addListener(() => this.handleViewportChange());
        desktopQuery.addListener(() => this.handleViewportChange());
        
        this.log('Responsive layout handlers set up');
    }
    
    /**
     * Handle viewport changes
     */
    handleViewportChange() {
        this.log('Viewport changed, re-aligning components');
        
        // Re-align all breadcrumbs
        this.components.forEach(component => {
            if (component.classList.contains('breadcrumbs') || component.getAttribute('aria-label')?.includes('Breadcrumb')) {
                this.fixBreadcrumbLayout(component);
            }
        });
    }
    
    /**
     * Setup resize observer for dynamic adjustments
     */
    setupResizeObserver() {
        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    if (this.components.has(entry.target)) {
                        this.validateAlignment(entry.target);
                    }
                });
            });
            
            this.log('ResizeObserver set up');
        } else {
            this.log('ResizeObserver not available, skipping setup');
        }
    }
    
    /**
     * Validate alignment of a component
     */
    validateAlignment(component) {
        if (component.classList.contains('breadcrumbs') || component.getAttribute('aria-label')?.includes('Breadcrumb')) {
            const ol = component.querySelector('ol, ul');
            if (ol) {
                const items = ol.querySelectorAll('li');
                const isAligned = this.checkVerticalAlignment(Array.from(items));
                
                if (!isAligned) {
                    this.log('Alignment issue detected, fixing...');
                    this.fixBreadcrumbLayout(component);
                }
            }
        }
    }
    
    /**
     * Check vertical alignment of elements
     */
    checkVerticalAlignment(elements) {
        if (elements.length < 2) return true;
        
        const firstTop = elements[0].getBoundingClientRect().top;
        const tolerance = 2; // 2px tolerance
        
        return elements.every(element => {
            const elementTop = element.getBoundingClientRect().top;
            return Math.abs(elementTop - firstTop) <= tolerance;
        });
    }
    
    /**
     * Get current viewport size category
     */
    getCurrentViewport() {
        const width = window.innerWidth;
        
        if (width < this.config.breakpoints.mobile) {
            return 'mobile';
        } else if (width < this.config.breakpoints.tablet) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }
    
    /**
     * Setup alignment rules for different component types
     */
    setupAlignmentRules() {
        // Breadcrumb alignment rules
        this.alignmentRules.set('breadcrumbs', {
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            flexWrap: 'wrap'
        });
        
        this.log('Alignment rules configured');
    }
    
    /**
     * Add a component to be managed
     */
    addComponent(component, type = 'generic') {
        this.components.add(component);
        
        if (this.resizeObserver) {
            this.resizeObserver.observe(component);
        }
        
        // Apply type-specific alignment
        if (type === 'breadcrumb') {
            this.fixBreadcrumbLayout(component);
        }
        
        this.log(`Added component: ${type}`);
    }
    
    /**
     * Remove a component from management
     */
    removeComponent(component) {
        this.components.delete(component);
        
        if (this.resizeObserver) {
            this.resizeObserver.unobserve(component);
        }
        
        this.log('Removed component');
    }
    
    /**
     * Force re-alignment of all components
     */
    realignAll() {
        this.log('Force re-aligning all components');
        
        this.components.forEach(component => {
            if (component.classList.contains('breadcrumbs') || component.getAttribute('aria-label')?.includes('Breadcrumb')) {
                this.fixBreadcrumbLayout(component);
            }
        });
    }
    
    /**
     * Logging utility
     */
    log(...args) {
        if (this.config.debug) {
            console.log('[LayoutManager]', ...args);
        }
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        // Disconnect resize observer
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
        
        // Remove media query listeners
        if (typeof window.matchMedia === 'function') {
            this.mediaQueries.forEach((query, name) => {
                query.removeListener(this.handleViewportChange);
            });
        }
        this.mediaQueries.clear();
        
        // Clear components
        this.components.clear();
        this.alignmentRules.clear();
        
        // Remove injected styles
        const injectedStyle = document.getElementById('layout-manager-breadcrumb-styles');
        if (injectedStyle) {
            injectedStyle.remove();
        }
        
        this.log('LayoutManager destroyed');
    }
}

// Create global instance
window.LayoutManager = LayoutManager;

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.layoutManagerInstance) {
        window.layoutManagerInstance = new LayoutManager({ debug: true });
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.layoutManagerInstance) {
        window.layoutManagerInstance.destroy();
    }
});

// Make available globally instead of using ES6 export
window.LayoutManager = LayoutManager;