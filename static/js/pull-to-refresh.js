/**
 * Pull-to-Refresh for Mobile Dashboard
 * Gaming-themed pull-to-refresh with custom animations
 */

class PullToRefresh {
    constructor(options = {}) {
        this.config = {
            container: options.container || document.getElementById('main-content'),
            threshold: options.threshold || 80,
            onRefresh: options.onRefresh || (() => window.location.reload()),
            enabled: this.isMobile(),
            ...options
        };

        this.startY = 0;
        this.currentY = 0;
        this.isPulling = false;
        this.isRefreshing = false;
        this.pullIndicator = null;

        if (this.config.enabled) {
            this.init();
        }
    }

    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
            || window.innerWidth <= 768;
    }

    init() {
        this.createPullIndicator();
        this.attachEvents();
    }

    createPullIndicator() {
        this.pullIndicator = document.createElement('div');
        this.pullIndicator.className = 'pull-to-refresh-indicator';
        this.pullIndicator.innerHTML = `
            <div class="pull-indicator-content">
                <div class="pull-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <p class="pull-text gaming-body"></p>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .pull-to-refresh-indicator {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(180deg, rgba(10, 10, 10, 0.95) 0%, transparent 100%);
                transform: translateY(-100%);
                transition: transform 0.3s ease;
                z-index: 9999;
                pointer-events: none;
            }

            .pull-to-refresh-indicator.pulling {
                transform: translateY(0);
            }

            .pull-indicator-content {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.5rem;
            }

            .pull-spinner {
                position: relative;
                width: 40px;
                height: 40px;
            }

            .spinner-ring {
                position: absolute;
                width: 100%;
                height: 100%;
                border: 3px solid transparent;
                border-top-color: #DC2626;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            .spinner-ring:nth-child(2) {
                border-top-color: #06B6D4;
                animation-delay: 0.15s;
            }

            .spinner-ring:nth-child(3) {
                border-top-color: #DC2626;
                animation-delay: 0.3s;
                opacity: 0.5;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .pull-text {
                color: #DC2626;
                font-size: 0.875rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .pull-to-refresh-indicator.refreshing .pull-spinner {
                animation: pulse 1.5s ease-in-out infinite;
            }

            @keyframes pulse {
                0%, 100% {
                    transform: scale(1);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.1);
                    opacity: 0.8;
                }
            }
        `;
        document.head.appendChild(style);

        document.body.insertBefore(this.pullIndicator, document.body.firstChild);
    }

    attachEvents() {
        const container = this.config.container;

        container.addEventListener('touchstart', (e) => {
            if (container.scrollTop === 0) {
                this.startY = e.touches[0].pageY;
                this.isPulling = true;
            }
        }, { passive: true });

        container.addEventListener('touchmove', (e) => {
            if (!this.isPulling || this.isRefreshing) return;

            this.currentY = e.touches[0].pageY;
            const pullDistance = this.currentY - this.startY;

            if (pullDistance > 0) {
                e.preventDefault();
                const progress = Math.min(pullDistance / this.config.threshold, 1);
                
                this.pullIndicator.style.transform = `translateY(${Math.min(pullDistance * 0.5, this.config.threshold)}px)`;
                this.pullIndicator.classList.add('pulling');

                const textEl = this.pullIndicator.querySelector('.pull-text');
                if (pullDistance >= this.config.threshold) {
                    textEl.textContent = '⚡ RELEASE TO REFRESH';
                    textEl.style.color = '#06B6D4';
                } else {
                    textEl.textContent = `↓ PULL TO REFRESH (${Math.round(progress * 100)}%)`;
                    textEl.style.color = '#DC2626';
                }
            }
        }, { passive: false });

        container.addEventListener('touchend', () => {
            if (!this.isPulling || this.isRefreshing) return;

            const pullDistance = this.currentY - this.startY;

            if (pullDistance >= this.config.threshold) {
                this.triggerRefresh();
            } else {
                this.resetPull();
            }

            this.isPulling = false;
        });
    }

    async triggerRefresh() {
        this.isRefreshing = true;
        this.pullIndicator.classList.add('refreshing');
        this.pullIndicator.querySelector('.pull-text').textContent = '🔄 REFRESHING...';

        try {
            await this.config.onRefresh();
            
            // Success feedback
            this.pullIndicator.querySelector('.pull-text').textContent = '✓ UPDATED!';
            this.pullIndicator.querySelector('.pull-text').style.color = '#10B981';
            
            setTimeout(() => {
                this.resetPull();
            }, 500);
        } catch (error) {
            // Error feedback
            this.pullIndicator.querySelector('.pull-text').textContent = '✗ ERROR';
            this.pullIndicator.querySelector('.pull-text').style.color = '#EF4444';
            
            setTimeout(() => {
                this.resetPull();
            }, 1000);
        }
    }

    resetPull() {
        this.pullIndicator.style.transform = 'translateY(-100%)';
        this.pullIndicator.classList.remove('pulling', 'refreshing');
        
        setTimeout(() => {
            this.isRefreshing = false;
            this.startY = 0;
            this.currentY = 0;
        }, 300);
    }

    destroy() {
        if (this.pullIndicator) {
            this.pullIndicator.remove();
        }
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth <= 768) {
        window.pullToRefresh = new PullToRefresh({
            container: document.getElementById('main-content'),
            threshold: 80,
            onRefresh: async () => {
                // Wait 1 second to simulate data refresh
                await new Promise(resolve => setTimeout(resolve, 1000));
                window.location.reload();
            }
        });
    }
});
