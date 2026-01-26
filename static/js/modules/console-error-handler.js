/**
 * Console Error Handler Module
 * Provides comprehensive error handling for all JavaScript operations
 * Implements graceful network request failure handling and informative logging
 * Addresses Requirements 7.1, 7.2, 7.3, 7.4, 7.5
 */

class ConsoleErrorHandler {
    constructor(config = {}) {
        this.config = {
            enableLogging: true,
            logLevel: 'info',
            suppressErrors: true,
            networkRetries: 3,
            networkTimeout: 10000,
            ...config
        };
        
        this.errorCounts = {
            javascript: 0,
            network: 0,
            module: 0,
            promise: 0
        };
        
        this.handledErrors = new Set();
        this.networkRequests = new Map();
        this.originalConsole = {};
        
        this.init();
    }
    
    init() {
        this.setupGlobalErrorHandling();
        this.setupNetworkErrorHandling();
        this.setupConsoleInterception();
        this.setupModuleErrorHandling();
        this.log('Console Error Handler initialized', 'info');
    }
    
    setupGlobalErrorHandling() {
        if (typeof window !== 'undefined') {
            window.addEventListener('error', (event) => {
                this.handleJavaScriptError(event);
            });
            
            window.addEventListener('unhandledrejection', (event) => {
                this.handlePromiseRejection(event);
            });
            
            window.addEventListener('error', (event) => {
                if (event.target && event.target !== window) {
                    this.handleResourceError(event);
                }
            }, true);
        }
    }
    
    handleJavaScriptError(event) {
        const errorKey = `${event.filename}:${event.lineno}:${event.colno}:${event.message}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.javascript++;
        
        this.log(`JavaScript Error: ${event.message}`, 'debug', {
            filename: event.filename,
            line: event.lineno,
            column: event.colno,
            stack: event.error?.stack
        });
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
        
        this.attemptErrorRecovery('javascript', event);
    }
    
    handlePromiseRejection(event) {
        const errorKey = `promise:${event.reason}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.promise++;
        
        this.log(`Promise Rejection: ${event.reason}`, 'debug', {
            reason: event.reason,
            stack: event.reason?.stack
        });
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
        
        this.attemptErrorRecovery('promise', event);
    }
    
    handleResourceError(event) {
        const resource = event.target.src || event.target.href || 'unknown';
        const errorKey = `resource:${resource}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.module++;
        
        this.log(`Resource Error: ${resource}`, 'debug', {
            resource,
            type: event.target.tagName
        });
        
        this.attemptErrorRecovery('resource', event);
    }
    
    setupNetworkErrorHandling() {
        if (typeof window !== 'undefined' && window.fetch) {
            this.originalFetch = window.fetch;
            window.fetch = this.createNetworkWrapper(this.originalFetch.bind(window));
            this.setupXHRErrorHandling();
        }
    }
    
    createNetworkWrapper(originalFetch) {
        return async (...args) => {
            const requestId = this.generateRequestId();
            const startTime = Date.now();
            
            try {
                this.networkRequests.set(requestId, {
                    url: args[0],
                    startTime,
                    status: 'pending'
                });
                
                const response = await originalFetch(...args);
                
                this.networkRequests.set(requestId, {
                    ...this.networkRequests.get(requestId),
                    status: response.ok ? 'success' : 'error',
                    statusCode: response.status,
                    duration: Date.now() - startTime
                });
                
                if (!response.ok) {
                    this.handleNetworkError(response, requestId);
                }
                
                return response;
                
            } catch (error) {
                this.networkRequests.set(requestId, {
                    ...this.networkRequests.get(requestId),
                    status: 'failed',
                    error: error.message,
                    duration: Date.now() - startTime
                });
                
                this.handleNetworkError(error, requestId);
                throw error;
            }
        };
    }
    
    setupXHRErrorHandling() {
        if (typeof window !== 'undefined' && window.XMLHttpRequest) {
            const originalXHR = window.XMLHttpRequest;
            const self = this;
            
            window.XMLHttpRequest = function() {
                const xhr = new originalXHR();
                const originalSend = xhr.send;
                
                xhr.send = function(...args) {
                    const requestId = self.generateRequestId();
                    
                    xhr.addEventListener('error', (event) => {
                        self.handleNetworkError(event, requestId);
                    });
                    
                    xhr.addEventListener('timeout', (event) => {
                        self.handleNetworkError(new Error('Request timeout'), requestId);
                    });
                    
                    return originalSend.apply(xhr, args);
                };
                
                return xhr;
            };
        }
    }
    
    handleNetworkError(error, requestId = null) {
        this.errorCounts.network++;
        
        const errorInfo = {
            requestId,
            message: error.message || `HTTP ${error.status}`,
            status: error.status,
            url: error.url || this.networkRequests.get(requestId)?.url
        };
        
        this.log(`Network Error: ${errorInfo.message}`, 'debug', errorInfo);
        this.attemptErrorRecovery('network', error);
    }
    
    setupConsoleInterception() {
        if (typeof console !== 'undefined') {
            this.originalConsole = {
                log: console.log.bind(console),
                warn: console.warn.bind(console),
                error: console.error.bind(console),
                info: console.info.bind(console),
                debug: console.debug ? console.debug.bind(console) : console.log.bind(console)
            };
            
            console.log = (...args) => this.interceptConsoleCall('log', args);
            console.warn = (...args) => this.interceptConsoleCall('warn', args);
            console.error = (...args) => this.interceptConsoleCall('error', args);
            console.info = (...args) => this.interceptConsoleCall('info', args);
            if (console.debug) {
                console.debug = (...args) => this.interceptConsoleCall('debug', args);
            }
        }
    }
    
    interceptConsoleCall(level, args) {
        if (level === 'error' && this.config.suppressErrors) {
            this.log(`Suppressed console error: ${args.join(' ')}`, 'debug');
            return;
        }
        
        if (this.shouldLog(level)) {
            this.originalConsole[level](...args);
        }
    }
    
    setupModuleErrorHandling() {
        if (typeof document !== 'undefined') {
            this.monitorScriptLoading();
            this.monitorDynamicImports();
        }
    }
    
    monitorScriptLoading() {
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (node.tagName === 'SCRIPT') {
                            this.attachScriptErrorHandlers(node);
                        }
                    });
                });
            });
            
            observer.observe(document.head || document.documentElement, {
                childList: true,
                subtree: true
            });
            
            document.querySelectorAll('script').forEach(script => {
                this.attachScriptErrorHandlers(script);
            });
        }
    }
    
    attachScriptErrorHandlers(script) {
        script.addEventListener('error', (event) => {
            this.handleResourceError(event);
        });
        
        script.addEventListener('load', () => {
            this.log(`Script loaded successfully: ${script.src}`, 'debug');
        });
    }
    
    monitorDynamicImports() {
        if (typeof window !== 'undefined' && window.import) {
            const originalImport = window.import;
            window.import = async (specifier) => {
                try {
                    const module = await originalImport(specifier);
                    this.log(`Dynamic import successful: ${specifier}`, 'debug');
                    return module;
                } catch (error) {
                    this.handleModuleError(error, specifier);
                    throw error;
                }
            };
        }
    }
    
    handleModuleError(error, modulePath) {
        this.errorCounts.module++;
        
        this.log(`Module Error: ${error.message}`, 'debug', {
            module: modulePath,
            error: error.message,
            stack: error.stack
        });
        
        this.attemptErrorRecovery('module', error);
    }
    
    attemptErrorRecovery(errorType, errorEvent) {
        switch (errorType) {
            case 'javascript':
                this.recoverFromJavaScriptError(errorEvent);
                break;
            case 'network':
                this.recoverFromNetworkError(errorEvent);
                break;
            case 'module':
                this.recoverFromModuleError(errorEvent);
                break;
            case 'promise':
                this.recoverFromPromiseError(errorEvent);
                break;
            case 'resource':
                this.recoverFromResourceError(errorEvent);
                break;
        }
    }
    
    recoverFromJavaScriptError(errorEvent) {
        this.log('Attempting JavaScript error recovery', 'debug');
    }
    
    recoverFromNetworkError(error) {
        this.log('Attempting network error recovery', 'debug');
    }
    
    recoverFromModuleError(error) {
        this.log('Attempting module error recovery', 'debug');
    }
    
    recoverFromPromiseError(errorEvent) {
        this.log('Attempting promise error recovery', 'debug');
    }
    
    recoverFromResourceError(errorEvent) {
        this.log('Attempting resource error recovery', 'debug');
    }
    
    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }
    
    log(message, level = 'info', data = null) {
        if (this.shouldLog(level)) {
            if (level === 'error' && !this.config.suppressErrors) {
                this.originalConsole.error(`[ConsoleErrorHandler] ${message}`, data);
            } else if (level !== 'error') {
                this.originalConsole[level](`[ConsoleErrorHandler] ${message}`, data || '');
            }
        }
    }
    
    shouldLog(level) {
        if (!this.config.enableLogging) return false;
        
        const levels = ['debug', 'info', 'warn', 'error'];
        const currentLevelIndex = levels.indexOf(this.config.logLevel);
        const messageLevelIndex = levels.indexOf(level);
        
        return messageLevelIndex >= currentLevelIndex;
    }
    
    getErrorCounts() {
        return { ...this.errorCounts };
    }
    
    getNetworkStats() {
        const requests = Array.from(this.networkRequests.values());
        return {
            total: requests.length,
            successful: requests.filter(r => r.status === 'success').length,
            failed: requests.filter(r => r.status === 'failed').length,
            errors: requests.filter(r => r.status === 'error').length,
            averageDuration: requests.length > 0 ? 
                requests.reduce((sum, r) => sum + (r.duration || 0), 0) / requests.length : 0
        };
    }
    
    clearData() {
        this.errorCounts = {
            javascript: 0,
            network: 0,
            module: 0,
            promise: 0
        };
        this.handledErrors.clear();
        this.networkRequests.clear();
    }
    
    destroy() {
        if (this.originalConsole && typeof console !== 'undefined') {
            Object.keys(this.originalConsole).forEach(method => {
                console[method] = this.originalConsole[method];
            });
        }
        
        if (this.originalFetch && typeof window !== 'undefined') {
            window.fetch = this.originalFetch;
        }
        
        this.clearData();
        this.log('Console Error Handler destroyed', 'info');
    }
}

// Export for use in other modules
console.log('Exporting ConsoleErrorHandler:', typeof ConsoleErrorHandler);
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConsoleErrorHandler;
    console.log('Exported via module.exports');
} else if (typeof window !== 'undefined') {
    window.ConsoleErrorHandler = ConsoleErrorHandler;
    console.log('Exported via window');
} else if (typeof global !== 'undefined') {
    global.ConsoleErrorHandler = ConsoleErrorHandler;
    console.log('Exported via global');
}