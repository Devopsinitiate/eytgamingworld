/**
 * Tournament Statistics Module
 * Handles real-time statistics updates and animations
 * Loaded lazily when statistics section is visible
 */

class TournamentStats {
    constructor(container) {
        this.container = container;
        this.tournamentId = container.dataset.tournamentId;
        this.updateInterval = null;
        this.animationQueue = [];
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.startRealTimeUpdates();
        this.setupAnimations();
        
        console.log('Tournament Stats module initialized');
    }
    
    setupElements() {
        this.elements = {
            participantCount: this.container.querySelector('.participant-count'),
            participantProgress: this.container.querySelector('.participant-progress'),
            viewCount: this.container.querySelector('.view-count'),
            shareCount: this.container.querySelector('.share-count'),
            registrationsToday: this.container.querySelector('.registrations-today'),
            matchesCompleted: this.container.querySelector('.matches-completed'),
            matchesTotal: this.container.querySelector('.matches-total')
        };
    }
    
    startRealTimeUpdates() {
        // Update every 30 seconds
        this.updateInterval = setInterval(() => {
            this.fetchLatestStats();
        }, 30000);
        
        // Initial fetch
        this.fetchLatestStats();
    }
    
    async fetchLatestStats() {
        try {
            const response = await fetch(`/tournaments/${this.tournamentId}/stats/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const stats = await response.json();
                this.updateStats(stats);
            }
        } catch (error) {
            console.error('Failed to fetch tournament stats:', error);
        }
    }
    
    updateStats(newStats) {
        // Update participant count with animation
        if (this.elements.participantCount && newStats.participants) {
            this.animateNumber(
                this.elements.participantCount,
                newStats.participants.registered
            );
            
            // Update progress bar
            if (this.elements.participantProgress) {
                this.animateProgressBar(
                    this.elements.participantProgress,
                    newStats.participants.percentage_full
                );
            }
        }
        
        // Update engagement metrics
        if (newStats.engagement) {
            if (this.elements.viewCount) {
                this.animateNumber(this.elements.viewCount, newStats.engagement.views);
            }
            
            if (this.elements.shareCount) {
                this.animateNumber(this.elements.shareCount, newStats.engagement.shares);
            }
            
            if (this.elements.registrationsToday) {
                this.animateNumber(this.elements.registrationsToday, newStats.engagement.registrations_today);
            }
        }
        
        // Update match statistics
        if (newStats.matches) {
            if (this.elements.matchesCompleted) {
                this.animateNumber(this.elements.matchesCompleted, newStats.matches.completed);
            }
            
            if (this.elements.matchesTotal) {
                this.animateNumber(this.elements.matchesTotal, newStats.matches.total);
            }
        }
    }
    
    animateNumber(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        
        if (currentValue === targetValue) {
            return;
        }
        
        // Add to animation queue to prevent overlapping animations
        this.animationQueue.push(() => {
            this.runNumberAnimation(element, currentValue, targetValue);
        });
        
        // Process queue if not already processing
        if (this.animationQueue.length === 1) {
            this.processAnimationQueue();
        }
    }
    
    async processAnimationQueue() {
        while (this.animationQueue.length > 0) {
            const animation = this.animationQueue.shift();
            await animation();
        }
    }
    
    runNumberAnimation(element, startValue, endValue) {
        return new Promise(resolve => {
            const duration = 1000; // 1 second
            const startTime = performance.now();
            const difference = endValue - startValue;
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function (ease-out)
                const easeOut = 1 - Math.pow(1 - progress, 3);
                const currentValue = Math.round(startValue + (difference * easeOut));
                
                element.textContent = currentValue.toLocaleString();
                
                // Add pulse effect for significant changes
                if (Math.abs(difference) > 0) {
                    element.classList.add('stat-updated');
                    setTimeout(() => element.classList.remove('stat-updated'), 300);
                }
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            };
            
            requestAnimationFrame(animate);
        });
    }
    
    animateProgressBar(progressElement, targetPercentage) {
        const progressBar = progressElement.querySelector('.progress-fill');
        if (!progressBar) return;
        
        const currentWidth = parseFloat(progressBar.style.width) || 0;
        const targetWidth = Math.min(targetPercentage, 100);
        
        // Animate progress bar width
        progressBar.style.transition = 'width 1s ease-out';
        progressBar.style.width = `${targetWidth}%`;
        
        // Update percentage text if exists
        const percentageText = progressElement.querySelector('.percentage-text');
        if (percentageText) {
            this.animateNumber(percentageText, Math.round(targetPercentage));
        }
        
        // Add visual feedback for progress changes
        if (Math.abs(targetWidth - currentWidth) > 1) {
            progressElement.classList.add('progress-updated');
            setTimeout(() => progressElement.classList.remove('progress-updated'), 1000);
        }
    }
    
    setupAnimations() {
        // Add CSS for animations if not already present
        if (!document.getElementById('tournament-stats-css')) {
            const style = document.createElement('style');
            style.id = 'tournament-stats-css';
            style.textContent = `
                .stat-updated {
                    animation: statPulse 0.3s ease-out;
                }
                
                @keyframes statPulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); color: #10b981; }
                    100% { transform: scale(1); }
                }
                
                .progress-updated .progress-fill {
                    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
                }
                
                .progress-fill {
                    transition: width 1s ease-out, box-shadow 0.3s ease-out;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Clear animation queue
        this.animationQueue = [];
        
        console.log('Tournament Stats module destroyed');
    }
}

// Auto-initialize when module is loaded
document.addEventListener('DOMContentLoaded', () => {
    const statsContainers = document.querySelectorAll('.tournament-stats-dashboard');
    statsContainers.forEach(container => {
        new TournamentStats(container);
    });
});

// Export for manual initialization
window.TournamentStats = TournamentStats;