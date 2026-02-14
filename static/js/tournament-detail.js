/**
 * Tournament Detail Page JavaScript
 * Main controller class that orchestrates all components
 * Requirements: 4.2, 8.1, 12.1, 12.4
 */

class TournamentDetailPage {
    constructor() {
        this.tournamentSlug = this.getTournamentSlug();
        this.currentTab = 'details';
        this.updateInterval = null;
        this.components = {};

        this.init();
    }

    init() {
        console.log('🎮 Initializing Tournament Detail Page');

        // Initialize core components in proper order
        this.initializeComponents();

        // Load initial data
        this.loadInitialData();

        console.log('✅ Tournament Detail Page initialized');
    }

    /**
     * Initialize all components in the correct order
     */
    initializeComponents() {
        // Initialize HeroSection component for animations and counters
        this.initHeroSection();

        // Initialize StatisticsDashboard component for real-time updates
        this.initStatisticsDashboard();

        // Initialize TabNavigation component for content switching
        this.initTabNavigation();

        // Initialize TournamentTimeline component for phase countdowns
        this.initTournamentTimeline();

        // Initialize SocialSharing component for platform integration
        this.initSocialSharing();

        // Initialize performance optimizations
        this.initPerformanceOptimizations();

        // Initialize real-time updates
        this.initRealTimeUpdates();

        // Initialize accessibility features
        this.initAccessibility();
    }

    /**
     * Initialize performance optimizations
     */
    initPerformanceOptimizations() {
        // Enable lazy loading for images
        this.initLazyLoading();

        // Initialize progressive loading for tab content
        this.initProgressiveLoading();

        // Set up efficient caching strategies
        this.initCachingStrategies();

        // Initialize intersection observer for performance
        this.initIntersectionObserver();

        // Preload critical resources
        this.preloadCriticalResources();

        console.log('⚡ Performance optimizations initialized');
    }

    /**
     * Initialize lazy loading for images
     */
    initLazyLoading() {
        // Native lazy loading support check
        if ('loading' in HTMLImageElement.prototype) {
            const lazyImages = document.querySelectorAll('img[loading="lazy"]');
            lazyImages.forEach(img => {
                img.addEventListener('load', () => {
                    img.classList.add('loaded');
                });
            });
        } else {
            // Fallback for browsers without native lazy loading
            this.initIntersectionObserverLazyLoading();
        }

        // Lazy load non-critical sections
        this.initSectionLazyLoading();
    }

    /**
     * Fallback lazy loading using Intersection Observer
     */
    initIntersectionObserverLazyLoading() {
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');

        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback: load all images immediately
            lazyImages.forEach(img => {
                img.src = img.dataset.src || img.src;
                img.classList.add('loaded');
            });
        }
    }

    /**
     * Initialize section lazy loading
     */
    initSectionLazyLoading() {
        const lazySections = document.querySelectorAll('.lazy-section');

        if ('IntersectionObserver' in window && lazySections.length > 0) {
            const sectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        sectionObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '100px 0px',
                threshold: 0.1
            });

            lazySections.forEach(section => sectionObserver.observe(section));
        } else {
            // Fallback: show all sections immediately
            lazySections.forEach(section => section.classList.add('visible'));
        }
    }

    /**
     * Initialize progressive loading for tab content
     */
    initProgressiveLoading() {
        this.tabContentCache = new Map();
        this.loadingStates = new Map();

        // Preload the active tab content - support both old and new class names
        const activeTab = document.querySelector('.gaming-tab-item.active, .tab-nav-item.active');
        if (activeTab) {
            const tabId = activeTab.getAttribute('data-tab');
            this.preloadTabContent(tabId);
        }
    }

    /**
     * Preload tab content for better perceived performance
     */
    async preloadTabContent(tabId) {
        if (this.tabContentCache.has(tabId) || this.loadingStates.get(tabId)) {
            return;
        }

        this.loadingStates.set(tabId, true);

        try {
            // Simulate content loading - in real implementation, this would fetch from API
            await new Promise(resolve => setTimeout(resolve, 100));

            const tabPane = document.querySelector(`#${tabId}-tab`);
            if (tabPane && !this.tabContentCache.has(tabId)) {
                this.tabContentCache.set(tabId, tabPane.innerHTML);
            }
        } catch (error) {
            console.warn(`Failed to preload tab content for ${tabId}:`, error);
        } finally {
            this.loadingStates.set(tabId, false);
        }
    }

    /**
     * Initialize efficient caching strategies
     */
    initCachingStrategies() {
        // Statistics caching
        this.statsCache = {
            data: null,
            timestamp: 0,
            ttl: 30000 // 30 seconds
        };

        // Enable browser caching for static assets
        this.enableAssetCaching();

        // Initialize memory-efficient data structures
        this.initDataStructures();
    }

    /**
     * Enable asset caching optimizations
     */
    enableAssetCaching() {
        // Add cache headers for images
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.crossOrigin) {
                img.crossOrigin = 'anonymous';
            }
        });

        // Preconnect to external domains
        this.preconnectExternalDomains();
    }

    /**
     * Preconnect to external domains for faster loading
     */
    preconnectExternalDomains() {
        const domains = [
            'fonts.googleapis.com',
            'fonts.gstatic.com'
        ];

        domains.forEach(domain => {
            const link = document.createElement('link');
            link.rel = 'preconnect';
            link.href = `https://${domain}`;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }

    /**
     * Initialize memory-efficient data structures
     */
    initDataStructures() {
        // Use WeakMap for component references to prevent memory leaks
        this.componentRefs = new WeakMap();

        // Initialize object pools for frequently created objects
        this.objectPools = {
            animations: [],
            events: []
        };
    }

    /**
     * Initialize intersection observer for performance monitoring
     */
    initIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            // Monitor viewport visibility for performance optimizations
            this.viewportObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.handleElementVisible(entry.target);
                    } else {
                        this.handleElementHidden(entry.target);
                    }
                });
            }, {
                rootMargin: '50px',
                threshold: [0, 0.25, 0.5, 0.75, 1]
            });

            // Observe performance-critical elements
            const criticalElements = document.querySelectorAll('.stats-dashboard, .tournament-timeline, .enhanced-participant-grid');
            criticalElements.forEach(element => {
                this.viewportObserver.observe(element);
            });
        }
    }

    /**
     * Handle element becoming visible
     */
    handleElementVisible(element) {
        // Start animations and updates for visible elements
        if (element.classList.contains('stats-dashboard')) {
            this.startStatisticsUpdates();
        } else if (element.classList.contains('tournament-timeline')) {
            this.startTimelineAnimations();
        } else if (element.classList.contains('enhanced-participant-grid')) {
            this.startParticipantAnimations();
        }
    }

    /**
     * Handle element becoming hidden
     */
    handleElementHidden(element) {
        // Pause animations and updates for hidden elements to save resources
        if (element.classList.contains('stats-dashboard')) {
            this.pauseStatisticsUpdates();
        } else if (element.classList.contains('tournament-timeline')) {
            this.pauseTimelineAnimations();
        }
    }

    /**
     * Preload critical resources
     */
    preloadCriticalResources() {
        // Preload critical CSS if not already loaded
        const criticalCSS = document.querySelector('link[href*="tournament-detail.css"]');
        if (criticalCSS && !criticalCSS.dataset.preloaded) {
            criticalCSS.dataset.preloaded = 'true';
        }

        // Preload critical JavaScript modules
        this.preloadJSModules();

        // Prefetch likely next pages
        this.prefetchLikelyPages();
    }

    /**
     * Preload JavaScript modules
     */
    preloadJSModules() {
        // Note: All components are included in the main tournament-detail.js file
        // No separate component files needed for preloading

        // If we had separate component files, they would be preloaded here:
        // const modules = [
        //     '/static/js/components/statistics-dashboard.js',
        //     '/static/js/components/tournament-timeline.js'
        // ];

        // For now, we'll preload other critical resources instead
        const criticalResources = [
            '/static/css/tournament-detail.css'
        ];

        criticalResources.forEach(resource => {
            const link = document.createElement('link');
            if (resource.endsWith('.css')) {
                link.rel = 'preload';
                link.as = 'style';
            } else if (resource.endsWith('.js')) {
                link.rel = 'modulepreload';
            }
            link.href = resource;
            document.head.appendChild(link);
        });
    }

    /**
     * Prefetch likely next pages
     */
    prefetchLikelyPages() {
        // Prefetch tournament registration page if registration is open
        const registrationButton = document.querySelector('.registration-button[href]');
        if (registrationButton) {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = registrationButton.href;
            document.head.appendChild(link);
        }

        // Prefetch bracket page if tournament is in progress
        const bracketTab = document.querySelector('[data-tab="bracket"]');
        if (bracketTab) {
            this.prefetchBracketData();
        }
    }

    /**
     * Prefetch bracket data
     */
    async prefetchBracketData() {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/bracket/`, {
                headers: { 'X-Prefetch': 'true' }
            });

            if (response.ok) {
                const data = await response.json();
                this.tabContentCache.set('bracket', data);
            }
        } catch (error) {
            console.warn('Failed to prefetch bracket data:', error);
        }
    }

    /**
     * Start statistics updates with performance optimization
     */
    startStatisticsUpdates() {
        if (this.statisticsUpdateInterval) return;

        this.statisticsUpdateInterval = setInterval(() => {
            this.updateStatisticsEfficiently();
        }, 30000);
    }

    /**
     * Pause statistics updates to save resources
     */
    pauseStatisticsUpdates() {
        if (this.statisticsUpdateInterval) {
            clearInterval(this.statisticsUpdateInterval);
            this.statisticsUpdateInterval = null;
        }
    }

    /**
     * Update statistics efficiently using caching
     */
    async updateStatisticsEfficiently() {
        const now = Date.now();

        // Check cache first
        if (this.statsCache.data && (now - this.statsCache.timestamp) < this.statsCache.ttl) {
            this.updateStatisticsDisplay(this.statsCache.data);
            return;
        }

        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/stats/`, {
                headers: {
                    'Cache-Control': 'max-age=30',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();

                // Update cache
                this.statsCache = {
                    data: data,
                    timestamp: now,
                    ttl: 30000
                };

                this.updateStatisticsDisplay(data);
            }
        } catch (error) {
            console.warn('Failed to update statistics:', error);
        }
    }

    /**
     * Update statistics display with smooth animations
     */
    updateStatisticsDisplay(data) {
        const dashboard = document.querySelector('.stats-dashboard');
        if (!dashboard) return;

        // Mark as updating for CSS animations
        dashboard.setAttribute('data-updating', 'true');

        // Update values with animation
        if (this.components.statisticsDashboard) {
            this.components.statisticsDashboard.updateStatistics(data);
        }

        // Remove updating state after animation
        setTimeout(() => {
            dashboard.setAttribute('data-updating', 'false');
            dashboard.setAttribute('data-cached', 'true');
        }, 600);
    }

    /**
     * Start timeline animations
     */
    startTimelineAnimations() {
        const timeline = document.querySelector('.tournament-timeline');
        if (timeline && this.components.tournamentTimeline) {
            this.components.tournamentTimeline.startAnimations();
        }
    }

    /**
     * Pause timeline animations
     */
    pauseTimelineAnimations() {
        if (this.components.tournamentTimeline) {
            this.components.tournamentTimeline.pauseAnimations();
        }
    }

    /**
     * Start participant animations
     */
    startParticipantAnimations() {
        const participantCards = document.querySelectorAll('.enhanced-participant-card');
        participantCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animationDelay = `${index * 50}ms`;
                card.classList.add('animate-in');
            }, index * 50);
        });
    }

    /**
     * Initialize HeroSection component for animations and counters
     * Requirements: 4.2
     */
    initHeroSection() {
        const heroElement = document.querySelector('.hero-section');
        if (!heroElement) return;

        this.components.heroSection = new HeroSection(heroElement, {
            tournamentSlug: this.tournamentSlug,
            onStatsUpdate: (stats) => this.handleStatsUpdate(stats)
        });

        console.log('✅ HeroSection component initialized');
    }

    /**
     * Initialize StatisticsDashboard component for real-time updates
     * Requirements: 12.1, 12.4
     */
    initStatisticsDashboard() {
        const dashboardElement = document.querySelector('.stats-dashboard');
        if (!dashboardElement) return;

        this.components.statisticsDashboard = new StatisticsDashboard(dashboardElement, {
            tournamentSlug: this.tournamentSlug,
            updateInterval: 30000, // 30 seconds
            onUpdate: (data) => this.handleDashboardUpdate(data)
        });

        console.log('✅ StatisticsDashboard component initialized');
    }

    /**
     * Initialize TabNavigation component for content switching
     * Requirements: 4.2
     */
    initTabNavigation() {
        const tabElement = document.querySelector('.tab-navigation');
        if (!tabElement) return;

        this.components.tabNavigation = new TabNavigation(tabElement, {
            tournamentSlug: this.tournamentSlug,
            onTabChange: (tabId) => this.handleTabChange(tabId),
            enableMobileScrolling: true,
            enableKeyboardNavigation: true
        });

        console.log('✅ TabNavigation component initialized');
    }

    /**
     * Initialize TournamentTimeline component for phase countdowns
     * Requirements: 12.1, 12.4
     */
    initTournamentTimeline() {
        const timelineElement = document.querySelector('.tournament-timeline');
        if (!timelineElement) return;

        this.components.tournamentTimeline = new TournamentTimeline(timelineElement);

        console.log('✅ TournamentTimeline component initialized');
    }

    /**
     * Initialize SocialSharing component for platform integration
     * Requirements: 8.1
     */
    initSocialSharing() {
        const shareElement = document.querySelector('.social-sharing');
        if (!shareElement) {
            // Create social sharing element if it doesn't exist
            this.createSocialSharingElement();
        }

        this.components.socialSharing = new SocialSharing(shareElement || document.querySelector('.social-sharing'), {
            tournamentSlug: this.tournamentSlug,
            tournamentData: this.getTournamentData(),
            onShare: (platform) => this.handleShare(platform)
        });

        console.log('✅ SocialSharing component initialized');
    }

    /**
     * Create social sharing element if it doesn't exist
     */
    createSocialSharingElement() {
        const heroSection = document.querySelector('.hero-section');
        if (!heroSection) return;

        const shareElement = document.createElement('div');
        shareElement.className = 'social-sharing';
        shareElement.innerHTML = `
            <div class="share-buttons">
                <button class="share-btn" data-platform="copy" aria-label="Copy tournament link">
                    <span class="material-symbols-outlined">link</span>
                </button>
                <button class="share-btn" data-platform="twitter" aria-label="Share on Twitter">
                    <span class="material-symbols-outlined">share</span>
                </button>
                <button class="share-btn" data-platform="discord" aria-label="Share on Discord">
                    <span class="material-symbols-outlined">forum</span>
                </button>
            </div>
        `;

        heroSection.appendChild(shareElement);
    }

    initDynamicBackground(heroSection) {
        const gameColors = heroSection.dataset.gameColors;
        const tournamentStatus = heroSection.dataset.tournamentStatus;
        const isFeatured = heroSection.dataset.isFeatured === 'true';

        if (gameColors) {
            const [primaryColor, secondaryColor] = gameColors.split(',');

            // Apply dynamic gradient if no banner image
            const gradientBg = heroSection.querySelector('.hero-gradient-bg');
            if (gradientBg) {
                gradientBg.style.background = `linear-gradient(135deg, 
                    ${primaryColor} 0%, 
                    ${secondaryColor} 50%, 
                    #0f172a 100%)`;
            }

            // Update pattern colors
            const pattern = heroSection.querySelector('.hero-pattern');
            if (pattern) {
                pattern.style.backgroundImage = `
                    radial-gradient(circle at 25% 25%, ${primaryColor}40 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, ${secondaryColor}40 0%, transparent 50%)
                `;
            }
        }

        // Add status-specific effects
        if (tournamentStatus === 'in_progress') {
            heroSection.classList.add('hero-live');
        } else if (tournamentStatus === 'registration') {
            heroSection.classList.add('hero-registration');
        }

        // Add featured tournament effects
        if (isFeatured) {
            heroSection.classList.add('hero-featured');
        }
    }

    initStatusBadgeAnimations() {
        const statusBadges = document.querySelectorAll('.tournament-status-badge');

        statusBadges.forEach(badge => {
            const status = badge.dataset.status;

            // Add hover effects
            badge.addEventListener('mouseenter', () => {
                badge.style.transform = 'translateY(-2px) scale(1.05)';
            });

            badge.addEventListener('mouseleave', () => {
                badge.style.transform = 'translateY(0) scale(1)';
            });

            // Add click effects for interactive badges
            if (status === 'registration' || status === 'in_progress') {
                badge.addEventListener('click', () => {
                    this.showStatusDetails(status);
                });

                badge.style.cursor = 'pointer';
                badge.setAttribute('tabindex', '0');
                badge.setAttribute('role', 'button');

                // Keyboard support
                badge.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.showStatusDetails(status);
                    }
                });
            }
        });
    }

    initFeaturedBadgeEffects() {
        const featuredBadge = document.querySelector('.featured-badge');
        if (!featuredBadge) return;

        // Add interactive sparkle effect
        featuredBadge.addEventListener('mouseenter', () => {
            featuredBadge.style.transform = 'translateY(-2px) scale(1.05)';

            // Create additional sparkles
            this.createSparkleEffect(featuredBadge);
        });

        featuredBadge.addEventListener('mouseleave', () => {
            featuredBadge.style.transform = 'translateY(0) scale(1)';
        });
    }

    createSparkleEffect(element) {
        const sparkles = 3;

        for (let i = 0; i < sparkles; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = 'sparkle-particle';
            sparkle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: currentColor;
                border-radius: 50%;
                pointer-events: none;
                animation: sparkle-float 1s ease-out forwards;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
            `;

            element.appendChild(sparkle);

            setTimeout(() => {
                if (sparkle.parentNode) {
                    sparkle.parentNode.removeChild(sparkle);
                }
            }, 1000);
        }

        // Add sparkle animation if not already present
        if (!document.querySelector('#sparkle-styles')) {
            const styles = document.createElement('style');
            styles.id = 'sparkle-styles';
            styles.textContent = `
                @keyframes sparkle-float {
                    0% { opacity: 0; transform: translateY(0) scale(0); }
                    50% { opacity: 1; transform: translateY(-10px) scale(1); }
                    100% { opacity: 0; transform: translateY(-20px) scale(0); }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    initMetaInformationEffects() {
        const metaItems = document.querySelectorAll('.meta-item');

        metaItems.forEach(item => {
            item.addEventListener('mouseenter', () => {
                const icon = item.querySelector('.meta-icon');
                if (icon) {
                    icon.style.transform = 'scale(1.1) rotate(5deg)';
                    icon.style.color = '#dc2626'; // Primary light color
                }
            });

            item.addEventListener('mouseleave', () => {
                const icon = item.querySelector('.meta-icon');
                if (icon) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                    icon.style.color = '';
                }
            });
        });
    }

    showStatusDetails(status) {
        let message = '';
        let type = 'info';

        switch (status) {
            case 'registration':
                message = 'Registration is currently open! Click the registration button to join.';
                type = 'success';
                break;
            case 'in_progress':
                message = 'Tournament is live! Check the bracket tab for current matches.';
                type = 'info';
                break;
        }

        if (message) {
            this.showNotification(message, type);
        }
    }

    /**
     * Handle statistics updates from components
     */
    handleStatsUpdate(stats) {
        // Propagate stats to other components that need them
        if (this.components.statisticsDashboard) {
            this.components.statisticsDashboard.updateStatistics(stats);
        }

        // Update social sharing data
        if (this.components.socialSharing) {
            this.components.socialSharing.updateTournamentData(this.getTournamentData());
        }
    }

    /**
     * Handle dashboard updates
     */
    handleDashboardUpdate(data) {
        // Update hero section with new stats
        if (this.components.heroSection) {
            this.components.heroSection.updateStatistics(data);
        }

        // Dispatch custom event for other components
        document.dispatchEvent(new CustomEvent('tournamentStatsUpdated', {
            detail: { data, timestamp: new Date() }
        }));
    }

    /**
     * Handle tab changes
     */
    handleTabChange(tabId) {
        this.currentTab = tabId;

        // Update URL without page reload
        const url = new URL(window.location);
        url.searchParams.set('tab', tabId);
        window.history.replaceState({}, '', url);

        // Track tab change for analytics
        this.trackEvent('tab_change', { tab: tabId });
    }

    /**
     * Handle social sharing
     */
    handleShare(platform) {
        // Track sharing event
        this.trackEvent('tournament_share', { platform });

        // Show success notification
        this.showNotification(`Tournament shared on ${platform}!`, 'success');
    }

    /**
     * Get tournament data for sharing and components
     */
    getTournamentData() {
        const heroSection = document.querySelector('.hero-section');
        const titleElement = document.querySelector('h1');

        return {
            name: titleElement?.textContent || 'Tournament',
            slug: this.tournamentSlug,
            url: window.location.href,
            game: document.querySelector('.game-badge span:last-child')?.textContent || '',
            status: heroSection?.dataset.tournamentStatus || '',
            participants: this.getStatValue('participants') || '0',
            prizePool: this.getStatValue('prize-pool') || '0',
            maxParticipants: this.getStatValue('capacity') || '0',
            date: document.querySelector('.meta-value')?.textContent || ''
        };
    }

    /**
     * Get stat value from dashboard
     */
    getStatValue(statType) {
        const statCard = document.querySelector(`[data-stat="${statType}"]`);
        return statCard?.querySelector('.stat-value')?.textContent || '0';
    }

    /**
     * Track analytics events
     */
    trackEvent(eventName, data = {}) {
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, {
                tournament_slug: this.tournamentSlug,
                ...data
            });
        }
    }

    /**
     * Get tournament slug from URL
     */
    getTournamentSlug() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[pathParts.length - 2] || pathParts[pathParts.length - 1];
    }

    /**
     * Load initial data for the page
     */
    loadInitialData() {
        console.log('Loading initial tournament data...');

        // Set initial tab from URL parameter
        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('tab') || 'details';

        if (this.components.tabNavigation && initialTab !== 'details') {
            this.components.tabNavigation.switchTab(initialTab);
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="material-symbols-outlined">
                    ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
                </span>
                <span>${message}</span>
            </div>
        `;

        // Add notification styles if not already present
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    animation: slideIn 0.3s ease-out;
                }
                .notification-success { background: #059669; }
                .notification-error { background: #dc2626; }
                .notification-info { background: #2563eb; }
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Cleanup and destroy all components
     */
    destroy() {
        console.log('🧹 Cleaning up Tournament Detail Page');

        // Destroy all components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.destroy === 'function') {
                component.destroy();
            }
        });

        // Clear intervals
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Clear components
        this.components = {};

        console.log('✅ Tournament Detail Page cleaned up');
    }

    /**
     * Enhanced Participant Display Component
     */
    initParticipantDisplay() {
        const participantTab = document.querySelector('#participants-tab');
        if (!participantTab) return;

        this.components.participantDisplay = new ParticipantDisplay(participantTab);

        // Initialize participant filters
        const filterButtons = participantTab.querySelectorAll('.filter-btn');
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const filter = button.getAttribute('data-filter');
                this.components.participantDisplay.filterParticipants(filter);

                // Update active filter button
                filterButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });

        // Initialize organizer actions if user is organizer
        this.initOrganizerActions();
    }

    /**
     * Initialize organizer-specific actions for participant management
     */
    initOrganizerActions() {
        const checkInButtons = document.querySelectorAll('.check-in-btn');
        const seedButtons = document.querySelectorAll('.seed-btn');

        // Check-in functionality
        checkInButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                const participantId = button.getAttribute('data-participant-id');
                await this.handleParticipantCheckIn(participantId, button);
            });
        });

        // Seed assignment functionality
        seedButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const participantId = button.getAttribute('data-participant-id');
                this.handleSeedAssignment(participantId, button);
            });
        });
    }

    /**
     * Handle participant check-in
     */
    async handleParticipantCheckIn(participantId, button) {
        try {
            button.disabled = true;
            button.innerHTML = '<span class="material-symbols-outlined text-sm animate-spin">refresh</span><span>Checking In...</span>';

            const response = await fetch(`/tournaments/${this.tournamentSlug}/participants/${participantId}/check-in/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                // Update UI to show checked-in status
                const participantCard = button.closest('.enhanced-participant-card');
                const statusIndicator = participantCard.querySelector('.status-indicator');

                if (statusIndicator) {
                    statusIndicator.classList.remove('pending');
                    statusIndicator.classList.add('checked-in');
                    statusIndicator.innerHTML = '<span class="material-symbols-outlined">check_circle</span>';
                    statusIndicator.setAttribute('aria-label', 'Checked in');
                    statusIndicator.setAttribute('title', 'Participant has checked in');
                }

                // Remove check-in button
                button.remove();

                // Update statistics
                this.components.statisticsDashboard?.updateCheckedInCount();

                // Show success message
                this.showToast('Participant checked in successfully', 'success');
            } else {
                throw new Error('Failed to check in participant');
            }
        } catch (error) {
            console.error('Check-in error:', error);
            this.showToast('Failed to check in participant', 'error');

            // Reset button
            button.disabled = false;
            button.innerHTML = '<span class="material-symbols-outlined text-sm">check_circle</span><span>Check In</span>';
        }
    }

    /**
     * Handle seed assignment
     */
    handleSeedAssignment(participantId, button) {
        const participantCard = button.closest('.enhanced-participant-card');
        const participantName = participantCard.querySelector('.participant-name').textContent;

        const seed = prompt(`Enter seed position for ${participantName}:`);
        if (seed && !isNaN(seed) && parseInt(seed) > 0) {
            this.assignSeed(participantId, parseInt(seed), button);
        }
    }

    /**
     * Assign seed to participant
     */
    async assignSeed(participantId, seed, button) {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/participants/${participantId}/seed/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ seed: seed })
            });

            if (response.ok) {
                // Update seed display
                const participantCard = button.closest('.enhanced-participant-card');
                const nameContainer = participantCard.querySelector('.participant-name-container');

                let seedBadge = nameContainer.querySelector('.seed-badge');
                if (!seedBadge) {
                    seedBadge = document.createElement('span');
                    seedBadge.className = 'seed-badge';
                    nameContainer.appendChild(seedBadge);
                }

                seedBadge.textContent = `#${seed}`;
                seedBadge.setAttribute('aria-label', `Seed position ${seed}`);
                seedBadge.setAttribute('title', `Tournament seed #${seed}`);

                // Update card data attribute
                participantCard.setAttribute('data-seed', seed);

                this.showToast(`Seed #${seed} assigned successfully`, 'success');
            } else {
                throw new Error('Failed to assign seed');
            }
        } catch (error) {
            console.error('Seed assignment error:', error);
            this.showToast('Failed to assign seed', 'error');
        }
    }

    /**
     * Initialize accessibility features and keyboard navigation
     */
    initAccessibility() {
        console.log('🔧 Initializing accessibility features');

        // Initialize keyboard navigation for tabs
        this.initTabKeyboardNavigation();

        // Initialize focus management
        this.initFocusManagement();

        // Initialize screen reader announcements
        this.initScreenReaderSupport();

        // Initialize high contrast mode detection
        this.initHighContrastSupport();

        // Initialize reduced motion support
        this.initReducedMotionSupport();

        console.log('✅ Accessibility features initialized');
    }

    /**
     * Initialize keyboard navigation for tab system
     */
    initTabKeyboardNavigation() {
        const tabButtons = document.querySelectorAll('.gaming-tab-item, .tab-nav-item');

        tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                let targetIndex = index;

                switch (e.key) {
                    case 'ArrowRight':
                    case 'ArrowDown':
                        e.preventDefault();
                        targetIndex = (index + 1) % tabButtons.length;
                        break;
                    case 'ArrowLeft':
                    case 'ArrowUp':
                        e.preventDefault();
                        targetIndex = (index - 1 + tabButtons.length) % tabButtons.length;
                        break;
                    case 'Home':
                        e.preventDefault();
                        targetIndex = 0;
                        break;
                    case 'End':
                        e.preventDefault();
                        targetIndex = tabButtons.length - 1;
                        break;
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        button.click();
                        return;
                    default:
                        return;
                }

                // Update tabindex and focus
                tabButtons.forEach((btn, i) => {
                    btn.setAttribute('tabindex', i === targetIndex ? '0' : '-1');
                    btn.setAttribute('aria-selected', i === targetIndex ? 'true' : 'false');
                });

                tabButtons[targetIndex].focus();
            });
        });
    }

    /**
     * Initialize focus management for dynamic content
     */
    initFocusManagement() {
        // Store the last focused element before tab switches
        let lastFocusedElement = null;

        document.addEventListener('focusin', (e) => {
            lastFocusedElement = e.target;
        });

        // Restore focus after dynamic content loads
        document.addEventListener('tabContentLoaded', (e) => {
            const newContent = e.detail.content;
            const firstFocusable = newContent.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');

            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
    }

    /**
     * Initialize screen reader support and announcements
     */
    initScreenReaderSupport() {
        // Create live region for announcements
        if (!document.querySelector('#sr-announcements')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'sr-announcements';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }

        // Announce tab changes
        document.addEventListener('tabChanged', (e) => {
            const tabName = e.detail.tabName;
            this.announceToScreenReader(`Switched to ${tabName} tab`);
        });

        // Announce statistics updates
        document.addEventListener('statisticsUpdated', (e) => {
            const stats = e.detail.stats;
            this.announceToScreenReader(`Tournament statistics updated. ${stats.participants.registered} participants registered.`);
        });
    }

    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message) {
        const liveRegion = document.querySelector('#sr-announcements');
        if (liveRegion) {
            liveRegion.textContent = message;

            // Clear after announcement
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    /**
     * Initialize high contrast mode support
     */
    initHighContrastSupport() {
        // Detect high contrast mode
        const isHighContrast = window.matchMedia('(prefers-contrast: high)').matches;

        if (isHighContrast) {
            document.documentElement.classList.add('high-contrast');
            console.log('🎨 High contrast mode detected');
        }

        // Listen for changes
        window.matchMedia('(prefers-contrast: high)').addEventListener('change', (e) => {
            if (e.matches) {
                document.documentElement.classList.add('high-contrast');
                this.announceToScreenReader('High contrast mode enabled');
            } else {
                document.documentElement.classList.remove('high-contrast');
                this.announceToScreenReader('High contrast mode disabled');
            }
        });
    }

    /**
     * Initialize reduced motion support
     */
    initReducedMotionSupport() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        if (prefersReducedMotion) {
            document.documentElement.classList.add('reduced-motion');
            console.log('🎭 Reduced motion preference detected');
        }

        // Listen for changes
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            if (e.matches) {
                document.documentElement.classList.add('reduced-motion');
            } else {
                document.documentElement.classList.remove('reduced-motion');
            }
        });
    }

    /**
     * Enhanced tab switching with progressive loading and accessibility support
     */
    switchTab(tabId) {
        const currentTab = document.querySelector('.gaming-tab-item.active, .tab-nav-item.active');
        const targetTab = document.querySelector(`[data-tab="${tabId}"]`);
        const currentPanel = document.querySelector('.tab-pane.active');
        const targetPanel = document.querySelector(`#${tabId}-tab`);

        if (!targetTab || !targetPanel) return;

        // Show loading state for progressive loading
        this.showTabLoadingState(targetPanel);

        // Update tab states
        document.querySelectorAll('.gaming-tab-item, .tab-nav-item').forEach(tab => {
            tab.classList.remove('active');
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');
        });

        targetTab.classList.add('active');
        targetTab.setAttribute('aria-selected', 'true');
        targetTab.setAttribute('tabindex', '0');

        // Update panel states with progressive loading
        document.querySelectorAll('.tab-pane').forEach(panel => {
            panel.classList.remove('active');
            panel.setAttribute('aria-hidden', 'true');
        });

        // Load content progressively
        this.loadTabContentProgressively(tabId, targetPanel).then(() => {
            targetPanel.classList.add('active');
            targetPanel.setAttribute('aria-hidden', 'false');

            // Hide loading state
            this.hideTabLoadingState(targetPanel);

            // Announce change to screen readers
            const tabName = targetTab.textContent.trim();
            this.announceToScreenReader(`Switched to ${tabName} tab`);

            // Dispatch custom event
            document.dispatchEvent(new CustomEvent('tabChanged', {
                detail: { tabId, tabName }
            }));

            // Update current tab reference
            this.currentTab = tabId;

            // Preload adjacent tabs for better UX
            this.preloadAdjacentTabs(tabId);
        });
    }

    /**
     * Show loading state for tab content
     */
    showTabLoadingState(panel) {
        panel.classList.add('loading-content');
        panel.setAttribute('aria-busy', 'true');

        // Add loading skeleton if content is empty
        if (!panel.innerHTML.trim()) {
            panel.innerHTML = `
                <div class="loading-skeleton" style="height: 20px; margin-bottom: 16px; border-radius: 4px;"></div>
                <div class="loading-skeleton" style="height: 100px; border-radius: 8px;"></div>
            `;
        }
    }

    /**
     * Hide loading state for tab content
     */
    hideTabLoadingState(panel) {
        panel.classList.remove('loading-content');
        panel.setAttribute('aria-busy', 'false');

        // Remove loading skeletons
        const skeletons = panel.querySelectorAll('.loading-skeleton');
        skeletons.forEach(skeleton => skeleton.remove());
    }

    /**
     * Load tab content progressively
     */
    async loadTabContentProgressively(tabId, panel) {
        // Check cache first
        if (this.tabContentCache.has(tabId)) {
            const cachedContent = this.tabContentCache.get(tabId);
            if (typeof cachedContent === 'string') {
                panel.innerHTML = cachedContent;
            }
            return;
        }

        // Simulate progressive loading delay for better UX
        await new Promise(resolve => setTimeout(resolve, 150));

        try {
            // Load specific tab content
            switch (tabId) {
                case 'bracket':
                    await this.loadBracketContent(panel);
                    break;
                case 'participants':
                    await this.loadParticipantsContent(panel);
                    break;
                case 'rules':
                    await this.loadRulesContent(panel);
                    break;
                case 'prizes':
                    await this.loadPrizesContent(panel);
                    break;
                default:
                    // Content already loaded in HTML
                    break;
            }

            // Cache the loaded content
            this.tabContentCache.set(tabId, panel.innerHTML);

        } catch (error) {
            console.error(`Failed to load content for tab ${tabId}:`, error);
            this.showTabError(panel, 'Failed to load content. Please try again.');
        }
    }

    /**
     * Load bracket content dynamically
     */
    async loadBracketContent(panel) {
        if (this.tabContentCache.has('bracket-data')) {
            const bracketData = this.tabContentCache.get('bracket-data');
            this.renderBracketContent(panel, bracketData);
            return;
        }

        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/bracket/`);
            if (response.ok) {
                const data = await response.json();
                this.tabContentCache.set('bracket-data', data);
                this.renderBracketContent(panel, data);
            } else {
                throw new Error('Failed to fetch bracket data');
            }
        } catch (error) {
            console.error('Bracket loading error:', error);
            throw error;
        }
    }

    /**
     * Render bracket content
     */
    renderBracketContent(panel, data) {
        if (data.matches && data.matches.length > 0) {
            const bracketHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Tournament Bracket</h3>
                    <div class="bracket-visualization">
                        ${data.matches.map(match => `
                            <div class="bracket-match" data-match-id="${match.id}">
                                <div class="match-participants">
                                    <div class="participant ${match.winner_id === match.participant1_id ? 'winner' : ''}">
                                        ${match.participant1_name || 'TBD'}
                                    </div>
                                    <div class="participant ${match.winner_id === match.participant2_id ? 'winner' : ''}">
                                        ${match.participant2_name || 'TBD'}
                                    </div>
                                </div>
                                <div class="match-score">${match.score || 'vs'}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            panel.innerHTML = bracketHTML;
        } else {
            panel.innerHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Tournament Bracket</h3>
                    <div class="text-center py-8">
                        <span class="material-symbols-outlined text-4xl text-gray-500 mb-4">pending</span>
                        <p class="text-gray-400">Bracket not yet generated</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Load participants content with lazy loading
     */
    async loadParticipantsContent(panel) {
        // Participants are usually loaded with the page, but we can refresh them
        const existingContent = panel.innerHTML;
        if (existingContent && !existingContent.includes('loading-skeleton')) {
            return; // Content already loaded
        }

        // Simulate loading delay
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    /**
     * Load rules content
     */
    async loadRulesContent(panel) {
        // Rules are static content, usually loaded with page
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    /**
     * Load prizes content
     */
    async loadPrizesContent(panel) {
        // Prizes are static content, usually loaded with page
        await new Promise(resolve => setTimeout(resolve, 50));
    }

    /**
     * Show error state for tab content
     */
    showTabError(panel, message) {
        panel.innerHTML = `
            <div class="content-card">
                <div class="text-center py-8">
                    <span class="material-symbols-outlined text-4xl text-red-500 mb-4">error</span>
                    <p class="text-gray-400 mb-4">${message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">
                        <span class="material-symbols-outlined text-sm">refresh</span>
                        Retry
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Preload adjacent tabs for better UX
     */
    preloadAdjacentTabs(currentTabId) {
        const tabButtons = Array.from(document.querySelectorAll('.gaming-tab-item, .tab-nav-item'));
        const currentIndex = tabButtons.findIndex(tab => tab.getAttribute('data-tab') === currentTabId);

        if (currentIndex === -1) return;

        // Preload next and previous tabs
        const adjacentIndices = [currentIndex - 1, currentIndex + 1];

        adjacentIndices.forEach(index => {
            if (index >= 0 && index < tabButtons.length) {
                const tabId = tabButtons[index].getAttribute('data-tab');
                if (tabId && !this.tabContentCache.has(tabId)) {
                    // Preload in background with low priority
                    setTimeout(() => {
                        this.preloadTabContent(tabId);
                    }, 500);
                }
            }
        });
    }

    /**
     * Enhanced Sticky Registration Card Component
     */
    initStickyRegistrationCard() {
        const registrationCard = document.querySelector('.enhanced-registration-card');
        if (!registrationCard) return;

        this.components.stickyRegistrationCard = new StickyRegistrationCard(registrationCard);
    }

    /**
     * Enhanced Social Sharing Integration
     */
    initShareButtons() {
        const shareButtons = document.querySelectorAll('.share-btn');

        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const shareType = button.getAttribute('data-share');
                this.handleShare(shareType);
            });

            // Add keyboard support for accessibility
            button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const shareType = button.getAttribute('data-share');
                    this.handleShare(shareType);
                }
            });
        });

        // Initialize share tracking
        this.initShareTracking();
    }

    async handleShare(type) {
        const url = window.location.href;
        const title = document.querySelector('h1').textContent;
        const tournament = this.getTournamentData();

        // Generate optimized share text with tournament details
        const shareText = this.generateShareText(tournament, type);

        try {
            switch (type) {
                case 'copy':
                    await this.copyToClipboard(url);
                    this.showShareConfirmation('Link copied to clipboard!', 'success');
                    break;

                case 'twitter':
                    const twitterText = this.formatTwitterShare(tournament);
                    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(twitterText)}&url=${encodeURIComponent(url)}&hashtags=EYTGaming,Tournament,Gaming`;
                    window.open(twitterUrl, '_blank', 'width=600,height=400');
                    this.trackShare('twitter');
                    break;

                case 'discord':
                    const discordText = this.formatDiscordShare(tournament, url);
                    await this.copyToClipboard(discordText);
                    this.showShareConfirmation('Tournament info copied for Discord! Paste it in your server.', 'success');
                    this.trackShare('discord');
                    break;

                case 'facebook':
                    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
                    window.open(facebookUrl, '_blank', 'width=600,height=400');
                    this.trackShare('facebook');
                    break;

                default:
                    // Try native Web Share API if available
                    if (navigator.share) {
                        await navigator.share({
                            title: title,
                            text: shareText,
                            url: url
                        });
                        this.trackShare('native');
                    } else {
                        // Fallback to copy
                        await this.copyToClipboard(url);
                        this.showShareConfirmation('Link copied to clipboard!', 'success');
                    }
                    break;
            }
        } catch (error) {
            console.error('Share failed:', error);
            this.showShareConfirmation('Share failed. Please try again.', 'error');
        }
    }

    /**
     * Get tournament data for sharing
     */
    getTournamentData() {
        const heroSection = document.querySelector('.hero-section');
        const statsCards = document.querySelectorAll('.stat-card');

        const tournament = {
            name: document.querySelector('h1').textContent,
            game: document.querySelector('.game-badge span:last-child')?.textContent || '',
            status: heroSection?.dataset.tournamentStatus || '',
            participants: this.getStatValue('participants') || '0',
            prizePool: this.getStatValue('prize-pool') || '0',
            maxParticipants: this.getStatValue('capacity') || '0',
            date: document.querySelector('.meta-value')?.textContent || '',
            venue: document.querySelector('[data-venue]')?.textContent || ''
        };

        return tournament;
    }

    /**
     * Get stat value from dashboard
     */
    getStatValue(statType) {
        const statCard = document.querySelector(`[data-stat="${statType}"]`);
        return statCard?.querySelector('.stat-value')?.textContent || '0';
    }

    /**
     * Generate optimized share text based on platform
     */
    generateShareText(tournament, platform) {
        const baseText = `🎮 ${tournament.name} Tournament`;

        switch (platform) {
            case 'twitter':
                return this.formatTwitterShare(tournament);
            case 'discord':
                return this.formatDiscordShare(tournament);
            case 'facebook':
                return `${baseText} - Join the competition! ${tournament.game ? `Playing ${tournament.game}` : ''}`;
            default:
                return `${baseText} - ${tournament.game ? `${tournament.game} tournament` : 'Gaming tournament'} with ${tournament.participants} participants${tournament.prizePool !== '0' ? ` and ${tournament.prizePool} prize pool` : ''}!`;
        }
    }

    /**
     * Format share text for Twitter (280 character limit)
     */
    formatTwitterShare(tournament) {
        let text = `🎮 ${tournament.name}`;

        if (tournament.game) {
            text += ` - ${tournament.game}`;
        }

        if (tournament.prizePool !== '0') {
            text += ` 💰 ${tournament.prizePool} prize pool`;
        }

        if (tournament.participants !== '0') {
            text += ` 👥 ${tournament.participants}/${tournament.maxParticipants} players`;
        }

        if (tournament.status === 'registration') {
            text += ' 🔥 Registration open!';
        } else if (tournament.status === 'in_progress') {
            text += ' 🚀 Live now!';
        }

        // Ensure we stay under Twitter's character limit (leaving room for URL)
        const maxLength = 240; // Leave room for URL and hashtags
        if (text.length > maxLength) {
            text = text.substring(0, maxLength - 3) + '...';
        }

        return text;
    }

    /**
     * Format share text for Discord gaming communities
     */
    formatDiscordShare(tournament, url = '') {
        let text = `🎮 **${tournament.name}** Tournament\n`;

        if (tournament.game) {
            text += `🎯 **Game:** ${tournament.game}\n`;
        }

        if (tournament.prizePool !== '0') {
            text += `💰 **Prize Pool:** ${tournament.prizePool}\n`;
        }

        if (tournament.participants !== '0') {
            text += `👥 **Players:** ${tournament.participants}/${tournament.maxParticipants}\n`;
        }

        if (tournament.date) {
            text += `📅 **Date:** ${tournament.date}\n`;
        }

        if (tournament.status === 'registration') {
            text += `🔥 **Status:** Registration Open - Join Now!\n`;
        } else if (tournament.status === 'in_progress') {
            text += `🚀 **Status:** Live Tournament!\n`;
        } else if (tournament.status === 'completed') {
            text += `🏆 **Status:** Tournament Completed\n`;
        }

        text += `\n🔗 **Join here:** ${url}`;

        return text;
    }

    /**
     * Enhanced clipboard functionality with fallback
     */
    async copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (error) {
                console.warn('Clipboard API failed, using fallback:', error);
            }
        }

        // Fallback for older browsers or insecure contexts
        return this.fallbackCopyToClipboard(text);
    }

    /**
     * Fallback clipboard method
     */
    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.setAttribute('readonly', '');
        textArea.setAttribute('aria-hidden', 'true');

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful;
        } catch (error) {
            document.body.removeChild(textArea);
            throw error;
        }
    }

    /**
     * Show share confirmation with enhanced feedback
     */
    showShareConfirmation(message, type = 'success') {
        // Create or update existing notification
        let notification = document.querySelector('.share-notification');

        if (!notification) {
            notification = document.createElement('div');
            notification.className = 'share-notification';
            notification.setAttribute('role', 'alert');
            notification.setAttribute('aria-live', 'polite');
            document.body.appendChild(notification);
        }

        notification.className = `share-notification ${type}`;
        notification.textContent = message;

        // Add animation classes
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            ${type === 'success' ? 'background: #059669;' : 'background: #dc2626;'}
        `;

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Track share actions for analytics
     */
    async trackShare(platform) {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/share/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    platform: platform,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                // Update share count display if present
                this.updateShareCount();
            }
        } catch (error) {
            console.warn('Share tracking failed:', error);
            // Don't show error to user for tracking failures
        }
    }

    /**
     * Update share count display
     */
    async updateShareCount() {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/share-count/`);
            if (response.ok) {
                const data = await response.json();
                const shareCountElements = document.querySelectorAll('.share-count');
                shareCountElements.forEach(element => {
                    element.textContent = data.count || 0;
                });
            }
        } catch (error) {
            console.warn('Failed to update share count:', error);
        }
    }

    /**
     * Initialize share tracking and analytics
     */
    initShareTracking() {
        // Track page views for sharing analytics
        this.trackPageView();

        // Update share counts on page load
        this.updateShareCount();
    }

    /**
     * Track page view for analytics
     */
    async trackPageView() {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/view/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    referrer: document.referrer || '',
                    user_agent: navigator.userAgent
                })
            });
        } catch (error) {
            console.warn('Page view tracking failed:', error);
        }
    }

    /**
     * Enhanced Real-time Updates with Connection Management
     */
    initRealTimeUpdates() {
        // Only enable real-time updates for active tournaments
        const statusElement = document.querySelector('.tournament-status-badge');
        if (!statusElement) return;

        const status = statusElement.classList.contains('status-in_progress') ||
            statusElement.classList.contains('status-registration') ||
            statusElement.classList.contains('status-check_in');

        if (status) {
            this.startRealTimeUpdates();
        }
    }

    startRealTimeUpdates() {
        // Initialize connection management
        this.connectionStatus = 'connected';
        this.retryCount = 0;
        this.maxRetries = 5;
        this.retryDelay = 1000; // Start with 1 second

        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.fetchUpdates();
        }, 30000);

        // Also update when page becomes visible
        this.handleVisibilityChange = () => {
            if (!document.hidden) {
                this.fetchUpdates();
            }
        };

        document.addEventListener('visibilitychange', this.handleVisibilityChange);

        // Initial fetch
        this.fetchUpdates();
    }

    async fetchUpdates() {
        try {
            // Show updating indicator
            this.setUpdatingState(true);

            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/updates/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache'
                },
                signal: AbortSignal.timeout(10000) // 10 second timeout
            });

            if (response.ok) {
                const data = await response.json();
                this.handleUpdates(data);
                this.handleConnectionSuccess();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Failed to fetch updates:', error);
            this.handleConnectionError(error);
        } finally {
            this.setUpdatingState(false);
        }
    }

    handleUpdates(data) {
        // Update statistics with smooth animations
        if (data.stats) {
            this.updateStatistics(data.stats);
        }

        // Update matches with real-time information
        if (data.matches && data.matches.length > 0) {
            this.updateMatches(data.matches);
        }

        // Update participants without page refresh
        if (data.participants) {
            this.updateParticipants(data.participants);
        }

        // Update tournament status and timeline progress
        if (data.status) {
            this.updateTournamentStatus(data.status);
        }

        // Update last updated timestamp
        this.updateLastUpdatedTime(data.timestamp);

        // Dispatch custom event for other components
        document.dispatchEvent(new CustomEvent('tournamentUpdated', {
            detail: { data, timestamp: new Date() }
        }));
    }

    updateStatistics(stats) {
        // Update stat cards with animation
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach(card => {
            const statType = card.dataset.stat;
            const value = card.querySelector('.stat-value');
            const progressBar = card.querySelector('.stat-progress-fill');

            if (value && statType) {
                let newValue;

                switch (statType) {
                    case 'participants':
                        newValue = stats.participants?.registered || 0;
                        break;
                    case 'capacity':
                        newValue = stats.participants?.capacity || 0;
                        break;
                    case 'views':
                        newValue = stats.engagement?.views || 0;
                        break;
                    case 'matches':
                        newValue = stats.matches?.completed || 0;
                        break;
                }

                if (newValue !== undefined) {
                    this.animateValueChange(value, newValue);
                }
            }

            // Update progress bars
            if (progressBar && stats.participants) {
                const percentage = stats.participants.percentage_full || 0;
                progressBar.style.width = `${percentage}%`;
                progressBar.setAttribute('aria-label', `Registration progress: ${percentage}% full`);
            }
        });

        // Update detailed statistics in hero section
        const heroStats = document.querySelectorAll('.hero-stat-value');
        heroStats.forEach(element => {
            const statType = element.dataset.stat;
            if (statType && stats.participants) {
                switch (statType) {
                    case 'registered':
                        this.animateValueChange(element, stats.participants.registered);
                        break;
                    case 'checked_in':
                        this.animateValueChange(element, stats.participants.checked_in);
                        break;
                }
            }
        });

        // Announce statistics update to screen readers
        this.announceToScreenReader(`Tournament statistics updated. ${stats.participants?.registered || 0} participants registered.`);
    }

    animateValueChange(element, newValue) {
        const currentValue = parseInt(element.textContent.replace(/[^\d]/g, '')) || 0;

        if (currentValue !== newValue) {
            // Highlight change with brand color
            element.style.transform = 'scale(1.1)';
            element.style.color = '#b91c1c'; // EYTGaming brand color
            element.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                element.textContent = newValue.toLocaleString();
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 150);
        }
    }

    updateMatches(matches) {
        // Update recent matches section if visible
        const recentMatchesContainer = document.querySelector('.recent-matches-list');
        if (recentMatchesContainer && matches.length > 0) {
            // Update match list with new data
            const matchElements = matches.slice(0, 5).map(match => `
                <div class="match-item" data-match-id="${match.id}">
                    <div class="match-participants">
                        <span class="participant ${match.winner === match.participant1 ? 'winner' : ''}">${match.participant1}</span>
                        <span class="vs">vs</span>
                        <span class="participant ${match.winner === match.participant2 ? 'winner' : ''}">${match.participant2}</span>
                    </div>
                    <div class="match-score">${match.score}</div>
                    <div class="match-time">${this.formatMatchTime(match.completed_at)}</div>
                </div>
            `).join('');

            recentMatchesContainer.innerHTML = matchElements;
        }

        // Update bracket information if bracket tab is active
        if (this.currentTab === 'bracket') {
            this.updateBracketMatches(matches);
        }
    }

    updateBracketMatches(matches) {
        // Update bracket matches with real-time status
        matches.forEach(match => {
            const matchElement = document.querySelector(`[data-match-id="${match.id}"]`);
            if (matchElement) {
                // Update match status
                matchElement.className = `bracket-match status-${match.status}`;

                // Update score
                const scoreElement = matchElement.querySelector('.match-score');
                if (scoreElement) {
                    scoreElement.textContent = match.score || 'vs';
                }

                // Update winner highlighting
                const participants = matchElement.querySelectorAll('.participant');
                participants.forEach((participant, index) => {
                    participant.classList.toggle('winner',
                        match.winner && match.winner === (index === 0 ? match.participant1 : match.participant2)
                    );
                });
            }
        });
    }

    updateParticipants(participantData) {
        // Update participant count displays
        const participantCountElements = document.querySelectorAll('.participant-count');
        participantCountElements.forEach(element => {
            this.animateValueChange(element, participantData.count);
        });

        // Update participant list if participants tab is active
        if (this.currentTab === 'participants') {
            this.refreshParticipantList();
        }

        // Update registration card if participant count changed
        this.updateRegistrationCard(participantData);
    }

    async refreshParticipantList() {
        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/participants/`);
            if (response.ok) {
                const data = await response.json();

                // Update participant grid
                const participantGrid = document.querySelector('.enhanced-participant-grid');
                if (participantGrid && data.participants) {
                    // Re-render participant cards with updated data
                    this.renderParticipantCards(participantGrid, data.participants);
                }
            }
        } catch (error) {
            console.warn('Failed to refresh participant list:', error);
        }
    }

    renderParticipantCards(container, participants) {
        const participantHTML = participants.map(participant => `
            <div class="enhanced-participant-card" data-participant-id="${participant.id}">
                <div class="participant-avatar-container">
                    <img src="${participant.user?.avatar_url || '/static/images/default-avatar.png'}" 
                         alt="${participant.display_name} avatar" 
                         class="participant-avatar"
                         loading="lazy">
                    <div class="status-indicator ${participant.checked_in ? 'checked-in' : 'registered'}"
                         aria-label="${participant.checked_in ? 'Checked in' : 'Registered'}"
                         title="${participant.checked_in ? 'Participant has checked in' : 'Participant is registered'}">
                        <span class="material-symbols-outlined">
                            ${participant.checked_in ? 'check_circle' : 'person'}
                        </span>
                    </div>
                </div>
                <div class="participant-info">
                    <div class="participant-name-container">
                        <h4 class="participant-name">${participant.display_name}</h4>
                        ${participant.seed ? `<span class="seed-badge" aria-label="Seed position ${participant.seed}" title="Tournament seed #${participant.seed}">#${participant.seed}</span>` : ''}
                    </div>
                    ${participant.team ? `
                        <div class="team-info">
                            <span class="team-name">${participant.team.name}</span>
                        </div>
                    ` : ''}
                    <div class="participant-meta">
                        <span class="registration-date" title="Registered on ${new Date(participant.registered_at).toLocaleDateString()}">
                            ${this.formatRelativeTime(participant.registered_at)}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = participantHTML;
    }

    updateRegistrationCard(participantData) {
        const registrationCard = document.querySelector('.enhanced-registration-card');
        if (!registrationCard) return;

        // Update spots remaining
        const spotsElement = registrationCard.querySelector('.spots-remaining');
        if (spotsElement && participantData.count !== undefined) {
            const tournament = this.getTournamentData();
            const spotsRemaining = tournament.maxParticipants - participantData.count;
            spotsElement.textContent = spotsRemaining;

            // Update urgency indicator
            const urgencyIndicator = registrationCard.querySelector('.urgency-indicator');
            if (urgencyIndicator) {
                if (spotsRemaining <= 5 && spotsRemaining > 0) {
                    urgencyIndicator.style.display = 'flex';
                    urgencyIndicator.querySelector('.spots-remaining').textContent = spotsRemaining;
                } else {
                    urgencyIndicator.style.display = 'none';
                }
            }
        }
    }

    updateTournamentStatus(status) {
        const statusBadge = document.querySelector('.tournament-status-badge');
        if (statusBadge) {
            // Update status badge classes and content
            statusBadge.className = `tournament-status-badge status-${status.toLowerCase()}`;

            const statusText = statusBadge.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = this.formatStatusText(status);
            }

            // Update ARIA label
            statusBadge.setAttribute('aria-label', `Tournament status: ${this.formatStatusText(status)}`);
        }

        // Update timeline progress if status changed
        this.updateTimelineProgress(status);

        // Announce status change to screen readers
        this.announceToScreenReader(`Tournament status updated to ${this.formatStatusText(status)}`);
    }

    updateTimelineProgress(status) {
        const timeline = document.querySelector('.tournament-timeline');
        if (!timeline) return;

        const phases = timeline.querySelectorAll('.phase-indicator');
        phases.forEach((phase, index) => {
            const phaseStatus = phase.dataset.phase;

            // Update phase status based on tournament status
            if (this.isPhaseCompleted(phaseStatus, status)) {
                phase.classList.add('completed');
                phase.classList.remove('active', 'pending');
            } else if (this.isPhaseActive(phaseStatus, status)) {
                phase.classList.add('active');
                phase.classList.remove('completed', 'pending');
            } else {
                phase.classList.add('pending');
                phase.classList.remove('completed', 'active');
            }
        });

        // Update progress line
        const progressFill = timeline.querySelector('.timeline-progress-fill');
        if (progressFill) {
            const progressPercentage = this.calculateTimelineProgress(status);
            progressFill.style.width = `${progressPercentage}%`;
        }
    }

    isPhaseCompleted(phaseStatus, tournamentStatus) {
        const phaseOrder = ['registration', 'check_in', 'in_progress', 'completed'];
        const phaseIndex = phaseOrder.indexOf(phaseStatus);
        const currentIndex = phaseOrder.indexOf(tournamentStatus);
        return phaseIndex < currentIndex;
    }

    isPhaseActive(phaseStatus, tournamentStatus) {
        return phaseStatus === tournamentStatus;
    }

    calculateTimelineProgress(status) {
        const progressMap = {
            'draft': 0,
            'registration': 25,
            'check_in': 50,
            'in_progress': 75,
            'completed': 100
        };
        return progressMap[status] || 0;
    }

    formatStatusText(status) {
        const statusMap = {
            'draft': 'Draft',
            'registration': 'Registration Open',
            'check_in': 'Check-in Period',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    updateLastUpdatedTime(timestamp) {
        const lastUpdatedElements = document.querySelectorAll('.last-updated');
        lastUpdatedElements.forEach(element => {
            const updateTime = new Date(timestamp);
            element.textContent = `Last updated: ${updateTime.toLocaleTimeString()}`;
            element.setAttribute('title', `Last updated at ${updateTime.toLocaleString()}`);
        });
    }

    formatMatchTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    formatRelativeTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    // Connection Management
    handleConnectionSuccess() {
        this.connectionStatus = 'connected';
        this.retryCount = 0;
        this.retryDelay = 1000;

        // Update connection status indicator
        this.updateConnectionStatus('connected');

        // Hide retry button if visible
        this.hideRetryButton();
    }

    handleConnectionError(error) {
        this.connectionStatus = 'error';
        console.error('Real-time update connection error:', error);

        // Update connection status indicator
        this.updateConnectionStatus('error');

        // Implement exponential backoff for retries
        if (this.retryCount < this.maxRetries) {
            this.retryCount++;
            this.retryDelay = Math.min(this.retryDelay * 2, 30000); // Max 30 seconds

            setTimeout(() => {
                if (this.connectionStatus === 'error') {
                    this.fetchUpdates();
                }
            }, this.retryDelay);

            // Show retry information
            this.showRetryInfo();
        } else {
            // Max retries reached, show manual retry option
            this.showRetryButton();
        }
    }

    updateConnectionStatus(status) {
        const statusIndicators = document.querySelectorAll('.connection-status');
        statusIndicators.forEach(indicator => {
            indicator.className = `connection-status status-${status}`;
            indicator.setAttribute('aria-label', `Connection status: ${status}`);

            const icon = indicator.querySelector('.status-icon');
            if (icon) {
                switch (status) {
                    case 'connected':
                        icon.textContent = 'wifi';
                        icon.style.color = '#059669'; // Green
                        break;
                    case 'error':
                        icon.textContent = 'wifi_off';
                        icon.style.color = '#dc2626'; // Red
                        break;
                    case 'connecting':
                        icon.textContent = 'sync';
                        icon.style.color = '#f59e0b'; // Yellow
                        break;
                }
            }
        });
    }

    setUpdatingState(isUpdating) {
        const dashboard = document.querySelector('.stats-dashboard');
        if (dashboard) {
            dashboard.setAttribute('data-updating', isUpdating.toString());
        }

        // Update loading indicators
        const loadingIndicators = document.querySelectorAll('.update-indicator');
        loadingIndicators.forEach(indicator => {
            if (isUpdating) {
                indicator.classList.add('updating');
                indicator.setAttribute('aria-label', 'Updating tournament data');
            } else {
                indicator.classList.remove('updating');
                indicator.setAttribute('aria-label', 'Tournament data up to date');
            }
        });
    }

    showRetryInfo() {
        const retryInfo = document.querySelector('.retry-info');
        if (retryInfo) {
            retryInfo.textContent = `Retrying in ${Math.ceil(this.retryDelay / 1000)} seconds... (${this.retryCount}/${this.maxRetries})`;
            retryInfo.style.display = 'block';
        }
    }

    showRetryButton() {
        const retryButton = document.querySelector('.retry-button');
        if (retryButton) {
            retryButton.style.display = 'inline-flex';
            retryButton.onclick = () => {
                this.retryCount = 0;
                this.retryDelay = 1000;
                this.fetchUpdates();
                this.hideRetryButton();
            };
        }
    }

    hideRetryButton() {
        const retryButton = document.querySelector('.retry-button');
        if (retryButton) {
            retryButton.style.display = 'none';
        }

        const retryInfo = document.querySelector('.retry-info');
        if (retryInfo) {
            retryInfo.style.display = 'none';
        }
    }

    /**
     * Load bracket data
     */
    async loadBracketData() {
        const bracketContainer = document.querySelector('.bracket-preview');
        if (!bracketContainer) return;

        try {
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/bracket/`);
            if (response.ok) {
                const data = await response.json();
                this.renderBracket(data);
            }
        } catch (error) {
            console.error('Failed to load bracket:', error);
        }
    }

    renderBracket(data) {
        // Simplified bracket rendering
        const container = document.querySelector('.bracket-preview');
        if (data.matches && data.matches.length > 0) {
            container.innerHTML = `
                <div class="bracket-rounds">
                    ${data.matches.map(match => `
                        <div class="bracket-match">
                            <div class="match-participants">
                                <div class="participant">${match.participant1 || 'TBD'}</div>
                                <div class="participant">${match.participant2 || 'TBD'}</div>
                            </div>
                            <div class="match-score">${match.score || 'vs'}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    /**
     * Load participants data
     */
    async loadParticipantsData() {
        // Participants are loaded with initial page, but could be refreshed here
        console.log('Loading participants data...');
    }

    /**
     * Accessibility Features
     */
    initAccessibility() {
        // Set up ARIA attributes
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach((button, index) => {
            button.setAttribute('role', 'tab');
            button.setAttribute('aria-selected', button.classList.contains('active'));
            button.setAttribute('tabindex', button.classList.contains('active') ? '0' : '-1');
        });

        tabPanes.forEach(pane => {
            pane.setAttribute('role', 'tabpanel');
            pane.setAttribute('aria-hidden', !pane.classList.contains('active'));
        });

        // Set up tab list
        const tabList = document.querySelector('.tab-navigation nav');
        if (tabList) {
            tabList.setAttribute('role', 'tablist');
        }
    }

    announceTabChange(tabId) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Switched to ${tabId} tab`;

        document.body.appendChild(announcement);

        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    /**
     * Notifications
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="material-symbols-outlined">
                    ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
                </span>
                <span>${message}</span>
            </div>
        `;

        // Add notification styles if not already present
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 1000;
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    animation: slideIn 0.3s ease-out;
                }
                .notification-success { background: #059669; }
                .notification-error { background: #dc2626; }
                .notification-info { background: #2563eb; }
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Get CSRF token for API requests
     */
    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Use existing global toast function if available
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }

        // Fallback toast implementation
        const toast = document.createElement('div');
        const colors = {
            'success': 'bg-green-600',
            'error': 'bg-red-600',
            'warning': 'bg-yellow-600',
            'info': 'bg-blue-600'
        };

        toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50`;
        toast.textContent = message;
        toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
        toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
        toast.setAttribute('aria-atomic', 'true');

        document.body.appendChild(toast);

        // Fade in
        setTimeout(() => toast.style.opacity = '1', 10);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Cleanup with performance optimizations
     */
    destroy() {
        // Clear all intervals
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        if (this.statisticsUpdateInterval) {
            clearInterval(this.statisticsUpdateInterval);
        }

        // Disconnect observers
        if (this.viewportObserver) {
            this.viewportObserver.disconnect();
        }

        if (this.imageObserver) {
            this.imageObserver.disconnect();
        }

        if (this.sectionObserver) {
            this.sectionObserver.disconnect();
        }

        // Clear caches
        if (this.tabContentCache) {
            this.tabContentCache.clear();
        }

        if (this.statsCache) {
            this.statsCache.data = null;
        }

        // Clear loading states
        if (this.loadingStates) {
            this.loadingStates.clear();
        }

        // Destroy components
        if (this.components.heroSection) {
            this.components.heroSection.destroy();
        }

        if (this.components.statisticsDashboard) {
            this.components.statisticsDashboard.destroy();
        }

        if (this.components.tournamentTimeline) {
            this.components.tournamentTimeline.destroy();
        }

        // Clear component references
        if (this.componentRefs) {
            // WeakMap will be garbage collected automatically
            this.componentRefs = null;
        }

        // Clear object pools
        if (this.objectPools) {
            this.objectPools.animations = [];
            this.objectPools.events = [];
        }

        // Remove event listeners
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);

        console.log('🧹 Tournament Detail Page cleaned up with performance optimizations');
    }
}

/**
 * Hero Section Component Class
 * Handles animations, counters, and dynamic background effects
 * Requirements: 4.2
 */
class HeroSection {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            tournamentSlug: '',
            onStatsUpdate: null,
            ...options
        };
        this.animationFrameId = null;
        this.counters = new Map();

        this.init();
    }

    init() {
        console.log('🎯 Initializing Hero Section');

        this.initCounters();
        this.initDynamicBackground();
        this.initStatusBadgeAnimations();
        this.initFeaturedBadgeEffects();
        this.initParallaxEffect();
        this.initResponsiveText();

        console.log('✅ Hero Section initialized');
    }

    initCounters() {
        const statValues = this.element.querySelectorAll('[data-value]');

        statValues.forEach(element => {
            const targetValue = parseInt(element.dataset.value) || 0;
            this.animateCounter(element, targetValue);
        });
    }

    animateCounter(element, targetValue, duration = 2000) {
        const startValue = 0;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuart);

            element.textContent = this.formatCounterValue(currentValue, element);

            if (progress < 1) {
                this.animationFrameId = requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    formatCounterValue(value, element) {
        // Check if element contains currency
        if (element.textContent.includes('$')) {
            return `$${value.toLocaleString()}`;
        }

        // Check if element is a percentage
        if (element.textContent.includes('%')) {
            return `${value}%`;
        }

        return value.toLocaleString();
    }

    initDynamicBackground() {
        const gameColors = this.element.dataset.gameColors;
        const tournamentStatus = this.element.dataset.tournamentStatus;
        const isFeatured = this.element.dataset.isFeatured === 'true';

        if (gameColors) {
            const [primaryColor, secondaryColor] = gameColors.split(',');

            // Apply dynamic gradient if no banner image
            const gradientBg = this.element.querySelector('.hero-gradient-bg');
            if (gradientBg) {
                gradientBg.style.background = `linear-gradient(135deg, 
                    ${primaryColor} 0%, 
                    ${secondaryColor} 50%, 
                    #0f172a 100%)`;
            }
        }

        // Add status-specific effects
        if (tournamentStatus === 'in_progress') {
            this.element.classList.add('hero-live');
        } else if (tournamentStatus === 'registration') {
            this.element.classList.add('hero-registration');
        }

        // Add featured tournament effects
        if (isFeatured) {
            this.element.classList.add('hero-featured');
        }
    }

    initStatusBadgeAnimations() {
        const statusBadges = this.element.querySelectorAll('.tournament-status-badge');

        statusBadges.forEach(badge => {
            const status = badge.dataset.status;

            // Add hover effects
            badge.addEventListener('mouseenter', () => {
                badge.style.transform = 'translateY(-2px) scale(1.05)';
            });

            badge.addEventListener('mouseleave', () => {
                badge.style.transform = 'translateY(0) scale(1)';
            });

            // Add click effects for interactive badges
            if (status === 'registration' || status === 'in_progress') {
                badge.addEventListener('click', () => {
                    this.showStatusDetails(status);
                });

                badge.style.cursor = 'pointer';
                badge.setAttribute('tabindex', '0');
                badge.setAttribute('role', 'button');

                // Keyboard support
                badge.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        this.showStatusDetails(status);
                    }
                });
            }
        });
    }

    initFeaturedBadgeEffects() {
        const featuredBadge = this.element.querySelector('.featured-badge');
        if (!featuredBadge) return;

        // Add interactive sparkle effect
        featuredBadge.addEventListener('mouseenter', () => {
            featuredBadge.style.transform = 'translateY(-2px) scale(1.05)';
            this.createSparkleEffect(featuredBadge);
        });

        featuredBadge.addEventListener('mouseleave', () => {
            featuredBadge.style.transform = 'translateY(0) scale(1)';
        });
    }

    createSparkleEffect(element) {
        const sparkles = 3;

        for (let i = 0; i < sparkles; i++) {
            const sparkle = document.createElement('div');
            sparkle.className = 'sparkle-particle';
            sparkle.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: currentColor;
                border-radius: 50%;
                pointer-events: none;
                animation: sparkle-float 1s ease-out forwards;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
            `;

            element.appendChild(sparkle);

            setTimeout(() => {
                if (sparkle.parentNode) {
                    sparkle.parentNode.removeChild(sparkle);
                }
            }, 1000);
        }

        // Add sparkle animation if not already present
        if (!document.querySelector('#sparkle-styles')) {
            const styles = document.createElement('style');
            styles.id = 'sparkle-styles';
            styles.textContent = `
                @keyframes sparkle-float {
                    0% { opacity: 0; transform: translateY(0) scale(0); }
                    50% { opacity: 1; transform: translateY(-10px) scale(1); }
                    100% { opacity: 0; transform: translateY(-20px) scale(0); }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    initParallaxEffect() {
        const background = this.element.querySelector('.hero-background');
        if (!background) return;

        const handleScroll = () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;

            background.style.transform = `translateY(${rate}px)`;
        };

        // Throttle scroll events for performance
        let ticking = false;
        const throttledScroll = () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        };

        window.addEventListener('scroll', throttledScroll, { passive: true });
        this.scrollHandler = throttledScroll;
    }

    initResponsiveText() {
        const title = this.element.querySelector('.tournament-title');
        if (!title) return;

        const adjustTitleSize = () => {
            const containerWidth = this.element.offsetWidth;
            const titleLength = title.textContent.length;

            // Adjust font size based on container width and title length
            let fontSize = Math.min(containerWidth / titleLength * 2.5, 96);
            fontSize = Math.max(fontSize, 32); // Minimum font size

            title.style.fontSize = `${fontSize}px`;
        };

        // Adjust on load and resize
        adjustTitleSize();
        window.addEventListener('resize', adjustTitleSize);
        this.resizeHandler = adjustTitleSize;
    }

    showStatusDetails(status) {
        let message = '';
        let type = 'info';

        switch (status) {
            case 'registration':
                message = 'Registration is currently open! Click the registration button to join.';
                type = 'success';
                break;
            case 'in_progress':
                message = 'Tournament is live! Check the bracket tab for current matches.';
                type = 'info';
                break;
        }

        if (message && this.options.onStatsUpdate) {
            // Notify parent component
            this.options.onStatsUpdate({ message, type });
        }
    }

    updateStatistics(stats) {
        if (!stats) return;

        // Update participant count with animation
        if (stats.participants) {
            const participantElements = this.element.querySelectorAll('[data-stat="participants"] .stat-value');
            participantElements.forEach(element => {
                this.animateValueChange(element, stats.participants.registered);
            });
        }

        // Update views with animation
        if (stats.engagement) {
            const viewElements = this.element.querySelectorAll('[data-stat="views"] .stat-value');
            viewElements.forEach(element => {
                this.animateValueChange(element, stats.engagement.views);
            });
        }
    }

    animateValueChange(element, newValue) {
        const currentValue = parseInt(element.textContent.replace(/[^\d]/g, '')) || 0;

        if (currentValue !== newValue) {
            // Highlight change
            element.style.transform = 'scale(1.1)';
            element.style.color = '#dc2626';

            // Animate to new value
            this.animateCounter(element, newValue, 800);

            // Reset styles
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 800);
        }
    }

    destroy() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }

        // Remove event listeners
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
        }

        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }

        // Clear counters
        this.counters.clear();

        console.log('🧹 Hero Section destroyed');
    }
}

/**
 * Statistics Dashboard Component Class
 * Handles real-time updates and visual indicators
 * Requirements: 12.1, 12.4
 */
class StatisticsDashboard {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            tournamentSlug: '',
            updateInterval: 30000,
            onUpdate: null,
            ...options
        };
        this.updateInterval = null;
        this.animationFrameId = null;
        this.cache = {
            data: null,
            timestamp: 0,
            ttl: 30000 // 30 seconds
        };

        this.init();
    }

    init() {
        console.log('📊 Initializing Statistics Dashboard');

        this.initProgressBars();
        this.initCounterAnimations();
        this.initHoverEffects();
        this.initAccessibility();
        this.startRealTimeUpdates();

        console.log('✅ Statistics Dashboard initialized');
    }

    initProgressBars() {
        const progressBars = this.element.querySelectorAll('.stat-progress-fill');

        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';

            // Animate progress bar on load
            setTimeout(() => {
                bar.style.transition = 'width 1.5s ease-out';
                bar.style.width = width;
            }, 500);
        });
    }

    initCounterAnimations() {
        const statValues = this.element.querySelectorAll('.stat-value[data-value]');

        statValues.forEach(element => {
            const targetValue = parseFloat(element.dataset.value) || 0;
            this.animateCounter(element, targetValue);
        });
    }

    animateCounter(element, targetValue, duration = 2000) {
        const startValue = 0;
        const startTime = performance.now();
        const isDecimal = targetValue % 1 !== 0;
        const isCurrency = element.textContent.includes('$');

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (targetValue - startValue) * easeOutQuart;

            // Format the value appropriately
            let displayValue;
            if (isCurrency) {
                displayValue = `$${Math.floor(currentValue).toLocaleString()}`;
            } else if (isDecimal) {
                displayValue = currentValue.toFixed(1);
            } else {
                displayValue = Math.floor(currentValue).toLocaleString();
            }

            element.textContent = displayValue;

            if (progress < 1) {
                this.animationFrameId = requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    initHoverEffects() {
        const statCards = this.element.querySelectorAll('.stat-card');

        statCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px) scale(1.02)';
                card.style.boxShadow = '0 8px 25px rgba(185, 28, 28, 0.15)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                card.style.boxShadow = '';
            });
        });
    }

    initAccessibility() {
        const statCards = this.element.querySelectorAll('.stat-card');

        statCards.forEach(card => {
            const statType = card.dataset.stat;
            const value = card.querySelector('.stat-value').textContent;
            const label = card.querySelector('.stat-label').textContent;

            card.setAttribute('role', 'img');
            card.setAttribute('aria-label', `${label}: ${value}`);
            card.setAttribute('tabindex', '0');

            // Add keyboard support
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.showStatDetails(statType);
                }
            });
        });
    }

    showStatDetails(statType) {
        let message = '';

        switch (statType) {
            case 'participants':
                message = 'Current participant registration status and capacity information.';
                break;
            case 'prize-pool':
                message = 'Total prize pool available for tournament winners.';
                break;
            case 'views':
                message = 'Number of times this tournament page has been viewed.';
                break;
            case 'capacity':
                message = 'Maximum number of participants allowed in this tournament.';
                break;
        }

        if (message && this.options.onUpdate) {
            this.options.onUpdate({ message, type: 'info' });
        }
    }

    startRealTimeUpdates() {
        if (!this.options.tournamentSlug) return;

        // Update immediately
        this.fetchUpdates();

        // Set up interval for regular updates
        this.updateInterval = setInterval(() => {
            this.fetchUpdates();
        }, this.options.updateInterval);

        console.log(`🔄 Real-time updates started (${this.options.updateInterval}ms interval)`);
    }

    async fetchUpdates() {
        try {
            const now = Date.now();

            // Check cache first
            if (this.cache.data && (now - this.cache.timestamp) < this.cache.ttl) {
                this.updateStatistics(this.cache.data);
                return;
            }

            const response = await fetch(`/tournaments/${this.options.tournamentSlug}/api/stats/`, {
                headers: {
                    'Cache-Control': 'max-age=30',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();

                // Update cache
                this.cache = {
                    data: data,
                    timestamp: now,
                    ttl: 30000
                };

                this.updateStatistics(data);

                // Notify parent component
                if (this.options.onUpdate) {
                    this.options.onUpdate(data);
                }
            }
        } catch (error) {
            console.warn('Failed to fetch statistics updates:', error);
        }
    }

    updateStatistics(newStats) {
        if (!newStats) return;

        // Mark as updating for CSS animations
        this.element.setAttribute('data-updating', 'true');

        // Update participant statistics
        if (newStats.participants) {
            this.updateStatCard('participants', newStats.participants.registered);
            this.updateProgressBar(newStats.participants.percentage_full);
        }

        // Update engagement statistics
        if (newStats.engagement) {
            this.updateStatCard('views', newStats.engagement.views);
        }

        // Update match statistics if available
        if (newStats.matches) {
            this.updateStatCard('matches', newStats.matches.completed);
        }

        // Remove updating state after animation
        setTimeout(() => {
            this.element.setAttribute('data-updating', 'false');
        }, 600);
    }

    updateStatCard(statType, newValue) {
        const card = this.element.querySelector(`[data-stat="${statType}"]`);
        if (!card) return;

        const valueElement = card.querySelector('.stat-value');
        if (!valueElement) return;
        const currentValue = parseFloat(valueElement.dataset.value) || 0;

        if (currentValue !== newValue) {
            // Highlight the change
            card.style.borderColor = '#b91c1c';
            card.style.boxShadow = '0 0 20px rgba(185, 28, 28, 0.3)';

            // Update the data attribute
            valueElement.dataset.value = newValue;

            // Animate to new value
            this.animateCounter(valueElement, newValue, 1000);

            // Reset highlighting after animation
            setTimeout(() => {
                card.style.borderColor = '';
                card.style.boxShadow = '';
            }, 1500);
        }
    }

    updateProgressBar(newPercentage) {
        const progressBar = this.element.querySelector('.stat-progress-fill');
        if (!progressBar) return;

        progressBar.style.transition = 'width 0.8s ease-out';
        progressBar.style.width = `${newPercentage}%`;
        progressBar.setAttribute('aria-label', `Registration progress: ${newPercentage}% full`);
    }

    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
            console.log('⏹️ Real-time updates stopped');
        }
    }

    destroy() {
        this.stopRealTimeUpdates();

        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }

        // Clear cache
        this.cache.data = null;

        console.log('🧹 Statistics Dashboard destroyed');
    }
}

/**
 * Enhanced Tab Navigation Component Class
 */
class TabNavigation {
    constructor(element) {
        this.element = element;
        this.tabButtons = element.querySelectorAll('.gaming-tab-item, .tab-nav-item');
        this.tabPanes = document.querySelectorAll('.tab-pane');
        this.currentTab = 'details';
        this.loadingTabs = new Set();

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAccessibility();
        this.setupKeyboardNavigation();
        this.setupMobileScrolling();

        // Set initial active tab
        this.setActiveTab('details', false);
    }

    setupEventListeners() {
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabId = button.getAttribute('data-tab');
                this.switchTab(tabId);
            });

            // Add hover effects
            button.addEventListener('mouseenter', () => {
                if (!button.classList.contains('active')) {
                    button.style.transform = 'translateY(-2px)';
                }
            });

            button.addEventListener('mouseleave', () => {
                if (!button.classList.contains('active')) {
                    button.style.transform = 'translateY(0)';
                }
            });
        });
    }

    setupAccessibility() {
        // Set up ARIA attributes for tab buttons
        this.tabButtons.forEach((button, index) => {
            button.setAttribute('role', 'tab');
            button.setAttribute('aria-controls', `${button.dataset.tab}-tab`);
            button.setAttribute('id', `tab-${button.dataset.tab}`);

            if (index === 0) {
                button.setAttribute('aria-selected', 'true');
                button.setAttribute('tabindex', '0');
            } else {
                button.setAttribute('aria-selected', 'false');
                button.setAttribute('tabindex', '-1');
            }
        });

        // Set up ARIA attributes for tab panels
        this.tabPanes.forEach(pane => {
            pane.setAttribute('role', 'tabpanel');
            const tabId = pane.id.replace('-tab', '');
            pane.setAttribute('aria-labelledby', `tab-${tabId}`);
            pane.setAttribute('tabindex', '0');

            if (pane.id === 'details-tab') {
                pane.setAttribute('aria-hidden', 'false');
            } else {
                pane.setAttribute('aria-hidden', 'true');
            }
        });
    }

    setupKeyboardNavigation() {
        this.tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                let targetIndex = index;

                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        targetIndex = index > 0 ? index - 1 : this.tabButtons.length - 1;
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        targetIndex = index < this.tabButtons.length - 1 ? index + 1 : 0;
                        break;
                    case 'Home':
                        e.preventDefault();
                        targetIndex = 0;
                        break;
                    case 'End':
                        e.preventDefault();
                        targetIndex = this.tabButtons.length - 1;
                        break;
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        this.switchTab(button.dataset.tab);
                        return;
                    default:
                        return;
                }

                // Focus and activate the target tab
                this.tabButtons[targetIndex].focus();
                this.switchTab(this.tabButtons[targetIndex].dataset.tab);
            });
        });
    }

    setupMobileScrolling() {
        const tabList = this.element.querySelector('.tab-nav-list');
        if (!tabList) return;

        // Add touch scrolling support
        let isScrolling = false;
        let startX = 0;
        let scrollLeft = 0;

        tabList.addEventListener('touchstart', (e) => {
            isScrolling = true;
            startX = e.touches[0].pageX - tabList.offsetLeft;
            scrollLeft = tabList.scrollLeft;
        }, { passive: true });

        tabList.addEventListener('touchmove', (e) => {
            if (!isScrolling) return;
            e.preventDefault();
            const x = e.touches[0].pageX - tabList.offsetLeft;
            const walk = (x - startX) * 2;
            tabList.scrollLeft = scrollLeft - walk;
        });

        tabList.addEventListener('touchend', () => {
            isScrolling = false;
        });

        // Scroll active tab into view on mobile
        this.scrollActiveTabIntoView();
    }

    switchTab(tabId) {
        if (this.currentTab === tabId) return;

        // Show loading state if tab content needs to be loaded
        if (this.shouldLoadTabContent(tabId)) {
            this.showLoadingState(tabId);
        }

        // Update tab button states
        this.setActiveTab(tabId);

        // Update tab panel states with smooth transition
        this.setActivePanel(tabId);

        // Load tab content if needed
        this.loadTabContent(tabId);

        // Update current tab
        this.currentTab = tabId;

        // Scroll active tab into view on mobile
        this.scrollActiveTabIntoView();

        // Announce change for screen readers
        this.announceTabChange(tabId);

        // Track tab switch for analytics
        this.trackTabSwitch(tabId);
    }

    setActiveTab(tabId, updateTabIndex = true) {
        this.tabButtons.forEach(button => {
            const isActive = button.dataset.tab === tabId;

            button.classList.toggle('active', isActive);
            button.setAttribute('aria-selected', isActive.toString());

            if (updateTabIndex) {
                button.setAttribute('tabindex', isActive ? '0' : '-1');
            }
        });
    }

    setActivePanel(tabId) {
        this.tabPanes.forEach(pane => {
            const isActive = pane.id === `${tabId}-tab`;

            if (isActive) {
                // Show the panel with animation
                pane.style.display = 'block';
                pane.setAttribute('aria-hidden', 'false');

                // Trigger reflow for animation
                pane.offsetHeight;

                pane.classList.add('active');
            } else {
                // Hide the panel
                pane.classList.remove('active');
                pane.setAttribute('aria-hidden', 'true');

                // Hide after animation completes
                setTimeout(() => {
                    if (!pane.classList.contains('active')) {
                        pane.style.display = 'none';
                    }
                }, 300);
            }
        });
    }

    shouldLoadTabContent(tabId) {
        // Check if tab content needs dynamic loading
        const tabPane = document.getElementById(`${tabId}-tab`);
        return tabPane && tabPane.dataset.needsLoading === 'true';
    }

    showLoadingState(tabId) {
        const tabPane = document.getElementById(`${tabId}-tab`);
        if (tabPane) {
            tabPane.classList.add('loading');
            this.loadingTabs.add(tabId);
        }
    }

    hideLoadingState(tabId) {
        const tabPane = document.getElementById(`${tabId}-tab`);
        if (tabPane) {
            tabPane.classList.remove('loading');
            this.loadingTabs.delete(tabId);
        }
    }

    async loadTabContent(tabId) {
        if (!this.shouldLoadTabContent(tabId)) {
            return;
        }

        try {
            const tournamentSlug = this.getTournamentSlug();
            let apiUrl = '';

            switch (tabId) {
                case 'bracket':
                    apiUrl = `/tournaments/${tournamentSlug}/api/bracket/`;
                    break;
                case 'participants':
                    apiUrl = `/tournaments/${tournamentSlug}/api/participants/`;
                    break;
                default:
                    return;
            }

            const response = await fetch(apiUrl, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.renderTabContent(tabId, data);
            } else {
                this.renderTabError(tabId);
            }
        } catch (error) {
            console.error(`Failed to load ${tabId} content:`, error);
            this.renderTabError(tabId);
        } finally {
            this.hideLoadingState(tabId);
        }
    }

    renderTabContent(tabId, data) {
        const tabPane = document.getElementById(`${tabId}-tab`);
        if (!tabPane) return;

        switch (tabId) {
            case 'bracket':
                this.renderBracketContent(tabPane, data);
                break;
            case 'participants':
                this.renderParticipantsContent(tabPane, data);
                break;
        }

        // Mark as loaded
        tabPane.dataset.needsLoading = 'false';
    }

    renderBracketContent(container, data) {
        // Simplified bracket rendering
        if (data.matches && data.matches.length > 0) {
            container.innerHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Tournament Bracket</h3>
                    <div class="bracket-rounds">
                        ${data.matches.map(match => `
                            <div class="bracket-match">
                                <div class="match-participants">
                                    <div class="participant">${match.participant1 || 'TBD'}</div>
                                    <div class="participant">${match.participant2 || 'TBD'}</div>
                                </div>
                                <div class="match-score">${match.score || 'vs'}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Tournament Bracket</h3>
                    <div class="text-center py-8">
                        <span class="material-symbols-outlined text-4xl text-gray-500 mb-4">pending</span>
                        <p class="text-gray-400">Bracket not yet generated</p>
                    </div>
                </div>
            `;
        }
    }

    renderParticipantsContent(container, data) {
        if (data.participants && data.participants.length > 0) {
            container.innerHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Participants (${data.participants.length})</h3>
                    <div class="participant-grid">
                        ${data.participants.map(participant => `
                            <div class="participant-card">
                                <div class="flex items-center space-x-3">
                                    ${participant.avatar_url ?
                    `<img src="${participant.avatar_url}" alt="${participant.display_name}" class="w-10 h-10 rounded-full">` :
                    `<div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                                            <span class="material-symbols-outlined text-primary">person</span>
                                        </div>`
                }
                                    <div class="flex-1">
                                        <div class="font-medium text-white">${participant.display_name}</div>
                                        ${participant.team ? `<div class="text-sm text-gray-400">${participant.team}</div>` : ''}
                                    </div>
                                    <div class="flex items-center space-x-2">
                                        ${participant.seed ? `<span class="seed-badge">#${participant.seed}</span>` : ''}
                                        ${participant.checked_in ?
                    `<span class="status-badge checked-in">
                                                <span class="material-symbols-outlined text-xs">check_circle</span>
                                            </span>` : ''
                }
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="content-card">
                    <h3 class="content-card-title">Participants (0)</h3>
                    <div class="text-center py-8">
                        <span class="material-symbols-outlined text-4xl text-gray-500 mb-4">group_off</span>
                        <p class="text-gray-400">No participants yet</p>
                    </div>
                </div>
            `;
        }
    }

    renderTabError(tabId) {
        const tabPane = document.getElementById(`${tabId}-tab`);
        if (!tabPane) return;

        tabPane.innerHTML = `
            <div class="content-card">
                <h3 class="content-card-title">${this.getTabTitle(tabId)}</h3>
                <div class="text-center py-8">
                    <span class="material-symbols-outlined text-4xl text-red-500 mb-4">error</span>
                    <p class="text-gray-400">Failed to load content</p>
                    <button class="btn btn-primary mt-4" onclick="window.tournamentDetailPage.components.tabNavigation.loadTabContent('${tabId}')">
                        Retry
                    </button>
                </div>
            </div>
        `;
    }

    getTabTitle(tabId) {
        const titles = {
            'details': 'Details',
            'bracket': 'Tournament Bracket',
            'participants': 'Participants',
            'rules': 'Tournament Rules',
            'prizes': 'Prize Distribution'
        };
        return titles[tabId] || 'Content';
    }

    scrollActiveTabIntoView() {
        const activeTab = this.element.querySelector('.gaming-tab-item.active, .tab-nav-item.active');
        const tabList = this.element.querySelector('.tab-nav-list, .gaming-tab-nav');

        if (activeTab && tabList && window.innerWidth <= 768) {
            const tabRect = activeTab.getBoundingClientRect();
            const listRect = tabList.getBoundingClientRect();

            if (tabRect.left < listRect.left || tabRect.right > listRect.right) {
                activeTab.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                });
            }
        }
    }

    announceTabChange(tabId) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Switched to ${this.getTabTitle(tabId)} tab`;

        document.body.appendChild(announcement);

        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    trackTabSwitch(tabId) {
        // Analytics tracking for tab switches
        if (typeof gtag !== 'undefined') {
            gtag('event', 'tab_switch', {
                'tab_name': tabId,
                'tournament_slug': this.getTournamentSlug()
            });
        }
    }

    getTournamentSlug() {
        const pathParts = window.location.pathname.split('/');
        return pathParts[pathParts.length - 2] || pathParts[pathParts.length - 1];
    }

    destroy() {
        // Remove event listeners
        this.tabButtons.forEach(button => {
            button.removeEventListener('click', this.handleTabClick);
            button.removeEventListener('keydown', this.handleKeyDown);
            button.removeEventListener('mouseenter', this.handleMouseEnter);
            button.removeEventListener('mouseleave', this.handleMouseLeave);
        });

        // Clear loading states
        this.loadingTabs.clear();
    }
}
/**
 * Tournament Timeline Component Class
 */
class TournamentTimeline {
    constructor(element) {
        this.element = element;
        this.countdownIntervals = new Map();
        this.tournamentStatus = element.dataset.tournamentStatus;
        this.phases = {
            registration: {
                start: new Date(element.dataset.registrationStart),
                end: new Date(element.dataset.registrationEnd)
            },
            check_in: {
                start: new Date(element.dataset.checkInStart)
            },
            tournament: {
                start: new Date(element.dataset.startDatetime),
                end: element.dataset.estimatedEnd ? new Date(element.dataset.estimatedEnd) : null
            }
        };

        this.init();
    }

    init() {
        this.initPhaseInteractions();
        this.initCountdownTimers();
        this.initProgressCalculation();
        this.initAccessibility();

        // Update timeline every minute
        this.updateInterval = setInterval(() => {
            this.updateTimeline();
        }, 60000);
    }

    initPhaseInteractions() {
        const phaseElements = this.element.querySelectorAll('.timeline-phase');

        phaseElements.forEach(phase => {
            const indicator = phase.querySelector('.phase-indicator');
            const phaseType = phase.dataset.phase;

            // Add click handlers for interactive phases
            indicator.addEventListener('click', () => {
                this.showPhaseDetails(phaseType);
            });

            // Add keyboard support
            indicator.setAttribute('tabindex', '0');
            indicator.setAttribute('role', 'button');

            indicator.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.showPhaseDetails(phaseType);
                }
            });

            // Add hover effects
            indicator.addEventListener('mouseenter', () => {
                this.showPhaseTooltip(indicator, phaseType);
            });

            indicator.addEventListener('mouseleave', () => {
                this.hidePhaseTooltip(indicator);
            });
        });
    }

    initCountdownTimers() {
        const countdownElements = this.element.querySelectorAll('.phase-countdown');

        countdownElements.forEach(countdown => {
            const targetStr = countdown.dataset.target;
            if (!targetStr) return;

            const targetDate = new Date(targetStr);
            const timerElement = countdown.querySelector('.countdown-timer');

            if (targetDate && !isNaN(targetDate.getTime()) && timerElement) {
                // Start countdown
                const intervalId = setInterval(() => {
                    const timeRemaining = this.calculateTimeRemaining(targetDate);
                    timerElement.textContent = this.formatTimeRemaining(timeRemaining);

                    // Stop countdown when time is up
                    if (timeRemaining.total <= 0) {
                        clearInterval(intervalId);
                        timerElement.textContent = 'Starting...';
                        this.handlePhaseTransition();
                    }
                }, 1000);

                this.countdownIntervals.set(countdown, intervalId);
            }
        });
    }

    startAnimations() {
        // Resume countdowns if they were paused
        if (this.countdownIntervals.size === 0) {
            this.initCountdownTimers();
        }
    }

    pauseAnimations() {
        // Clear all intervals but keep the target dates
        this.countdownIntervals.forEach(intervalId => {
            clearInterval(intervalId);
        });
        this.countdownIntervals.clear();
    }

    calculateTimeRemaining(targetDate) {
        const now = new Date();
        const total = targetDate - now;

        if (total <= 0) {
            return { total: 0, days: 0, hours: 0, minutes: 0, seconds: 0 };
        }

        const days = Math.floor(total / (1000 * 60 * 60 * 24));
        const hours = Math.floor((total % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((total % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((total % (1000 * 60)) / 1000);

        return { total, days, hours, minutes, seconds };
    }

    formatTimeRemaining(timeRemaining) {
        const { days, hours, minutes, seconds } = timeRemaining;

        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m ${seconds}s`;
        } else {
            return `${minutes}m ${seconds}s`;
        }
    }

    initProgressCalculation() {
        const progressFill = this.element.querySelector('.timeline-progress-fill');
        if (!progressFill) return;

        const progress = this.calculateOverallProgress();

        // Animate progress bar
        setTimeout(() => {
            progressFill.style.width = `${progress}%`;
            progressFill.setAttribute('aria-label', `Tournament progress: ${progress}%`);
        }, 500);
    }

    calculateOverallProgress() {
        const now = new Date();

        switch (this.tournamentStatus) {
            case 'registration':
                // Progress within registration phase (0-25%)
                const regStart = this.phases.registration.start;
                const regEnd = this.phases.registration.end;
                const regProgress = Math.min(25, (now - regStart) / (regEnd - regStart) * 25);
                return Math.max(0, regProgress);

            case 'check_in':
                // Registration complete, check-in active (25-50%)
                return 35;

            case 'in_progress':
                // Tournament active (50-90%)
                const tournamentStart = this.phases.tournament.start;
                const tournamentEnd = this.phases.tournament.end;

                if (tournamentEnd) {
                    const tournamentProgress = (now - tournamentStart) / (tournamentEnd - tournamentStart) * 40;
                    return Math.min(90, 50 + tournamentProgress);
                } else {
                    return 70; // Default progress for active tournament
                }

            case 'completed':
                return 100;

            default:
                return 0;
        }
    }

    showPhaseDetails(phaseType) {
        let message = '';
        let type = 'info';

        switch (phaseType) {
            case 'registration':
                if (this.tournamentStatus === 'registration') {
                    const timeLeft = this.calculateTimeRemaining(this.phases.registration.end);
                    message = `Registration is open! ${this.formatTimeRemaining(timeLeft)} remaining to register.`;
                    type = 'success';
                } else {
                    message = 'Registration phase has ended.';
                }
                break;

            case 'check_in':
                if (this.tournamentStatus === 'check_in') {
                    message = 'Check-in is now open! Please check in before the tournament starts.';
                    type = 'info';
                } else if (this.tournamentStatus === 'registration') {
                    message = 'Check-in will open closer to the tournament start time.';
                } else {
                    message = 'Check-in phase has ended.';
                }
                break;

            case 'tournament':
                if (this.tournamentStatus === 'in_progress') {
                    message = 'Tournament is currently in progress! Check the bracket for live matches.';
                    type = 'info';
                } else if (this.tournamentStatus === 'completed') {
                    message = 'Tournament has finished. Check the results tab for final standings.';
                } else {
                    message = 'Tournament will begin after check-in is complete.';
                }
                break;

            case 'results':
                if (this.tournamentStatus === 'completed') {
                    message = 'Tournament results are now available!';
                    type = 'success';
                } else {
                    message = 'Results will be available after the tournament concludes.';
                }
                break;
        }

        if (message && window.tournamentDetailPage) {
            window.tournamentDetailPage.showNotification(message, type);
        }
    }

    showPhaseTooltip(indicator, phaseType) {
        // Tooltip is handled by CSS :hover pseudo-class
        // This method can be used for additional tooltip enhancements
    }

    hidePhaseTooltip(indicator) {
        // Tooltip hiding is handled by CSS
        // This method can be used for additional tooltip cleanup
    }

    handlePhaseTransition() {
        // Refresh the page or update the timeline when a phase transition occurs
        if (window.tournamentDetailPage) {
            window.tournamentDetailPage.fetchUpdates();
        }
    }

    updateTimeline() {
        // Recalculate progress and update display
        const progressFill = this.element.querySelector('.timeline-progress-fill');
        if (progressFill) {
            const progress = this.calculateOverallProgress();
            progressFill.style.width = `${progress}%`;
            progressFill.setAttribute('aria-label', `Tournament progress: ${progress}%`);
        }

        // Update any dynamic content
        this.updatePhaseStates();
    }

    updatePhaseStates() {
        // This method can be used to update phase states based on current time
        // For now, we rely on server-side updates through the real-time update system
    }

    initAccessibility() {
        // Announce timeline updates for screen readers
        const timeline = this.element;
        timeline.setAttribute('role', 'progressbar');
        timeline.setAttribute('aria-label', 'Tournament timeline progress');

        // Add live region for countdown updates
        const countdownElements = this.element.querySelectorAll('.countdown-timer');
        countdownElements.forEach(timer => {
            timer.setAttribute('aria-live', 'polite');
            timer.setAttribute('aria-atomic', 'true');
        });
    }

    destroy() {
        // Clear all countdown intervals
        this.countdownIntervals.forEach(intervalId => {
            clearInterval(intervalId);
        });
        this.countdownIntervals.clear();

        // Clear update interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Remove event listeners
        const phaseElements = this.element.querySelectorAll('.timeline-phase .phase-indicator');
        phaseElements.forEach(indicator => {
            indicator.removeEventListener('click', this.handlePhaseClick);
            indicator.removeEventListener('keydown', this.handlePhaseKeydown);
            indicator.removeEventListener('mouseenter', this.handlePhaseMouseEnter);
            indicator.removeEventListener('mouseleave', this.handlePhaseMouseLeave);
        });
    }
}

/**
 * Enhanced Participant Display Component Class
 */
class ParticipantDisplay {
    constructor(element) {
        this.element = element;
        this.participants = [];
        this.currentFilter = 'all';

        this.init();
    }

    init() {
        this.cacheParticipants();
        this.setupAccessibility();
    }

    /**
     * Cache participant cards for filtering
     */
    cacheParticipants() {
        const participantCards = this.element.querySelectorAll('.enhanced-participant-card');
        this.participants = Array.from(participantCards).map(card => ({
            element: card,
            type: card.getAttribute('data-participant-type'),
            checkedIn: card.getAttribute('data-checked-in') === 'true',
            seed: card.getAttribute('data-seed')
        }));
    }

    /**
     * Filter participants based on type
     */
    filterParticipants(filter) {
        this.currentFilter = filter;

        this.participants.forEach(participant => {
            let shouldShow = true;

            switch (filter) {
                case 'teams':
                    shouldShow = participant.type === 'team';
                    break;
                case 'individuals':
                    shouldShow = participant.type === 'individual';
                    break;
                case 'checked-in':
                    shouldShow = participant.checkedIn;
                    break;
                case 'all':
                default:
                    shouldShow = true;
                    break;
            }

            if (shouldShow) {
                participant.element.style.display = '';
                participant.element.setAttribute('aria-hidden', 'false');
            } else {
                participant.element.style.display = 'none';
                participant.element.setAttribute('aria-hidden', 'true');
            }
        });

        // Update visible count
        this.updateVisibleCount();

        // Announce filter change to screen readers
        this.announceFilterChange(filter);
    }

    /**
     * Update visible participant count
     */
    updateVisibleCount() {
        const visibleCount = this.participants.filter(p =>
            p.element.style.display !== 'none'
        ).length;

        const titleElement = this.element.querySelector('.content-card-title');
        if (titleElement) {
            const baseText = titleElement.textContent.split('(')[0].trim();
            titleElement.textContent = `${baseText} (${visibleCount} shown)`;
        }
    }

    /**
     * Announce filter changes to screen readers
     */
    announceFilterChange(filter) {
        const visibleCount = this.participants.filter(p =>
            p.element.style.display !== 'none'
        ).length;

        let message = '';
        switch (filter) {
            case 'teams':
                message = `Showing ${visibleCount} team participants`;
                break;
            case 'individuals':
                message = `Showing ${visibleCount} individual participants`;
                break;
            case 'checked-in':
                message = `Showing ${visibleCount} checked-in participants`;
                break;
            case 'all':
            default:
                message = `Showing all ${visibleCount} participants`;
                break;
        }

        // Create temporary announcement element
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;

        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Add keyboard navigation for participant cards
        this.participants.forEach(participant => {
            const card = participant.element;

            // Make cards focusable
            if (!card.hasAttribute('tabindex')) {
                card.setAttribute('tabindex', '0');
            }

            // Add keyboard event listeners
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const viewButton = card.querySelector('.action-btn');
                    if (viewButton) {
                        viewButton.click();
                    }
                }
            });
        });

        // Setup filter button accessibility
        const filterButtons = this.element.querySelectorAll('.filter-btn');
        filterButtons.forEach((button, index) => {
            button.setAttribute('role', 'tab');
            button.setAttribute('aria-selected', button.classList.contains('active'));

            // Keyboard navigation between filter buttons
            button.addEventListener('keydown', (e) => {
                let targetIndex = index;

                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    targetIndex = (index + 1) % filterButtons.length;
                } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    targetIndex = (index - 1 + filterButtons.length) % filterButtons.length;
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    targetIndex = 0;
                } else if (e.key === 'End') {
                    e.preventDefault();
                    targetIndex = filterButtons.length - 1;
                }

                if (targetIndex !== index) {
                    filterButtons[targetIndex].focus();
                }
            });
        });
    }

    /**
     * Update participant data (for real-time updates)
     */
    updateParticipantData(participantData) {
        // Find and update participant card
        const participantCard = this.element.querySelector(`[data-participant-id="${participantData.id}"]`);
        if (!participantCard) return;

        // Update check-in status
        if (participantData.checked_in !== undefined) {
            const statusIndicator = participantCard.querySelector('.status-indicator');
            if (statusIndicator) {
                if (participantData.checked_in) {
                    statusIndicator.classList.remove('pending');
                    statusIndicator.classList.add('checked-in');
                    statusIndicator.innerHTML = '<span class="material-symbols-outlined">check_circle</span>';
                } else {
                    statusIndicator.classList.remove('checked-in');
                    statusIndicator.classList.add('pending');
                    statusIndicator.innerHTML = '<span class="material-symbols-outlined">schedule</span>';
                }
            }
        }

        // Update seed
        if (participantData.seed !== undefined) {
            const nameContainer = participantCard.querySelector('.participant-name-container');
            let seedBadge = nameContainer.querySelector('.seed-badge');

            if (participantData.seed) {
                if (!seedBadge) {
                    seedBadge = document.createElement('span');
                    seedBadge.className = 'seed-badge';
                    nameContainer.appendChild(seedBadge);
                }
                seedBadge.textContent = `#${participantData.seed}`;
                seedBadge.setAttribute('aria-label', `Seed position ${participantData.seed}`);
            } else if (seedBadge) {
                seedBadge.remove();
            }
        }

        // Refresh cached data
        this.cacheParticipants();
    }
}

/**
 * Enhanced Sticky Registration Card Component
 * Handles registration state management, urgency indicators, and real-time updates
 */
class StickyRegistrationCard {
    constructor(element) {
        this.element = element;
        this.tournamentStatus = element.dataset.tournamentStatus;
        this.registrationStatus = element.dataset.registrationStatus;
        this.spotsRemaining = parseInt(element.dataset.spotsRemaining) || 0;
        this.registrationFee = parseFloat(element.dataset.registrationFee) || 0;

        this.updateInterval = null;
        this.urgencyThreshold = 5; // Show urgency when <= 5 spots remain

        this.init();
    }

    init() {
        console.log('🎫 Initializing Sticky Registration Card');

        this.initStickyBehavior();
        this.initUrgencyIndicators();
        this.initRealTimeUpdates();
        this.initAccessibility();
        this.initMobileOptimizations();

        console.log('✅ Sticky Registration Card initialized');
    }

    initStickyBehavior() {
        // Enhanced sticky positioning with scroll detection
        let lastScrollY = window.scrollY;
        let isScrollingDown = false;

        const handleScroll = () => {
            const currentScrollY = window.scrollY;
            isScrollingDown = currentScrollY > lastScrollY;
            lastScrollY = currentScrollY;

            // Add scroll direction class for enhanced animations
            this.element.classList.toggle('scrolling-down', isScrollingDown);
            this.element.classList.toggle('scrolling-up', !isScrollingDown);

            // Handle mobile sticky behavior
            this.handleMobileStickyBehavior(currentScrollY);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });

        // Store cleanup function
        this.cleanup = () => {
            window.removeEventListener('scroll', handleScroll);
        };
    }

    initUrgencyIndicators() {
        if (this.tournamentStatus !== 'registration') return;

        const urgencyIndicator = this.element.querySelector('.urgency-indicator');
        const registrationButton = this.element.querySelector('.registration-button');

        // Update urgency based on spots remaining
        this.updateUrgencyDisplay();

        // Add pulsing animation for very low spots
        if (this.spotsRemaining <= 2 && this.spotsRemaining > 0) {
            this.element.classList.add('critical-urgency');

            // Add critical urgency effects
            if (registrationButton) {
                registrationButton.classList.add('critical-pulse');
            }
        }
    }

    updateUrgencyDisplay() {
        const urgencyIndicator = this.element.querySelector('.urgency-indicator');
        const footerStats = this.element.querySelector('.footer-stats');

        if (this.spotsRemaining <= this.urgencyThreshold && this.spotsRemaining > 0) {
            // Show urgency indicator
            if (urgencyIndicator) {
                urgencyIndicator.style.display = 'flex';

                // Update urgency message based on spots remaining
                const urgencySubtitle = urgencyIndicator.querySelector('.urgency-subtitle');
                if (urgencySubtitle) {
                    const spotsText = this.spotsRemaining === 1 ? 'spot' : 'spots';
                    urgencySubtitle.textContent = `Only ${this.spotsRemaining} ${spotsText} remaining`;
                }
            }

            // Hide spots remaining in footer to avoid redundancy
            if (footerStats) {
                const spotsStatItem = footerStats.querySelector('.stat-item:last-child');
                if (spotsStatItem) {
                    spotsStatItem.style.display = 'none';
                }
            }
        } else {
            // Hide urgency indicator
            if (urgencyIndicator) {
                urgencyIndicator.style.display = 'none';
            }

            // Show spots remaining in footer
            if (footerStats) {
                const spotsStatItem = footerStats.querySelector('.stat-item:last-child');
                if (spotsStatItem) {
                    spotsStatItem.style.display = 'flex';
                }
            }
        }
    }

    initRealTimeUpdates() {
        if (this.tournamentStatus !== 'registration') return;

        // Start real-time updates for registration data
        this.updateInterval = setInterval(() => {
            this.fetchRegistrationUpdates();
        }, 30000); // Update every 30 seconds

        // Listen for real-time events from the main page
        document.addEventListener('tournament-stats-updated', (event) => {
            this.handleStatsUpdate(event.detail);
        });
    }

    async fetchRegistrationUpdates() {
        try {
            const tournamentSlug = window.tournamentDetailPage?.tournamentSlug;
            if (!tournamentSlug) return;

            const response = await fetch(`/tournaments/${tournamentSlug}/api/registration-status/`);
            if (!response.ok) return;

            const data = await response.json();
            this.updateRegistrationData(data);

        } catch (error) {
            console.warn('Failed to fetch registration updates:', error);
        }
    }

    updateRegistrationData(data) {
        const oldSpotsRemaining = this.spotsRemaining;

        // Update internal state
        this.spotsRemaining = data.spots_remaining || 0;

        // Update capacity display
        this.updateCapacityDisplay(data);

        // Update urgency indicators if spots changed
        if (oldSpotsRemaining !== this.spotsRemaining) {
            this.updateUrgencyDisplay();
            this.announceCapacityChange(oldSpotsRemaining, this.spotsRemaining);
        }

        // Update footer stats
        this.updateFooterStats(data);

        // Handle tournament full state
        if (this.spotsRemaining === 0 && oldSpotsRemaining > 0) {
            this.handleTournamentFull();
        }
    }

    updateCapacityDisplay(data) {
        const capacityFill = this.element.querySelector('.capacity-fill');
        const registeredCount = this.element.querySelector('.registered-count');
        const maxParticipants = this.element.querySelector('.max-participants');

        if (capacityFill && data.percentage_full !== undefined) {
            capacityFill.style.width = `${data.percentage_full}%`;
            capacityFill.parentElement.setAttribute('aria-label',
                `Registration progress: ${data.percentage_full}% full`);
        }

        if (registeredCount && data.registered !== undefined) {
            // Animate number change
            this.animateNumberChange(registeredCount, data.registered);
        }

        if (maxParticipants && data.capacity !== undefined) {
            maxParticipants.textContent = data.capacity;
        }
    }

    updateFooterStats(data) {
        const footerStats = this.element.querySelector('.footer-stats');
        if (!footerStats) return;

        const registeredStat = footerStats.querySelector('.stat-item:first-child .stat-text');
        const spotsStat = footerStats.querySelector('.stat-item:last-child .stat-text');

        if (registeredStat && data.registered !== undefined) {
            registeredStat.textContent = `${data.registered} registered`;
        }

        if (spotsStat && data.spots_remaining !== undefined) {
            const spotsText = data.spots_remaining === 1 ? 'spot' : 'spots';
            spotsStat.textContent = `${data.spots_remaining} ${spotsText} left`;
        }
    }

    animateNumberChange(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;

        if (currentValue === newValue) return;

        // Add animation class
        element.classList.add('number-changing');

        // Animate the number change
        const duration = 1000;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const currentDisplayValue = Math.round(currentValue + (newValue - currentValue) * progress);
            element.textContent = currentDisplayValue;

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.classList.remove('number-changing');
            }
        };

        requestAnimationFrame(animate);
    }

    handleTournamentFull() {
        // Replace registration button with full indicator
        const registrationActions = this.element.querySelector('.registration-actions');
        if (!registrationActions) return;

        registrationActions.innerHTML = `
            <div class="tournament-full-indicator" role="alert" aria-live="assertive">
                <span class="material-symbols-outlined" aria-hidden="true">group_off</span>
                <div class="full-content">
                    <div class="full-title">Tournament Full</div>
                    <div class="full-subtitle">No spots available</div>
                </div>
            </div>
        `;

        // Show notification
        if (window.tournamentDetailPage) {
            window.tournamentDetailPage.showNotification(
                'Tournament is now full! Registration is no longer available.',
                'info'
            );
        }
    }

    announceCapacityChange(oldSpots, newSpots) {
        // Announce capacity changes for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';

        if (newSpots < oldSpots) {
            const spotsText = newSpots === 1 ? 'spot' : 'spots';
            announcement.textContent = `${newSpots} ${spotsText} remaining in tournament`;
        }

        document.body.appendChild(announcement);

        // Remove after announcement
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    initAccessibility() {
        // Enhance keyboard navigation
        const registrationButton = this.element.querySelector('.registration-button');
        if (registrationButton) {
            registrationButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    registrationButton.click();
                }
            });
        }

        // Add focus management
        this.element.addEventListener('focusin', () => {
            this.element.classList.add('focused');
        });

        this.element.addEventListener('focusout', () => {
            this.element.classList.remove('focused');
        });

        // Ensure proper ARIA labels are updated dynamically
        this.updateAriaLabels();
    }

    updateAriaLabels() {
        const capacityIndicator = this.element.querySelector('.capacity-indicator');
        if (capacityIndicator) {
            const registered = this.element.querySelector('.registered-count')?.textContent || '0';
            const capacity = this.element.querySelector('.max-participants')?.textContent || '0';

            capacityIndicator.setAttribute('aria-label',
                `Tournament capacity: ${registered} of ${capacity} spots filled`);
        }
    }

    initMobileOptimizations() {
        // Handle mobile-specific behavior
        if (window.innerWidth <= 768) {
            this.initMobileStickyBehavior();
        }

        // Listen for resize events
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 768) {
                this.initMobileStickyBehavior();
            } else {
                this.removeMobileStickyBehavior();
            }
        });
    }

    initMobileStickyBehavior() {
        // On mobile, make the card stick to bottom instead of sidebar
        this.element.classList.add('mobile-sticky');

        // Add minimize/expand functionality
        const header = this.element.querySelector('.registration-card-header');
        if (header) {
            header.addEventListener('click', () => {
                this.element.classList.toggle('minimized');
            });
        }
    }

    removeMobileStickyBehavior() {
        this.element.classList.remove('mobile-sticky', 'minimized');
    }

    handleMobileStickyBehavior(scrollY) {
        if (!this.element.classList.contains('mobile-sticky')) return;

        // Hide card when scrolling down, show when scrolling up
        if (scrollY > 100) {
            this.element.classList.add('scroll-hidden');
        } else {
            this.element.classList.remove('scroll-hidden');
        }
    }

    handleStatsUpdate(stats) {
        if (stats.participants) {
            this.updateRegistrationData({
                registered: stats.participants.registered,
                capacity: stats.participants.capacity,
                spots_remaining: stats.participants.spots_remaining,
                percentage_full: stats.participants.percentage_full
            });
        }
    }

    destroy() {
        // Clean up intervals and event listeners
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        if (this.cleanup) {
            this.cleanup();
        }

        // Remove event listeners
        document.removeEventListener('tournament-stats-updated', this.handleStatsUpdate);
    }
}

// Initialize the tournament detail page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tournamentDetailPage = new TournamentDetailPage();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', () => {
    if (window.tournamentDetailPage) {
        window.tournamentDetailPage.destroy();
    }
});

/**
 * Mobile-First Responsive Design Enhancements
 */

// Extend TabNavigation class with mobile functionality
if (typeof TabNavigation !== 'undefined') {
    // Add mobile scrolling setup to existing TabNavigation
    const originalInit = TabNavigation.prototype.init;
    TabNavigation.prototype.init = function () {
        originalInit.call(this);
        this.setupMobileScrolling();
    };

    TabNavigation.prototype.setupMobileScrolling = function () {
        const tabNavigation = this.element;
        const tabList = tabNavigation.querySelector('.tab-nav-list');

        if (!tabList) return;

        // Add mobile scrolling indicators
        this.addScrollIndicators(tabNavigation, tabList);

        // Handle horizontal scrolling for mobile
        this.initHorizontalScrolling(tabList);

        // Add touch/swipe support
        this.initTouchSupport(tabList);

        // Update scroll indicators on scroll
        tabList.addEventListener('scroll', () => {
            this.updateScrollIndicators(tabNavigation, tabList);
        });

        // Update indicators on resize
        window.addEventListener('resize', () => {
            this.updateScrollIndicators(tabNavigation, tabList);
        });

        // Initial indicator update
        setTimeout(() => {
            this.updateScrollIndicators(tabNavigation, tabList);
        }, 100);
    };

    TabNavigation.prototype.addScrollIndicators = function (container, scrollElement) {
        // Only add indicators on mobile
        if (window.innerWidth > 768) return;

        // Remove existing indicators
        const existingIndicators = container.querySelectorAll('.scroll-indicator');
        existingIndicators.forEach(indicator => indicator.remove());

        // Left scroll indicator
        const leftIndicator = document.createElement('div');
        leftIndicator.className = 'scroll-indicator scroll-indicator-left';
        leftIndicator.innerHTML = '<span class="material-symbols-outlined">chevron_left</span>';
        leftIndicator.setAttribute('aria-hidden', 'true');
        leftIndicator.style.cssText = `
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 32px;
            height: 32px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            cursor: pointer;
            z-index: 20;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        `;

        // Right scroll indicator
        const rightIndicator = document.createElement('div');
        rightIndicator.className = 'scroll-indicator scroll-indicator-right';
        rightIndicator.innerHTML = '<span class="material-symbols-outlined">chevron_right</span>';
        rightIndicator.setAttribute('aria-hidden', 'true');
        rightIndicator.style.cssText = `
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 32px;
            height: 32px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            cursor: pointer;
            z-index: 20;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        `;

        container.appendChild(leftIndicator);
        container.appendChild(rightIndicator);

        // Add click handlers for indicators
        leftIndicator.addEventListener('click', () => {
            scrollElement.scrollBy({ left: -200, behavior: 'smooth' });
        });

        rightIndicator.addEventListener('click', () => {
            scrollElement.scrollBy({ left: 200, behavior: 'smooth' });
        });
    };

    TabNavigation.prototype.updateScrollIndicators = function (container, scrollElement) {
        const leftIndicator = container.querySelector('.scroll-indicator-left');
        const rightIndicator = container.querySelector('.scroll-indicator-right');

        if (!leftIndicator || !rightIndicator) return;

        const { scrollLeft, scrollWidth, clientWidth } = scrollElement;
        const maxScroll = scrollWidth - clientWidth;

        // Show/hide left indicator
        if (scrollLeft > 10) {
            leftIndicator.style.opacity = '1';
            leftIndicator.style.pointerEvents = 'auto';
        } else {
            leftIndicator.style.opacity = '0';
            leftIndicator.style.pointerEvents = 'none';
        }

        // Show/hide right indicator
        if (scrollLeft < maxScroll - 10) {
            rightIndicator.style.opacity = '1';
            rightIndicator.style.pointerEvents = 'auto';
        } else {
            rightIndicator.style.opacity = '0';
            rightIndicator.style.pointerEvents = 'none';
        }
    };

    TabNavigation.prototype.initHorizontalScrolling = function (scrollElement) {
        // Ensure active tab is visible when switching
        const scrollToActiveTab = () => {
            const activeTab = scrollElement.querySelector('.gaming-tab-item.active, .tab-nav-item.active');
            if (activeTab) {
                const containerRect = scrollElement.getBoundingClientRect();
                const tabRect = activeTab.getBoundingClientRect();

                if (tabRect.left < containerRect.left || tabRect.right > containerRect.right) {
                    const scrollLeft = activeTab.offsetLeft - (scrollElement.clientWidth / 2) + (activeTab.clientWidth / 2);
                    scrollElement.scrollTo({ left: scrollLeft, behavior: 'smooth' });
                }
            }
        };

        // Store reference for later use
        this.scrollToActiveTab = scrollToActiveTab;

        // Override switchTab to include scrolling
        const originalSwitchTab = this.switchTab;
        this.switchTab = function (tabId) {
            originalSwitchTab.call(this, tabId);
            setTimeout(scrollToActiveTab, 100);
        };
    };

    TabNavigation.prototype.initTouchSupport = function (scrollElement) {
        let startX = 0;
        let scrollLeft = 0;
        let isScrolling = false;

        // Touch start
        scrollElement.addEventListener('touchstart', (e) => {
            startX = e.touches[0].pageX - scrollElement.offsetLeft;
            scrollLeft = scrollElement.scrollLeft;
            isScrolling = true;
        }, { passive: true });

        // Touch move
        scrollElement.addEventListener('touchmove', (e) => {
            if (!isScrolling) return;

            const x = e.touches[0].pageX - scrollElement.offsetLeft;
            const walk = (x - startX) * 2; // Scroll speed multiplier
            scrollElement.scrollLeft = scrollLeft - walk;
        }, { passive: true });

        // Touch end
        scrollElement.addEventListener('touchend', () => {
            isScrolling = false;
        }, { passive: true });

        // Prevent default touch behavior on tab buttons during scroll
        this.tabButtons.forEach(button => {
            button.addEventListener('touchstart', (e) => {
                // Allow normal tap behavior
                setTimeout(() => {
                    if (isScrolling) {
                        e.preventDefault();
                    }
                }, 50);
            });
        });
    };
}

/**
 * Mobile Registration Card Enhancements
 */

// Extend StickyRegistrationCard class with mobile functionality
if (typeof StickyRegistrationCard !== 'undefined') {
    const originalInit = StickyRegistrationCard.prototype.init;
    StickyRegistrationCard.prototype.init = function () {
        originalInit.call(this);
        this.initMobileBehavior();
    };

    StickyRegistrationCard.prototype.initMobileBehavior = function () {
        if (window.innerWidth <= 768) {
            this.initMobileSticky();
            this.initScrollHiding();
            this.initMinimizedState();
        }

        // Re-initialize on resize
        window.addEventListener('resize', () => {
            if (window.innerWidth <= 768) {
                this.initMobileSticky();
            } else {
                this.resetDesktopBehavior();
            }
        });
    };

    StickyRegistrationCard.prototype.initMobileSticky = function () {
        const card = this.element;

        // Make card sticky at bottom on mobile
        card.style.cssText += `
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 50;
            margin: 0;
            border-radius: 16px 16px 0 0;
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
            transform: translateY(0);
            transition: transform 0.3s ease;
        `;

        // Add mobile-specific classes
        card.classList.add('mobile-sticky');
    };

    StickyRegistrationCard.prototype.initScrollHiding = function () {
        let lastScrollY = window.scrollY;
        let isHidden = false;

        const handleScroll = () => {
            const currentScrollY = window.scrollY;
            const scrollingDown = currentScrollY > lastScrollY;
            const scrollThreshold = 100;

            if (scrollingDown && currentScrollY > scrollThreshold && !isHidden) {
                // Hide card when scrolling down
                this.element.style.transform = 'translateY(100%)';
                isHidden = true;
            } else if (!scrollingDown && isHidden) {
                // Show card when scrolling up
                this.element.style.transform = 'translateY(0)';
                isHidden = false;
            }

            lastScrollY = currentScrollY;
        };

        // Throttle scroll events
        let ticking = false;
        const throttledScroll = () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        };

        window.addEventListener('scroll', throttledScroll, { passive: true });

        // Store reference for cleanup
        this.scrollHandler = throttledScroll;
    };

    StickyRegistrationCard.prototype.initMinimizedState = function () {
        const card = this.element;
        const header = card.querySelector('.registration-card-header');
        const content = card.querySelector('.registration-card-content');

        if (!header || !content) return;

        // Add minimize button
        const minimizeBtn = document.createElement('button');
        minimizeBtn.className = 'minimize-btn';
        minimizeBtn.innerHTML = '<span class="material-symbols-outlined">expand_less</span>';
        minimizeBtn.setAttribute('aria-label', 'Minimize registration card');
        minimizeBtn.style.cssText = `
            position: absolute;
            top: 12px;
            right: 12px;
            width: 32px;
            height: 32px;
            background: rgba(51, 65, 85, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 50%;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        `;

        header.appendChild(minimizeBtn);

        let isMinimized = false;

        minimizeBtn.addEventListener('click', () => {
            if (isMinimized) {
                // Expand
                content.style.display = 'block';
                minimizeBtn.innerHTML = '<span class="material-symbols-outlined">expand_less</span>';
                minimizeBtn.setAttribute('aria-label', 'Minimize registration card');
                card.style.borderRadius = '16px 16px 0 0';
                isMinimized = false;
            } else {
                // Minimize
                content.style.display = 'none';
                minimizeBtn.innerHTML = '<span class="material-symbols-outlined">expand_more</span>';
                minimizeBtn.setAttribute('aria-label', 'Expand registration card');
                card.style.borderRadius = '16px';
                isMinimized = true;
            }
        });

        // Auto-minimize after 5 seconds of inactivity
        let inactivityTimer;
        const resetInactivityTimer = () => {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(() => {
                if (!isMinimized) {
                    minimizeBtn.click();
                }
            }, 5000);
        };

        // Reset timer on user interaction
        card.addEventListener('touchstart', resetInactivityTimer);
        card.addEventListener('click', resetInactivityTimer);
        window.addEventListener('scroll', resetInactivityTimer);

        // Initial timer
        resetInactivityTimer();
    };

    StickyRegistrationCard.prototype.resetDesktopBehavior = function () {
        const card = this.element;

        // Remove mobile-specific styles
        card.style.position = '';
        card.style.bottom = '';
        card.style.left = '';
        card.style.right = '';
        card.style.transform = '';
        card.style.borderRadius = '';
        card.classList.remove('mobile-sticky');

        // Remove minimize button
        const minimizeBtn = card.querySelector('.minimize-btn');
        if (minimizeBtn) {
            minimizeBtn.remove();
        }

        // Show content
        const content = card.querySelector('.registration-card-content');
        if (content) {
            content.style.display = '';
        }

        // Remove scroll handler
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
        }
    };
}

/**
 * Mobile Touch Target Optimization
 */
function optimizeTouchTargets() {
    // Ensure minimum 44px touch targets on mobile
    if (window.innerWidth <= 768) {
        const touchElements = document.querySelectorAll('button, a, .tab-nav-item, .stat-card, .action-btn');

        touchElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            if (rect.height < 44) {
                element.style.minHeight = '44px';
                element.style.display = 'flex';
                element.style.alignItems = 'center';
                element.style.justifyContent = 'center';
            }
        });
    }
}

/**
 * Mobile Gesture Support
 */
function initMobileGestures() {
    // Add swipe gesture support for tab navigation
    const tabContent = document.querySelector('.tab-content');
    if (!tabContent) return;

    let startX = 0;
    let startY = 0;
    let isSwipeGesture = false;

    tabContent.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        isSwipeGesture = false;
    }, { passive: true });

    tabContent.addEventListener('touchmove', (e) => {
        if (!startX || !startY) return;

        const currentX = e.touches[0].clientX;
        const currentY = e.touches[0].clientY;

        const diffX = Math.abs(currentX - startX);
        const diffY = Math.abs(currentY - startY);

        // Determine if this is a horizontal swipe
        if (diffX > diffY && diffX > 50) {
            isSwipeGesture = true;
        }
    }, { passive: true });

    tabContent.addEventListener('touchend', (e) => {
        if (!isSwipeGesture || !startX) return;

        const endX = e.changedTouches[0].clientX;
        const diffX = startX - endX;

        // Minimum swipe distance
        if (Math.abs(diffX) < 100) return;

        const tabNavigation = window.tournamentDetailPage?.components?.tabNavigation;
        if (!tabNavigation) return;

        const currentTabIndex = Array.from(tabNavigation.tabButtons).findIndex(btn => btn.classList.contains('active'));
        let targetIndex;

        if (diffX > 0) {
            // Swipe left - next tab
            targetIndex = currentTabIndex < tabNavigation.tabButtons.length - 1 ? currentTabIndex + 1 : 0;
        } else {
            // Swipe right - previous tab
            targetIndex = currentTabIndex > 0 ? currentTabIndex - 1 : tabNavigation.tabButtons.length - 1;
        }

        const targetTab = tabNavigation.tabButtons[targetIndex];
        if (targetTab) {
            const tabId = targetTab.getAttribute('data-tab');
            tabNavigation.switchTab(tabId);
        }

        // Reset
        startX = 0;
        startY = 0;
        isSwipeGesture = false;
    }, { passive: true });
}

/**
 * Initialize Mobile Enhancements
 */
function initMobileEnhancements() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            optimizeTouchTargets();
            initMobileGestures();
        });
    } else {
        optimizeTouchTargets();
        initMobileGestures();
    }

    // Re-optimize on resize
    window.addEventListener('resize', () => {
        setTimeout(optimizeTouchTargets, 100);
    });
}

// Initialize mobile enhancements
initMobileEnhancements();

// Export for global access
window.MobileEnhancements = {
    optimizeTouchTargets,
    initMobileGestures,
    initMobileEnhancements
};

/**
 * Social Sharing Component Class
 * Handles platform integration and sharing functionality
 * Requirements: 8.1
 */
class SocialSharing {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            tournamentSlug: '',
            tournamentData: {},
            onShare: null,
            ...options
        };

        this.init();
    }

    init() {
        console.log('🔗 Initializing Social Sharing');

        this.setupShareButtons();
        this.setupClipboardAPI();
        this.setupNativeShareAPI();
        this.initShareTracking();

        console.log('✅ Social Sharing initialized');
    }

    setupShareButtons() {
        const shareButtons = this.element.querySelectorAll('.share-btn');

        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = button.dataset.platform;
                this.handleShare(platform);
            });

            // Add keyboard support
            button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const platform = button.dataset.platform;
                    this.handleShare(platform);
                }
            });

            // Add hover effects
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px) scale(1.05)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0) scale(1)';
            });
        });
    }

    setupClipboardAPI() {
        // Check if Clipboard API is available
        this.hasClipboardAPI = navigator.clipboard && window.isSecureContext;

        if (!this.hasClipboardAPI) {
            console.warn('Clipboard API not available, using fallback method');
        }
    }

    setupNativeShareAPI() {
        // Check if Web Share API is available
        this.hasNativeShare = navigator.share && navigator.canShare;

        if (this.hasNativeShare) {
            console.log('Native Web Share API available');
        }
    }

    async handleShare(platform) {
        const url = window.location.href;
        const tournament = this.options.tournamentData;

        try {
            switch (platform) {
                case 'copy':
                    await this.copyToClipboard(url);
                    this.showShareConfirmation('Link copied to clipboard!', 'success');
                    break;

                case 'twitter':
                    const twitterText = this.formatTwitterShare(tournament);
                    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(twitterText)}&url=${encodeURIComponent(url)}&hashtags=EYTGaming,Tournament,Gaming`;
                    window.open(twitterUrl, '_blank', 'width=600,height=400');
                    break;

                case 'discord':
                    const discordText = this.formatDiscordShare(tournament, url);
                    await this.copyToClipboard(discordText);
                    this.showShareConfirmation('Tournament info copied for Discord! Paste it in your server.', 'success');
                    break;

                case 'facebook':
                    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;
                    window.open(facebookUrl, '_blank', 'width=600,height=400');
                    break;

                case 'native':
                    if (this.hasNativeShare) {
                        await navigator.share({
                            title: tournament.name || 'Tournament',
                            text: this.generateShareText(tournament),
                            url: url
                        });
                    } else {
                        // Fallback to copy
                        await this.copyToClipboard(url);
                        this.showShareConfirmation('Link copied to clipboard!', 'success');
                    }
                    break;

                default:
                    await this.copyToClipboard(url);
                    this.showShareConfirmation('Link copied to clipboard!', 'success');
                    break;
            }

            // Track the share
            this.trackShare(platform);

            // Notify parent component
            if (this.options.onShare) {
                this.options.onShare(platform);
            }

        } catch (error) {
            console.error('Share failed:', error);
            this.showShareConfirmation('Share failed. Please try again.', 'error');
        }
    }

    formatTwitterShare(tournament) {
        let text = `🎮 ${tournament.name || 'Tournament'}`;

        if (tournament.game) {
            text += ` - ${tournament.game}`;
        }

        if (tournament.prizePool && tournament.prizePool !== '0') {
            text += ` 💰 ${tournament.prizePool} prize pool`;
        }

        if (tournament.participants && tournament.participants !== '0') {
            text += ` 👥 ${tournament.participants}/${tournament.maxParticipants} players`;
        }

        if (tournament.status === 'registration') {
            text += ' 🔥 Registration open!';
        } else if (tournament.status === 'in_progress') {
            text += ' 🚀 Live now!';
        }

        // Ensure we stay under Twitter's character limit
        const maxLength = 240;
        if (text.length > maxLength) {
            text = text.substring(0, maxLength - 3) + '...';
        }

        return text;
    }

    formatDiscordShare(tournament, url = '') {
        let text = `🎮 **${tournament.name || 'Tournament'}** Tournament\n`;

        if (tournament.game) {
            text += `🎯 **Game:** ${tournament.game}\n`;
        }

        if (tournament.prizePool && tournament.prizePool !== '0') {
            text += `💰 **Prize Pool:** ${tournament.prizePool}\n`;
        }

        if (tournament.participants && tournament.participants !== '0') {
            text += `👥 **Players:** ${tournament.participants}/${tournament.maxParticipants}\n`;
        }

        if (tournament.date) {
            text += `📅 **Date:** ${tournament.date}\n`;
        }

        if (tournament.status === 'registration') {
            text += `🔥 **Status:** Registration Open - Join Now!\n`;
        } else if (tournament.status === 'in_progress') {
            text += `🚀 **Status:** Live Tournament!\n`;
        } else if (tournament.status === 'completed') {
            text += `🏆 **Status:** Tournament Completed\n`;
        }

        text += `\n🔗 **Join here:** ${url}`;

        return text;
    }

    generateShareText(tournament) {
        const baseText = `🎮 ${tournament.name || 'Tournament'}`;
        return `${baseText} - ${tournament.game ? `${tournament.game} tournament` : 'Gaming tournament'} with ${tournament.participants || 0} participants${tournament.prizePool && tournament.prizePool !== '0' ? ` and ${tournament.prizePool} prize pool` : ''}!`;
    }

    async copyToClipboard(text) {
        if (this.hasClipboardAPI) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (error) {
                console.warn('Clipboard API failed, using fallback:', error);
            }
        }

        // Fallback method
        return this.fallbackCopyToClipboard(text);
    }

    fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.setAttribute('readonly', '');
        textArea.setAttribute('aria-hidden', 'true');

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            return successful;
        } catch (error) {
            document.body.removeChild(textArea);
            throw error;
        }
    }

    showShareConfirmation(message, type = 'success') {
        // Create or update existing notification
        let notification = document.querySelector('.share-notification');

        if (!notification) {
            notification = document.createElement('div');
            notification.className = 'share-notification';
            notification.setAttribute('role', 'alert');
            notification.setAttribute('aria-live', 'polite');
            document.body.appendChild(notification);
        }

        notification.className = `share-notification ${type}`;
        notification.textContent = message;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            ${type === 'success' ? 'background: #059669;' : 'background: #dc2626;'}
        `;

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    async trackShare(platform) {
        try {
            const response = await fetch(`/tournaments/${this.options.tournamentSlug}/share/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    platform: platform,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                this.updateShareCount();
            }
        } catch (error) {
            console.warn('Share tracking failed:', error);
        }
    }

    async updateShareCount() {
        try {
            const response = await fetch(`/tournaments/${this.options.tournamentSlug}/share-count/`);
            if (response.ok) {
                const data = await response.json();
                const shareCountElements = document.querySelectorAll('.share-count');
                shareCountElements.forEach(element => {
                    element.textContent = data.count || 0;
                });
            }
        } catch (error) {
            console.warn('Failed to update share count:', error);
        }
    }

    initShareTracking() {
        // Track page views for sharing analytics
        this.trackPageView();

        // Update share counts on page load
        this.updateShareCount();
    }

    async trackPageView() {
        try {
            const response = await fetch(`/tournaments/${this.options.tournamentSlug}/view/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    referrer: document.referrer || '',
                    user_agent: navigator.userAgent
                })
            });
        } catch (error) {
            console.warn('Page view tracking failed:', error);
        }
    }

    getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }

    updateTournamentData(newData) {
        this.options.tournamentData = { ...this.options.tournamentData, ...newData };
    }

    destroy() {
        // Remove event listeners
        const shareButtons = this.element.querySelectorAll('.share-btn');
        shareButtons.forEach(button => {
            button.removeEventListener('click', this.handleShare);
            button.removeEventListener('keydown', this.handleKeyDown);
        });

        console.log('🧹 Social Sharing destroyed');
    }
}

// Export classes for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TournamentDetailPage,
        HeroSection,
        StatisticsDashboard,
        TabNavigation,
        TournamentTimeline,
        SocialSharing
    };
}