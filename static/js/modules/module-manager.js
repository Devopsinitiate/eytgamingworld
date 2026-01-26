/**
 * JavaScript Module Manager
 * Handles loading and managing JavaScript modules with proper error handling and fallbacks
 */

class ModuleManager {
    constructor(config = {}) {
        this.modules = new Map();
        this.fallbacks = new Map();
        this.loadingPromises = new Map();
        this.config = {
            debug: false,
            retryAttempts: 3,
            retryDelay: 1000,
            ...config
        };
        
        this.init();
    }
    
    init() {
        this.log('ModuleManager initialized');
        
        // Register default fallbacks
        this.registerDefaultFallbacks();
        
        // Set up global error handling
        this.setupErrorHandling();
    }
    
    registerDefaultFallbacks() {
        // Bracket preview fallback
        this.registerFallback('bracket-preview', () => {
            this.log('Using bracket preview fallback');
            const containers = document.querySelectorAll('.bracket-preview-container');
            containers.forEach(container => {
                const message = document.createElement('div');
                message.className = 'fallback-message text-center p-4 text-gray-500';
                message.innerHTML = `
                    <p>Bracket preview temporarily unavailable</p>
                    <a href="/tournaments/${this.getTournamentSlug()}/bracket/" class="text-blue-500 hover:underline">
                        View full bracket →
                    </a>
                `;
                container.appendChild(message);
            });
        });
        
        // Social sharing fallback
        this.registerFallback('social-sharing', () => {
            this.log('Using social sharing fallback');
            const shareButtons = document.querySelectorAll('.share-button');
            shareButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showShareModal();
                });
            });
        });
        
        // Live updates fallback
        this.registerFallback('live-updates', () => {
            this.log('Using live updates fallback - manual refresh');
            this.showManualRefreshOption();
        });
        
        // Timeline animations fallback
        this.registerFallback('timeline-animations', () => {
            this.log('Using timeline animations fallback - static timeline');
            const timelines = document.querySelectorAll('.tournament-timeline');
            timelines.forEach(timeline => {
                timeline.classList.add('static-timeline');
            });
        });
    }
    
    async loadModule(name, path, fallback = null) {
        // Check if module is already loaded
        if (this.modules.has(name)) {
            return this.modules.get(name);
        }
        
        // Check if module is currently loading
        if (this.loadingPromises.has(name)) {
            return this.loadingPromises.get(name);
        }
        
        this.log(`Loading module: ${name} from ${path}`);
        
        const loadPromise = this.attemptModuleLoad(name, path, fallback);
        this.loadingPromises.set(name, loadPromise);
        
        try {
            const module = await loadPromise;
            this.modules.set(name, module);
            this.loadingPromises.delete(name);
            return module;
        } catch (error) {
            this.loadingPromises.delete(name);
            throw error;
        }
    }
    
    async attemptModuleLoad(name, path, fallback, attempt = 1) {
        try {
            // Try to load the module
            const module = await this.loadScript(path);
            this.log(`Module ${name} loaded successfully`);
            return module;
            
        } catch (error) {
            this.log(`Failed to load module ${name} (attempt ${attempt}):`, error);
            
            // Retry if we haven't exceeded max attempts
            if (attempt < this.config.retryAttempts) {
                await this.delay(this.config.retryDelay);
                return this.attemptModuleLoad(name, path, fallback, attempt + 1);
            }
            
            // Execute fallback if available
            if (fallback) {
                this.log(`Executing fallback for module ${name}`);
                if (typeof fallback === 'string' && this.fallbacks.has(fallback)) {
                    this.fallbacks.get(fallback)();
                } else if (typeof fallback === 'function') {
                    fallback();
                }
                return { fallback: true, name };
            }
            
            // Execute registered fallback if available
            if (this.fallbacks.has(name)) {
                this.log(`Executing registered fallback for module ${name}`);
                this.fallbacks.get(name)();
                return { fallback: true, name };
            }
            
            throw error;
        }
    }
    
    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if script is already loaded
            const existingScript = document.querySelector(`script[src="${src}"]`);
            if (existingScript) {
                resolve({ existing: true });
                return;
            }
            
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            
            script.onload = () => {
                this.log(`Script loaded: ${src}`);
                resolve({ loaded: true });
            };
            
            script.onerror = () => {
                this.log(`Script failed to load: ${src}`);
                reject(new Error(`Failed to load script: ${src}`));
            };
            
            document.head.appendChild(script);
        });
    }
    
    registerFallback(moduleName, fallbackFunction) {
        this.fallbacks.set(moduleName, fallbackFunction);
        this.log(`Fallback registered for module: ${moduleName}`);
    }
    
    getModuleStatus(name) {
        if (this.modules.has(name)) {
            const module = this.modules.get(name);
            return module.fallback ? 'fallback' : 'loaded';
        }
        
        if (this.loadingPromises.has(name)) {
            return 'loading';
        }
        
        return 'not_loaded';
    }
    
    getAllModuleStatuses() {
        const statuses = {};
        
        // Get status of all attempted modules
        const allModules = new Set([
            ...this.modules.keys(),
            ...this.loadingPromises.keys()
        ]);
        
        allModules.forEach(name => {
            statuses[name] = this.getModuleStatus(name);
        });
        
        return statuses;
    }
    
    showShareModal() {
        // Create simple share modal as fallback
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <h3 class="text-lg font-semibold mb-4">Share Tournament</h3>
                <div class="space-y-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Tournament URL:</label>
                        <div class="flex">
                            <input type="text" value="${window.location.href}" 
                                   class="flex-1 px-3 py-2 border border-gray-300 rounded-l-md text-sm"
                                   readonly id="share-url-input">
                            <button onclick="this.copyUrl()" 
                                    class="px-4 py-2 bg-blue-500 text-white rounded-r-md hover:bg-blue-600 text-sm">
                                Copy
                            </button>
                        </div>
                    </div>
                    <div class="flex gap-2">
                        <a href="https://twitter.com/intent/tweet?url=${encodeURIComponent(window.location.href)}" 
                           target="_blank" class="flex-1 bg-blue-400 text-white px-4 py-2 rounded text-center text-sm hover:bg-blue-500">
                            Twitter
                        </a>
                        <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}" 
                           target="_blank" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded text-center text-sm hover:bg-blue-700">
                            Facebook
                        </a>
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        class="mt-4 w-full px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
                    Close
                </button>
            </div>
        `;
        
        // Add copy functionality
        modal.querySelector('button[onclick="this.copyUrl()"]').onclick = async () => {
            const input = modal.querySelector('#share-url-input');
            try {
                await navigator.clipboard.writeText(input.value);
                this.showToast('URL copied to clipboard!', 'success');
            } catch (err) {
                input.select();
                document.execCommand('copy');
                this.showToast('URL copied to clipboard!', 'success');
            }
        };
        
        document.body.appendChild(modal);
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    showManualRefreshOption() {
        // Add manual refresh button for live updates fallback
        const refreshButton = document.createElement('button');
        refreshButton.className = 'fixed bottom-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-600 z-50';
        refreshButton.innerHTML = `
            <svg class="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh
        `;
        
        refreshButton.addEventListener('click', () => {
            window.location.reload();
        });
        
        document.body.appendChild(refreshButton);
        
        // Show notification about manual refresh
        this.showToast('Live updates unavailable. Use refresh button for latest data.', 'info', 5000);
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`;
        
        const typeClasses = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'warning': 'bg-yellow-500 text-white',
            'info': 'bg-blue-500 text-white'
        };
        
        toast.className += ` ${typeClasses[type] || typeClasses.info}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after duration
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    setupErrorHandling() {
        // Handle global JavaScript errors
        window.addEventListener('error', (event) => {
            if (event.filename && event.filename.includes('/static/js/modules/')) {
                this.log('Module error detected:', event.error);
                // Could trigger fallback for specific modules here
            }
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.log('Unhandled promise rejection in modules:', event.reason);
        });
    }
    
    getTournamentSlug() {
        const pathParts = window.location.pathname.split('/');
        const tournamentsIndex = pathParts.indexOf('tournaments');
        
        if (tournamentsIndex !== -1 && pathParts[tournamentsIndex + 1]) {
            return pathParts[tournamentsIndex + 1];
        }
        
        return document.body.dataset.tournamentSlug || '';
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    log(...args) {
        if (this.config.debug) {
            console.log('[ModuleManager]', ...args);
        }
    }
    
    destroy() {
        // Clean up all modules
        this.modules.forEach((module, name) => {
            if (module && typeof module.destroy === 'function') {
                try {
                    module.destroy();
                } catch (error) {
                    this.log(`Error destroying module ${name}:`, error);
                }
            }
        });
        
        this.modules.clear();
        this.fallbacks.clear();
        this.loadingPromises.clear();
        
        this.log('ModuleManager destroyed');
    }
}

// Make available globally
window.ModuleManager = ModuleManager;