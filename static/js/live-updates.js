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
            
            this.eventSource.onopen = (event) => {
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

    handleFullUpdate(data) {
        this.log('Processing full update');
        
        // Update live matches
        if (data.live_matches) {
            this.updateLiveMatches(data.live_matches);
        }
        
        // Update recent matches
        if (data.recent_matches) {
            this.updateRecentMatches(data.recent_matches);
        }
        
        // Update upcoming matches
        if (data.upcoming_matches) {
            this.updateUpcomingMatches(data.upcoming_matches);
        }
        
        // Update statistics
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        
        // Update participants
        if (data.participants) {
            this.updateParticipants(data.participants);
        }
        
        // Trigger event for components
        this.triggerEvent('full_update', data);
    }

    handleMatchUpdate(data) {
        this.log('Processing match update');
        
        const match = data.match;
        const matchElement = document.querySelector(`[data-match-id="${match.id}"]`);
        
        if (matchElement) {
            this.updateMatchCard(matchElement, match);
            
            // Add visual feedback for update
            this.highlightUpdate(matchElement);
        }
        
        // Update match in appropriate sections
        this.updateMatchInSections(match);
        
        this.triggerEvent('match_update', data);
    }

    handleParticipantUpdate(data) {
        this.log('Processing participant update');
        
        const participant = data.participant;
        const participantElement = document.querySelector(`[data-participant-id="${participant.id}"]`);
        
        if (participantElement) {
            this.updateParticipantCard(participantElement, participant);
            
            // Add visual feedback for update
            this.highlightUpdate(participantElement);
        }
        
        this.triggerEvent('participant_update', data);
    }

    handleTournamentUpdate(data) {
        this.log('Processing tournament update');
        
        // Update tournament status
        if (data.status) {
            this.updateTournamentStatus(data.status);
        }
        
        // Update statistics if provided
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        
        this.triggerEvent('tournament_update', data);
    }

    handleStatisticsUpdate(data) {
        this.log('Processing statistics update');
        
        if (data.statistics) {
            this.updateStatistics(data.statistics);
        }
        
        this.triggerEvent('statistics_update', data);
    }

    handleTournamentEnded(data) {
        this.log('Tournament ended:', data.status);
        
        // Stop live updates
        this.disconnect();
        
        // Show tournament ended message
        this.showTournamentEndedMessage(data.status);
        
        this.triggerEvent('tournament_ended', data);
    }

    handleHeartbeat(data) {
        // Silent heartbeat to keep connection alive
        this.lastUpdateTime = new Date();
    }

    handleError(data) {
        this.log('Received error:', data.message);
        this.triggerEvent('error', data);
        
        // Try to reconnect after error
        this.onConnectionError();
    }

    updateMatchCard(element, match) {
        // Update participant names
        const p1Name = element.querySelector('.participant-1 .name');
        const p2Name = element.querySelector('.participant-2 .name');
        
        if (p1Name) p1Name.textContent = match.participant1.display_name;
        if (p2Name) p2Name.textContent = match.participant2.display_name;
        
        // Update scores
        const p1Score = element.querySelector('.participant-1 .score');
        const p2Score = element.querySelector('.participant-2 .score');
        
        if (p1Score) p1Score.textContent = match.score_p1;
        if (p2Score) p2Score.textContent = match.score_p2;
        
        // Update status
        const statusElement = element.querySelector('.match-status');
        if (statusElement) {
            statusElement.textContent = this.formatMatchStatus(match.status);
            statusElement.className = `match-status status-${match.status}`;
        }
        
        // Update winner highlighting
        element.querySelector('.participant-1')?.classList.toggle('winner', match.participant1.is_winner);
        element.querySelector('.participant-2')?.classList.toggle('winner', match.participant2.is_winner);
        
        // Update live indicator
        const liveIndicator = element.querySelector('.live-indicator');
        if (liveIndicator) {
            liveIndicator.style.display = match.status === 'in_progress' ? 'block' : 'none';
        }
    }

    updateParticipantCard(element, participant) {
        // Update check-in status
        const checkInBadge = element.querySelector('.check-in-badge');
        if (checkInBadge) {
            checkInBadge.style.display = participant.checked_in ? 'block' : 'none';
        }
        
        // Update seed
        const seedBadge = element.querySelector('.seed-badge');
        if (seedBadge && participant.seed) {
            seedBadge.textContent = `Seed #${participant.seed}`;
        }
        
        // Update win/loss record
        const recordElement = element.querySelector('.participant-record');
        if (recordElement) {
            recordElement.textContent = `${participant.matches_won}-${participant.matches_lost}`;
        }
        
        // Update status
        element.setAttribute('data-status', participant.status);
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
        
        // Update progress bar
        const progressBar = document.querySelector('.participant-progress .progress-fill');
        if (progressBar) {
            const percentage = participantStats.percentage_full;
            progressBar.style.width = `${percentage}%`;
            
            // Update color based on capacity
            if (percentage > 80) {
                progressBar.className = 'progress-fill bg-red-500';
            } else if (percentage > 60) {
                progressBar.className = 'progress-fill bg-yellow-500';
            } else {
                progressBar.className = 'progress-fill bg-blue-500';
            }
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

    highlightUpdate(element) {
        // Add visual feedback for updates
        element.classList.add('updated');
        element.style.boxShadow = '0 0 10px rgba(59, 130, 246, 0.5)';
        
        setTimeout(() => {
            element.classList.remove('updated');
            element.style.boxShadow = '';
        }, 2000);
    }

    updateMatchInSections(match) {
        // Update match in live matches section
        if (match.status === 'in_progress') {
            this.addToLiveMatches(match);
        } else {
            this.removeFromLiveMatches(match.id);
        }
        
        // Update match in recent matches if completed
        if (match.status === 'completed') {
            this.addToRecentMatches(match);
        }
        
        // Remove from upcoming if no longer pending
        if (!['ready', 'pending'].includes(match.status)) {
            this.removeFromUpcomingMatches(match.id);
        }
    }

    updateLiveMatches(matches) {
        const container = document.getElementById('live-matches-container');
        if (!container) return;
        
        // Clear existing matches
        container.innerHTML = '';
        
        if (matches.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No live matches currently</p>';
            return;
        }
        
        // Add live matches
        matches.forEach(match => {
            const matchElement = this.createMatchElement(match, 'live');
            container.appendChild(matchElement);
        });
    }

    updateRecentMatches(matches) {
        const container = document.getElementById('recent-matches-container');
        if (!container) return;
        
        // Clear existing matches
        container.innerHTML = '';
        
        if (matches.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No recent matches</p>';
            return;
        }
        
        // Add recent matches
        matches.forEach(match => {
            const matchElement = this.createMatchElement(match, 'recent');
            container.appendChild(matchElement);
        });
    }

    updateUpcomingMatches(matches) {
        const container = document.getElementById('upcoming-matches-container');
        if (!container) return;
        
        // Clear existing matches
        container.innerHTML = '';
        
        if (matches.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No upcoming matches</p>';
            return;
        }
        
        // Add upcoming matches
        matches.forEach(match => {
            const matchElement = this.createMatchElement(match, 'upcoming');
            container.appendChild(matchElement);
        });
    }

    createMatchElement(match, type) {
        const element = document.createElement('div');
        element.className = `match-card ${type}`;
        element.setAttribute('data-match-id', match.id);
        
        const liveIndicator = match.status === 'in_progress' ? 
            '<span class="live-indicator">LIVE</span>' : '';
        
        const scoreDisplay = match.status === 'completed' ? 
            `<span class="score">${match.score_p1}-${match.score_p2}</span>` : '';
        
        element.innerHTML = `
            <div class="match-header">
                <span class="round-info">${match.bracket_name} - Round ${match.round_number}</span>
                ${liveIndicator}
            </div>
            <div class="match-participants">
                <div class="participant participant-1 ${match.participant1.is_winner ? 'winner' : ''}">
                    <span class="name">${match.participant1.display_name}</span>
                    <span class="score">${match.score_p1}</span>
                </div>
                <div class="vs-divider">VS</div>
                <div class="participant participant-2 ${match.participant2.is_winner ? 'winner' : ''}">
                    <span class="name">${match.participant2.display_name}</span>
                    <span class="score">${match.score_p2}</span>
                </div>
            </div>
            ${scoreDisplay}
        `;
        
        return element;
    }

    addToLiveMatches(match) {
        const container = document.getElementById('live-matches-container');
        if (!container) return;
        
        // Remove "no matches" message
        const noMatchesMsg = container.querySelector('.text-gray-500');
        if (noMatchesMsg) {
            noMatchesMsg.remove();
        }
        
        // Check if match already exists
        const existingMatch = container.querySelector(`[data-match-id="${match.id}"]`);
        if (existingMatch) {
            this.updateMatchCard(existingMatch, match);
        } else {
            const matchElement = this.createMatchElement(match, 'live');
            container.appendChild(matchElement);
        }
    }

    removeFromLiveMatches(matchId) {
        const container = document.getElementById('live-matches-container');
        if (!container) return;
        
        const matchElement = container.querySelector(`[data-match-id="${matchId}"]`);
        if (matchElement) {
            matchElement.remove();
        }
        
        // Add "no matches" message if container is empty
        if (container.children.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No live matches currently</p>';
        }
    }

    addToRecentMatches(match) {
        const container = document.getElementById('recent-matches-container');
        if (!container) return;
        
        // Remove "no matches" message
        const noMatchesMsg = container.querySelector('.text-gray-500');
        if (noMatchesMsg) {
            noMatchesMsg.remove();
        }
        
        // Add to top of recent matches
        const matchElement = this.createMatchElement(match, 'recent');
        container.insertBefore(matchElement, container.firstChild);
        
        // Limit to 5 recent matches
        const matches = container.querySelectorAll('.match-card');
        if (matches.length > 5) {
            matches[matches.length - 1].remove();
        }
    }

    removeFromUpcomingMatches(matchId) {
        const container = document.getElementById('upcoming-matches-container');
        if (!container) return;
        
        const matchElement = container.querySelector(`[data-match-id="${matchId}"]`);
        if (matchElement) {
            matchElement.remove();
        }
        
        // Add "no matches" message if container is empty
        if (container.children.length === 0) {
            container.innerHTML = '<p class="text-gray-500">No upcoming matches</p>';
        }
    }

    updateParticipants(participants) {
        // This would update the participant list
        // Implementation depends on the specific participant display component
        this.triggerEvent('participants_update', { participants });
    }

    updateTournamentStatus(status) {
        // Update status badges and indicators
        const statusElements = document.querySelectorAll('[data-tournament-status]');
        statusElements.forEach(element => {
            element.setAttribute('data-tournament-status', status);
            element.textContent = this.formatTournamentStatus(status);
        });
    }

    formatMatchStatus(status) {
        const statusMap = {
            'pending': 'Pending',
            'ready': 'Ready',
            'in_progress': 'Live',
            'completed': 'Completed',
            'disputed': 'Disputed',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    formatTournamentStatus(status) {
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

    showTournamentEndedMessage(status) {
        const message = status === 'completed' ? 
            'Tournament has finished! Check the final results.' :
            'Tournament has been cancelled.';
        
        // Show notification
        this.showNotification(message, 'info', 10000);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform translate-x-full transition-transform duration-300`;
        
        const typeClasses = {
            'info': 'bg-blue-500 text-white',
            'success': 'bg-green-500 text-white',
            'warning': 'bg-yellow-500 text-white',
            'error': 'bg-red-500 text-white'
        };
        
        notification.className += ` ${typeClasses[type] || typeClasses.info}`;
        notification.innerHTML = `
            <div class="flex items-center gap-2">
                <span>${message}</span>
                <button class="ml-2 text-white/80 hover:text-white" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        }, duration);
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
}

// Export for use in other modules
window.LiveUpdatesManager = LiveUpdatesManager;