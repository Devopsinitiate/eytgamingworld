/**
 * Lazy loading utility for non-critical JavaScript modules
 * Implements code splitting and progressive enhancement
 */

class LazyLoader {
    constructor() {
        this.loadedModules = new Set();
        this.loadingPromises = new Map();
        this.observers = new Map();
        
        // Initialize intersection observer for viewport-based loading
        this.initIntersectionObserver();
    }
    
    /**
     * Load a JavaScript module dynamically
     * @param {string} moduleName - Name of the module to load
     * @param {Object} options - Loading options
     * @returns {Promise} - Promise that resolves when module is loaded
     */
    async loadModule(moduleName, options = {}) {
        const {
            condition = true,
            timeout = 10000,
            retries = 2
        } = options;
        
        // Check if module should be loaded
        if (!condition) {
            return null;
        }
        
        // Return existing promise if already loading
        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }
        
        // Return immediately if already loaded
        if (this.loadedModules.has(moduleName)) {
            return Promise.resolve();
        }
        
        // Create loading promise
        const loadingPromise = this._loadModuleWithRetry(moduleName, timeout, retries);
        this.loadingPromises.set(moduleName, loadingPromise);
        
        try {
            await loadingPromise;
            this.loadedModules.add(moduleName);
            this.loadingPromises.delete(moduleName);
            
            console.log(`✓ Loaded module: ${moduleName}`);
            return true;
        } catch (error) {
            this.loadingPromises.delete(moduleName);
            console.error(`✗ Failed to load module: ${moduleName}`, error);
            throw error;
        }
    }
    
    /**
     * Load module with retry logic
     */
    async _loadModuleWithRetry(moduleName, timeout, retries) {
        let lastError;
        
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                return await this._loadModuleScript(moduleName, timeout);
            } catch (error) {
                lastError = error;
                if (attempt < retries) {
                    // Wait before retry (exponential backoff)
                    await this._delay(Math.pow(2, attempt) * 1000);
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Load module script with timeout
     */
    _loadModuleScript(moduleName, timeout) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            const timeoutId = setTimeout(() => {
                reject(new Error(`Module ${moduleName} load timeout`));
            }, timeout);
            
            script.onload = () => {
                clearTimeout(timeoutId);
                resolve();
            };
            
            script.onerror = () => {
                clearTimeout(timeoutId);
                reject(new Error(`Failed to load module: ${moduleName}`));
            };
            
            // Set module path
            script.src = this._getModulePath(moduleName);
            script.async = true;
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * Get the full path for a module
     */
    _getModulePath(moduleName) {
        const basePath = '/static/js/modules/';
        return `${basePath}${moduleName}.js`;
    }
    
    /**
     * Load module when element enters viewport
     */
    loadOnVisible(element, moduleName, options = {}) {
        if (!element || this.loadedModules.has(moduleName)) {
            return;
        }
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadModule(moduleName, options);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px' // Load 50px before element is visible
        });
        
        observer.observe(element);
        this.observers.set(element, observer);
    }
    
    /**
     * Load module on user interaction
     */
    loadOnInteraction(element, moduleName, events = ['click', 'touchstart'], options = {}) {
        if (!element || this.loadedModules.has(moduleName)) {
            return;
        }
        
        const loadHandler = () => {
            this.loadModule(moduleName, options);
            // Remove event listeners after first interaction
            events.forEach(event => {
                element.removeEventListener(event, loadHandler);
            });
        };
        
        events.forEach(event => {
            element.addEventListener(event, loadHandler, { once: true, passive: true });
        });
    }
    
    /**
     * Load module after a delay
     */
    loadAfterDelay(moduleName, delay = 2000, options = {}) {
        setTimeout(() => {
            this.loadModule(moduleName, options);
        }, delay);
    }
    
    /**
     * Load module when page is idle
     */
    loadOnIdle(moduleName, options = {}) {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                this.loadModule(moduleName, options);
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            this.loadAfterDelay(moduleName, 1000, options);
        }
    }
    
    /**
     * Preload module (download but don't execute)
     */
    preloadModule(moduleName) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'script';
        link.href = this._getModulePath(moduleName);
        document.head.appendChild(link);
    }
    
    /**
     * Initialize intersection observer for general use
     */
    initIntersectionObserver() {
        // Observer for lazy loading images and content
        this.contentObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    
                    // Handle lazy loading images
                    if (element.dataset.src) {
                        element.src = element.dataset.src;
                        element.removeAttribute('data-src');
                    }
                    
                    // Handle lazy loading background images
                    if (element.dataset.bgSrc) {
                        element.style.backgroundImage = `url(${element.dataset.bgSrc})`;
                        element.removeAttribute('data-bg-src');
                    }
                    
                    // Add loaded class for CSS transitions
                    element.classList.add('lazy-loaded');
                    
                    this.contentObserver.unobserve(element);
                }
            });
        }, {
            rootMargin: '50px'
        });
    }
    
    /**
     * Observe element for lazy loading
     */
    observeElement(element) {
        if (element && this.contentObserver) {
            this.contentObserver.observe(element);
        }
    }
    
    /**
     * Utility delay function
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * Clean up observers
     */
    cleanup() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        if (this.contentObserver) {
            this.contentObserver.disconnect();
        }
    }
}

// Create global instance
window.LazyLoader = new LazyLoader();

// Auto-initialize lazy loading for elements with data attributes
document.addEventListener('DOMContentLoaded', () => {
    const lazyLoader = window.LazyLoader;
    
    // Find elements that need lazy loading
    const lazyImages = document.querySelectorAll('img[data-src], [data-bg-src]');
    lazyImages.forEach(img => lazyLoader.observeElement(img));
    
    // Find elements that should trigger module loading
    const moduleElements = document.querySelectorAll('[data-lazy-module]');
    moduleElements.forEach(element => {
        const moduleName = element.dataset.lazyModule;
        const loadTrigger = element.dataset.loadTrigger || 'visible';
        
        switch (loadTrigger) {
            case 'visible':
                lazyLoader.loadOnVisible(element, moduleName);
                break;
            case 'interaction':
                lazyLoader.loadOnInteraction(element, moduleName);
                break;
            case 'idle':
                lazyLoader.loadOnIdle(moduleName);
                break;
            case 'delay':
                const delay = parseInt(element.dataset.loadDelay) || 2000;
                lazyLoader.loadAfterDelay(moduleName, delay);
                break;
        }
    });
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.LazyLoader) {
        window.LazyLoader.cleanup();
    }
});

export default LazyLoader;