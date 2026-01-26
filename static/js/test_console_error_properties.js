/**
 * Property-Based Tests for Console Error-Free Operation
 * Tests that all JavaScript operations maintain clean console logs without errors
 * 
 * **Feature: tournament-detail-page-fixes, Property 7: Console Error-Free Operation**
 * **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
 */

// Setup mock environment for Node.js testing
if (typeof window === 'undefined') {
    global.window = {
        location: {
            href: 'http://localhost/tournaments/test-tournament/',
            pathname: '/tournaments/test-tournament/',
            origin: 'http://localhost'
        },
        addEventListener: () => {},
        removeEventListener: () => {},
        setTimeout: setTimeout,
        clearTimeout: clearTimeout,
        fetch: () => Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({})
        }),
        navigator: {
            userAgent: 'Mozilla/5.0 (Test Environment)'
        }
    };
}

if (typeof document === 'undefined') {
    global.document = {
        createElement: () => ({
            src: '',
            onload: null,
            onerror: null,
            setAttribute: () => {},
            getAttribute: () => null
        }),
        head: {
            appendChild: () => {}
        },
        addEventListener: () => {},
        querySelector: () => null,
        querySelectorAll: () => []
    };
}

// Mock ConsoleErrorHandler for testing
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
        this.interceptedLogs = [];
        
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
    
    setupNetworkErrorHandling() {
        // Mock network request handling
        if (typeof window !== 'undefined' && window.fetch) {
            this.originalFetch = window.fetch;
            window.fetch = this.createNetworkWrapper(this.originalFetch);
        }
    }
    
    setupConsoleInterception() {
        // Store original console methods
        this.originalConsole = {
            log: console.log || (() => {}),
            warn: console.warn || (() => {}),
            error: console.error || (() => {}),
            info: console.info || (() => {}),
            debug: console.debug || (() => {})
        };
        
        // Intercept console methods
        console.log = (...args) => this.interceptConsoleCall('log', args);
        console.warn = (...args) => this.interceptConsoleCall('warn', args);
        console.error = (...args) => this.interceptConsoleCall('error', args);
        console.info = (...args) => this.interceptConsoleCall('info', args);
        if (console.debug) {
            console.debug = (...args) => this.interceptConsoleCall('debug', args);
        }
    }
    
    setupModuleErrorHandling() {
        // Mock module loading error handling
        this.moduleLoadErrors = new Set();
    }
    
    handleJavaScriptError(event) {
        const errorKey = `${event.filename}:${event.lineno}:${event.colno}:${event.message}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.javascript++;
        
        // Log for debugging but suppress from console
        this.log(`JavaScript Error handled: ${event.message}`, 'debug', {
            filename: event.filename,
            line: event.lineno,
            column: event.colno
        });
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
    }
    
    handlePromiseRejection(event) {
        this.errorCounts.promise++;
        this.log(`Promise rejection handled: ${event.reason}`, 'debug');
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
    }
    
    handleResourceError(event) {
        this.errorCounts.module++;
        this.log(`Resource error handled: ${event.target.src || event.target.href}`, 'debug');
    }
    
    createNetworkWrapper(originalFetch) {
        return async (...args) => {
            try {
                const response = await originalFetch.apply(window, args);
                if (!response.ok) {
                    this.handleNetworkError(response);
                }
                return response;
            } catch (error) {
                this.handleNetworkError(error);
                throw error;
            }
        };
    }
    
    handleNetworkError(error) {
        this.errorCounts.network++;
        this.log(`Network error handled: ${error.message || error.status}`, 'debug');
    }
    
    interceptConsoleCall(level, args) {
        const logEntry = {
            level,
            args,
            timestamp: Date.now(),
            isError: level === 'error'
        };
        
        this.interceptedLogs.push(logEntry);
        
        // Only call original console methods for non-error logs or when debugging
        if (level !== 'error' || this.config.logLevel === 'debug') {
            const originalMethod = this.originalConsole[level];
            if (originalMethod && typeof originalMethod === 'function') {
                originalMethod.apply(console, args);
            }
        }
    }
    
    log(message, level = 'info', data = null) {
        if (this.shouldLog(level)) {
            const logEntry = {
                level,
                message,
                data,
                timestamp: Date.now(),
                isError: level === 'error'
            };
            
            this.interceptedLogs.push(logEntry);
            
            if (level !== 'error' || this.config.logLevel === 'debug') {
                const originalMethod = this.originalConsole[level];
                if (originalMethod && typeof originalMethod === 'function') {
                    originalMethod(message, data);
                }
            }
        }
    }
    
    shouldLog(level) {
        const levels = ['debug', 'info', 'warn', 'error'];
        const currentLevelIndex = levels.indexOf(this.config.logLevel);
        const messageLevelIndex = levels.indexOf(level);
        return messageLevelIndex >= currentLevelIndex;
    }
    
    getErrorCounts() {
        return { ...this.errorCounts };
    }
    
    getInterceptedLogs() {
        return [...this.interceptedLogs];
    }
    
    getConsoleErrors() {
        return this.interceptedLogs.filter(log => log.isError);
    }
    
    clearLogs() {
        this.interceptedLogs = [];
    }
    
    destroy() {
        // Restore original console methods
        Object.keys(this.originalConsole).forEach(method => {
            console[method] = this.originalConsole[method];
        });
        
        // Restore original fetch
        if (this.originalFetch && typeof window !== 'undefined') {
            window.fetch = this.originalFetch;
        }
        
        this.clearLogs();
    }
}

// Property test generators for console error scenarios
class ConsoleErrorTestGenerators {
    /**
     * Generate random JavaScript operations that might cause errors
     */
    static generateJavaScriptOperation() {
        const operations = [
            () => { throw new Error('Test JavaScript error'); },
            () => { return undefined.property; },
            () => { return nonExistentFunction(); },
            () => { JSON.parse('invalid json'); },
            () => { new Date('invalid date').getTime(); },
            () => { return 'valid operation'; }
        ];
        
        return operations[Math.floor(Math.random() * operations.length)];
    }
    
    /**
     * Generate random network request scenarios
     */
    static generateNetworkRequest() {
        const requests = [
            { url: '/api/valid-endpoint', shouldFail: false },
            { url: '/api/nonexistent-endpoint', shouldFail: true },
            { url: '/api/timeout-endpoint', shouldFail: true },
            { url: '/api/server-error', shouldFail: true },
            { url: 'invalid-url', shouldFail: true }
        ];
        
        return requests[Math.floor(Math.random() * requests.length)];
    }
    
    /**
     * Generate random module loading scenarios
     */
    static generateModuleLoadScenario() {
        const scenarios = [
            { path: '/static/js/valid-module.js', shouldFail: false },
            { path: '/static/js/nonexistent-module.js', shouldFail: true },
            { path: '/static/js/syntax-error-module.js', shouldFail: true },
            { path: 'invalid-path', shouldFail: true }
        ];
        
        return scenarios[Math.floor(Math.random() * scenarios.length)];
    }
    
    /**
     * Generate random promise operations
     */
    static generatePromiseOperation() {
        const operations = [
            () => Promise.resolve('success'),
            () => Promise.reject(new Error('Test promise rejection')),
            () => new Promise((resolve, reject) => {
                setTimeout(() => reject(new Error('Async error')), 10);
            }),
            () => Promise.all([Promise.resolve(1), Promise.reject('error')]),
            () => Promise.race([Promise.resolve('fast'), Promise.reject('slow')])
        ];
        
        return operations[Math.floor(Math.random() * operations.length)];
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ConsoleErrorHandler, ConsoleErrorTestGenerators };
}