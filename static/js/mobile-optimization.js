/**
 * Mobile Optimization Class for Tournament System
 * Handles touch-friendly interactions, responsive navigation, and mobile-specific optimizations
 */
class MobileOptimization {
    constructor() {
        this.isMobile = this.detectMobile();
        this.isTablet = this.detectTablet();
        this.touchStartY = 0;
        this.touchEndY = 0;
        this.isScrolling = false;

        this.init();
    }

    /**
     * Initialize mobile optimizations
     */
    init() {
        this.setupViewportMeta();
        this.setupTouchHandlers();
        this.setupMobileNavigation();
        this.setupFormOptimizations();
        this.setupScrollOptimizations();
        this.setupOrientationHandling();
        this.setupAccessibilityEnhancements();
        this.setupLazyLoading();

        // Add mobile class to body for CSS targeting
        if (this.isMobile) {
            document.body.classList.add('mobile-device');
        }
        if (this.isTablet) {
            document.body.classList.add('tablet-device');
        }

        console.log('✅ Mobile optimization initialized', {
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            userAgent: navigator.userAgent
        });
    }

    /**
     * Detect if device is mobile
     */
    detectMobile() {
        const userAgent = navigator.userAgent.toLowerCase();
        const mobileKeywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone'];
        return mobileKeywords.some(keyword => userAgent.includes(keyword)) ||
            window.innerWidth <= 768;
    }

    /**
     * Detect if device is tablet
     */
    detectTablet() {
        const userAgent = navigator.userAgent.toLowerCase();
        const tabletKeywords = ['ipad', 'tablet', 'kindle'];
        return tabletKeywords.some(keyword => userAgent.includes(keyword)) ||
            (window.innerWidth > 768 && window.innerWidth <= 1024);
    }

    /**
     * Setup viewport meta tag for iOS devices
     */
    setupViewportMeta() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }

        // Optimize viewport for mobile devices
        if (this.isMobile) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover';
        } else {
            viewport.content = 'width=device-width, initial-scale=1.0';
        }
    }

    /**
     * Setup touch event handlers
     */
    setupTouchHandlers() {
        if (!('ontouchstart' in window)) return;

        // Add touch feedback to buttons
        document.addEventListener('touchstart', (e) => {
            if (e.target.matches('.btn, button, [role="button"]')) {
                e.target.classList.add('touch-active');
            }
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (e.target.matches('.btn, button, [role="button"]')) {
                setTimeout(() => {
                    e.target.classList.remove('touch-active');
                }, 150);
            }
        }, { passive: true });

        // Handle swipe gestures
        document.addEventListener('touchstart', (e) => {
            this.touchStartY = e.touches[0].clientY;
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            this.isScrolling = true;
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!this.isScrolling) {
                this.touchEndY = e.changedTouches[0].clientY;
                this.handleSwipeGesture();
            }
            this.isScrolling = false;
        }, { passive: true });
    }

    /**
     * Handle swipe gestures
     */
    handleSwipeGesture() {
        const swipeThreshold = 50;
        const swipeDistance = this.touchStartY - this.touchEndY;

        if (Math.abs(swipeDistance) > swipeThreshold) {
            if (swipeDistance > 0) {
                // Swipe up
                this.handleSwipeUp();
            } else {
                // Swipe down
                this.handleSwipeDown();
            }
        }
    }

    /**
     * Handle swipe up gesture
     */
    handleSwipeUp() {
        // Close mobile navigation if open
        const mobileNav = document.querySelector('.nav-menu');
        if (mobileNav && mobileNav.classList.contains('active')) {
            this.closeMobileNav();
        }
    }

    /**
     * Handle swipe down gesture
     */
    handleSwipeDown() {
        // Could be used for pull-to-refresh functionality
        console.log('Swipe down detected');
    }

    /**
     * Setup mobile navigation
     */
    setupMobileNavigation() {
        // Create mobile nav toggle if it doesn't exist
        let navToggle = document.querySelector('.mobile-nav-toggle');
        if (!navToggle && this.isMobile) {
            navToggle = this.createMobileNavToggle();
        }

        if (navToggle) {
            navToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMobileNav();
            });
        }

        // Create overlay for mobile nav
        this.createNavOverlay();

        // Handle nav link clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-menu a')) {
                this.closeMobileNav();
            }
        });
    }

    /**
     * Create mobile navigation toggle button
     */
    createMobileNavToggle() {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-nav-toggle';
        toggle.innerHTML = '☰';
        toggle.setAttribute('aria-label', 'Toggle navigation menu');
        toggle.setAttribute('aria-expanded', 'false');

        // Insert into header or create one
        const header = document.querySelector('header, .header, .navbar');
        if (header) {
            header.appendChild(toggle);
        } else {
            document.body.insertBefore(toggle, document.body.firstChild);
        }

        return toggle;
    }

    /**
     * Create navigation overlay
     */
    createNavOverlay() {
        if (document.querySelector('.nav-overlay')) return;

        const overlay = document.createElement('div');
        overlay.className = 'nav-overlay';
        overlay.addEventListener('click', () => {
            this.closeMobileNav();
        });

        document.body.appendChild(overlay);
    }

    /**
     * Toggle mobile navigation
     */
    toggleMobileNav() {
        const navMenu = document.querySelector('.nav-menu');
        const navToggle = document.querySelector('.mobile-nav-toggle');
        const overlay = document.querySelector('.nav-overlay');

        if (!navMenu) return;

        const isActive = navMenu.classList.contains('active');

        if (isActive) {
            this.closeMobileNav();
        } else {
            this.openMobileNav();
        }
    }

    /**
     * Open mobile navigation
     */
    openMobileNav() {
        const navMenu = document.querySelector('.nav-menu');
        const navToggle = document.querySelector('.mobile-nav-toggle');
        const overlay = document.querySelector('.nav-overlay');

        if (navMenu) navMenu.classList.add('active');
        if (overlay) overlay.classList.add('active');
        if (navToggle) {
            navToggle.setAttribute('aria-expanded', 'true');
            navToggle.innerHTML = '✕';
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    /**
     * Close mobile navigation
     */
    closeMobileNav() {
        const navMenu = document.querySelector('.nav-menu');
        const navToggle = document.querySelector('.mobile-nav-toggle');
        const overlay = document.querySelector('.nav-overlay');

        if (navMenu) navMenu.classList.remove('active');
        if (overlay) overlay.classList.remove('active');
        if (navToggle) {
            navToggle.setAttribute('aria-expanded', 'false');
            navToggle.innerHTML = '☰';
        }

        // Restore body scroll
        document.body.style.overflow = '';
    }

    /**
     * Setup form optimizations for mobile
     */
    setupFormOptimizations() {
        // Optimize input types for mobile keyboards
        const inputs = document.querySelectorAll('input[type="text"]');
        inputs.forEach(input => {
            const name = input.name || input.id || '';
            const placeholder = input.placeholder || '';

            // Set appropriate input types for mobile keyboards
            if (name.includes('email') || placeholder.includes('email')) {
                input.type = 'email';
            } else if (name.includes('phone') || name.includes('tel') || placeholder.includes('phone')) {
                input.type = 'tel';
            } else if (name.includes('url') || placeholder.includes('url')) {
                input.type = 'url';
            } else if (name.includes('number') || placeholder.includes('number')) {
                input.type = 'number';
            }
        });

        // Add touch-friendly focus handling
        document.addEventListener('focusin', (e) => {
            if (e.target.matches('input, textarea, select')) {
                e.target.classList.add('focused');
                this.scrollToElement(e.target);
            }
        });

        document.addEventListener('focusout', (e) => {
            if (e.target.matches('input, textarea, select')) {
                e.target.classList.remove('focused');
            }
        });
    }

    /**
     * Scroll element into view with mobile-friendly offset
     */
    scrollToElement(element, offset = 100) {
        if (!this.isMobile) return;

        setTimeout(() => {
            const elementRect = element.getBoundingClientRect();
            const absoluteElementTop = elementRect.top + window.pageYOffset;
            const middle = absoluteElementTop - (window.innerHeight / 2) + offset;

            window.scrollTo({
                top: middle,
                behavior: 'smooth'
            });
        }, 300); // Delay to allow keyboard to appear
    }

    /**
     * Setup scroll optimizations
     */
    setupScrollOptimizations() {
        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });

        // Add scroll-based classes for styling
        let ticking = false;
        const updateScrollClasses = () => {
            const scrollTop = window.pageYOffset;

            if (scrollTop > 100) {
                document.body.classList.add('scrolled');
            } else {
                document.body.classList.remove('scrolled');
            }

            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollClasses);
                ticking = true;
            }
        }, { passive: true });
    }

    /**
     * Handle orientation changes
     */
    setupOrientationHandling() {
        const handleOrientationChange = () => {
            // Close mobile nav on orientation change
            this.closeMobileNav();

            // Update mobile/tablet detection
            setTimeout(() => {
                this.isMobile = this.detectMobile();
                this.isTablet = this.detectTablet();

                // Update body classes
                document.body.classList.toggle('mobile-device', this.isMobile);
                document.body.classList.toggle('tablet-device', this.isTablet);

                // Trigger resize event for other components
                window.dispatchEvent(new Event('resize'));
            }, 100);
        };

        window.addEventListener('orientationchange', handleOrientationChange);
        window.addEventListener('resize', handleOrientationChange);
    }

    /**
     * Setup accessibility enhancements for mobile
     */
    setupAccessibilityEnhancements() {
        // Improve focus visibility on mobile
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Add skip link for mobile navigation
        this.addSkipLink();
    }

    /**
     * Add skip link for accessibility
     */
    addSkipLink() {
        if (document.querySelector('.skip-link')) return;

        const skipLink = document.createElement('a');
        skipLink.className = 'skip-link';
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            z-index: 1001;
            border-radius: 4px;
        `;

        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);
    }

    /**
     * Get mobile optimization status
     */
    getStatus() {
        return {
            isMobile: this.isMobile,
            isTablet: this.isTablet,
            hasTouch: 'ontouchstart' in window,
            orientation: window.orientation || 0,
            screenWidth: window.innerWidth,
            screenHeight: window.innerHeight,
            userAgent: navigator.userAgent
        };
    }

    /**
     * Optimize tournament cards for mobile
     */
    optimizeTournamentCards() {
        const cards = document.querySelectorAll('.tournament-card');
        cards.forEach(card => {
            // Add touch feedback
            card.addEventListener('touchstart', () => {
                card.classList.add('touch-active');
            }, { passive: true });

            card.addEventListener('touchend', () => {
                setTimeout(() => {
                    card.classList.remove('touch-active');
                }, 150);
            }, { passive: true });
        });
    }

    /**
     * Optimize registration forms for mobile
     */
    optimizeRegistrationForms() {
        const forms = document.querySelectorAll('.registration-form');
        forms.forEach(form => {
            // Add mobile-friendly validation
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('invalid', (e) => {
                    e.preventDefault();
                    this.showMobileValidationError(input);
                });
            });
        });
    }

    /**
     * Show mobile-friendly validation error
     */
    showMobileValidationError(input) {
        // Remove existing error
        const existingError = input.parentNode.querySelector('.mobile-validation-error');
        if (existingError) {
            existingError.remove();
        }

        // Create new error message
        const error = document.createElement('div');
        error.className = 'mobile-validation-error';
        error.textContent = input.validationMessage;
        error.style.cssText = `
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            padding: 0.5rem;
            background: #f8d7da;
            border-radius: 4px;
            border: 1px solid #f5c6cb;
        `;

        input.parentNode.appendChild(error);

        // Scroll to error
        this.scrollToElement(input);

        // Remove error when input becomes valid
        const removeError = () => {
            if (input.checkValidity()) {
                error.remove();
                input.removeEventListener('input', removeError);
            }
        };

        input.addEventListener('input', removeError);
    }

    /**
     * Setup lazy loading for images and iframes
     * Task 10: Performance Optimizations
     */
    setupLazyLoading() {
        // Check for Intersection Observer support
        if (!('IntersectionObserver' in window)) {
            console.warn('IntersectionObserver not supported, lazy loading disabled');
            return;
        }

        // Create intersection observer
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    this.loadLazyElement(element);
                    observer.unobserve(element);
                }
            });
        }, {
            root: null,
            rootMargin: '50px', // Start loading 50px before element enters viewport
            threshold: 0.01
        });

        // Observe all lazy elements
        const lazyElements = document.querySelectorAll('img[data-src], iframe[data-src], [data-lazy]');
        lazyElements.forEach(element => {
            imageObserver.observe(element);
        });

        // Also observe images with loading="lazy" attribute
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        lazyImages.forEach(img => {
            // Add placeholder while loading
            if (!img.complete) {
                img.classList.add('lazy-loading');
                img.addEventListener('load', () => {
                    img.classList.remove('lazy-loading');
                    img.classList.add('lazy-loaded');
                }, { once: true });
            }
        });

        console.log(`✅ Lazy loading initialized for ${lazyElements.length} elements`);
    }

    /**
     * Load a lazy element
     */
    loadLazyElement(element) {
        const src = element.dataset.src;
        const srcset = element.dataset.srcset;

        if (!src && !srcset) return;

        // Add loading class
        element.classList.add('lazy-loading');

        // Handle images
        if (element.tagName === 'IMG') {
            if (srcset) {
                element.srcset = srcset;
            }
            if (src) {
                element.src = src;
            }

            // Remove data attributes
            delete element.dataset.src;
            delete element.dataset.srcset;

            // Add loaded class when image loads
            element.addEventListener('load', () => {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-loaded');
            }, { once: true });

            // Handle load errors
            element.addEventListener('error', () => {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-error');
                console.warn('Failed to load lazy image:', src);
            }, { once: true });
        }
        // Handle iframes
        else if (element.tagName === 'IFRAME') {
            element.src = src;
            delete element.dataset.src;

            element.addEventListener('load', () => {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-loaded');
            }, { once: true });
        }
        // Handle other elements with background images
        else if (element.dataset.lazy) {
            element.style.backgroundImage = `url('${src}')`;
            delete element.dataset.src;
            delete element.dataset.lazy;

            // Simulate load event for background images
            const img = new Image();
            img.onload = () => {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-loaded');
            };
            img.onerror = () => {
                element.classList.remove('lazy-loading');
                element.classList.add('lazy-error');
            };
            img.src = src;
        }
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileOptimization = new MobileOptimization();
    });
} else {
    window.mobileOptimization = new MobileOptimization();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileOptimization;
}