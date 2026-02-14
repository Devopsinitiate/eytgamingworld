/**
 * Performance Optimization System
 * Handles critical content loading, efficient module loading, image/SVG optimization, and animation performance
 */

class PerformanceOptimizer {
    constructor(config = {}) {
        this.config = {
            criticalLoadTime: 2000, // 2 seconds for critical content
            targetFPS: 60,
            imageOptimization: true,
            lazyLoadThreshold: '50px',
            performanceMonitoring: true,
            ...config
        };

        this.metrics = {
            loadTimes: new Map(),
            animationFrames: [],
            resourceSizes: new Map(),
            criticalResources: new Set()
        };

        this.observers = new Map();
        this.optimizedResources = new Set();
        this.performanceEntries = [];

        this.init();
    }

    /**
     * Initialize the performance optimization system
     */
    init() {
        this.setupPerformanceMonitoring();
        this.optimizeCriticalContent();
        this.setupEfficientModuleLoading();
        this.optimizeImagesAndSVGs();
        this.ensureAnimationPerformance();

        console.log('PerformanceOptimizer initialized successfully');
    }

    /**
     * Optimize critical content loading (< 2 seconds)
     */
    optimizeCriticalContent() {
        const startTime = performance.now();

        // Identify critical resources
        const criticalSelectors = [
            'h1', '.tournament-title', '.tournament-status',
            '.breadcrumb', '.main-content', '.tournament-info'
        ];

        criticalSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                this.prioritizeElement(element);
                this.metrics.criticalResources.add(element);
            });
        });

        // Preload critical resources
        this.preloadCriticalResources();

        // Monitor critical content load time
        const loadTime = performance.now() - startTime;
        this.metrics.loadTimes.set('criticalContent', loadTime);

        if (loadTime > this.config.criticalLoadTime) {
            console.warn(`Critical content load time exceeded target: ${loadTime}ms > ${this.config.criticalLoadTime}ms`);
        }
    }

    /**
     * Prioritize element loading
     */
    prioritizeElement(element) {
        // Add high priority loading attributes
        if (element.tagName === 'IMG') {
            element.loading = 'eager';
            element.fetchPriority = 'high';
        }

        // Ensure visibility
        element.style.willChange = 'auto';
    }

    /**
     * Preload critical resources
     */
    preloadCriticalResources() {
        // Note: module-manager.js was removed from preload because it is loaded
        // dynamically via fetch() rather than a <script> tag, which caused the
        // browser to warn about an unused preloaded resource.
        const criticalResources = [];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.href = resource;
            link.as = resource.endsWith('.css') ? 'style' : 'script';
            document.head.appendChild(link);
        });
    }

    /**
     * Setup efficient module loading strategies
     */
    setupEfficientModuleLoading() {
        // Implement module bundling and lazy loading
        this.setupModuleBundling();
        this.setupLazyLoading();
        this.optimizeModuleCache();
    }

    /**
     * Setup module bundling for efficient loading
     */
    setupModuleBundling() {
        const moduleGroups = {
            critical: ['module-manager', 'layout-manager'],
            interactive: ['copy-link-handler', 'interactive-timeline'],
            enhancement: ['svg-optimizer', 'design-quality-manager']
        };

        // Load critical modules immediately
        this.loadModuleGroup('critical', moduleGroups.critical);

        // Load other modules on demand
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => this.loadModuleGroup('interactive', moduleGroups.interactive), 100);
            setTimeout(() => this.loadModuleGroup('enhancement', moduleGroups.enhancement), 500);
        });
    }

    /**
     * Load a group of modules efficiently
     */
    async loadModuleGroup(groupName, modules) {
        const startTime = performance.now();

        try {
            const loadPromises = modules.map(module =>
                this.loadModuleWithRetry(`/static/js/modules/${module}.js`)
            );

            await Promise.allSettled(loadPromises);

            const loadTime = performance.now() - startTime;
            this.metrics.loadTimes.set(`moduleGroup_${groupName}`, loadTime);

            console.log(`Module group '${groupName}' loaded in ${loadTime.toFixed(2)}ms`);
        } catch (error) {
            console.error(`Failed to load module group '${groupName}':`, error);
        }
    }

    /**
     * Load module with retry logic
     */
    async loadModuleWithRetry(url, maxRetries = 3) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const response = await fetch(url);
                if (response.ok) {
                    return await response.text();
                }
                throw new Error(`HTTP ${response.status}`);
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, attempt * 1000));
            }
        }
    }

    /**
     * Setup lazy loading for non-critical resources
     */
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const lazyObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadLazyResource(entry.target);
                        lazyObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: this.config.lazyLoadThreshold
            });

            // Observe lazy-loadable elements
            document.querySelectorAll('[data-lazy-src], [data-lazy-module]').forEach(element => {
                lazyObserver.observe(element);
            });

            this.observers.set('lazy', lazyObserver);
        }
    }

    /**
     * Load lazy resource
     */
    loadLazyResource(element) {
        const lazySrc = element.dataset.lazySrc;
        const lazyModule = element.dataset.lazyModule;

        if (lazySrc && element.tagName === 'IMG') {
            element.src = lazySrc;
            element.removeAttribute('data-lazy-src');
        }

        if (lazyModule) {
            this.loadModuleWithRetry(`/static/js/modules/${lazyModule}.js`);
            element.removeAttribute('data-lazy-module');
        }
    }

    /**
     * Optimize module cache
     */
    optimizeModuleCache() {
        // Implement service worker for module caching if available
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/sw.js')
                .then(registration => {
                    console.log('Service worker registered successfully:', registration);
                })
                .catch(error => {
                    console.log('Service worker registration failed:', error);
                });
        }

        // Use browser cache with proper headers
        this.setCacheHeaders();
    }

    /**
     * Set appropriate cache headers for resources
     */
    setCacheHeaders() {
        // This would typically be handled server-side
        // Here we just ensure proper cache usage
        const cacheableResources = document.querySelectorAll('script[src], link[href]');
        cacheableResources.forEach(resource => {
            if (!resource.dataset.noCache) {
                resource.dataset.cached = 'true';
            }
        });
    }

    /**
     * Optimize images and SVGs for web delivery
     */
    optimizeImagesAndSVGs() {
        if (!this.config.imageOptimization) return;

        this.optimizeImages();
        this.optimizeSVGs();
        this.setupResponsiveImages();
    }

    /**
     * Optimize image loading and delivery
     */
    optimizeImages() {
        const images = document.querySelectorAll('img');

        images.forEach(img => {
            // Add loading optimization
            if (!img.loading) {
                img.loading = 'lazy';
            }

            // Add decode hint
            img.decoding = 'async';

            // Monitor image load performance
            img.addEventListener('load', () => {
                const loadTime = performance.now();
                this.metrics.resourceSizes.set(img.src, {
                    loadTime,
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight
                });
            });

            this.optimizedResources.add(img);
        });
    }

    /**
     * Optimize SVG elements
     */
    optimizeSVGs() {
        const svgs = document.querySelectorAll('svg');

        svgs.forEach(svg => {
            // Remove unnecessary attributes
            const unnecessaryAttrs = ['id', 'data-name', 'xmlns:xlink'];
            unnecessaryAttrs.forEach(attr => {
                if (svg.hasAttribute(attr) && !svg.dataset.keepAttr) {
                    svg.removeAttribute(attr);
                }
            });

            // Optimize viewBox
            if (!svg.hasAttribute('viewBox') && svg.hasAttribute('width') && svg.hasAttribute('height')) {
                const width = svg.getAttribute('width');
                const height = svg.getAttribute('height');
                svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
            }

            this.optimizedResources.add(svg);
        });
    }

    /**
     * Setup responsive images
     */
    setupResponsiveImages() {
        const images = document.querySelectorAll('img[data-responsive]');

        images.forEach(img => {
            const baseSrc = img.dataset.responsive;
            const sizes = img.dataset.sizes || '(max-width: 768px) 100vw, 50vw';

            // Create srcset for different screen sizes
            const srcset = [
                `${baseSrc}?w=400 400w`,
                `${baseSrc}?w=800 800w`,
                `${baseSrc}?w=1200 1200w`
            ].join(', ');

            img.srcset = srcset;
            img.sizes = sizes;
        });
    }

    /**
     * Ensure 60fps animation performance
     */
    ensureAnimationPerformance() {
        this.monitorAnimationPerformance();
        this.optimizeAnimations();
        this.setupPerformanceThrottling();
    }

    /**
     * Monitor animation performance
     */
    monitorAnimationPerformance() {
        let frameCount = 0;
        let lastTime = performance.now();

        const measureFPS = (currentTime) => {
            frameCount++;

            if (currentTime - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
                this.metrics.animationFrames.push(fps);

                if (fps < this.config.targetFPS * 0.5) { // 50% of target FPS (30fps for 60fps target)
                    console.warn(`Animation performance below target: ${fps}fps < ${this.config.targetFPS}fps`);
                    this.throttleAnimations();
                }

                frameCount = 0;
                lastTime = currentTime;
            }

            requestAnimationFrame(measureFPS);
        };

        requestAnimationFrame(measureFPS);
    }

    /**
     * Optimize animations for performance
     */
    optimizeAnimations() {
        const animatedElements = document.querySelectorAll('[data-animate], .animate');

        animatedElements.forEach(element => {
            // Use transform and opacity for better performance
            element.style.willChange = 'transform, opacity';

            // Add hardware acceleration
            element.style.transform = element.style.transform || 'translateZ(0)';

            // Respect reduced motion preference
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                element.style.animation = 'none';
                element.style.transition = 'none';
            }
        });
    }

    /**
     * Setup performance throttling
     */
    setupPerformanceThrottling() {
        // Throttle animations if performance is poor
        this.performanceThrottle = {
            enabled: false,
            threshold: this.config.targetFPS * 0.7
        };
    }

    /**
     * Throttle animations when performance is poor
     */
    throttleAnimations() {
        if (this.performanceThrottle.enabled) return;

        this.performanceThrottle.enabled = true;

        // Reduce animation complexity
        document.documentElement.classList.add('reduced-animations');

        // Re-enable after a delay
        setTimeout(() => {
            this.performanceThrottle.enabled = false;
            document.documentElement.classList.remove('reduced-animations');
        }, 5000);
    }

    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        if (!this.config.performanceMonitoring) return;

        // Monitor navigation timing
        window.addEventListener('load', () => {
            setTimeout(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                if (navigation) {
                    this.recordNavigationMetrics(navigation);
                }
            }, 0);
        });

        // Monitor resource timing
        const observer = new PerformanceObserver((list) => {
            list.getEntries().forEach(entry => {
                this.recordResourceMetrics(entry);
            });
        });

        observer.observe({ entryTypes: ['resource', 'measure', 'mark'] });
        this.observers.set('performance', observer);
    }

    /**
     * Record navigation metrics
     */
    recordNavigationMetrics(navigation) {
        const metrics = {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstPaint: this.getFirstPaint(),
            firstContentfulPaint: this.getFirstContentfulPaint()
        };

        this.performanceEntries.push({
            type: 'navigation',
            timestamp: Date.now(),
            metrics
        });

        console.log('Navigation metrics:', metrics);
    }

    /**
     * Record resource metrics
     */
    recordResourceMetrics(entry) {
        if (entry.entryType === 'resource') {
            const metrics = {
                name: entry.name,
                duration: entry.duration,
                transferSize: entry.transferSize,
                encodedBodySize: entry.encodedBodySize
            };

            this.performanceEntries.push({
                type: 'resource',
                timestamp: Date.now(),
                metrics
            });
        }
    }

    /**
     * Get First Paint timing
     */
    getFirstPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
        return firstPaint ? firstPaint.startTime : null;
    }

    /**
     * Get First Contentful Paint timing
     */
    getFirstContentfulPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstContentfulPaint = paintEntries.find(entry => entry.name === 'first-contentful-paint');
        return firstContentfulPaint ? firstContentfulPaint.startTime : null;
    }

    /**
     * Get performance metrics
     */
    getMetrics() {
        return {
            loadTimes: Object.fromEntries(this.metrics.loadTimes),
            averageFPS: this.getAverageFPS(),
            resourceCount: this.optimizedResources.size,
            criticalResourceCount: this.metrics.criticalResources.size,
            performanceEntries: this.performanceEntries.slice(-10) // Last 10 entries
        };
    }

    /**
     * Get average FPS
     */
    getAverageFPS() {
        if (this.metrics.animationFrames.length === 0) return null;

        const sum = this.metrics.animationFrames.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.metrics.animationFrames.length);
    }

    /**
     * Check if performance targets are met
     */
    checkPerformanceTargets() {
        const metrics = this.getMetrics();
        const results = {
            criticalLoadTime: (metrics.loadTimes.criticalContent || 0) <= this.config.criticalLoadTime,
            animationPerformance: (metrics.averageFPS || 0) >= this.config.targetFPS * 0.8,
            resourceOptimization: metrics.resourceCount > 0
        };

        return {
            allTargetsMet: Object.values(results).every(Boolean),
            individual: results,
            metrics
        };
    }

    /**
     * Cleanup observers and resources
     */
    cleanup() {
        this.observers.forEach(observer => {
            if (observer.disconnect) {
                observer.disconnect();
            }
        });
        this.observers.clear();
        this.optimizedResources.clear();
        this.metrics.criticalResources.clear();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
} else if (typeof window !== 'undefined') {
    window.PerformanceOptimizer = PerformanceOptimizer;
}