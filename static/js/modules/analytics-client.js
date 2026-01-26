/**
 * Analytics Client for Tournament Detail Pages
 * Handles client-side analytics tracking including performance, engagement, conversions, and errors
 */

class AnalyticsClient {
    constructor(options = {}) {
        this.options = {
            trackPerformance: true,
            trackEngagement: true,
            trackErrors: true,
            trackConversions: true,
            batchSize: 10,
            flushInterval: 30000, // 30 seconds
            maxRetries: 3,
            ...options
        };
        
        this.sessionId = this.generateSessionId();
        this.pageLoadTime = performance.now();
        this.engagementData = {
            timeOnPage: 0,
            scrollDepth: 0,
            clicksCount: 0,
            registrationButtonClicks: 0,
            shareButtonClicks: 0,
            tabSwitches: 0,
            participantCardClicks: 0,
            bracketPreviewClicks: 0
        };
        
        this.eventQueue = [];
        this.isTracking = true;
        this.retryCount = 0;
        
        this.init();
    }
    
    init() {
        console.log('Analytics Client initialized');
        
        // Track initial page load performance
        if (this.options.trackPerformance) {
            this.trackPageLoadPerformance();
        }
        
        // Set up engagement tracking
        if (this.options.trackEngagement) {
            this.setupEngagementTracking();
        }
        
        // Set up error tracking
        if (this.options.trackErrors) {
            this.setupErrorTracking();
        }
        
        // Set up conversion tracking
        if (this.options.trackConversions) {
            this.setupConversionTracking();
        }
        
        // Set up periodic data flushing
        this.setupPeriodicFlush();
        
        // Track page unload
        this.setupUnloadTracking();
    }
    
    trackPageLoadPerformance() {
        // Wait for page to fully load
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = this.getPerformanceData();
                this.sendAnalyticsData('/tournaments/analytics/performance/', perfData);
            }, 100);
        });
    }
    
    getPerformanceData() {
        const navigation = performance.getEntriesByType('navigation')[0];
        const paint = performance.getEntriesByType('paint');
        
        const data = {
            url: window.location.href,
            loadTime: Math.round(performance.now()),
            screenWidth: screen.width,
            screenHeight: screen.height,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight
        };
        
        if (navigation) {
            data.domContentLoaded = Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart);
        }
        
        // First Paint
        const firstPaint = paint.find(entry => entry.name === 'first-paint');
        if (firstPaint) {
            data.firstPaint = Math.round(firstPaint.startTime);
        }
        
        // First Contentful Paint
        const firstContentfulPaint = paint.find(entry => entry.name === 'first-contentful-paint');
        if (firstContentfulPaint) {
            data.firstContentfulPaint = Math.round(firstContentfulPaint.startTime);
        }
        
        // Largest Contentful Paint (if supported)
        if ('PerformanceObserver' in window) {
            try {
                const observer = new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    if (lastEntry) {
                        data.largestContentfulPaint = Math.round(lastEntry.startTime);
                    }
                });
                observer.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                console.warn('LCP tracking not supported:', e);
            }
        }
        
        return data;
    }
    
    setupEngagementTracking() {
        // Track time on page
        this.startTime = Date.now();
        
        // Track scroll depth
        let maxScrollDepth = 0;
        const trackScroll = this.throttle(() => {
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = Math.round((scrollTop / docHeight) * 100);
            
            if (scrollPercent > maxScrollDepth) {
                maxScrollDepth = scrollPercent;
                this.engagementData.scrollDepth = Math.min(100, maxScrollDepth);
            }
        }, 250);
        
        window.addEventListener('scroll', trackScroll, { passive: true });
        
        // Track clicks
        document.addEventListener('click', (e) => {
            this.engagementData.clicksCount++;
            
            // Track specific element clicks
            const target = e.target.closest('[data-analytics]');
            if (target) {
                const analyticsType = target.dataset.analytics;
                switch (analyticsType) {
                    case 'registration-button':
                        this.engagementData.registrationButtonClicks++;
                        break;
                    case 'share-button':
                        this.engagementData.shareButtonClicks++;
                        break;
                    case 'tab-button':
                        this.engagementData.tabSwitches++;
                        break;
                    case 'participant-card':
                        this.engagementData.participantCardClicks++;
                        break;
                    case 'bracket-preview':
                        this.engagementData.bracketPreviewClicks++;
                        break;
                }
            }
        });
        
        // Track visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.updateTimeOnPage();
                this.flushEngagementData();
            } else {
                this.startTime = Date.now();
            }
        });
    }
    
    setupErrorTracking() {
        // JavaScript errors
        window.addEventListener('error', (e) => {
            this.trackError({
                errorType: 'javascript',
                message: e.message,
                fileName: e.filename,
                lineNumber: e.lineno,
                columnNumber: e.colno,
                stackTrace: e.error ? e.error.stack : '',
                severity: 'high'
            });
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (e) => {
            this.trackError({
                errorType: 'javascript',
                message: `Unhandled Promise Rejection: ${e.reason}`,
                stackTrace: e.reason && e.reason.stack ? e.reason.stack : '',
                severity: 'medium'
            });
        });
        
        // Network errors (fetch failures)
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                if (!response.ok) {
                    this.trackError({
                        errorType: 'network',
                        message: `HTTP ${response.status}: ${response.statusText}`,
                        metadata: {
                            url: args[0],
                            status: response.status,
                            statusText: response.statusText
                        },
                        severity: response.status >= 500 ? 'high' : 'medium'
                    });
                }
                return response;
            } catch (error) {
                this.trackError({
                    errorType: 'network',
                    message: `Network Error: ${error.message}`,
                    metadata: {
                        url: args[0]
                    },
                    severity: 'high'
                });
                throw error;
            }
        };
    }
    
    setupConversionTracking() {
        // Track registration button clicks
        document.addEventListener('click', (e) => {
            const target = e.target.closest('a[href*="register"], button[data-action="register"]');
            if (target) {
                this.trackConversion('registration_started', {
                    buttonText: target.textContent.trim(),
                    buttonLocation: this.getElementLocation(target)
                });
            }
        });
        
        // Track share button clicks
        document.addEventListener('click', (e) => {
            const target = e.target.closest('[data-analytics="share-button"]');
            if (target) {
                const platform = target.dataset.platform || 'unknown';
                this.trackConversion('share_completed', {
                    platform: platform,
                    buttonLocation: this.getElementLocation(target)
                });
            }
        });
        
        // Track form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.matches('[data-analytics="registration-form"]')) {
                this.trackConversion('registration_completed', {
                    formId: form.id,
                    formAction: form.action
                });
            }
        });
    }
    
    setupPeriodicFlush() {
        setInterval(() => {
            this.flushEngagementData();
        }, this.options.flushInterval);
    }
    
    setupUnloadTracking() {
        // Use sendBeacon for reliable data sending on page unload
        window.addEventListener('beforeunload', () => {
            this.updateTimeOnPage();
            this.flushEngagementData(true);
        });
        
        // Fallback for browsers that don't support beforeunload properly
        window.addEventListener('pagehide', () => {
            this.updateTimeOnPage();
            this.flushEngagementData(true);
        });
    }
    
    updateTimeOnPage() {
        if (this.startTime) {
            const timeSpent = Math.round((Date.now() - this.startTime) / 1000);
            this.engagementData.timeOnPage += timeSpent;
        }
    }
    
    flushEngagementData(useBeacon = false) {
        this.updateTimeOnPage();
        
        const data = { ...this.engagementData };
        
        if (useBeacon && navigator.sendBeacon) {
            const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
            navigator.sendBeacon('/tournaments/analytics/engagement/', blob);
        } else {
            this.sendAnalyticsData('/tournaments/analytics/engagement/', data);
        }
        
        // Reset start time
        this.startTime = Date.now();
    }
    
    trackError(errorData) {
        const data = {
            ...errorData,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
        
        this.sendAnalyticsData('/tournaments/analytics/error/', data);
    }
    
    trackConversion(eventType, metadata = {}) {
        const tournamentSlug = this.getTournamentSlug();
        if (!tournamentSlug) {
            console.warn('Cannot track conversion: tournament slug not found');
            return;
        }
        
        const data = {
            eventType: eventType,
            tournamentSlug: tournamentSlug,
            metadata: {
                ...metadata,
                timestamp: new Date().toISOString(),
                url: window.location.href
            }
        };
        
        this.sendAnalyticsData('/tournaments/analytics/conversion/', data);
    }
    
    trackCustomMetric(metricName, metricValue, metricType = 'user_timing', metricUnit = 'ms') {
        const data = {
            metricName: metricName,
            metricValue: metricValue,
            metricType: metricType,
            metricUnit: metricUnit,
            metadata: {
                timestamp: new Date().toISOString(),
                url: window.location.href
            }
        };
        
        this.sendAnalyticsData('/tournaments/analytics/metric/', data);
    }
    
    async sendAnalyticsData(endpoint, data) {
        if (!this.isTracking) return;
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Reset retry count on success
            this.retryCount = 0;
            
        } catch (error) {
            console.warn('Analytics tracking failed:', error);
            
            // Retry logic
            if (this.retryCount < this.options.maxRetries) {
                this.retryCount++;
                setTimeout(() => {
                    this.sendAnalyticsData(endpoint, data);
                }, 1000 * this.retryCount);
            } else {
                console.error('Analytics tracking failed after retries:', error);
            }
        }
    }
    
    getTournamentSlug() {
        // Extract tournament slug from URL
        const pathParts = window.location.pathname.split('/');
        const tournamentsIndex = pathParts.indexOf('tournaments');
        
        if (tournamentsIndex !== -1 && pathParts[tournamentsIndex + 1]) {
            return pathParts[tournamentsIndex + 1];
        }
        
        // Fallback to data attribute
        return document.body.dataset.tournamentSlug || null;
    }
    
    getElementLocation(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: Math.round(rect.left + window.pageXOffset),
            y: Math.round(rect.top + window.pageYOffset),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        };
    }
    
    generateSessionId() {
        return 'analytics_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Public API methods
    
    /**
     * Manually track a conversion event
     */
    conversion(eventType, metadata = {}) {
        this.trackConversion(eventType, metadata);
    }
    
    /**
     * Manually track a custom performance metric
     */
    metric(name, value, type = 'user_timing', unit = 'ms') {
        this.trackCustomMetric(name, value, type, unit);
    }
    
    /**
     * Manually track an error
     */
    error(message, type = 'javascript', severity = 'medium', metadata = {}) {
        this.trackError({
            errorType: type,
            message: message,
            severity: severity,
            metadata: metadata
        });
    }
    
    /**
     * Stop tracking (for privacy compliance)
     */
    stop() {
        this.isTracking = false;
        console.log('Analytics tracking stopped');
    }
    
    /**
     * Resume tracking
     */
    start() {
        this.isTracking = true;
        console.log('Analytics tracking resumed');
    }
    
    /**
     * Get current engagement data
     */
    getEngagementData() {
        this.updateTimeOnPage();
        return { ...this.engagementData };
    }
    
    destroy() {
        this.stop();
        this.flushEngagementData();
        console.log('Analytics Client destroyed');
    }
}

// Auto-initialize if not in test environment
if (typeof window !== 'undefined' && !window.TESTING) {
    document.addEventListener('DOMContentLoaded', () => {
        // Check for opt-out
        const optOut = localStorage.getItem('analytics-opt-out') === 'true';
        if (!optOut) {
            window.AnalyticsClient = new AnalyticsClient();
        }
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsClient;
}