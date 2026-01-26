// Bracket Preview Component (Requirement 15.4 - Automatic bracket preview updates)
class BracketPreview {
    constructor() {
        this.previewContainer = document.querySelector('.bracket-preview-visual');
        this.updateInterval = null;
        this.tournamentSlug = this.getTournamentSlug();
        this.init();
    }

    init() {
        if (!this.previewContainer) return;
        
        // Set up automatic updates for in-progress tournaments
        this.setupAutomaticUpdates();
        
        // Set up click handlers for match navigation
        this.setupMatchNavigation();
        
        // Set up keyboard navigation
        this.setupKeyboardNavigation();
        
        console.log('Bracket Preview initialized with automatic updates');
    }

    getTournamentSlug() {
        // Extract tournament slug from URL
        const pathParts = window.location.pathname.split('/');
        return pathParts[pathParts.length - 1] || pathParts[pathParts.length - 2];
    }

    setupAutomaticUpdates() {
        // Check if tournament is in progress
        const statusBadge = document.querySelector('.status-badge.status-in_progress');
        if (!statusBadge) return;
        
        // Update bracket preview every 30 seconds
        this.updateInterval = setInterval(() => {
            this.refreshBracketPreview();
        }, 30000);
        
        // Also update when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.refreshBracketPreview();
            }
        });
        
        console.log('Automatic bracket preview updates enabled');
    }

    async refreshBracketPreview() {
        try {
            // Fetch updated bracket data
            const response = await fetch(`/tournaments/${this.tournamentSlug}/bracket-preview-data/`);
            
            if (!response.ok) {
                console.warn('Failed to fetch bracket preview data');
                return;
            }
            
            const data = await response.json();
            
            // Update the preview with new data
            this.updatePreviewDisplay(data);
            
            // Announce update to screen readers
            this.announceUpdate();
            
        } catch (error) {
            console.error('Error refreshing bracket preview:', error);
        }
    }

    updatePreviewDisplay(data) {
        if (!data || !data.rounds) return;
        
        // Find all match preview elements
        const matchPreviews = this.previewContainer.querySelectorAll('.match-preview');
        
        // Update each match with new data
        data.rounds.forEach(round => {
            round.matches.forEach(match => {
                const matchElement = this.previewContainer.querySelector(`[data-match-id="${match.id}"]`);
                if (matchElement) {
                    this.updateMatchElement(matchElement, match);
                }
            });
        });
        
        // Update statistics
        const statsElement = this.previewContainer.closest('.bracket-preview-container').querySelector('.bracket-preview-header');
        if (statsElement && data.stats) {
            this.updateStats(statsElement, data.stats);
        }
    }

    updateMatchElement(element, matchData) {
        // Update participant names
        const p1Name = element.querySelector('.participant:first-child .participant-name');
        const p2Name = element.querySelector('.participant:last-child .participant-name');
        
        if (p1Name) {
            p1Name.textContent = matchData.participant1.name;
            p1Name.parentElement.classList.toggle('text-green-400', matchData.participant1.is_winner);
            p1Name.parentElement.classList.toggle('font-medium', matchData.participant1.is_winner);
        }
        
        if (p2Name) {
            p2Name.textContent = matchData.participant2.name;
            p2Name.parentElement.classList.toggle('text-green-400', matchData.participant2.is_winner);
            p2Name.parentElement.classList.toggle('font-medium', matchData.participant2.is_winner);
        }
        
        // Update score
        const scoreElement = element.querySelector('.match-vs');
        if (scoreElement && matchData.score) {
            scoreElement.innerHTML = `<span class="text-xs text-gray-400">${matchData.score}</span>`;
        }
        
        // Update status badge
        const statusBadge = element.querySelector('.status-badge');
        if (statusBadge) {
            this.updateStatusBadge(statusBadge, matchData.status);
        }
        
        // Add update animation
        element.style.animation = 'pulse 0.5s ease-in-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    updateStatusBadge(badge, status) {
        // Remove all status classes
        badge.className = 'status-badge text-xs px-2 py-1 rounded-full border';
        
        // Add appropriate status classes
        switch (status) {
            case 'completed':
                badge.classList.add('bg-green-500/20', 'text-green-400', 'border-green-500/30');
                badge.textContent = 'Completed';
                break;
            case 'in_progress':
                badge.classList.add('bg-red-500/20', 'text-red-400', 'border-red-500/30');
                badge.textContent = 'Live';
                break;
            case 'ready':
                badge.classList.add('bg-blue-500/20', 'text-blue-400', 'border-blue-500/30');
                badge.textContent = 'Ready';
                break;
            default:
                badge.classList.add('bg-gray-500/20', 'text-gray-400', 'border-gray-500/30');
                badge.textContent = 'Pending';
        }
    }

    updateStats(statsElement, stats) {
        const completedStat = statsElement.querySelector('.text-green-400');
        const inProgressStat = statsElement.querySelector('.text-yellow-400');
        const currentRoundStat = statsElement.querySelector('.text-purple-400');
        
        if (completedStat && stats.completed_matches !== undefined) {
            completedStat.textContent = stats.completed_matches;
        }
        
        if (inProgressStat && stats.in_progress_matches !== undefined) {
            inProgressStat.textContent = stats.in_progress_matches;
        }
        
        if (currentRoundStat && stats.current_round !== undefined) {
            currentRoundStat.textContent = stats.current_round;
        }
    }

    setupMatchNavigation() {
        // Add click handlers to navigate to full bracket view
        const matchPreviews = this.previewContainer.querySelectorAll('.match-preview');
        
        matchPreviews.forEach(match => {
            match.addEventListener('click', (e) => {
                e.preventDefault();
                const matchId = match.dataset.matchId || match.getAttribute('onclick')?.match(/#match-([^']+)/)?.[1];
                
                if (matchId) {
                    // Navigate to full bracket with match highlighted
                    window.location.href = `/tournaments/${this.tournamentSlug}/bracket/#match-${matchId}`;
                }
            });
            
            // Add hover effect
            match.addEventListener('mouseenter', () => {
                match.style.transform = 'scale(1.02)';
                match.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
            });
            
            match.addEventListener('mouseleave', () => {
                match.style.transform = '';
                match.style.boxShadow = '';
            });
        });
    }

    setupKeyboardNavigation() {
        const matchPreviews = this.previewContainer.querySelectorAll('.match-preview');
        
        matchPreviews.forEach((match, index) => {
            // Make matches keyboard accessible
            match.setAttribute('tabindex', '0');
            match.setAttribute('role', 'button');
            match.setAttribute('aria-label', `View match details`);
            
            match.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'Enter':
                    case ' ':
                        e.preventDefault();
                        match.click();
                        break;
                    case 'ArrowDown':
                    case 'ArrowRight':
                        e.preventDefault();
                        if (matchPreviews[index + 1]) {
                            matchPreviews[index + 1].focus();
                        }
                        break;
                    case 'ArrowUp':
                    case 'ArrowLeft':
                        e.preventDefault();
                        if (matchPreviews[index - 1]) {
                            matchPreviews[index - 1].focus();
                        }
                        break;
                }
            });
        });
    }

    announceUpdate() {
        // Announce bracket update to screen readers
        const liveRegion = document.getElementById('accessibility-announcements');
        if (liveRegion) {
            liveRegion.textContent = 'Bracket preview updated with latest match results';
            
            // Clear after announcement
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}