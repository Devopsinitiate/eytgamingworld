/**
 * Simple Console Error Handler Module
 * Simplified version for testing purposes
 */

class ConsoleErrorHandler {
    constructor(config = {}) {
        this.config = {
            enableLogging: true,
            logLevel: 'info',
            suppressErrors: true,
            ...config
        };
        
        this.errorCounts = {
            javascript: 0,
            network: 0,
            module: 0,
            promise: 0
        };
        
        this.handledErrors = new Set();
        this.originalConsole = {};
        
        this.init();
    }
    
    init() {
        this.log('Console Error Handler initialized', 'info');
    }
    
    handleJavaScriptError(event) {
        const errorKey = `${event.filename}:${event.lineno}:${event.message}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.javascript++;
        this.log(`JavaScript Error: ${event.message}`, 'debug');
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
    }
    
    handlePromiseRejection(event) {
        const errorKey = `promise:${event.reason}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.promise++;
        this.log(`Promise Rejection: ${event.reason}`, 'debug');
        
        if (this.config.suppressErrors && event.preventDefault) {
            event.preventDefault();
        }
    }
    
    handleResourceError(event) {
        const resource = event.target.src || event.target.href || 'unknown';
        const errorKey = `resource:${resource}`;
        
        if (this.handledErrors.has(errorKey)) {
            return;
        }
        this.handledErrors.add(errorKey);
        
        this.errorCounts.module++;
        this.log(`Resource Error: ${resource}`, 'debug');
    }
    
    handleNetworkError(error) {
        this.errorCounts.network++;
        
        const errorInfo = {
            message: error.message || `HTTP ${error.status}`,
            status: error.status,
            url: error.url
        };
        
        this.log(`Network Error: ${errorInfo.message}`, 'debug');
    }
    
    shouldLog(level) {
        if (!this.config.enableLogging) return false;
        
        const levels = ['debug', 'info', 'warn', 'error'];
        const currentLevelIndex = levels.indexOf(this.config.logLevel);
        const messageLevelIndex = levels.indexOf(level);
        
        return messageLevelIndex >= currentLevelIndex;
    }
    
    log(message, level = 'info') {
        if (this.shouldLog(level) && typeof console !== 'undefined') {
            console[level](`[ConsoleErrorHandler] ${message}`);
        }
    }
    
    getErrorCounts() {
        return { ...this.errorCounts };
    }
    
    clearData() {
        this.errorCounts = {
            javascript: 0,
            network: 0,
            module: 0,
            promise: 0
        };
        this.handledErrors.clear();
    }
    
    destroy() {
        this.clearData();
        this.log('Console Error Handler destroyed', 'info');
    }
}

// Export for use in other modules
module.exports = ConsoleErrorHandler;