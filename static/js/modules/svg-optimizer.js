/**
 * SVG Optimization System
 * Handles dynamic resizing and optimization of SVG elements based on context and viewport
 */

class SVGOptimizer {
    constructor() {
        this.observers = new Map();
        this.breakpoints = {
            mobile: 768,
            tablet: 1024,
            desktop: 1200
        };
        
        // Context-based sizing rules
        this.contextRules = {
            'icon': {
                maxWidth: 24,
                maxHeight: 24,
                minWidth: 16,
                minHeight: 16,
                unit: 'px'
            },
            'decorative': {
                maxWidth: 20,
                minWidth: 100,
                unit: 'vw',
                fallbackUnit: 'px',
                maintainAspectRatio: true
            },
            'illustration': {
                maxWidth: 40,
                minWidth: 200,
                unit: 'vw',
                fallbackUnit: 'px',
                responsive: true,
                maintainAspectRatio: true
            },
            'default': {
                maxWidth: 100,
                maxHeight: 100,
                unit: 'px',
                maintainAspectRatio: true
            }
        };
        
        this.initialized = false;
        this.optimizedElements = new Set();
    }
    
    /**
     * Initialize the SVG optimization system
     */
    init() {
        if (this.initialized) return;
        
        this.setupResponsiveScaling();
        this.optimizeAllSVGs();
        this.initialized = true;
        
        console.log('SVGOptimizer initialized successfully');
    }
    
    /**
     * Optimize a specific SVG element based on context
     * @param {Element} element - The SVG element to optimize
     * @param {string} context - The context type ('icon', 'decorative', 'illustration', 'default')
     */
    optimizeSVG(element, context = 'default') {
        if (!element || element.tagName.toLowerCase() !== 'svg') {
            console.warn('SVGOptimizer: Invalid SVG element provided');
            return;
        }
        
        const rules = this.contextRules[context] || this.contextRules.default;
        const viewport = this.getViewportDimensions();
        
        // Store original dimensions if not already stored
        if (!element.dataset.originalWidth) {
            const bbox = element.getBBox ? element.getBBox() : { width: 100, height: 100 };
            element.dataset.originalWidth = bbox.width || element.getAttribute('width') || 100;
            element.dataset.originalHeight = bbox.height || element.getAttribute('height') || 100;
        }
        
        const originalWidth = parseFloat(element.dataset.originalWidth);
        const originalHeight = parseFloat(element.dataset.originalHeight);
        
        // Calculate new dimensions based on context rules
        let newWidth, newHeight;
        
        if (rules.unit === 'vw') {
            // Viewport-based sizing
            newWidth = Math.min(
                viewport.width * (rules.maxWidth / 100),
                rules.minWidth || originalWidth
            );
            
            if (rules.maintainAspectRatio) {
                const aspectRatio = originalHeight / originalWidth;
                newHeight = newWidth * aspectRatio;
            } else {
                newHeight = originalHeight;
            }
        } else {
            // Pixel-based sizing
            newWidth = Math.min(Math.max(originalWidth, rules.minWidth || 0), rules.maxWidth);
            newHeight = Math.min(Math.max(originalHeight, rules.minHeight || 0), rules.maxHeight || newWidth);
            
            if (rules.maintainAspectRatio) {
                const aspectRatio = originalHeight / originalWidth;
                newHeight = newWidth * aspectRatio;
            }
        }
        
        // Apply mobile scaling if needed
        if (viewport.width <= this.breakpoints.mobile) {
            newWidth *= 0.75; // 25% reduction for mobile
            newHeight *= 0.75;
        }
        
        // Apply the new dimensions
        this.applyDimensions(element, newWidth, newHeight);
        
        // Mark as optimized
        this.optimizedElements.add(element);
        element.dataset.svgOptimized = 'true';
        element.dataset.svgContext = context;
    }
    
    /**
     * Apply dimensions to an SVG element
     * @param {Element} element - The SVG element
     * @param {number} width - New width
     * @param {number} height - New height
     */
    applyDimensions(element, width, height) {
        // Set width and height attributes
        element.setAttribute('width', Math.round(width));
        element.setAttribute('height', Math.round(height));
        
        // Also set CSS for better control
        element.style.width = Math.round(width) + 'px';
        element.style.height = Math.round(height) + 'px';
        element.style.maxWidth = '100%';
        element.style.height = 'auto'; // Allow height to adjust naturally
    }
    
    /**
     * Set up responsive scaling with viewport change detection
     */
    setupResponsiveScaling() {
        // Use ResizeObserver if available, otherwise fall back to window resize
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver((entries) => {
                this.handleViewportChange();
            });
            resizeObserver.observe(document.documentElement);
            this.observers.set('resize', resizeObserver);
        } else {
            // Fallback for older browsers
            let resizeTimeout;
            const handleResize = () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    this.handleViewportChange();
                }, 250);
            };
            window.addEventListener('resize', handleResize);
            this.observers.set('resize', handleResize);
        }
    }
    
    /**
     * Handle viewport changes by re-optimizing all SVGs
     */
    handleViewportChange() {
        this.optimizedElements.forEach(element => {
            if (element.isConnected) {
                const context = element.dataset.svgContext || 'default';
                this.optimizeSVG(element, context);
            } else {
                // Remove disconnected elements
                this.optimizedElements.delete(element);
            }
        });
    }
    
    /**
     * Optimize all SVGs on the page
     */
    optimizeAllSVGs() {
        const svgElements = document.querySelectorAll('svg');
        
        svgElements.forEach(svg => {
            // Skip if already optimized
            if (svg.dataset.svgOptimized === 'true') return;
            
            // Determine context based on element attributes and classes
            const context = this.determineContext(svg);
            this.optimizeSVG(svg, context);
        });
    }
    
    /**
     * Determine the context of an SVG element based on its attributes and classes
     * @param {Element} element - The SVG element
     * @returns {string} The determined context
     */
    determineContext(element) {
        const classList = Array.from(element.classList);
        const parentClasses = element.parentElement ? Array.from(element.parentElement.classList) : [];
        const allClasses = [...classList, ...parentClasses];
        
        // Check for icon indicators
        if (allClasses.some(cls => cls.includes('icon') || cls.includes('btn') || cls.includes('nav'))) {
            return 'icon';
        }
        
        // Check for decorative indicators
        if (allClasses.some(cls => cls.includes('decorative') || cls.includes('ornament') || cls.includes('accent'))) {
            return 'decorative';
        }
        
        // Check for illustration indicators
        if (allClasses.some(cls => cls.includes('illustration') || cls.includes('hero') || cls.includes('banner'))) {
            return 'illustration';
        }
        
        // Check data attributes
        if (element.dataset.svgContext) {
            return element.dataset.svgContext;
        }
        
        // Default context based on size
        const width = parseFloat(element.getAttribute('width') || 100);
        const height = parseFloat(element.getAttribute('height') || 100);
        
        if (width <= 32 && height <= 32) {
            return 'icon';
        } else if (width > 200 || height > 200) {
            return 'illustration';
        } else {
            return 'decorative';
        }
    }
    
    /**
     * Get current viewport dimensions
     * @returns {Object} Viewport width and height
     */
    getViewportDimensions() {
        return {
            width: window.innerWidth || document.documentElement.clientWidth,
            height: window.innerHeight || document.documentElement.clientHeight
        };
    }
    
    /**
     * Maintain aspect ratio for an SVG element
     * @param {Element} element - The SVG element
     */
    maintainAspectRatio(element) {
        const originalWidth = parseFloat(element.dataset.originalWidth || element.getAttribute('width') || 100);
        const originalHeight = parseFloat(element.dataset.originalHeight || element.getAttribute('height') || 100);
        const aspectRatio = originalHeight / originalWidth;
        
        const currentWidth = parseFloat(element.getAttribute('width'));
        const newHeight = currentWidth * aspectRatio;
        
        element.setAttribute('height', Math.round(newHeight));
        element.style.height = Math.round(newHeight) + 'px';
    }
    
    /**
     * Add a new SVG element to be optimized
     * @param {Element} element - The SVG element
     * @param {string} context - The context type
     */
    addSVG(element, context = 'default') {
        this.optimizeSVG(element, context);
    }
    
    /**
     * Remove an SVG element from optimization
     * @param {Element} element - The SVG element
     */
    removeSVG(element) {
        this.optimizedElements.delete(element);
        if (element.dataset.svgOptimized) {
            delete element.dataset.svgOptimized;
            delete element.dataset.svgContext;
        }
    }
    
    /**
     * Get optimization status
     * @returns {Object} Status information
     */
    getStatus() {
        return {
            initialized: this.initialized,
            optimizedCount: this.optimizedElements.size,
            breakpoints: this.breakpoints,
            contextRules: Object.keys(this.contextRules)
        };
    }
    
    /**
     * Cleanup method to remove observers and event listeners
     */
    destroy() {
        this.observers.forEach((observer, key) => {
            if (key === 'resize' && typeof observer === 'function') {
                window.removeEventListener('resize', observer);
            } else if (observer && observer.disconnect) {
                observer.disconnect();
            }
        });
        
        this.observers.clear();
        this.optimizedElements.clear();
        this.initialized = false;
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SVGOptimizer;
}

// Global availability
window.SVGOptimizer = SVGOptimizer;