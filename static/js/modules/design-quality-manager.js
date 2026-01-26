/**
 * Design Quality Manager
 * Ensures consistent spacing, typography, color schemes, visual feedback,
 * visual hierarchy, and element alignment across the tournament detail page
 * 
 * Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
 */

class DesignQualityManager {
    constructor() {
        this.initialized = false;
        this.designTokens = this.loadDesignTokens();
        this.observers = new Map();
        this.interactiveElements = new Set();
    }

    /**
     * Load design tokens from CSS custom properties
     */
    loadDesignTokens() {
        const root = document.documentElement;
        const computedStyle = getComputedStyle(root);
        
        return {
            colors: {
                primary: computedStyle.getPropertyValue('--eyt-red').trim() || '#b91c1c',
                primaryDark: computedStyle.getPropertyValue('--eyt-red-dark').trim() || '#991b1b',
                primaryLight: computedStyle.getPropertyValue('--eyt-red-light').trim() || '#dc2626',
                bgDark: computedStyle.getPropertyValue('--bg-dark').trim() || '#111827',
                bgGray800: computedStyle.getPropertyValue('--bg-gray-800').trim() || '#1f2937',
                bgGray700: computedStyle.getPropertyValue('--bg-gray-700').trim() || '#374151',
                textWhite: computedStyle.getPropertyValue('--text-white').trim() || '#ffffff',
                textGray300: computedStyle.getPropertyValue('--text-gray-300').trim() || '#d1d5db',
                textGray400: computedStyle.getPropertyValue('--text-gray-400').trim() || '#9ca3af',
                textGray500: computedStyle.getPropertyValue('--text-gray-500').trim() || '#6b7280',
                statusGreen: computedStyle.getPropertyValue('--status-green').trim() || '#10b981',
                statusBlue: computedStyle.getPropertyValue('--status-blue').trim() || '#3b82f6',
                statusYellow: computedStyle.getPropertyValue('--status-yellow').trim() || '#f59e0b',
                statusRed: computedStyle.getPropertyValue('--status-red').trim() || '#ef4444'
            },
            spacing: {
                xs: computedStyle.getPropertyValue('--spacing-xs').trim() || '0.25rem',
                sm: computedStyle.getPropertyValue('--spacing-sm').trim() || '0.5rem',
                md: computedStyle.getPropertyValue('--spacing-md').trim() || '1rem',
                lg: computedStyle.getPropertyValue('--spacing-lg').trim() || '1.5rem',
                xl: computedStyle.getPropertyValue('--spacing-xl').trim() || '2rem',
                '2xl': computedStyle.getPropertyValue('--spacing-2xl').trim() || '3rem'
            },
            borderRadius: {
                sm: computedStyle.getPropertyValue('--radius-sm').trim() || '0.375rem',
                md: computedStyle.getPropertyValue('--radius-md').trim() || '0.5rem',
                lg: computedStyle.getPropertyValue('--radius-lg').trim() || '0.75rem',
                xl: computedStyle.getPropertyValue('--radius-xl').trim() || '1rem'
            },
            animation: {
                fast: computedStyle.getPropertyValue('--animation-fast').trim() || '0.15s',
                normal: computedStyle.getPropertyValue('--animation-normal').trim() || '0.3s',
                slow: computedStyle.getPropertyValue('--animation-slow').trim() || '0.5s'
            }
        };
    }

    /**
     * Initialize design quality management
     */
    initialize() {
        if (this.initialized) {
            console.log('DesignQualityManager already initialized');
            return;
        }

        console.log('Initializing DesignQualityManager...');

        try {
            // Apply consistent spacing
            this.applyConsistentSpacing();

            // Apply consistent typography
            this.applyConsistentTypography();

            // Apply consistent color schemes
            this.applyConsistentColors();

            // Enhance interactive feedback
            this.enhanceInteractiveFeedback();

            // Ensure visual hierarchy
            this.ensureVisualHierarchy();

            // Fix element alignment
            this.fixElementAlignment();

            // Setup observers for dynamic content
            this.setupObservers();

            this.initialized = true;
            console.log('DesignQualityManager initialized successfully');
        } catch (error) {
            console.error('Error initializing DesignQualityManager:', error);
        }
    }

    /**
     * Apply consistent spacing throughout the page
     * Validates: Requirement 6.1
     */
    applyConsistentSpacing() {
        // Ensure consistent spacing for cards
        const cards = document.querySelectorAll('.bg-gray-800, .card, [class*="card"]');
        cards.forEach(card => {
            if (!card.style.padding) {
                card.style.padding = this.designTokens.spacing.lg;
            }
        });

        // Ensure consistent gap in flex/grid containers
        const containers = document.querySelectorAll('.flex, .grid, [class*="flex"], [class*="grid"]');
        containers.forEach(container => {
            if (!container.style.gap && !container.classList.contains('gap-0')) {
                const computedGap = getComputedStyle(container).gap;
                if (computedGap === 'normal' || computedGap === '0px') {
                    container.style.gap = this.designTokens.spacing.md;
                }
            }
        });

        // Ensure consistent section spacing
        const sections = document.querySelectorAll('section, .section, [class*="section"]');
        sections.forEach(section => {
            if (!section.style.marginBottom) {
                section.style.marginBottom = this.designTokens.spacing.xl;
            }
        });

        console.log('Applied consistent spacing');
    }

    /**
     * Apply consistent typography
     * Validates: Requirement 6.1
     */
    applyConsistentTypography() {
        // Ensure headings have consistent font weights
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            
            // Apply font weight based on heading level
            if (level <= 2) {
                heading.style.fontWeight = '800';
            } else if (level <= 4) {
                heading.style.fontWeight = '700';
            } else {
                heading.style.fontWeight = '600';
            }

            // Ensure proper color
            if (!heading.classList.contains('text-gray-400') && 
                !heading.classList.contains('text-gray-500')) {
                heading.style.color = this.designTokens.colors.textWhite;
            }
        });

        // Ensure consistent body text
        const paragraphs = document.querySelectorAll('p:not([class*="text-"])');
        paragraphs.forEach(p => {
            p.style.color = this.designTokens.colors.textGray300;
            p.style.lineHeight = '1.6';
        });

        // Ensure consistent link styling
        const links = document.querySelectorAll('a:not(.btn):not(.button):not([class*="btn"])');
        links.forEach(link => {
            if (!link.style.color) {
                link.style.color = this.designTokens.colors.statusBlue;
            }
            link.style.textDecoration = 'none';
            link.style.transition = `color ${this.designTokens.animation.normal} ease`;
        });

        console.log('Applied consistent typography');
    }

    /**
     * Apply consistent color schemes
     * Validates: Requirement 6.1
     */
    applyConsistentColors() {
        // Ensure primary buttons use brand colors
        const primaryButtons = document.querySelectorAll('.btn-primary, [class*="bg-red"]');
        primaryButtons.forEach(btn => {
            if (!btn.style.backgroundColor) {
                btn.style.backgroundColor = this.designTokens.colors.primary;
            }
            if (!btn.style.color) {
                btn.style.color = this.designTokens.colors.textWhite;
            }
        });

        // Ensure status badges use consistent colors
        const statusBadges = document.querySelectorAll('[class*="status-"], .badge');
        statusBadges.forEach(badge => {
            if (badge.classList.contains('status-registration') || 
                badge.textContent.toLowerCase().includes('open')) {
                badge.style.backgroundColor = `${this.designTokens.colors.statusGreen}33`;
                badge.style.color = this.designTokens.colors.statusGreen;
            } else if (badge.classList.contains('status-in-progress') || 
                       badge.textContent.toLowerCase().includes('progress')) {
                badge.style.backgroundColor = `${this.designTokens.colors.statusBlue}33`;
                badge.style.color = this.designTokens.colors.statusBlue;
            } else if (badge.classList.contains('status-completed') || 
                       badge.textContent.toLowerCase().includes('completed')) {
                badge.style.backgroundColor = `${this.designTokens.colors.textGray500}33`;
                badge.style.color = this.designTokens.colors.textGray400;
            }
        });

        // Ensure borders use consistent colors
        const borderedElements = document.querySelectorAll('[class*="border"]');
        borderedElements.forEach(el => {
            const computedBorder = getComputedStyle(el).borderColor;
            if (computedBorder === 'rgb(0, 0, 0)' || computedBorder === 'initial') {
                el.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }
        });

        console.log('Applied consistent color schemes');
    }

    /**
     * Enhance interactive feedback for all interactive elements
     * Validates: Requirement 6.2
     */
    enhanceInteractiveFeedback() {
        // Find all interactive elements
        const interactiveSelectors = [
            'button',
            'a',
            'input',
            'select',
            'textarea',
            '[role="button"]',
            '[tabindex]:not([tabindex="-1"])',
            '.btn',
            '.tab-button',
            '.participant-card',
            '.match-card',
            '.stat-card'
        ];

        interactiveSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                this.enhanceElementFeedback(el);
                this.interactiveElements.add(el);
            });
        });

        console.log(`Enhanced interactive feedback for ${this.interactiveElements.size} elements`);
    }

    /**
     * Enhance feedback for a single element
     */
    enhanceElementFeedback(element) {
        // Ensure transition is set
        if (!element.style.transition) {
            element.style.transition = `all ${this.designTokens.animation.normal} ease`;
        }

        // Add hover effect for non-touch devices
        if (window.matchMedia('(hover: hover)').matches) {
            element.addEventListener('mouseenter', () => {
                if (!element.disabled && !element.classList.contains('disabled')) {
                    element.style.transform = 'translateY(-1px)';
                    
                    // Enhance shadow for cards
                    if (element.classList.contains('card') || 
                        element.classList.contains('participant-card') ||
                        element.classList.contains('match-card') ||
                        element.classList.contains('stat-card')) {
                        element.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.3)';
                    }
                }
            });

            element.addEventListener('mouseleave', () => {
                element.style.transform = '';
                element.style.boxShadow = '';
            });
        }

        // Add focus indicator
        element.addEventListener('focus', () => {
            element.style.outline = `2px solid ${this.designTokens.colors.statusBlue}`;
            element.style.outlineOffset = '2px';
        });

        element.addEventListener('blur', () => {
            element.style.outline = '';
            element.style.outlineOffset = '';
        });

        // Add active state for touch devices
        element.addEventListener('touchstart', () => {
            if (!element.disabled && !element.classList.contains('disabled')) {
                element.style.transform = 'scale(0.98)';
            }
        });

        element.addEventListener('touchend', () => {
            element.style.transform = '';
        });
    }

    /**
     * Ensure proper visual hierarchy
     * Validates: Requirement 6.3
     */
    ensureVisualHierarchy() {
        // Ensure headings are properly sized
        const h1Elements = document.querySelectorAll('h1');
        h1Elements.forEach(h1 => {
            if (!h1.style.fontSize) {
                h1.style.fontSize = 'clamp(2rem, 5vw, 4rem)';
            }
        });

        const h2Elements = document.querySelectorAll('h2');
        h2Elements.forEach(h2 => {
            if (!h2.style.fontSize) {
                h2.style.fontSize = 'clamp(1.5rem, 4vw, 2.5rem)';
            }
        });

        const h3Elements = document.querySelectorAll('h3');
        h3Elements.forEach(h3 => {
            if (!h3.style.fontSize) {
                h3.style.fontSize = 'clamp(1.25rem, 3vw, 1.875rem)';
            }
        });

        // Ensure proper content separation
        const contentSections = document.querySelectorAll('.prose, .content, [class*="content"]');
        contentSections.forEach(section => {
            section.style.marginBottom = this.designTokens.spacing.xl;
        });

        // Ensure cards have proper elevation
        const cards = document.querySelectorAll('.bg-gray-800, .card, [class*="card"]');
        cards.forEach(card => {
            if (!card.style.boxShadow) {
                card.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.2)';
            }
        });

        console.log('Ensured visual hierarchy');
    }

    /**
     * Fix element alignment and positioning
     * Validates: Requirement 6.4, 6.5
     */
    fixElementAlignment() {
        // Ensure flex containers are properly aligned
        const flexContainers = document.querySelectorAll('.flex, [class*="flex"]');
        flexContainers.forEach(container => {
            if (!container.style.alignItems && !container.classList.contains('items-start')) {
                container.style.alignItems = 'center';
            }
        });

        // Ensure grid containers have proper gaps
        const gridContainers = document.querySelectorAll('.grid, [class*="grid"]');
        gridContainers.forEach(container => {
            if (!container.style.gap) {
                container.style.gap = this.designTokens.spacing.md;
            }
        });

        // Fix breadcrumb alignment
        const breadcrumbs = document.querySelectorAll('.breadcrumb, [class*="breadcrumb"]');
        breadcrumbs.forEach(breadcrumb => {
            breadcrumb.style.display = 'flex';
            breadcrumb.style.alignItems = 'center';
            breadcrumb.style.gap = this.designTokens.spacing.sm;
        });

        // Ensure buttons are properly aligned in button groups
        const buttonGroups = document.querySelectorAll('.button-group, [class*="button-group"]');
        buttonGroups.forEach(group => {
            group.style.display = 'flex';
            group.style.gap = this.designTokens.spacing.sm;
            group.style.alignItems = 'center';
        });

        console.log('Fixed element alignment');
    }

    /**
     * Setup observers for dynamic content
     */
    setupObservers() {
        // Observe DOM changes to apply design quality to new elements
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        this.applyDesignQualityToElement(node);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        this.observers.set('dom', observer);
        console.log('Setup observers for dynamic content');
    }

    /**
     * Apply design quality to a single element
     */
    applyDesignQualityToElement(element) {
        // Check if element is interactive
        const interactiveSelectors = ['button', 'a', 'input', 'select', 'textarea', '[role="button"]'];
        if (interactiveSelectors.some(selector => element.matches(selector))) {
            this.enhanceElementFeedback(element);
            this.interactiveElements.add(element);
        }

        // Apply spacing if it's a card
        if (element.classList.contains('card') || element.classList.contains('bg-gray-800')) {
            if (!element.style.padding) {
                element.style.padding = this.designTokens.spacing.lg;
            }
        }

        // Apply typography if it's a heading
        if (element.matches('h1, h2, h3, h4, h5, h6')) {
            const level = parseInt(element.tagName.charAt(1));
            if (level <= 2) {
                element.style.fontWeight = '800';
            } else if (level <= 4) {
                element.style.fontWeight = '700';
            } else {
                element.style.fontWeight = '600';
            }
            element.style.color = this.designTokens.colors.textWhite;
        }
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        // Remove all observers
        this.observers.forEach((observer, key) => {
            observer.disconnect();
        });
        this.observers.clear();

        // Clear interactive elements
        this.interactiveElements.clear();

        this.initialized = false;
        console.log('DesignQualityManager destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DesignQualityManager;
}

// Auto-initialize on DOM ready
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.designQualityManager = new DesignQualityManager();
            window.designQualityManager.initialize();
        });
    } else {
        window.designQualityManager = new DesignQualityManager();
        window.designQualityManager.initialize();
    }
}
