/**
 * Graceful Fallbacks Module for Tournament Detail Page
 * Provides comprehensive fallback handling for JavaScript-disabled scenarios,
 * failed modules, network failures, and progressive enhancement failures
 * Addresses Requirements 9.1, 9.2, 9.3, 9.4, 9.5
 */

class GracefulFallbacks {
    constructor(config = {}) {
        this.config = {
            enableLogging: true,
            fallbackTimeout: 5000,
            retryAttempts: 2,
            cacheExpiry: 300000, // 5 minutes
            ...config
        };
        
        this.fallbackStrategies = new Map();
        this.cachedContent = new Map();
        this.networkStatus = 'online';
        this.jsEnabled = true;
        
        this.init();
    }
    
    init() {
        this.log('GracefulFallbacks initialized');
        
        // Detect JavaScript availability
        this.detectJavaScriptSupport();
        
        // Monitor network status
        this.setupNetworkMonitoring();
        
        // Register default fallback strategies
        this.registerDefaultFallbacks();
        
        // Set up progressive enhancement detection
        this.setupProgressiveEnhancementDetection();
        
        // Initialize no-JS fallbacks
        this.initializeNoJSFallbacks();
    }
    
    /**
     * Detect if JavaScript is properly supported and enabled
     */
    detectJavaScriptSupport() {
        // This runs, so JS is enabled, but check for feature support
        this.jsEnabled = true;
        
        // Check for essential JavaScript features
        const requiredFeatures = [
            'Promise',
            'fetch',
            'addEventListener',
            'querySelector'
        ];
        
        const missingFeatures = requiredFeatures.filter(feature => 
            typeof window[feature] === 'undefined'
        );
        
        if (missingFeatures.length > 0) {
            this.log('Missing JavaScript features:', missingFeatures);
            this.handleLegacyBrowser(missingFeatures);
        }
    }
    /**
     * Set up network status monitoring
     */
    setupNetworkMonitoring() {
        if ('navigator' in window && 'onLine' in navigator) {
            this.networkStatus = navigator.onLine ? 'online' : 'offline';
            
            window.addEventListener('online', () => {
                this.networkStatus = 'online';
                this.log('Network status: online');
                this.handleNetworkRecovery();
            });
            
            window.addEventListener('offline', () => {
                this.networkStatus = 'offline';
                this.log('Network status: offline');
                this.handleNetworkFailure();
            });
        }
    }
    
    /**
     * Register default fallback strategies for common scenarios
     */
    registerDefaultFallbacks() {
        // Tournament data fallback
        this.registerFallback('tournament-data', () => {
            return this.showStaticTournamentInfo();
        });
        
        // Participant list fallback
        this.registerFallback('participant-list', () => {
            return this.showStaticParticipantList();
        });
        
        // Registration form fallback
        this.registerFallback('registration-form', () => {
            return this.showBasicRegistrationForm();
        });
        
        // Interactive elements fallback
        this.registerFallback('interactive-elements', () => {
            return this.convertToStaticElements();
        });
        
        // Timeline fallback
        this.registerFallback('tournament-timeline', () => {
            return this.showStaticTimeline();
        });
        
        // Bracket preview fallback
        this.registerFallback('bracket-preview', () => {
            return this.showStaticBracket();
        });
        
        // Social sharing fallback
        this.registerFallback('social-sharing', () => {
            return this.showBasicShareLinks();
        });
    }
    
    /**
     * Register a fallback strategy for a specific component
     */
    registerFallback(componentName, fallbackFunction) {
        this.fallbackStrategies.set(componentName, fallbackFunction);
        this.log(`Registered fallback for: ${componentName}`);
    }
    
    /**
     * Execute fallback for a specific component
     */
    async executeFallback(componentName, context = {}) {
        const fallbackFunction = this.fallbackStrategies.get(componentName);
        
        if (!fallbackFunction) {
            this.log(`No fallback strategy found for: ${componentName}`);
            return this.showGenericFallback(componentName);
        }
        
        try {
            this.log(`Executing fallback for: ${componentName}`);
            const result = await fallbackFunction(context);
            return { success: true, result, component: componentName };
        } catch (error) {
            this.log(`Fallback execution failed for ${componentName}:`, error);
            return this.showGenericFallback(componentName);
        }
    }
    /**
     * Set up progressive enhancement detection
     */
    setupProgressiveEnhancementDetection() {
        // Monitor for failed module loads
        window.addEventListener('error', (event) => {
            if (event.target && event.target.tagName === 'SCRIPT') {
                const src = event.target.src;
                this.log(`Script failed to load: ${src}`);
                this.handleModuleFailure(src);
            }
        });
        
        // Monitor for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.log('Unhandled promise rejection:', event.reason);
            this.handleProgressiveEnhancementFailure(event.reason);
        });
    }
    
    /**
     * Initialize fallbacks for no-JavaScript scenarios
     */
    initializeNoJSFallbacks() {
        // Add noscript content for essential functionality
        this.addNoScriptContent();
        
        // Enhance forms for no-JS submission
        this.enhanceFormsForNoJS();
        
        // Add static alternatives for dynamic content
        this.addStaticAlternatives();
    }
    
    /**
     * Handle network failure scenarios
     */
    handleNetworkFailure() {
        this.log('Handling network failure');
        
        // Show cached content where available
        this.showCachedContent();
        
        // Display offline message
        this.showOfflineMessage();
        
        // Disable network-dependent features
        this.disableNetworkFeatures();
    }
    
    /**
     * Handle network recovery
     */
    handleNetworkRecovery() {
        this.log('Handling network recovery');
        
        // Hide offline message
        this.hideOfflineMessage();
        
        // Re-enable network features
        this.enableNetworkFeatures();
        
        // Attempt to reload failed content
        this.reloadFailedContent();
    }
    
    /**
     * Handle module loading failures
     */
    handleModuleFailure(modulePath) {
        const moduleName = this.extractModuleName(modulePath);
        this.log(`Module failure detected: ${moduleName}`);
        
        // Execute appropriate fallback
        this.executeFallback(moduleName);
    }
    
    /**
     * Handle progressive enhancement failures
     */
    handleProgressiveEnhancementFailure(error) {
        this.log('Progressive enhancement failure:', error);
        
        // Fallback to basic functionality
        this.enableBasicMode();
    }
    
    /**
     * Handle legacy browser scenarios
     */
    handleLegacyBrowser(missingFeatures) {
        this.log('Legacy browser detected, missing features:', missingFeatures);
        
        // Provide polyfills where possible
        this.loadPolyfills(missingFeatures);
        
        // Fallback to basic functionality
        this.enableBasicMode();
    }
    /**
     * Show static tournament information
     */
    showStaticTournamentInfo() {
        const container = document.querySelector('.tournament-info-dynamic');
        if (container) {
            container.innerHTML = `
                <div class="fallback-content">
                    <div class="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4 mb-4">
                        <p class="text-yellow-400 text-sm font-medium">⚠ Dynamic content unavailable</p>
                        <p class="text-yellow-300 text-xs mt-1">Showing basic tournament information</p>
                    </div>
                    <div class="space-y-4">
                        <p class="text-gray-300">Tournament details are available. Please refresh the page or contact support if you need updated information.</p>
                        <button onclick="location.reload()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                            Refresh Page
                        </button>
                    </div>
                </div>
            `;
        }
        return 'static-tournament-info';
    }
    
    /**
     * Show static participant list
     */
    showStaticParticipantList() {
        const container = document.querySelector('.participant-list-dynamic');
        if (container) {
            container.innerHTML = `
                <div class="fallback-content">
                    <div class="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4 mb-4">
                        <p class="text-blue-400 text-sm font-medium">📋 Static participant list</p>
                        <p class="text-blue-300 text-xs mt-1">Live updates unavailable</p>
                    </div>
                    <p class="text-gray-300 mb-4">Participant information is shown as last cached. For the most current list, please refresh the page.</p>
                    <a href="?refresh=participants" class="text-blue-400 hover:text-blue-300 underline">
                        View full participant list →
                    </a>
                </div>
            `;
        }
        return 'static-participant-list';
    }
    
    /**
     * Show basic registration form
     */
    showBasicRegistrationForm() {
        const container = document.querySelector('.registration-form-dynamic');
        if (container) {
            container.innerHTML = `
                <div class="fallback-content">
                    <div class="bg-green-500/20 border border-green-500/50 rounded-lg p-4 mb-4">
                        <p class="text-green-400 text-sm font-medium">📝 Basic registration form</p>
                        <p class="text-green-300 text-xs mt-1">Enhanced features unavailable</p>
                    </div>
                    <form method="POST" action="" class="space-y-4">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${this.getCSRFToken()}">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">Display Name</label>
                            <input type="text" name="display_name" required 
                                   class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white">
                        </div>
                        <button type="submit" class="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700">
                            Register for Tournament
                        </button>
                    </form>
                </div>
            `;
        }
        return 'basic-registration-form';
    }
    
    /**
     * Convert interactive elements to static alternatives
     */
    convertToStaticElements() {
        // Convert dynamic buttons to static links
        const dynamicButtons = document.querySelectorAll('[data-dynamic]');
        dynamicButtons.forEach(button => {
            const staticVersion = document.createElement('a');
            staticVersion.href = button.dataset.fallbackUrl || '#';
            staticVersion.textContent = button.textContent;
            staticVersion.className = button.className;
            button.parentNode.replaceChild(staticVersion, button);
        });
        
        // Convert animated elements to static versions
        const animatedElements = document.querySelectorAll('.animate-pulse, .animate-spin, .animate-bounce');
        animatedElements.forEach(element => {
            element.classList.remove('animate-pulse', 'animate-spin', 'animate-bounce');
            element.classList.add('static-element');
        });
        
        return 'static-elements';
    }
    /**
     * Show static timeline
     */
    showStaticTimeline() {
        const container = document.querySelector('.tournament-timeline');
        if (container) {
            container.classList.add('static-timeline');
            container.classList.remove('interactive-timeline');
            
            // Remove animation classes
            const animatedElements = container.querySelectorAll('[class*="animate-"]');
            animatedElements.forEach(element => {
                element.className = element.className.replace(/animate-\S+/g, '');
            });
            
            // Add static timeline indicator
            const indicator = document.createElement('div');
            indicator.className = 'bg-gray-500/20 border border-gray-500/50 rounded-lg p-3 mb-4';
            indicator.innerHTML = `
                <p class="text-gray-400 text-sm font-medium">📅 Static timeline view</p>
                <p class="text-gray-500 text-xs mt-1">Interactive features disabled</p>
            `;
            container.insertBefore(indicator, container.firstChild);
        }
        return 'static-timeline';
    }
    
    /**
     * Show static bracket
     */
    showStaticBracket() {
        const container = document.querySelector('.bracket-preview');
        if (container) {
            container.innerHTML = `
                <div class="fallback-content">
                    <div class="bg-purple-500/20 border border-purple-500/50 rounded-lg p-4 mb-4">
                        <p class="text-purple-400 text-sm font-medium">🏆 Bracket preview unavailable</p>
                        <p class="text-purple-300 text-xs mt-1">Interactive bracket disabled</p>
                    </div>
                    <div class="text-center py-8">
                        <svg class="mx-auto h-16 w-16 text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                        <p class="text-gray-400 mb-4">Bracket information will be available when the tournament begins.</p>
                        <a href="?view=bracket" class="text-blue-400 hover:text-blue-300 underline">
                            View bracket page →
                        </a>
                    </div>
                </div>
            `;
        }
        return 'static-bracket';
    }
    
    /**
     * Show basic share links
     */
    showBasicShareLinks() {
        const container = document.querySelector('.social-sharing');
        if (container) {
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);
            
            container.innerHTML = `
                <div class="fallback-content">
                    <div class="bg-indigo-500/20 border border-indigo-500/50 rounded-lg p-4 mb-4">
                        <p class="text-indigo-400 text-sm font-medium">🔗 Basic sharing options</p>
                        <p class="text-indigo-300 text-xs mt-1">Advanced sharing unavailable</p>
                    </div>
                    <div class="space-y-2">
                        <a href="https://twitter.com/intent/tweet?url=${url}&text=${title}" 
                           target="_blank" rel="noopener"
                           class="block w-full bg-blue-600 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-700">
                            Share on Twitter
                        </a>
                        <a href="https://www.facebook.com/sharer/sharer.php?u=${url}" 
                           target="_blank" rel="noopener"
                           class="block w-full bg-blue-800 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-900">
                            Share on Facebook
                        </a>
                        <div class="bg-gray-700 p-3 rounded-lg">
                            <p class="text-xs text-gray-400 mb-2">Copy link manually:</p>
                            <input type="text" value="${window.location.href}" readonly
                                   class="w-full bg-gray-800 text-gray-300 px-2 py-1 rounded text-sm"
                                   onclick="this.select()">
                        </div>
                    </div>
                </div>
            `;
        }
        return 'basic-share-links';
    }
    /**
     * Add noscript content for essential functionality
     */
    addNoScriptContent() {
        // Add noscript tags for critical content
        const noscriptElements = [
            {
                selector: '.registration-section',
                content: `
                    <div class="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-4">
                        <p class="text-red-400 text-sm font-medium">⚠ JavaScript Required</p>
                        <p class="text-red-300 text-xs mt-1">Please enable JavaScript for full functionality</p>
                    </div>
                `
            },
            {
                selector: '.dynamic-content',
                content: `
                    <div class="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4">
                        <p class="text-yellow-400 text-sm">Some features require JavaScript to be enabled.</p>
                    </div>
                `
            }
        ];
        
        noscriptElements.forEach(({ selector, content }) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                const noscript = document.createElement('noscript');
                noscript.innerHTML = content;
                element.appendChild(noscript);
            });
        });
    }
    
    /**
     * Enhance forms for no-JS submission
     */
    enhanceFormsForNoJS() {
        const forms = document.querySelectorAll('form[data-enhance]');
        forms.forEach(form => {
            // Ensure forms have proper action and method attributes
            if (!form.action) {
                form.action = window.location.pathname;
            }
            if (!form.method) {
                form.method = 'POST';
            }
            
            // Add hidden fields for context
            const contextField = document.createElement('input');
            contextField.type = 'hidden';
            contextField.name = 'no_js_fallback';
            contextField.value = 'true';
            form.appendChild(contextField);
        });
    }
    
    /**
     * Add static alternatives for dynamic content
     */
    addStaticAlternatives() {
        // Add refresh links for dynamic content
        const dynamicSections = document.querySelectorAll('[data-dynamic-content]');
        dynamicSections.forEach(section => {
            const refreshLink = document.createElement('div');
            refreshLink.className = 'text-center mt-4';
            refreshLink.innerHTML = `
                <a href="?refresh=${section.dataset.dynamicContent}" 
                   class="text-blue-400 hover:text-blue-300 text-sm underline">
                    Refresh ${section.dataset.dynamicContent} →
                </a>
            `;
            section.appendChild(refreshLink);
        });
    }
    
    /**
     * Show cached content when network is unavailable
     */
    showCachedContent() {
        this.cachedContent.forEach((content, key) => {
            const container = document.querySelector(`[data-cache-key="${key}"]`);
            if (container && this.isCacheValid(key)) {
                container.innerHTML = content;
                
                // Add cache indicator
                const indicator = document.createElement('div');
                indicator.className = 'bg-orange-500/20 border border-orange-500/50 rounded-lg p-2 mb-2';
                indicator.innerHTML = `
                    <p class="text-orange-400 text-xs">📦 Showing cached content (offline)</p>
                `;
                container.insertBefore(indicator, container.firstChild);
            }
        });
    }
    
    /**
     * Show offline message
     */
    showOfflineMessage() {
        let offlineMessage = document.getElementById('offline-message');
        if (!offlineMessage) {
            offlineMessage = document.createElement('div');
            offlineMessage.id = 'offline-message';
            offlineMessage.className = 'fixed top-4 right-4 bg-red-600 text-white p-4 rounded-lg shadow-lg z-50';
            offlineMessage.innerHTML = `
                <div class="flex items-center gap-2">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-sm font-medium">You're offline</span>
                </div>
                <p class="text-xs mt-1">Some features may be limited</p>
            `;
            document.body.appendChild(offlineMessage);
        }
        offlineMessage.style.display = 'block';
    }
    /**
     * Hide offline message
     */
    hideOfflineMessage() {
        const offlineMessage = document.getElementById('offline-message');
        if (offlineMessage) {
            offlineMessage.style.display = 'none';
        }
    }
    
    /**
     * Disable network-dependent features
     */
    disableNetworkFeatures() {
        // Disable forms that require network
        const networkForms = document.querySelectorAll('form[data-requires-network]');
        networkForms.forEach(form => {
            const inputs = form.querySelectorAll('input, button, select, textarea');
            inputs.forEach(input => {
                input.disabled = true;
            });
            
            // Add offline notice
            const notice = document.createElement('div');
            notice.className = 'offline-notice bg-gray-600 text-gray-300 p-2 rounded text-sm';
            notice.textContent = 'This feature requires an internet connection';
            form.insertBefore(notice, form.firstChild);
        });
        
        // Disable AJAX-dependent buttons
        const ajaxButtons = document.querySelectorAll('[data-ajax]');
        ajaxButtons.forEach(button => {
            button.disabled = true;
            button.title = 'Requires internet connection';
        });
    }
    
    /**
     * Enable network features
     */
    enableNetworkFeatures() {
        // Re-enable forms
        const networkForms = document.querySelectorAll('form[data-requires-network]');
        networkForms.forEach(form => {
            const inputs = form.querySelectorAll('input, button, select, textarea');
            inputs.forEach(input => {
                input.disabled = false;
            });
            
            // Remove offline notices
            const notices = form.querySelectorAll('.offline-notice');
            notices.forEach(notice => notice.remove());
        });
        
        // Re-enable AJAX buttons
        const ajaxButtons = document.querySelectorAll('[data-ajax]');
        ajaxButtons.forEach(button => {
            button.disabled = false;
            button.title = '';
        });
    }
    
    /**
     * Attempt to reload failed content
     */
    reloadFailedContent() {
        // Retry failed module loads
        const failedScripts = document.querySelectorAll('script[data-failed]');
        failedScripts.forEach(script => {
            const newScript = document.createElement('script');
            newScript.src = script.src;
            newScript.async = true;
            script.parentNode.replaceChild(newScript, script);
        });
    }
    
    /**
     * Enable basic mode for legacy browsers or failures
     */
    enableBasicMode() {
        document.body.classList.add('basic-mode');
        
        // Show basic mode indicator
        const indicator = document.createElement('div');
        indicator.className = 'basic-mode-indicator bg-gray-600 text-gray-300 p-2 text-center text-sm';
        indicator.textContent = 'Running in basic mode - some features may be limited';
        document.body.insertBefore(indicator, document.body.firstChild);
        
        // Convert all dynamic elements to static
        this.convertToStaticElements();
    }
    
    /**
     * Load polyfills for missing features
     */
    loadPolyfills(missingFeatures) {
        const polyfills = {
            'Promise': 'https://cdn.jsdelivr.net/npm/es6-promise@4/dist/es6-promise.auto.min.js',
            'fetch': 'https://cdn.jsdelivr.net/npm/whatwg-fetch@3.6.2/dist/fetch.umd.js'
        };
        
        missingFeatures.forEach(feature => {
            if (polyfills[feature]) {
                const script = document.createElement('script');
                script.src = polyfills[feature];
                script.async = true;
                document.head.appendChild(script);
                this.log(`Loading polyfill for: ${feature}`);
            }
        });
    }
    /**
     * Show generic fallback for unknown components
     */
    showGenericFallback(componentName) {
        return {
            success: false,
            result: `generic-fallback-${componentName}`,
            component: componentName,
            message: `Fallback activated for ${componentName}`
        };
    }
    
    /**
     * Cache content for offline use
     */
    cacheContent(key, content) {
        this.cachedContent.set(key, {
            content,
            timestamp: Date.now()
        });
        this.log(`Content cached: ${key}`);
    }
    
    /**
     * Check if cached content is still valid
     */
    isCacheValid(key) {
        const cached = this.cachedContent.get(key);
        if (!cached) return false;
        
        const age = Date.now() - cached.timestamp;
        return age < this.config.cacheExpiry;
    }
    
    /**
     * Extract module name from path
     */
    extractModuleName(path) {
        const parts = path.split('/');
        const filename = parts[parts.length - 1];
        return filename.replace(/\.(js|css)$/, '');
    }
    
    /**
     * Get CSRF token for forms
     */
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    /**
     * Logging utility
     */
    log(...args) {
        if (this.config.enableLogging) {
            console.log('[GracefulFallbacks]', ...args);
        }
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        this.fallbackStrategies.clear();
        this.cachedContent.clear();
        
        // Remove event listeners
        window.removeEventListener('online', this.handleNetworkRecovery);
        window.removeEventListener('offline', this.handleNetworkFailure);
        
        // Remove created elements
        const createdElements = document.querySelectorAll('.offline-notice, .basic-mode-indicator, #offline-message');
        createdElements.forEach(element => element.remove());
        
        this.log('GracefulFallbacks destroyed');
    }
}

// Create global instance
window.GracefulFallbacks = new GracefulFallbacks({ enableLogging: true });

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const gracefulFallbacks = window.GracefulFallbacks;
    
    // Check for failed modules and execute fallbacks
    const moduleElements = document.querySelectorAll('[data-module-failed]');
    moduleElements.forEach(element => {
        const moduleName = element.dataset.moduleFailed;
        gracefulFallbacks.executeFallback(moduleName);
    });
    
    // Set up automatic fallback detection
    setTimeout(() => {
        // Check if critical modules loaded
        const criticalModules = ['module-manager', 'copy-link-handler', 'layout-manager'];
        criticalModules.forEach(moduleName => {
            if (!window[moduleName] && !window[moduleName.replace('-', '')]) {
                gracefulFallbacks.executeFallback(moduleName);
            }
        });
    }, 3000); // Wait 3 seconds for modules to load
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.GracefulFallbacks) {
        window.GracefulFallbacks.destroy();
    }
});

export default GracefulFallbacks;