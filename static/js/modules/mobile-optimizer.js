/**
 * Mobile Optimization Module
 * Implements mobile-optimized layouts, touch-friendly interactions, SVG scaling, and performance optimizations
 * Addresses Requirements 8.1, 8.2, 8.3, 8.4, 8.5
 */

class MobileOptimizer {
    constructor(config = {}) {
        this.config = {
            debug: false,
            breakpoints: {
                mobile: 768,
                tablet: 1024,
                desktop: 1200
            },
            touchTargetMinSize: 44, // WCAG minimum
            performanceThresholds: {
                loadTime: 2000,
                animationFrameRate: 60
            },
            ...config
        };
        
        this.isInitialized = false;
        this.isMobile = false;
        this.isTouch = false;
        this.observers = new Map();
        this.optimizedElements = new Set();
        this.performanceMetrics = {};
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.log('Mobile Optimizer initializing...');
        
        // Detect mobile and touch capabilities
        this.detectDeviceCapabilities();
        
        // Set up viewport handling
        this.setupViewportHandling();
        
        // Implement mobile-optimized layouts
        this.implementMobileLayouts();
        
        // Add touch-friendly interactions
        this.addTouchFriendlyInteractions();
        
        // Optimize SVG scaling for mobile
        this.optimizeSVGScaling();
        
        // Ensure fast loading and smooth performance
        this.optimizePerformance();
        
        // Set up responsive monitoring
        this.setupResponsiveMonitoring();
        
        this.isInitialized = true;
        this.log('Mobile Optimizer initialized successfully');
    }
    
    /**
     * Detect device capabilities and set appropriate classes
     * Addresses Requirements 8.1, 8.2
     */
    detectDeviceCapabilities() {
        const userAgent = navigator.userAgent;
        const viewport = this.getViewportDimensions();
        
        // Detect mobile devices
        this.isMobile = viewport.width < this.config.breakpoints.mobile || 
                       /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        
        // Detect touch capability
        this.isTouch = 'ontouchstart' in window || 
                      navigator.maxTouchPoints > 0 || 
                      navigator.msMaxTouchPoints > 0;
        
        // Apply device classes
        if (this.isMobile) {
            document.body.classList.add('mobile-device');
        }
        
        if (this.isTouch) {
            document.body.classList.add('touch-device');
        }
        
        this.log(`Device detection: Mobile=${this.isMobile}, Touch=${this.isTouch}`);
    }
    
    /**
     * Set up viewport handling for mobile browsers
     * Addresses Requirements 8.1, 8.5
     */
    setupViewportHandling() {
        // Handle viewport height for mobile browsers (address bar issues)
        const setViewportHeight = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };
        
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
        window.addEventListener('orientationchange', () => {
            setTimeout(setViewportHeight, 100); // Delay for orientation change
        });
        
        // Prevent overscroll on mobile
        if (this.isMobile) {
            document.body.style.overscrollBehavior = 'none';
        }
    }
    
    /**
     * Implement mobile-optimized layouts for all components
     * Addresses Requirements 8.1
     */
    implementMobileLayouts() {
        if (!this.isMobile) return;
        
        this.log('Implementing mobile-optimized layouts');
        
        // Optimize tournament grid layout
        this.optimizeTournamentGrid();
        
        // Optimize hero section for mobile
        this.optimizeHeroSection();
        
        // Optimize participant display
        this.optimizeParticipantDisplay();
        
        // Optimize registration card for mobile
        this.optimizeRegistrationCard();
        
        // Optimize tab navigation
        this.optimizeTabNavigation();
        
        // Optimize statistics dashboard
        this.optimizeStatsDashboard();
    }
    
    optimizeTournamentGrid() {
        const tournamentGrid = document.querySelector('.tournament-grid');
        if (!tournamentGrid) return;
        
        // Force single column layout on mobile
        const mobileStyles = {
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: '1rem',
            padding: '1rem',
            maxWidth: '100%',
            boxSizing: 'border-box'
        };
        
        Object.assign(tournamentGrid.style, mobileStyles);
        this.optimizedElements.add(tournamentGrid);
        
        this.log('Tournament grid optimized for mobile');
    }
    
    optimizeHeroSection() {
        const heroSection = document.querySelector('.tournament-hero');
        if (!heroSection) return;
        
        // Reduce height for mobile and optimize content
        const mobileStyles = {
            minHeight: '350px',
            padding: '1rem',
            boxSizing: 'border-box'
        };
        
        Object.assign(heroSection.style, mobileStyles);
        
        // Optimize hero content
        const heroContent = heroSection.querySelector('.hero-content');
        if (heroContent) {
            const contentStyles = {
                padding: '1rem',
                boxSizing: 'border-box'
            };
            Object.assign(heroContent.style, contentStyles);
        }
        
        // Optimize tournament title for mobile
        const title = heroSection.querySelector('.tournament-title, h1');
        if (title) {
            const titleStyles = {
                fontSize: 'clamp(1.75rem, 5vw, 2.5rem)',
                lineHeight: '1.1',
                marginBottom: '1rem'
            };
            Object.assign(title.style, titleStyles);
        }
        
        // Optimize meta items for mobile
        const metaItems = heroSection.querySelectorAll('.meta-item');
        metaItems.forEach(item => {
            const itemStyles = {
                fontSize: '0.8rem',
                padding: '0.5rem',
                marginBottom: '0.5rem',
                minHeight: '44px',
                display: 'flex',
                alignItems: 'center',
                boxSizing: 'border-box'
            };
            Object.assign(item.style, itemStyles);
        });
        
        this.optimizedElements.add(heroSection);
        this.log('Hero section optimized for mobile');
    }
    
    optimizeParticipantDisplay() {
        const participantGrid = document.querySelector('.participant-grid');
        if (!participantGrid) return;
        
        // Optimize grid for mobile
        const gridStyles = {
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: '1rem',
            padding: '0 1rem'
        };
        
        Object.assign(participantGrid.style, gridStyles);
        
        // Optimize individual participant cards for mobile
        const participantCards = participantGrid.querySelectorAll('.participant-card');
        participantCards.forEach(card => {
            const cardStyles = {
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '1rem',
                minHeight: '44px',
                borderRadius: '0.5rem',
                transition: 'transform 0.2s ease',
                cursor: 'pointer',
                boxSizing: 'border-box'
            };
            
            Object.assign(card.style, cardStyles);
            
            // Optimize avatar
            const avatar = card.querySelector('.participant-avatar, .avatar');
            if (avatar) {
                const avatarStyles = {
                    flexShrink: '0',
                    width: '2.5rem',
                    height: '2.5rem',
                    borderRadius: '50%'
                };
                Object.assign(avatar.style, avatarStyles);
            }
            
            // Optimize participant info
            const info = card.querySelector('.participant-info');
            if (info) {
                const infoStyles = {
                    flex: '1',
                    minWidth: '0',
                    overflow: 'hidden'
                };
                Object.assign(info.style, infoStyles);
                
                // Optimize name display
                const name = info.querySelector('.participant-name, .name');
                if (name) {
                    const nameStyles = {
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        fontSize: '0.875rem',
                        fontWeight: '600'
                    };
                    Object.assign(name.style, nameStyles);
                }
            }
        });
        
        this.optimizedElements.add(participantGrid);
        this.log('Participant display optimized for mobile');
    }
    
    optimizeRegistrationCard() {
        const registrationCard = document.querySelector('.enhanced-registration-card, .registration-card');
        if (!registrationCard) return;
        
        // Position at bottom of screen on mobile
        const mobileStyles = {
            position: 'fixed',
            bottom: '0',
            left: '0',
            right: '0',
            top: 'auto',
            zIndex: '50',
            borderRadius: '1rem 1rem 0 0',
            margin: '0',
            maxHeight: '60vh',
            overflowY: 'auto',
            paddingBottom: 'calc(1rem + env(safe-area-inset-bottom, 0))',
            boxSizing: 'border-box'
        };
        
        Object.assign(registrationCard.style, mobileStyles);
        
        // Add swipe handle
        this.addSwipeHandle(registrationCard);
        
        // Optimize buttons in registration card
        const buttons = registrationCard.querySelectorAll('button, .btn');
        buttons.forEach(button => {
            const buttonStyles = {
                minHeight: '48px',
                padding: '1rem 1.5rem',
                fontSize: '1rem',
                fontWeight: '600',
                borderRadius: '0.75rem',
                width: '100%',
                boxSizing: 'border-box'
            };
            Object.assign(button.style, buttonStyles);
        });
        
        this.optimizedElements.add(registrationCard);
        this.log('Registration card optimized for mobile');
    }
    
    addSwipeHandle(card) {
        // Add visual swipe handle for mobile UX
        const handle = document.createElement('div');
        handle.className = 'mobile-swipe-handle';
        handle.style.cssText = `
            position: absolute;
            top: 8px;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 2px;
            z-index: 10;
        `;
        
        card.insertBefore(handle, card.firstChild);
    }
    
    optimizeTabNavigation() {
        const tabContainer = document.querySelector('.tab-container');
        if (!tabContainer) return;
        
        // Make horizontally scrollable on mobile
        const containerStyles = {
            display: 'flex',
            gap: '0.5rem',
            overflowX: 'auto',
            scrollBehavior: 'smooth',
            WebkitOverflowScrolling: 'touch',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            padding: '0 1rem',
            boxSizing: 'border-box'
        };
        
        Object.assign(tabContainer.style, containerStyles);
        
        // Hide scrollbar
        const style = document.createElement('style');
        style.textContent = `
            .tab-container::-webkit-scrollbar {
                display: none;
            }
        `;
        document.head.appendChild(style);
        
        // Optimize tab buttons
        const tabButtons = tabContainer.querySelectorAll('.tab-button, button');
        tabButtons.forEach(button => {
            const buttonStyles = {
                minHeight: '44px',
                padding: '0.75rem 1.5rem',
                fontSize: '0.8rem',
                whiteSpace: 'nowrap',
                flexShrink: '0',
                borderRadius: '0.75rem',
                transition: 'all 0.2s ease',
                boxSizing: 'border-box'
            };
            Object.assign(button.style, buttonStyles);
        });
        
        // Add scroll indicators
        this.addScrollIndicators(tabContainer);
        
        this.optimizedElements.add(tabContainer);
        this.log('Tab navigation optimized for mobile');
    }
    
    addScrollIndicators(container) {
        const indicators = document.createElement('div');
        indicators.className = 'tab-scroll-indicators';
        indicators.style.cssText = `
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            z-index: 15;
            pointer-events: none;
        `;
        
        const leftIndicator = document.createElement('button');
        leftIndicator.innerHTML = '‹';
        leftIndicator.className = 'scroll-indicator left';
        leftIndicator.style.cssText = `
            position: absolute;
            left: -0.5rem;
            width: 2rem;
            height: 2rem;
            background: linear-gradient(135deg, #1f2937, #374151);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            color: #9ca3af;
            cursor: pointer;
            pointer-events: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        `;
        
        const rightIndicator = document.createElement('button');
        rightIndicator.innerHTML = '›';
        rightIndicator.className = 'scroll-indicator right';
        rightIndicator.style.cssText = leftIndicator.style.cssText.replace('left: -0.5rem', 'right: -0.5rem');
        
        indicators.appendChild(leftIndicator);
        indicators.appendChild(rightIndicator);
        
        // Position relative to container
        container.parentElement.style.position = 'relative';
        container.parentElement.appendChild(indicators);
        
        // Add scroll functionality
        leftIndicator.addEventListener('click', () => {
            container.scrollBy({ left: -100, behavior: 'smooth' });
        });
        
        rightIndicator.addEventListener('click', () => {
            container.scrollBy({ left: 100, behavior: 'smooth' });
        });
        
        // Update indicator visibility based on scroll position
        const updateIndicators = () => {
            const { scrollLeft, scrollWidth, clientWidth } = container;
            leftIndicator.style.opacity = scrollLeft > 0 ? '1' : '0.3';
            rightIndicator.style.opacity = scrollLeft < scrollWidth - clientWidth ? '1' : '0.3';
        };
        
        container.addEventListener('scroll', updateIndicators);
        updateIndicators();
    }
    
    optimizeStatsDashboard() {
        const statsDashboard = document.querySelector('#stats-dashboard, .stats-dashboard');
        if (!statsDashboard) return;
        
        // Optimize grid layouts for mobile
        const grids = statsDashboard.querySelectorAll('.grid');
        grids.forEach(grid => {
            const gridStyles = {
                display: 'grid',
                gridTemplateColumns: '1fr',
                gap: '1rem',
                padding: '0 1rem'
            };
            Object.assign(grid.style, gridStyles);
        });
        
        // Optimize stat cards
        const statCards = statsDashboard.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            const cardStyles = {
                padding: '1rem',
                borderRadius: '0.75rem',
                minHeight: '44px',
                boxSizing: 'border-box'
            };
            Object.assign(card.style, cardStyles);
            
            // Optimize stat values
            const statValue = card.querySelector('.stat-value');
            if (statValue) {
                statValue.style.fontSize = '1.125rem';
            }
            
            // Optimize stat labels
            const statLabel = card.querySelector('.stat-label');
            if (statLabel) {
                statLabel.style.fontSize = '0.7rem';
            }
        });
        
        this.optimizedElements.add(statsDashboard);
        this.log('Statistics dashboard optimized for mobile');
    }
    
    /**
     * Add touch-friendly interactions for timeline and buttons
     * Addresses Requirements 8.2
     */
    addTouchFriendlyInteractions() {
        if (!this.isTouch) return;
        
        this.log('Adding touch-friendly interactions');
        
        // Ensure minimum touch target sizes
        this.ensureTouchTargetSizes();
        
        // Add touch feedback
        this.addTouchFeedback();
        
        // Optimize timeline for touch
        this.optimizeTimelineForTouch();
        
        // Add swipe gestures where appropriate
        this.addSwipeGestures();
    }
    
    ensureTouchTargetSizes() {
        const interactiveElements = document.querySelectorAll(
            'button, .btn, a[href], .tab-button, .participant-card, .match-card, .copy-button, .share-button, [role="button"], [tabindex="0"]'
        );
        
        interactiveElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const computedStyle = window.getComputedStyle(element);
            
            // Ensure minimum touch target size
            const minSize = this.config.touchTargetMinSize;
            
            if (rect.width < minSize || rect.height < minSize) {
                const styles = {
                    minHeight: `${minSize}px`,
                    minWidth: `${minSize}px`,
                    padding: 'max(12px, 0.75rem)',
                    boxSizing: 'border-box',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                };
                
                Object.assign(element.style, styles);
                this.optimizedElements.add(element);
            }
        });
        
        this.log(`Ensured touch target sizes for ${interactiveElements.length} elements`);
    }
    
    addTouchFeedback() {
        const touchElements = document.querySelectorAll(
            'button, .btn, .participant-card, .match-card, .tab-button, .copy-button'
        );
        
        touchElements.forEach(element => {
            // Add active state for touch feedback
            element.addEventListener('touchstart', () => {
                element.style.transform = 'scale(0.98)';
                element.style.transition = 'transform 0.1s ease';
            });
            
            element.addEventListener('touchend', () => {
                element.style.transform = '';
            });
            
            element.addEventListener('touchcancel', () => {
                element.style.transform = '';
            });
        });
        
        this.log(`Added touch feedback to ${touchElements.length} elements`);
    }
    
    optimizeTimelineForTouch() {
        const timeline = document.querySelector('.tournament-timeline, .interactive-timeline, [data-timeline]');
        if (!timeline) return;
        
        const timelineItems = timeline.querySelectorAll('.timeline-item, [data-phase]');
        
        timelineItems.forEach(item => {
            const touchStyles = {
                minHeight: '48px',
                padding: '1rem',
                cursor: 'pointer',
                transition: 'transform 0.2s ease',
                borderRadius: '0.75rem',
                boxSizing: 'border-box'
            };
            
            Object.assign(item.style, touchStyles);
            
            // Add touch interactions
            item.addEventListener('touchstart', () => {
                item.style.transform = 'scale(0.98)';
            });
            
            item.addEventListener('touchend', () => {
                item.style.transform = '';
            });
        });
        
        this.optimizedElements.add(timeline);
        this.log('Timeline optimized for touch interactions');
    }
    
    addSwipeGestures() {
        // Add swipe gestures to tab container
        const tabContainer = document.querySelector('.tab-container');
        if (tabContainer) {
            this.addSwipeToElement(tabContainer, {
                onSwipeLeft: () => tabContainer.scrollBy({ left: 100, behavior: 'smooth' }),
                onSwipeRight: () => tabContainer.scrollBy({ left: -100, behavior: 'smooth' })
            });
        }
        
        // Add swipe gestures to registration card
        const registrationCard = document.querySelector('.enhanced-registration-card');
        if (registrationCard && this.isMobile) {
            this.addSwipeToElement(registrationCard, {
                onSwipeDown: () => this.minimizeRegistrationCard(registrationCard),
                onSwipeUp: () => this.expandRegistrationCard(registrationCard)
            });
        }
    }
    
    addSwipeToElement(element, handlers) {
        let startX = 0;
        let startY = 0;
        let startTime = 0;
        
        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            startTime = Date.now();
        });
        
        element.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const endTime = Date.now();
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            const deltaTime = endTime - startTime;
            
            // Minimum swipe distance and maximum time
            const minDistance = 50;
            const maxTime = 300;
            
            if (deltaTime > maxTime) return;
            
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minDistance) {
                // Horizontal swipe
                if (deltaX > 0 && handlers.onSwipeRight) {
                    handlers.onSwipeRight();
                } else if (deltaX < 0 && handlers.onSwipeLeft) {
                    handlers.onSwipeLeft();
                }
            } else if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > minDistance) {
                // Vertical swipe
                if (deltaY > 0 && handlers.onSwipeDown) {
                    handlers.onSwipeDown();
                } else if (deltaY < 0 && handlers.onSwipeUp) {
                    handlers.onSwipeUp();
                }
            }
        });
    }
    
    minimizeRegistrationCard(card) {
        card.style.transform = 'translateY(calc(100% - 60px))';
        card.style.opacity = '0.9';
        card.classList.add('minimized');
    }
    
    expandRegistrationCard(card) {
        card.style.transform = 'translateY(0)';
        card.style.opacity = '1';
        card.classList.remove('minimized');
    }
    
    /**
     * Optimize SVG scaling for mobile viewports
     * Addresses Requirements 8.3
     */
    optimizeSVGScaling() {
        this.log('Optimizing SVG scaling for mobile');
        
        const svgElements = document.querySelectorAll('svg');
        const viewport = this.getViewportDimensions();
        
        svgElements.forEach(svg => {
            const rect = svg.getBoundingClientRect();
            
            // Apply mobile-specific scaling
            if (this.isMobile) {
                const maxWidth = viewport.width * 0.8; // Max 80% of viewport width
                
                if (rect.width > maxWidth) {
                    const scaleFactor = maxWidth / rect.width;
                    
                    const mobileStyles = {
                        maxWidth: `${maxWidth}px`,
                        height: 'auto',
                        transform: `scale(${scaleFactor})`,
                        transformOrigin: 'center',
                        display: 'block',
                        margin: '0 auto'
                    };
                    
                    Object.assign(svg.style, mobileStyles);
                    this.optimizedElements.add(svg);
                }
            }
            
            // Ensure responsive behavior
            if (!svg.style.maxWidth) {
                svg.style.maxWidth = '100%';
                svg.style.height = 'auto';
            }
        });
        
        this.log(`Optimized ${svgElements.length} SVG elements for mobile`);
    }
    
    /**
     * Ensure fast loading times and smooth performance
     * Addresses Requirements 8.4, 8.5
     */
    optimizePerformance() {
        this.log('Optimizing performance for mobile');
        
        // Reduce animation complexity on mobile
        this.optimizeAnimations();
        
        // Optimize images for mobile
        this.optimizeImages();
        
        // Implement lazy loading where appropriate
        this.implementLazyLoading();
        
        // Optimize scroll performance
        this.optimizeScrollPerformance();
        
        // Monitor performance metrics
        this.monitorPerformance();
    }
    
    optimizeAnimations() {
        if (this.isMobile) {
            // Reduce animation duration for better mobile performance
            const style = document.createElement('style');
            style.textContent = `
                @media (max-width: 767px) {
                    * {
                        animation-duration: 0.2s !important;
                        transition-duration: 0.2s !important;
                    }
                    
                    .animate-pulse,
                    .animate-bounce,
                    .animate-spin {
                        animation-duration: 1s !important;
                    }
                }
                
                @media (prefers-reduced-motion: reduce) {
                    * {
                        animation-duration: 0.01ms !important;
                        animation-iteration-count: 1 !important;
                        transition-duration: 0.01ms !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    optimizeImages() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            // Add loading="lazy" for better performance
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
            
            // Optimize for mobile display
            if (this.isMobile && !img.style.maxWidth) {
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
            }
        });
        
        this.log(`Optimized ${images.length} images for mobile performance`);
    }
    
    implementLazyLoading() {
        // Implement intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            const lazyElements = document.querySelectorAll('[data-lazy], .lazy-load');
            
            const lazyObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        
                        // Load the element
                        if (element.dataset.src) {
                            element.src = element.dataset.src;
                            element.removeAttribute('data-src');
                        }
                        
                        element.classList.remove('lazy-load');
                        lazyObserver.unobserve(element);
                    }
                });
            }, {
                rootMargin: '50px'
            });
            
            lazyElements.forEach(element => {
                lazyObserver.observe(element);
            });
            
            this.observers.set('lazy', lazyObserver);
        }
    }
    
    optimizeScrollPerformance() {
        // Add smooth scrolling with touch optimization
        const scrollableElements = document.querySelectorAll('.tab-container, [data-scrollable]');
        
        scrollableElements.forEach(element => {
            element.style.WebkitOverflowScrolling = 'touch';
            element.style.overscrollBehavior = 'contain';
        });
        
        // Throttle scroll events for better performance
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) return;
            
            scrollTimeout = setTimeout(() => {
                scrollTimeout = null;
                // Handle scroll-based optimizations
                this.handleScrollOptimizations();
            }, 16); // ~60fps
        }, { passive: true });
    }
    
    handleScrollOptimizations() {
        // Hide/show registration card based on scroll direction on mobile
        if (this.isMobile) {
            const registrationCard = document.querySelector('.enhanced-registration-card');
            if (registrationCard) {
                const scrollY = window.scrollY;
                const lastScrollY = this.lastScrollY || 0;
                
                if (scrollY > lastScrollY && scrollY > 100) {
                    // Scrolling down - hide card
                    registrationCard.classList.add('scroll-hidden');
                } else {
                    // Scrolling up - show card
                    registrationCard.classList.remove('scroll-hidden');
                }
                
                this.lastScrollY = scrollY;
            }
        }
    }
    
    monitorPerformance() {
        // Monitor key performance metrics
        if ('performance' in window) {
            const startTime = performance.now();
            
            // Monitor layout performance
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.entryType === 'measure') {
                        this.performanceMetrics[entry.name] = entry.duration;
                    }
                });
            });
            
            if (observer.observe) {
                observer.observe({ entryTypes: ['measure'] });
                this.observers.set('performance', observer);
            }
            
            // Measure initial load performance
            window.addEventListener('load', () => {
                const loadTime = performance.now() - startTime;
                this.performanceMetrics.loadTime = loadTime;
                
                if (loadTime > this.config.performanceThresholds.loadTime) {
                    this.log(`Warning: Load time ${loadTime.toFixed(2)}ms exceeds threshold`);
                }
            });
        }
    }
    
    /**
     * Set up responsive monitoring for dynamic adjustments
     */
    setupResponsiveMonitoring() {
        // Monitor viewport changes
        const mediaQuery = window.matchMedia(`(max-width: ${this.config.breakpoints.mobile - 1}px)`);
        
        const handleViewportChange = (e) => {
            const wasMobile = this.isMobile;
            this.isMobile = e.matches;
            
            if (wasMobile !== this.isMobile) {
                this.log(`Viewport changed: Mobile=${this.isMobile}`);
                
                // Re-apply optimizations
                if (this.isMobile) {
                    document.body.classList.add('mobile-device');
                    this.implementMobileLayouts();
                } else {
                    document.body.classList.remove('mobile-device');
                    this.resetDesktopLayouts();
                }
            }
        };
        
        mediaQuery.addListener(handleViewportChange);
        this.observers.set('viewport', mediaQuery);
        
        // Monitor orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
    }
    
    handleOrientationChange() {
        this.log('Orientation changed, re-optimizing layouts');
        
        // Re-calculate viewport dimensions
        this.setupViewportHandling();
        
        // Re-optimize layouts if needed
        if (this.isMobile) {
            this.optimizedElements.forEach(element => {
                // Force layout recalculation
                element.offsetHeight;
            });
        }
    }
    
    resetDesktopLayouts() {
        // Reset mobile-specific styles when switching to desktop
        this.optimizedElements.forEach(element => {
            if (element.classList.contains('tournament-grid')) {
                element.style.gridTemplateColumns = '';
            }
            
            if (element.classList.contains('enhanced-registration-card')) {
                element.style.position = '';
                element.style.bottom = '';
                element.style.left = '';
                element.style.right = '';
            }
        });
    }
    
    /**
     * Get current viewport dimensions
     */
    getViewportDimensions() {
        return {
            width: window.innerWidth || document.documentElement.clientWidth,
            height: window.innerHeight || document.documentElement.clientHeight
        };
    }
    
    /**
     * Get optimization status and metrics
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isMobile: this.isMobile,
            isTouch: this.isTouch,
            optimizedElements: this.optimizedElements.size,
            performanceMetrics: this.performanceMetrics,
            viewport: this.getViewportDimensions()
        };
    }
    
    /**
     * Logging utility
     */
    log(...args) {
        if (this.config.debug) {
            console.log('[MobileOptimizer]', ...args);
        }
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        // Disconnect observers
        this.observers.forEach((observer, key) => {
            if (observer && observer.disconnect) {
                observer.disconnect();
            } else if (observer && observer.removeListener) {
                observer.removeListener();
            }
        });
        this.observers.clear();
        
        // Remove event listeners
        window.removeEventListener('resize', this.setupViewportHandling);
        window.removeEventListener('orientationchange', this.handleOrientationChange);
        
        // Clear optimized elements
        this.optimizedElements.clear();
        
        // Remove device classes
        document.body.classList.remove('mobile-device', 'touch-device');
        
        this.isInitialized = false;
        this.log('Mobile Optimizer destroyed');
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.MobileOptimizer) {
        window.MobileOptimizer = new MobileOptimizer({ debug: true });
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.MobileOptimizer && window.MobileOptimizer.destroy) {
        window.MobileOptimizer.destroy();
    }
});

export default MobileOptimizer;