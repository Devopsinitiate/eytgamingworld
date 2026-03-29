/**
 * UnifiedPollingManager - Centralized polling coordinator for tournament detail page
 * 
 * Consolidates multiple independent polling mechanisms into a single coordinated system
 * to prevent rate limit errors while maintaining real-time update functionality.
 * 
 * Features:
 * - Single coordinated polling interval (reduces 5+ intervals to 1)
 * - Page visibility detection (pauses/slows when tab hidden)
 * - Exponential backoff on rate limit errors
 * - Component subscription system for distributing updates
 * - Request deduplication to prevent concurrent requests
 */

export class UnifiedPollingManager {
    constructor(tournamentSlug, options = {}) {
        this.tournamentSlug = tournamentSlug;
        
        // Configuration options
        this.config = {
            baseInterval: options.baseInterval || 60000, // 60 seconds default
            hiddenInterval: options.hiddenInterval || 300000, // 5 minutes when hidden
            enableBackoff: options.enableBackoff !== false,
            enableVisibilityDetection: options.enableVisibilityDetection !== false,
            maxBackoffDelay: options.maxBackoffDelay || 600000, // 10 minutes max
            jitterPercent: options.jitterPercent || 0.1, // 10% jitter
            ...options
        };
        
        // State management
        this.isRunning = false;
        this.isPaused = false;
        this.currentInterval = this.config.baseInterval;
        this.backoffAttempts = 0;
        this.pollingTimer = null;
        this.isRequestInProgress = false;
        this.lastUpdateTimestamp = null;
        
        // Component subscription registry
        this.subscribers = new Map();
        
        // Bind methods for event listeners
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    }
    
    /**
     * Register a component to receive updates
     * @param {string} componentName - Unique identifier for the component
     * @param {Function} callback - Function to call with update data
     */
    registerComponent(componentName, callback) {
        if (typeof callback !== 'function') {
            console.error(`[UnifiedPollingManager] Invalid callback for component: ${componentName}`);
            return;
        }
        
        this.subscribers.set(componentName, callback);
        console.log(`[UnifiedPollingManager] Registered component: ${componentName}`);
    }
    
    /**
     * Unregister a component from receiving updates
     * @param {string} componentName - Component identifier to remove
     */
    unregisterComponent(componentName) {
        const removed = this.subscribers.delete(componentName);
        if (removed) {
            console.log(`[UnifiedPollingManager] Unregistered component: ${componentName}`);
        }
    }
    
    /**
     * Start the unified polling mechanism
     */
    start() {
        if (this.isRunning) {
            console.warn('[UnifiedPollingManager] Already running');
            return;
        }
        
        this.isRunning = true;
        this.isPaused = false;
        
        // Set up page visibility detection
        if (this.config.enableVisibilityDetection) {
            this.setupVisibilityDetection();
        }
        
        // Perform immediate initial fetch
        this.fetchUnifiedUpdates();
        
        // Start polling interval
        this.scheduleNextPoll();
        
        console.log(`[UnifiedPollingManager] Started with interval: ${this.currentInterval}ms`);
    }
    
    /**
     * Stop the unified polling mechanism
     */
    stop() {
        if (!this.isRunning) {
            return;
        }
        
        this.isRunning = false;
        this.isPaused = false;
        
        // Clear polling timer
        if (this.pollingTimer) {
            clearTimeout(this.pollingTimer);
            this.pollingTimer = null;
        }
        
        // Remove visibility detection listeners with cross-browser support
        if (this.config.enableVisibilityDetection) {
            if (typeof document.hidden !== 'undefined') {
                document.removeEventListener('visibilitychange', this.handleVisibilityChange);
            } else if (typeof document.webkitHidden !== 'undefined') {
                document.removeEventListener('webkitvisibilitychange', this.handleVisibilityChange);
            } else {
                // Remove focus/blur fallback listeners
                window.removeEventListener('focus', this.handleVisibilityChange);
                window.removeEventListener('blur', this.handleVisibilityChange);
            }
        }
        
        console.log('[UnifiedPollingManager] Stopped');
    }
    
    /**
     * Pause polling (used when tab is hidden)
     */
    pause() {
        if (this.isPaused) {
            return;
        }
        
        this.isPaused = true;
        
        // Clear current timer
        if (this.pollingTimer) {
            clearTimeout(this.pollingTimer);
            this.pollingTimer = null;
        }
        
        console.log('[UnifiedPollingManager] Paused');
    }
    
    /**
     * Resume polling (used when tab becomes visible)
     */
    resume() {
        if (!this.isPaused || !this.isRunning) {
            return;
        }
        
        this.isPaused = false;
        
        // Fetch immediately on resume
        this.fetchUnifiedUpdates();
        
        // Restart polling
        this.scheduleNextPoll();
        
        console.log('[UnifiedPollingManager] Resumed');
    }
    
    /**
     * Schedule the next poll with current interval and jitter
     */
    scheduleNextPoll() {
        if (!this.isRunning || this.isPaused) {
            return;
        }
        
        // Clear any existing timer
        if (this.pollingTimer) {
            clearTimeout(this.pollingTimer);
        }
        
        // Add jitter to prevent thundering herd
        const jitter = this.currentInterval * this.config.jitterPercent * Math.random();
        const delay = this.currentInterval + jitter;
        
        this.pollingTimer = setTimeout(() => {
            this.fetchUnifiedUpdates();
            this.scheduleNextPoll();
        }, delay);
    }
    
    /**
     * Fetch unified updates from the server
     * Implements request deduplication and error handling with fallback support
     */
    async fetchUnifiedUpdates() {
        // Prevent concurrent requests
        if (this.isRequestInProgress) {
            console.log('[UnifiedPollingManager] Request already in progress, skipping');
            return;
        }
        
        this.isRequestInProgress = true;
        
        try {
            const response = await fetch(`/api/tournament/${this.tournamentSlug}/unified-updates/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });
            
            if (response.status === 429) {
                // Rate limit hit - trigger exponential backoff
                this.handleRateLimitError();
                return;
            }
            
            if (response.status === 404) {
                // Unified endpoint not available - fallback to legacy polling
                console.warn('[UnifiedPollingManager] Unified endpoint not found, falling back to legacy mode');
                this.fallbackToLegacyPolling();
                return;
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Successful response - reset backoff
            if (this.backoffAttempts > 0) {
                console.log('[UnifiedPollingManager] Request successful, resetting backoff');
                this.resetBackoff();
            }
            
            // Update timestamp
            this.lastUpdateTimestamp = data.timestamp || Date.now();
            
            // Distribute updates to subscribers
            this.distributeUpdates(data);
            
        } catch (error) {
            console.error('[UnifiedPollingManager] Fetch error:', error);
            // Don't trigger backoff for network errors, only for rate limits
            // Network errors will be retried on next poll cycle
        } finally {
            this.isRequestInProgress = false;
        }
    }
    
    /**
     * Fallback to legacy polling if unified endpoint is not available
     */
    fallbackToLegacyPolling() {
        console.warn('[UnifiedPollingManager] Falling back to legacy polling mode');
        
        // Stop unified polling
        this.stop();
        
        // Notify subscribers that fallback mode is active
        this.subscribers.forEach((callback, componentName) => {
            try {
                callback({
                    fallbackMode: true,
                    message: 'Using legacy polling mode'
                });
            } catch (error) {
                console.error(`[UnifiedPollingManager] Error notifying ${componentName} of fallback:`, error);
            }
        });
        
        // In a real implementation, you might want to re-enable legacy polling here
        // For now, we just stop and log the issue
        console.log('[UnifiedPollingManager] Legacy polling would be re-enabled here');
    }
    
    /**
     * Distribute fetched data to all registered components
     * @param {Object} data - Unified update data from server
     */
    distributeUpdates(data) {
        if (!data) {
            return;
        }
        
        // Notify each subscriber with relevant data
        this.subscribers.forEach((callback, componentName) => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[UnifiedPollingManager] Error in ${componentName} callback:`, error);
            }
        });
    }
    
    /**
     * Handle rate limit error with exponential backoff
     */
    handleRateLimitError() {
        if (!this.config.enableBackoff) {
            console.warn('[UnifiedPollingManager] Rate limit hit but backoff disabled');
            return;
        }
        
        this.backoffAttempts++;
        
        // Calculate new interval with exponential backoff
        const backoffDelay = this.calculateBackoffDelay();
        this.currentInterval = Math.min(backoffDelay, this.config.maxBackoffDelay);
        
        console.warn(
            `[UnifiedPollingManager] Rate limit hit (attempt ${this.backoffAttempts}), ` +
            `backing off to ${this.currentInterval}ms`
        );
        
        // Reschedule with new interval
        this.scheduleNextPoll();
    }
    
    /**
     * Calculate exponential backoff delay
     * @returns {number} Delay in milliseconds
     */
    calculateBackoffDelay() {
        // Exponential: baseInterval * 2^attemptNumber
        return this.config.baseInterval * Math.pow(2, this.backoffAttempts);
    }
    
    /**
     * Reset backoff state after successful request
     */
    resetBackoff() {
        this.backoffAttempts = 0;
        this.currentInterval = this.config.baseInterval;
    }
    
    /**
     * Set up page visibility detection with fallback
     */
    setupVisibilityDetection() {
        // Check if Page Visibility API is supported
        if (typeof document.hidden !== 'undefined') {
            // Modern browsers - use Page Visibility API
            document.addEventListener('visibilitychange', this.handleVisibilityChange);
            console.log('[UnifiedPollingManager] Using Page Visibility API');
        } else if (typeof document.webkitHidden !== 'undefined') {
            // Webkit browsers fallback
            document.addEventListener('webkitvisibilitychange', this.handleVisibilityChange);
            console.log('[UnifiedPollingManager] Using webkit Page Visibility API');
        } else {
            // Fallback to focus/blur events for older browsers
            console.warn('[UnifiedPollingManager] Page Visibility API not supported, using focus/blur fallback');
            window.addEventListener('focus', () => {
                if (this.isPaused) {
                    this.resume();
                }
            });
            window.addEventListener('blur', () => {
                if (!this.isPaused) {
                    this.pause();
                }
            });
        }
    }
    
    /**
     * Handle page visibility changes with cross-browser support
     */
    handleVisibilityChange() {
        // Check visibility state with fallbacks
        const isHidden = document.hidden || document.webkitHidden || false;
        
        if (isHidden) {
            // Tab is hidden - pause or slow down polling
            console.log('[UnifiedPollingManager] Tab hidden, pausing polling');
            this.pause();
        } else {
            // Tab is visible - resume normal polling
            console.log('[UnifiedPollingManager] Tab visible, resuming polling');
            this.resume();
        }
    }
    
    /**
     * Get current polling status
     * @returns {Object} Status information
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            isPaused: this.isPaused,
            currentInterval: this.currentInterval,
            backoffAttempts: this.backoffAttempts,
            subscriberCount: this.subscribers.size,
            lastUpdate: this.lastUpdateTimestamp
        };
    }
}
