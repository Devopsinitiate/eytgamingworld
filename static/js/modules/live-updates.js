/**
 * Real-time Updates System for Tournament Detail Pages
 * Handles Server-Sent Events (SSE) and fallback polling for live updates
 */

class LiveUpdatesManager {
    constructor(tournamentSlug, options = {}) {
        this.tournamentSlug = tournamentSlug;
        this.options = {
            enableSSE: true,
            fallbackPolling: true,
            pollingInterval: 30000, // 30 seconds
            reconnectDelay: 5000,   // 5 seconds
            maxReconnectAttempts: 10,
            debug: false,
            ...options
        };
        
        this.eventSource = null;
        this.pollingInterval = null;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        this.lastUpdateTime = null;
        this.connectionStatus = 'disconnected';
        
        // Event handlers
        this.eventHandlers = {
            'match_update': [],
            'participant_update': [],
            'tournament_update': [],
            'statistics_update': [],
            'connection_status': [],
            'error': []
        };
        
        this.init();
    }

    init() {
        this.log('Initializing Live Updates Manager');
        
        // Check if tournament supports live updates
        if (!this.shouldEnableLiveUpdates()) {
            this.log('Live updates not enabled for this tournament status');
            return;
        }
        
        // Set up connection status indicator
        this.setupConnectionStatusIndicator();
        
        // Try SSE first, fallback to polling if needed
        if (this.options.enableSSE && this.supportsSSE()) {
            this.connectSSE();
        } else if (this.options.fallbackPolling) {
            this.startPolling();
        }
        
        // Handle page visibility changes
        this.setupVisibilityHandling();
        
        // Handle connection failures gracefully
        this.setupErrorHandling();
        
        this.log('Live Updates Manager initialized');
    }

    shouldEnableLiveUpdates() {
        // Check tournament status from page data
        const tournamentStatus = document.querySelector('[data-tournament-status]')?.dataset.tournamentStatus;
        return ['check_in', 'in_progress'].includes(tournamentStatus);
    }

    supportsSSE() {
        return typeof EventSource !== 'undefined';
    }

    connectSSE() {
        this.log('Attempting SSE connection');
        
        try {
            const url = `/tournaments/${this.tournamentSlug}/live-updates/`;
            this.eventSource = new EventSource(url);
            
            this.eventSource.onopen = () => {
                this.log('SSE connection opened');
                this.onConnectionOpen();
            };
            
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleUpdate(data);
                } catch (error) {
                    this.log('Error parsing SSE message:', error);
                }
            };
            
            this.eventSource.onerror = (event) => {
                this.log('SSE connection error:', event);
                this.onConnectionError();
            };
            
        } catch (error) {
            this.log('Failed to create SSE connection:', error);
            this.fallbackToPolling();
        }
    }

    startPolling() {
        this.log('Starting polling mode');
        this.connectionStatus = 'polling';
        this.updateConnectionStatus();
        
        // Initial fetch
        this.fetchUpdates();
        
        // Set up polling interval
        this.pollingInterval = setInterval(() => {
            this.fetchUpdates();
        }, this.options.pollingInterval);
    }

    async fetchUpdates() {
        try {
            const url = `/tournaments/api/${this.tournamentSlug}/stats/`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success) {
                    // Convert API response to update format
                    const update = {
                        type: 'statistics_update',
                        statistics: data.statistics,
                        tournament_status: data.status,
                        timestamp: data.timestamp
                    };
                    
                    this.handleUpdate(update);
                    this.onConnectionOpen(); // Mark as connected
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            this.log('Polling fetch error:', error);
            this.onConnectionError();
        }
    }

    handleUpdate(data) {
        this.log('Received update:', data);
        this.lastUpdateTime = new Date();
        
        switch (data.type) {
            case 'full_update':
                this.handleFullUpdate(data);
                break;
            case 'match_update':
                this.handleMatchUpdate(data);
                break;
            case 'participant_update':
                this.handleParticipantUpdate(data);
                break;
            case 'tournament_update':
                this.handleTournamentUpdate(data);
                break;
            case 'statistics_update':
                this.handleStatisticsUpdate(data);
                break;
            case 'tournament_ended':
                this.handleTournamentEnded(data);
                break;
            case 'heartbeat':
                this.handleHeartbeat(data);
                break;
            case 'error':
                this.handleError(data);
                break;
            default:
                this.log('Unknown update type:', data.type);
        }
        
        // Update last updated time display
        this.updateLastUpdatedDisplay();
    }

    handleStatisticsUpdate(data) {
        this.log('Processing statistics update');
        
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        
        this.triggerEvent('statistics_update', data);
    }

    updateStatistics(stats) {
        // Update participant statistics
        if (stats.participants) {
            this.updateParticipantStats(stats.participants);
        }
        
        // Update match statistics
        if (stats.matches) {
            this.updateMatchStats(stats.matches);
        }
        
        // Update engagement metrics
        if (stats.engagement) {
            this.updateEngagementStats(stats.engagement);
        }
        
        // Update current round
        if (stats.current_round) {
            this.updateCurrentRound(stats.current_round);
        }
    }

    updateParticipantStats(participantStats) {
        // Update registered count
        const registeredElement = document.querySelector('[data-stat="participants-registered"]');
        if (registeredElement) {
            this.animateValueChange(registeredElement, participantStats.registered);
        }
        
        // Update checked in count
        const checkedInElement = document.querySelector('[data-stat="participants-checked-in"]');
        if (checkedInElement) {
            this.animateValueChange(checkedInElement, participantStats.checked_in);
        }
    }

    updateMatchStats(matchStats) {
        const elements = {
            'matches-total': matchStats.total,
            'matches-completed': matchStats.completed,
            'matches-in-progress': matchStats.in_progress,
            'matches-upcoming': matchStats.upcoming
        };
        
        Object.entries(elements).forEach(([stat, value]) => {
            const element = document.querySelector(`[data-stat="${stat}"]`);
            if (element) {
                this.animateValueChange(element, value);
            }
        });
    }

    animateValueChange(element, newValue) {
        const currentValue = parseInt(element.textContent) || 0;
        
        if (currentValue !== newValue) {
            // Add update animation
            element.style.transform = 'scale(1.1)';
            element.style.color = '#10b981'; // Green flash
            
            setTimeout(() => {
                element.textContent = newValue;
                element.style.transform = 'scale(1)';
                element.style.color = ''; // Reset to original color
            }, 150);
        }
    }

    onConnectionOpen() {
        this.isConnected = true;
        this.connectionStatus = this.eventSource ? 'connected' : 'polling';
        this.reconnectAttempts = 0;
        this.updateConnectionStatus();
        this.triggerEvent('connection_status', { status: 'connected' });
    }

    onConnectionError() {
        this.isConnected = false;
        this.connectionStatus = 'error';
        this.updateConnectionStatus();
        
        // Try to reconnect
        if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.log(`Attempting reconnect ${this.reconnectAttempts}/${this.options.maxReconnectAttempts}`);
            
            setTimeout(() => {
                if (this.eventSource) {
                    this.connectSSE();
                } else {
                    this.startPolling();
                }
            }, this.options.reconnectDelay);
        } else {
            this.log('Max reconnect attempts reached, falling back to polling');
            this.fallbackToPolling();
        }
        
        this.triggerEvent('connection_status', { status: 'error' });
    }

    fallbackToPolling() {
        this.disconnect();
        
        if (this.options.fallbackPolling) {
            this.startPolling();
        }
    }

    setupConnectionStatusIndicator() {
        // Create connection status indicator
        const indicator = document.createElement('div');
        indicator.id = 'live-updates-status';
        indicator.className = 'fixed top-4 left-4 z-50 px-3 py-1 rounded-full text-xs font-medium transition-all duration-300';
        indicator.style.display = 'none';
        
        document.body.appendChild(indicator);
        this.statusIndicator = indicator;
    }

    updateConnectionStatus() {
        if (!this.statusIndicator) return;
        
        const statusConfig = {
            'connected': {
                text: 'Live Updates Active',
                class: 'bg-green-500 text-white',
                show: true
            },
            'polling': {
                text: 'Live Updates (Polling)',
                class: 'bg-yellow-500 text-white',
                show: true
            },
            'error': {
                text: 'Connection Issues',
                class: 'bg-red-500 text-white',
                show: true
            },
            'disconnected': {
                text: 'Disconnected',
                class: 'bg-gray-500 text-white',
                show: false
            }
        };
        
        const config = statusConfig[this.connectionStatus] || statusConfig.disconnected;
        
        this.statusIndicator.textContent = config.text;
        this.statusIndicator.className = `fixed top-4 left-4 z-50 px-3 py-1 rounded-full text-xs font-medium transition-all duration-300 ${config.class}`;
        this.statusIndicator.style.display = config.show ? 'block' : 'none';
        
        // Auto-hide success status after 3 seconds
        if (this.connectionStatus === 'connected') {
            setTimeout(() => {
                if (this.statusIndicator && this.connectionStatus === 'connected') {
                    this.statusIndicator.style.display = 'none';
                }
            }, 3000);
        }
    }

    updateLastUpdatedDisplay() {
        const element = document.getElementById('last-updated');
        if (element && this.lastUpdateTime) {
            const timeString = this.lastUpdateTime.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            element.textContent = timeString;
        }
    }

    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page is hidden, reduce update frequency or pause
                this.log('Page hidden, reducing update frequency');
                if (this.pollingInterval) {
                    clearInterval(this.pollingInterval);
                    // Increase polling interval when hidden
                    this.pollingInterval = setInterval(() => {
                        this.fetchUpdates();
                    }, this.options.pollingInterval * 2);
                }
            } else {
                // Page is visible, resume normal updates
                this.log('Page visible, resuming normal updates');
                if (this.pollingInterval) {
                    clearInterval(this.pollingInterval);
                    this.startPolling();
                }
                
                // Reconnect SSE if needed
                if (!this.isConnected && this.options.enableSSE && this.supportsSSE()) {
                    this.connectSSE();
                }
            }
        });
    }

    setupErrorHandling() {
        // Handle global errors
        window.addEventListener('error', (event) => {
            if (event.filename && event.filename.includes('live-updates')) {
                this.log('JavaScript error in live updates:', event.error);
                this.triggerEvent('error', { message: 'JavaScript error occurred' });
            }
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.log('Unhandled promise rejection:', event.reason);
        });
    }

    // Event system for components to listen to updates
    on(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].push(handler);
        }
    }

    off(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            const index = this.eventHandlers[eventType].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[eventType].splice(index, 1);
            }
        }
    }

    triggerEvent(eventType, data) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    this.log('Error in event handler:', error);
                }
            });
        }
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    log(...args) {
        if (this.options.debug) {
            console.log('[LiveUpdates]', ...args);
        }
    }

    disconnect() {
        this.log('Disconnecting live updates');
        
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        this.isConnected = false;
        this.connectionStatus = 'disconnected';
        this.updateConnectionStatus();
    }

    destroy() {
        this.disconnect();
        
        if (this.statusIndicator) {
            this.statusIndicator.remove();
        }
        
        // Clear all event handlers
        Object.keys(this.eventHandlers).forEach(key => {
            this.eventHandlers[key] = [];
        });
    }

    // Simplified handlers for basic functionality
    handleFullUpdate(data) {
        this.log('Processing full update');
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        this.triggerEvent('full_update', data);
    }

    handleMatchUpdate(data) {
        this.log('Processing match update');
        this.triggerEvent('match_update', data);
    }

    handleParticipantUpdate(data) {
        this.log('Processing participant update');
        this.triggerEvent('participant_update', data);
    }

    handleTournamentUpdate(data) {
        this.log('Processing tournament update');
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        this.triggerEvent('tournament_update', data);
    }

    handleTournamentEnded(data) {
        this.log('Tournament ended:', data.status);
        this.disconnect();
        this.triggerEvent('tournament_ended', data);
    }

    handleHeartbeat(data) {
        // Silent heartbeat to keep connection alive
        this.lastUpdateTime = new Date();
    }

    handleError(data) {
        this.log('Received error:', data.message);
        this.triggerEvent('error', data);
        this.onConnectionError();
    }

    updateEngagementStats(engagementStats) {
        const elements = {
            'tournament-views': engagementStats.views,
            'tournament-shares': engagementStats.shares,
            'registrations-today': engagementStats.registrations_today
        };
        
        Object.entries(elements).forEach(([stat, value]) => {
            const element = document.querySelector(`[data-stat="${stat}"]`);
            if (element) {
                this.animateValueChange(element, value);
            }
        });
    }

    updateCurrentRound(currentRound) {
        const element = document.querySelector('[data-stat="current-round"]');
        if (element) {
            element.textContent = `Round ${currentRound}`;
        }
    }
}

// Make available globally
window.LiveUpdatesManager = LiveUpdatesManager;

// Auto-initialize for tournaments that support live updates
document.addEventListener('DOMContentLoaded', () => {
    const tournamentStatus = document.querySelector('[data-tournament-status]')?.dataset.tournamentStatus;
    if (['check_in', 'in_progress'].includes(tournamentStatus)) {
        const pathParts = window.location.pathname.split('/');
        const tournamentsIndex = pathParts.indexOf('tournaments');
        
        if (tournamentsIndex !== -1 && pathParts[tournamentsIndex + 1]) {
            const tournamentSlug = pathParts[tournamentsIndex + 1];
            new LiveUpdatesManager(tournamentSlug, { debug: true });
        }
    }
});