/**
 * Participant List Module
 * Handles efficient pagination, filtering, and virtual scrolling
 * Loaded lazily when participant section is visible
 */

class ParticipantList {
    constructor(container) {
        this.container = container;
        this.tournamentSlug = container.dataset.tournamentSlug;
        this.currentPage = 1;
        this.perPage = 20;
        this.totalPages = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.participants = [];
        this.filters = {
            status: '',
            checked_in: '',
            search: '',
            sort: 'seed'
        };
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.setupIntersectionObserver();
        this.loadParticipants();
        
        console.log('Participant List module initialized');
    }
    
    setupElements() {
        this.elements = {
            list: this.container.querySelector('.participant-list'),
            loadingIndicator: this.container.querySelector('.loading-indicator'),
            searchInput: this.container.querySelector('.participant-search'),
            statusFilter: this.container.querySelector('.status-filter'),
            checkedInFilter: this.container.querySelector('.checked-in-filter'),
            sortSelect: this.container.querySelector('.sort-select'),
            loadMoreButton: this.container.querySelector('.load-more-button'),
            totalCount: this.container.querySelector('.total-participants'),
            emptyState: this.container.querySelector('.empty-state')
        };
        
        // Create elements if they don't exist
        if (!this.elements.list) {
            this.elements.list = document.createElement('div');
            this.elements.list.className = 'participant-list';
            this.container.appendChild(this.elements.list);
        }
        
        if (!this.elements.loadingIndicator) {
            this.elements.loadingIndicator = this.createLoadingIndicator();
            this.container.appendChild(this.elements.loadingIndicator);
        }
    }
    
    setupEventListeners() {
        // Search input with debouncing
        if (this.elements.searchInput) {
            let searchTimeout;
            this.elements.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.resetAndReload();
                }, 300);
            });
        }
        
        // Filter dropdowns
        if (this.elements.statusFilter) {
            this.elements.statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.resetAndReload();
            });
        }
        
        if (this.elements.checkedInFilter) {
            this.elements.checkedInFilter.addEventListener('change', (e) => {
                this.filters.checked_in = e.target.value;
                this.resetAndReload();
            });
        }
        
        if (this.elements.sortSelect) {
            this.elements.sortSelect.addEventListener('change', (e) => {
                this.filters.sort = e.target.value;
                this.resetAndReload();
            });
        }
        
        // Load more button
        if (this.elements.loadMoreButton) {
            this.elements.loadMoreButton.addEventListener('click', () => {
                this.loadMoreParticipants();
            });
        }
    }
    
    setupIntersectionObserver() {
        // Infinite scroll observer
        this.scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMore && !this.isLoading) {
                    this.loadMoreParticipants();
                }
            });
        }, {
            rootMargin: '100px'
        });
        
        // Observe the loading indicator for infinite scroll
        if (this.elements.loadingIndicator) {
            this.scrollObserver.observe(this.elements.loadingIndicator);
        }
    }
    
    async loadParticipants(append = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                ...this.filters
            });
            
            const response = await fetch(`/tournaments/${this.tournamentSlug}/api/participants/?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (append) {
                this.participants = [...this.participants, ...data.participants];
            } else {
                this.participants = data.participants;
            }
            
            this.totalPages = data.total_pages;
            this.hasMore = data.has_next;
            
            this.renderParticipants(append);
            this.updateTotalCount(data.total);
            
        } catch (error) {
            console.error('Failed to load participants:', error);
            this.showError('Failed to load participants. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadMoreParticipants() {
        if (!this.hasMore || this.isLoading) return;
        
        this.currentPage++;
        await this.loadParticipants(true);
    }
    
    resetAndReload() {
        this.currentPage = 1;
        this.hasMore = true;
        this.participants = [];
        this.loadParticipants();
    }
    
    renderParticipants(append = false) {
        if (!append) {
            this.elements.list.innerHTML = '';
        }
        
        if (this.participants.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        // Use document fragment for better performance
        const fragment = document.createDocumentFragment();
        
        const startIndex = append ? this.elements.list.children.length : 0;
        const newParticipants = append ? 
            this.participants.slice(startIndex) : 
            this.participants;
        
        newParticipants.forEach(participant => {
            const participantElement = this.createParticipantCard(participant);
            fragment.appendChild(participantElement);
        });
        
        this.elements.list.appendChild(fragment);
        
        // Animate new cards
        if (append) {
            const newCards = Array.from(this.elements.list.children).slice(startIndex);
            this.animateNewCards(newCards);
        }
    }
    
    createParticipantCard(participant) {
        const card = document.createElement('div');
        card.className = 'participant-card';
        card.dataset.participantId = participant.id;
        
        // Add status classes
        if (participant.checked_in) {
            card.classList.add('checked-in');
        }
        card.classList.add(`status-${participant.status}`);
        
        const avatarUrl = participant.user?.avatar_url || '/static/images/default-avatar.png';
        const teamLogo = participant.team?.logo_url;
        
        card.innerHTML = `
            <div class="participant-avatar">
                <img src="${avatarUrl}" alt="${participant.display_name}" loading="lazy">
                ${participant.checked_in ? '<div class="check-in-badge">✓</div>' : ''}
            </div>
            <div class="participant-info">
                <h4 class="participant-name">${participant.display_name}</h4>
                ${participant.team ? `
                    <div class="team-info">
                        ${teamLogo ? `<img src="${teamLogo}" class="team-logo" alt="${participant.team.name}">` : ''}
                        <span class="team-name">${participant.team.name}</span>
                    </div>
                ` : ''}
                ${participant.seed ? `<div class="seed-badge">Seed #${participant.seed}</div>` : ''}
                <div class="participant-stats">
                    <span class="wins">${participant.matches_won}W</span>
                    <span class="losses">${participant.matches_lost}L</span>
                    ${participant.win_rate > 0 ? `<span class="win-rate">${participant.win_rate}%</span>` : ''}
                </div>
            </div>
            <div class="participant-status">
                <span class="status-badge status-${participant.status}">${this.getStatusLabel(participant.status)}</span>
                <time class="registered-date" datetime="${participant.registered_at}">
                    ${this.formatDate(participant.registered_at)}
                </time>
            </div>
        `;
        
        return card;
    }
    
    animateNewCards(cards) {
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }
    
    createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'loading-indicator';
        indicator.innerHTML = `
            <div class="loading-spinner"></div>
            <span class="loading-text">Loading participants...</span>
        `;
        return indicator;
    }
    
    showLoading() {
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.style.display = 'flex';
        }
    }
    
    hideLoading() {
        if (this.elements.loadingIndicator) {
            this.elements.loadingIndicator.style.display = 'none';
        }
    }
    
    showEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = 'block';
        } else {
            // Create empty state if it doesn't exist
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-icon">👥</div>
                <h3>No participants found</h3>
                <p>Try adjusting your filters or search terms.</p>
            `;
            this.elements.list.appendChild(emptyState);
        }
    }
    
    hideEmptyState() {
        if (this.elements.emptyState) {
            this.elements.emptyState.style.display = 'none';
        }
    }
    
    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.innerHTML = `
            <div class="error-icon">⚠️</div>
            <p>${message}</p>
            <button class="retry-button">Retry</button>
        `;
        
        errorElement.querySelector('.retry-button').addEventListener('click', () => {
            errorElement.remove();
            this.loadParticipants();
        });
        
        this.elements.list.appendChild(errorElement);
    }
    
    updateTotalCount(total) {
        if (this.elements.totalCount) {
            this.elements.totalCount.textContent = total.toLocaleString();
        }
    }
    
    getStatusLabel(status) {
        const labels = {
            'confirmed': 'Confirmed',
            'pending': 'Pending',
            'pending_payment': 'Payment Due',
            'rejected': 'Rejected',
            'withdrawn': 'Withdrawn',
            'disqualified': 'Disqualified'
        };
        return labels[status] || status;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }
    
    destroy() {
        if (this.scrollObserver) {
            this.scrollObserver.disconnect();
        }
        
        console.log('Participant List module destroyed');
    }
}

// Auto-initialize when module is loaded
document.addEventListener('DOMContentLoaded', () => {
    const participantContainers = document.querySelectorAll('.participant-list-container');
    participantContainers.forEach(container => {
        new ParticipantList(container);
    });
});

// Export for manual initialization
window.ParticipantList = ParticipantList;