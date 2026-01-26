/**
 * Unit tests for the LiveUpdatesManager JavaScript class
 * Tests WebSocket/SSE connection handling, message processing, UI refresh functionality, and connection failure recovery
 * 
 * **Feature: tournament-detail-ui-enhancement, Property 17.1: Real-time Update System Tests**
 * **Validates: Requirements 5.5, 2.4**
 */

// Mock DOM elements and browser APIs for testing
class MockEventSource {
    constructor(url) {
        this.url = url;
        this.readyState = 0; // CONNECTING
        this.onopen = null;
        this.onmessage = null;
        this.onerror = null;
        this.addEventListener = jest.fn();
        this.close = jest.fn();
        
        // Simulate connection opening after a short delay
        setTimeout(() => {
            this.readyState = 1; // OPEN
            if (this.onopen) {
                this.onopen({ type: 'open' });
            }
        }, 10);
    }
    
    // Helper method to simulate receiving a message
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }
    
    // Helper method to simulate an error
    simulateError() {
        if (this.onerror) {
            this.onerror({ type: 'error' });
        }
    }
}

// Mock fetch API
global.fetch = jest.fn();

// Mock DOM methods and properties
global.document = {
    querySelector: jest.fn(),
    querySelectorAll: jest.fn(),
    getElementById: jest.fn(),
    createElement: jest.fn(),
    addEventListener: jest.fn(),
    hidden: false,
    body: {
        appendChild: jest.fn()
    }
};

global.window = {
    addEventListener: jest.fn(),
    EventSource: MockEventSource,
    pageYOffset: 0
};

// Mock console for testing
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Mock setTimeout and clearInterval for testing
global.setTimeout = jest.fn((callback, delay) => {
    return setTimeout(callback, delay);
});

global.clearInterval = jest.fn();
global.setInterval = jest.fn();

// Load the LiveUpdatesManager class
require('./live-updates.js');

describe('LiveUpdatesManager', () => {
    let manager;
    let mockTournamentElement;
    let mockMatchElement;
    let mockParticipantElement;
    let mockStatsElement;

    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();
        
        // Setup mock DOM elements
        mockTournamentElement = {
            dataset: { tournamentStatus: 'in_progress' },
            querySelector: jest.fn(),
            setAttribute: jest.fn(),
            classList: { toggle: jest.fn(), add: jest.fn(), remove: jest.fn() },
            style: {},
            textContent: ''
        };
        
        mockMatchElement = {
            querySelector: jest.fn(),
            classList: { toggle: jest.fn(), add: jest.fn(), remove: jest.fn() },
            style: {},
            setAttribute: jest.fn()
        };
        
        mockParticipantElement = {
            querySelector: jest.fn(),
            classList: { toggle: jest.fn(), add: jest.fn(), remove: jest.fn() },
            style: {},
            setAttribute: jest.fn()
        };
        
        mockStatsElement = {
            textContent: '0',
            style: {}
        };
        
        // Setup document.querySelector to return appropriate elements
        document.querySelector.mockImplementation((selector) => {
            if (selector.includes('tournament-status')) return mockTournamentElement;
            if (selector.includes('match-id')) return mockMatchElement;
            if (selector.includes('participant-id')) return mockParticipantElement;
            if (selector.includes('data-stat')) return mockStatsElement;
            if (selector === '[name=csrfmiddlewaretoken]') return { value: 'test-csrf-token' };
            return null;
        });
        
        document.getElementById.mockImplementation((id) => {
            if (id === 'live-matches-container') return { innerHTML: '', appendChild: jest.fn(), querySelector: jest.fn(), children: [] };
            if (id === 'recent-matches-container') return { innerHTML: '', appendChild: jest.fn(), querySelector: jest.fn(), children: [] };
            if (id === 'upcoming-matches-container') return { innerHTML: '', appendChild: jest.fn(), querySelector: jest.fn(), children: [] };
            if (id === 'last-updated') return { textContent: '' };
            return null;
        });
        
        document.createElement.mockReturnValue({
            className: '',
            innerHTML: '',
            style: {},
            appendChild: jest.fn(),
            remove: jest.fn(),
            setAttribute: jest.fn(),
            classList: { add: jest.fn(), remove: jest.fn(), toggle: jest.fn() }
        });
        
        // Create manager instance
        manager = new LiveUpdatesManager('test-tournament', { debug: true });
    });

    afterEach(() => {
        if (manager) {
            manager.destroy();
        }
    });

    describe('Initialization', () => {
        test('should initialize with correct default options', () => {
            expect(manager.tournamentSlug).toBe('test-tournament');
            expect(manager.options.enableSSE).toBe(true);
            expect(manager.options.fallbackPolling).toBe(true);
            expect(manager.options.pollingInterval).toBe(30000);
            expect(manager.options.reconnectDelay).toBe(5000);
            expect(manager.options.maxReconnectAttempts).toBe(10);
        });

        test('should setup connection status indicator', () => {
            expect(document.createElement).toHaveBeenCalledWith('div');
            expect(document.body.appendChild).toHaveBeenCalled();
        });

        test('should not enable live updates for inactive tournament', () => {
            mockTournamentElement.dataset.tournamentStatus = 'completed';
            const inactiveManager = new LiveUpdatesManager('test-tournament');
            
            expect(inactiveManager.connectionStatus).toBe('disconnected');
        });
    });

    describe('SSE Connection Handling', () => {
        test('should create SSE connection when supported', async () => {
            expect(manager.eventSource).toBeInstanceOf(MockEventSource);
            expect(manager.eventSource.url).toBe('/tournaments/test-tournament/live-updates/');
        });

        test('should handle SSE connection open event', (done) => {
            manager.on('connection_status', (data) => {
                if (data.status === 'connected') {
                    expect(manager.isConnected).toBe(true);
                    expect(manager.connectionStatus).toBe('connected');
                    done();
                }
            });
            
            // Trigger connection open
            setTimeout(() => {
                manager.eventSource.onopen({ type: 'open' });
            }, 20);
        });

        test('should handle SSE connection error', (done) => {
            manager.on('connection_status', (data) => {
                if (data.status === 'error') {
                    expect(manager.isConnected).toBe(false);
                    expect(manager.connectionStatus).toBe('error');
                    done();
                }
            });
            
            // Trigger connection error
            setTimeout(() => {
                manager.eventSource.simulateError();
            }, 20);
        });

        test('should close SSE connection on disconnect', () => {
            manager.disconnect();
            
            expect(manager.eventSource.close).toHaveBeenCalled();
            expect(manager.eventSource).toBeNull();
            expect(manager.isConnected).toBe(false);
        });
    });

    describe('Message Processing', () => {
        test('should handle full update message', (done) => {
            const fullUpdateData = {
                type: 'full_update',
                tournament_slug: 'test-tournament',
                live_matches: [
                    {
                        id: '1',
                        status: 'in_progress',
                        participant1: { display_name: 'Player 1', is_winner: false },
                        participant2: { display_name: 'Player 2', is_winner: false },
                        score_p1: 1,
                        score_p2: 0,
                        round_number: 1,
                        bracket_name: 'Main Bracket'
                    }
                ],
                statistics: {
                    participants: { registered: 8, checked_in: 6, capacity: 16, percentage_full: 50 },
                    matches: { total: 4, completed: 2, in_progress: 1, upcoming: 1 }
                }
            };

            manager.on('full_update', (data) => {
                expect(data.tournament_slug).toBe('test-tournament');
                expect(data.live_matches).toHaveLength(1);
                expect(data.statistics.participants.registered).toBe(8);
                done();
            });

            manager.eventSource.simulateMessage(fullUpdateData);
        });

        test('should handle match update message', (done) => {
            const matchUpdateData = {
                type: 'match_update',
                match: {
                    id: '1',
                    status: 'completed',
                    participant1: { display_name: 'Player 1', is_winner: true },
                    participant2: { display_name: 'Player 2', is_winner: false },
                    score_p1: 2,
                    score_p2: 1
                }
            };

            manager.on('match_update', (data) => {
                expect(data.match.status).toBe('completed');
                expect(data.match.participant1.is_winner).toBe(true);
                done();
            });

            manager.eventSource.simulateMessage(matchUpdateData);
        });

        test('should handle participant update message', (done) => {
            const participantUpdateData = {
                type: 'participant_update',
                participant: {
                    id: '1',
                    display_name: 'Player 1',
                    checked_in: true,
                    seed: 1
                }
            };

            manager.on('participant_update', (data) => {
                expect(data.participant.checked_in).toBe(true);
                expect(data.participant.display_name).toBe('Player 1');
                done();
            });

            manager.eventSource.simulateMessage(participantUpdateData);
        });

        test('should handle tournament update message', (done) => {
            const tournamentUpdateData = {
                type: 'tournament_update',
                status: 'completed',
                statistics: {
                    participants: { registered: 16, checked_in: 16 }
                }
            };

            manager.on('tournament_update', (data) => {
                expect(data.status).toBe('completed');
                done();
            });

            manager.eventSource.simulateMessage(tournamentUpdateData);
        });

        test('should handle error message', (done) => {
            const errorData = {
                type: 'error',
                message: 'Connection failed'
            };

            manager.on('error', (data) => {
                expect(data.message).toBe('Connection failed');
                done();
            });

            manager.eventSource.simulateMessage(errorData);
        });

        test('should handle tournament ended message', (done) => {
            const tournamentEndedData = {
                type: 'tournament_ended',
                status: 'completed'
            };

            manager.on('tournament_ended', (data) => {
                expect(data.status).toBe('completed');
                expect(manager.isConnected).toBe(false);
                done();
            });

            manager.eventSource.simulateMessage(tournamentEndedData);
        });
    });

    describe('UI Refresh Functionality', () => {
        test('should update match card with new data', () => {
            const matchData = {
                id: '1',
                status: 'completed',
                participant1: { display_name: 'Player 1', is_winner: true },
                participant2: { display_name: 'Player 2', is_winner: false },
                score_p1: 2,
                score_p2: 1
            };

            // Mock DOM elements for match card
            const mockP1Name = { textContent: '' };
            const mockP2Name = { textContent: '' };
            const mockP1Score = { textContent: '' };
            const mockP2Score = { textContent: '' };
            const mockStatus = { textContent: '', className: '' };
            const mockP1Element = { classList: { toggle: jest.fn() } };
            const mockP2Element = { classList: { toggle: jest.fn() } };

            mockMatchElement.querySelector.mockImplementation((selector) => {
                if (selector === '.participant-1 .name') return mockP1Name;
                if (selector === '.participant-2 .name') return mockP2Name;
                if (selector === '.participant-1 .score') return mockP1Score;
                if (selector === '.participant-2 .score') return mockP2Score;
                if (selector === '.match-status') return mockStatus;
                if (selector === '.participant-1') return mockP1Element;
                if (selector === '.participant-2') return mockP2Element;
                return null;
            });

            manager.updateMatchCard(mockMatchElement, matchData);

            expect(mockP1Name.textContent).toBe('Player 1');
            expect(mockP2Name.textContent).toBe('Player 2');
            expect(mockP1Score.textContent).toBe(2);
            expect(mockP2Score.textContent).toBe(1);
            expect(mockP1Element.classList.toggle).toHaveBeenCalledWith('winner', true);
            expect(mockP2Element.classList.toggle).toHaveBeenCalledWith('winner', false);
        });

        test('should update participant card with new data', () => {
            const participantData = {
                id: '1',
                display_name: 'Player 1',
                checked_in: true,
                seed: 1,
                matches_won: 2,
                matches_lost: 1,
                status: 'active'
            };

            // Mock DOM elements for participant card
            const mockCheckInBadge = { style: { display: '' } };
            const mockSeedBadge = { textContent: '' };
            const mockRecord = { textContent: '' };

            mockParticipantElement.querySelector.mockImplementation((selector) => {
                if (selector === '.check-in-badge') return mockCheckInBadge;
                if (selector === '.seed-badge') return mockSeedBadge;
                if (selector === '.participant-record') return mockRecord;
                return null;
            });

            manager.updateParticipantCard(mockParticipantElement, participantData);

            expect(mockCheckInBadge.style.display).toBe('block');
            expect(mockSeedBadge.textContent).toBe('Seed #1');
            expect(mockRecord.textContent).toBe('2-1');
            expect(mockParticipantElement.setAttribute).toHaveBeenCalledWith('data-status', 'active');
        });

        test('should animate value changes in statistics', () => {
            const element = { textContent: '5', style: {} };
            
            manager.animateValueChange(element, 8);

            expect(element.style.transform).toBe('scale(1.1)');
            expect(element.style.color).toBe('#10b981');

            // Simulate timeout completion
            setTimeout(() => {
                expect(element.textContent).toBe(8);
                expect(element.style.transform).toBe('scale(1)');
                expect(element.style.color).toBe('');
            }, 200);
        });

        test('should highlight updated elements', () => {
            manager.highlightUpdate(mockMatchElement);

            expect(mockMatchElement.classList.add).toHaveBeenCalledWith('updated');
            expect(mockMatchElement.style.boxShadow).toBe('0 0 10px rgba(59, 130, 246, 0.5)');

            // Simulate timeout completion
            setTimeout(() => {
                expect(mockMatchElement.classList.remove).toHaveBeenCalledWith('updated');
                expect(mockMatchElement.style.boxShadow).toBe('');
            }, 2100);
        });
    });

    describe('Polling Fallback', () => {
        beforeEach(() => {
            // Mock fetch for polling tests
            fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({
                    success: true,
                    tournament_slug: 'test-tournament',
                    status: 'in_progress',
                    statistics: {
                        participants: { registered: 8, checked_in: 6 },
                        matches: { total: 4, completed: 2 }
                    },
                    timestamp: new Date().toISOString()
                })
            });
        });

        test('should start polling when SSE is not supported', () => {
            // Create manager without SSE support
            window.EventSource = undefined;
            const pollingManager = new LiveUpdatesManager('test-tournament');

            expect(pollingManager.connectionStatus).toBe('polling');
            expect(setInterval).toHaveBeenCalled();
        });

        test('should fetch updates via polling', async () => {
            manager.startPolling();

            await manager.fetchUpdates();

            expect(fetch).toHaveBeenCalledWith('/tournaments/api/test-tournament/stats/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': 'test-csrf-token'
                }
            });
        });

        test('should handle polling fetch errors', async () => {
            fetch.mockRejectedValue(new Error('Network error'));

            const errorSpy = jest.fn();
            manager.on('connection_status', errorSpy);

            await manager.fetchUpdates();

            expect(errorSpy).toHaveBeenCalledWith({ status: 'error' });
        });

        test('should fallback to polling after SSE failure', () => {
            manager.fallbackToPolling();

            expect(manager.eventSource).toBeNull();
            expect(manager.connectionStatus).toBe('polling');
        });
    });

    describe('Connection Recovery', () => {
        test('should attempt reconnection after error', (done) => {
            manager.options.reconnectDelay = 100; // Reduce delay for testing
            
            let reconnectAttempted = false;
            const originalConnectSSE = manager.connectSSE;
            manager.connectSSE = jest.fn(() => {
                reconnectAttempted = true;
                originalConnectSSE.call(manager);
            });

            manager.onConnectionError();

            setTimeout(() => {
                expect(reconnectAttempted).toBe(true);
                expect(manager.reconnectAttempts).toBe(1);
                done();
            }, 150);
        });

        test('should stop reconnecting after max attempts', () => {
            manager.options.maxReconnectAttempts = 2;
            manager.reconnectAttempts = 2;

            const fallbackSpy = jest.spyOn(manager, 'fallbackToPolling');
            manager.onConnectionError();

            expect(fallbackSpy).toHaveBeenCalled();
        });

        test('should handle page visibility changes', () => {
            const visibilityHandler = document.addEventListener.mock.calls.find(
                call => call[0] === 'visibilitychange'
            )[1];

            // Simulate page becoming hidden
            document.hidden = true;
            visibilityHandler();

            expect(clearInterval).toHaveBeenCalled();

            // Simulate page becoming visible
            document.hidden = false;
            const connectSpy = jest.spyOn(manager, 'connectSSE');
            visibilityHandler();

            expect(connectSpy).toHaveBeenCalled();
        });
    });

    describe('Event System', () => {
        test('should register and trigger event handlers', () => {
            const handler = jest.fn();
            manager.on('match_update', handler);

            const testData = { match: { id: '1' } };
            manager.triggerEvent('match_update', testData);

            expect(handler).toHaveBeenCalledWith(testData);
        });

        test('should remove event handlers', () => {
            const handler = jest.fn();
            manager.on('match_update', handler);
            manager.off('match_update', handler);

            manager.triggerEvent('match_update', { match: { id: '1' } });

            expect(handler).not.toHaveBeenCalled();
        });

        test('should handle errors in event handlers gracefully', () => {
            const errorHandler = jest.fn(() => {
                throw new Error('Handler error');
            });
            const goodHandler = jest.fn();

            manager.on('match_update', errorHandler);
            manager.on('match_update', goodHandler);

            manager.triggerEvent('match_update', { match: { id: '1' } });

            expect(errorHandler).toHaveBeenCalled();
            expect(goodHandler).toHaveBeenCalled();
        });
    });

    describe('Cleanup and Destruction', () => {
        test('should clean up resources on destroy', () => {
            const statusIndicator = { remove: jest.fn() };
            manager.statusIndicator = statusIndicator;

            manager.destroy();

            expect(manager.eventSource).toBeNull();
            expect(manager.pollingInterval).toBeNull();
            expect(statusIndicator.remove).toHaveBeenCalled();
            expect(manager.isConnected).toBe(false);
        });

        test('should clear all event handlers on destroy', () => {
            const handler = jest.fn();
            manager.on('match_update', handler);

            manager.destroy();

            manager.triggerEvent('match_update', { match: { id: '1' } });
            expect(handler).not.toHaveBeenCalled();
        });
    });

    describe('Utility Functions', () => {
        test('should get CSRF token from DOM', () => {
            const token = manager.getCSRFToken();
            expect(token).toBe('test-csrf-token');
        });

        test('should format match status correctly', () => {
            expect(manager.formatMatchStatus('in_progress')).toBe('Live');
            expect(manager.formatMatchStatus('completed')).toBe('Completed');
            expect(manager.formatMatchStatus('pending')).toBe('Pending');
        });

        test('should format tournament status correctly', () => {
            expect(manager.formatTournamentStatus('in_progress')).toBe('In Progress');
            expect(manager.formatTournamentStatus('registration')).toBe('Registration Open');
            expect(manager.formatTournamentStatus('completed')).toBe('Completed');
        });

        test('should check if live updates should be enabled', () => {
            mockTournamentElement.dataset.tournamentStatus = 'in_progress';
            expect(manager.shouldEnableLiveUpdates()).toBe(true);

            mockTournamentElement.dataset.tournamentStatus = 'completed';
            expect(manager.shouldEnableLiveUpdates()).toBe(false);
        });

        test('should detect SSE support', () => {
            window.EventSource = MockEventSource;
            expect(manager.supportsSSE()).toBe(true);

            window.EventSource = undefined;
            expect(manager.supportsSSE()).toBe(false);
        });
    });
});
   