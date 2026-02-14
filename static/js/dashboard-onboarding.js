/**
 * Dashboard Onboarding Tour
 * Gaming-themed interactive tour for new users
 */

class DashboardOnboarding {
    constructor(options = {}) {
        this.config = {
            storageKey: 'eyt_dashboard_tour_completed',
            autoStart: options.autoStart !== false,
            steps: options.steps || this.getDefaultSteps(),
            ...options
        };

        this.currentStep = 0;
        this.overlay = null;
        this.tooltip = null;
        this.isActive = false;

        if (this.config.autoStart && !this.isCompleted()) {
            setTimeout(() => this.start(), 1000);
        }
    }

    getDefaultSteps() {
        return [
            {
                target: '.sidebar-gaming .gaming-subheader',
                title: '🎮 WELCOME TO EYTGAMING',
                content: 'This is your command center! Navigate through tournaments, teams, coaching, and more. Let\'s take a quick tour.',
                position: 'right',
                highlight: true
            },
            {
                target: 'a[href*="dashboard:home"]',
                title: '🏠 DASHBOARD',
                content: 'Your personal dashboard shows stats, activity, and quick actions. Click here anytime to return home.',
                position: 'right',
                highlight: true
            },
            {
                target: 'a[href*="tournaments:list"]',
                title: '🏆 TOURNAMENTS',
                content: 'Browse, register, and track all gaming tournaments. Find your next competition here!',
                position: 'right',
                highlight: true
            },
            {
                target: 'a[href*="teams:list"]',
                title: '👥 TEAMS',
                content: 'Create or join teams, manage members, and compete together. Teamwork makes the dream work!',
                position: 'right',
                highlight: true
            },
            {
                target: '.stat-card-gaming:first-child',
                title: '📊 YOUR STATS',
                content: 'Track your performance with real-time statistics. Tournaments played, win rate, team count, and notifications.',
                position: 'bottom',
                highlight: true
            },
            {
                target: '.mobile-bottom-nav, #user-dropdown',
                title: '⚙️ PROFILE & SETTINGS',
                content: 'Access your profile, payment history, and account settings. Customize your gaming experience!',
                position: 'top',
                highlight: true
            },
            {
                target: 'button[aria-label*="Notification"]',
                title: '🔔 STAY UPDATED',
                content: 'Never miss important updates! Check notifications for tournament alerts, team invites, and more.',
                position: 'bottom',
                highlight: true
            }
        ];
    }

    isCompleted() {
        return localStorage.getItem(this.config.storageKey) === 'true';
    }

    markCompleted() {
        localStorage.setItem(this.config.storageKey, 'true');
    }

    start() {
        if (this.isActive) return;

        this.isActive = true;
        this.currentStep = 0;
        this.createOverlay();
        this.showStep(0);
    }

    createOverlay() {
        // Create darkened overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 9998;
            backdrop-filter: blur(2px);
            animation: fadeIn 0.3s ease;
        `;

        // Create tooltip
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        this.tooltip.style.cssText = `
            position: fixed;
            z-index: 9999;
            background: linear-gradient(135deg, #0A0A0A 0%, #1F1F1F 100%);
            border: 2px solid #DC2626;
            border-radius: 0.5rem;
            padding: 1.5rem;
            max-width: 400px;
            box-shadow: 0 0 30px rgba(220, 38, 38, 0.5),
                        0 20px 40px rgba(0, 0, 0, 0.5);
            transform: skewY(-2deg);
            animation: slideIn 0.4s ease;
        `;

        document.body.appendChild(this.overlay);
        document.body.appendChild(this.tooltip);

        // Add styles
        this.addStyles();

        // Click overlay to skip
        this.overlay.addEventListener('click', () => this.end());
    }

    addStyles() {
        if (document.getElementById('onboarding-styles')) return;

        const style = document.createElement('style');
        style.id = 'onboarding-styles';
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: skewY(-2deg) translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: skewY(-2deg) translateY(0);
                }
            }

            @keyframes pulse-glow {
                0%, 100% {
                    box-shadow: 0 0 20px rgba(220, 38, 38, 0.6);
                }
                50% {
                    box-shadow: 0 0 40px rgba(220, 38, 38, 0.9),
                                0 0 60px rgba(220, 38, 38, 0.6);
                }
            }

            .onboarding-highlight {
                position: relative;
                z-index: 9999 !important;
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.85);
                animation: pulse-glow 2s ease-in-out infinite;
                border-radius: 0.5rem;
            }

            .onboarding-tooltip-content {
                transform: skewY(2deg);
            }

            .onboarding-title {
                color: #DC2626;
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 1.5rem;
                font-weight: 900;
                text-transform: uppercase;
                font-style: italic;
                margin-bottom: 0.75rem;
                text-shadow: 0 0 10px rgba(220, 38, 38, 0.5);
            }

            .onboarding-content {
                color: #D1D5DB;
                font-family: 'Inter', sans-serif;
                font-size: 1rem;
                line-height: 1.6;
                margin-bottom: 1.5rem;
            }

            .onboarding-progress {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }

            .onboarding-progress-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: rgba(220, 38, 38, 0.3);
                transition: all 0.3s ease;
            }

            .onboarding-progress-dot.active {
                background: #DC2626;
                box-shadow: 0 0 10px rgba(220, 38, 38, 0.8);
                transform: scale(1.3);
            }

            .onboarding-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
            }

            .onboarding-button {
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 0.375rem;
                font-family: 'Barlow Condensed', sans-serif;
                font-size: 1rem;
                font-weight: 900;
                text-transform: uppercase;
                font-style: italic;
                cursor: pointer;
                transition: all 0.3s ease;
                transform: skewX(-12deg);
                min-height: 44px;
            }

            .onboarding-button span {
                display: block;
                transform: skewX(12deg);
            }

            .onboarding-button-primary {
                background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%);
                color: white;
                box-shadow: 0 0 20px rgba(220, 38, 38, 0.4);
            }

            .onboarding-button-primary:hover {
                transform: skewX(0deg);
                box-shadow: 0 0 30px rgba(220, 38, 38, 0.6);
            }

            .onboarding-button-secondary {
                background: transparent;
                color: #9CA3AF;
                border: 2px solid rgba(220, 38, 38, 0.3);
            }

            .onboarding-button-secondary:hover {
                color: white;
                border-color: #DC2626;
                transform: skewX(0deg);
            }

            @media (max-width: 768px) {
                .onboarding-tooltip {
                    max-width: 90vw;
                    left: 50% !important;
                    transform: translateX(-50%) skewY(-2deg) !important;
                    bottom: 100px !important;
                    top: auto !important;
                }
            }
        `;
        document.head.appendChild(style);
    }

    showStep(stepIndex) {
        const step = this.config.steps[stepIndex];
        if (!step) {
            this.end();
            return;
        }

        // Remove previous highlight
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });

        // Find target element
        const target = document.querySelector(step.target);
        if (!target) {
            // Skip to next if target not found
            this.showStep(stepIndex + 1);
            return;
        }

        // Highlight target
        if (step.highlight) {
            target.classList.add('onboarding-highlight');
        }

        // Position tooltip
        this.positionTooltip(target, step.position || 'right');

        // Update tooltip content
        this.tooltip.innerHTML = `
            <div class="onboarding-tooltip-content">
                <div class="onboarding-progress">
                    ${this.config.steps.map((_, i) => `
                        <div class="onboarding-progress-dot ${i === stepIndex ? 'active' : ''}"></div>
                    `).join('')}
                </div>
                <h3 class="onboarding-title">${step.title}</h3>
                <p class="onboarding-content">${step.content}</p>
                <div class="onboarding-actions">
                    <button class="onboarding-button onboarding-button-secondary" id="tour-skip">
                        <span>SKIP TOUR</span>
                    </button>
                    <button class="onboarding-button onboarding-button-primary" id="tour-next">
                        <span>${stepIndex === this.config.steps.length - 1 ? 'FINISH' : 'NEXT'}</span>
                    </button>
                </div>
            </div>
        `;

        // Attach event listeners
        document.getElementById('tour-skip').addEventListener('click', () => this.end());
        document.getElementById('tour-next').addEventListener('click', () => {
            if (stepIndex === this.config.steps.length - 1) {
                this.complete();
            } else {
                this.showStep(stepIndex + 1);
            }
        });

        this.currentStep = stepIndex;
    }

    positionTooltip(target, position) {
        const rect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const spacing = 20;

        let top, left;

        switch (position) {
            case 'right':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.right + spacing;
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                left = rect.left - tooltipRect.width - spacing;
                break;
            case 'top':
                top = rect.top - tooltipRect.height - spacing;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'bottom':
                top = rect.bottom + spacing;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            default:
                top = rect.top;
                left = rect.right + spacing;
        }

        // Keep tooltip within viewport
        const maxTop = window.innerHeight - tooltipRect.height - 20;
        const maxLeft = window.innerWidth - tooltipRect.width - 20;

        top = Math.max(20, Math.min(top, maxTop));
        left = Math.max(20, Math.min(left, maxLeft));

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }

    complete() {
        this.markCompleted();
        this.end();
        
        // Show completion message
        this.showCompletionMessage();
    }

    showCompletionMessage() {
        const message = document.createElement('div');
        message.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) skewY(-2deg);
            background: linear-gradient(135deg, #0A0A0A 0%, #1F1F1F 100%);
            border: 3px solid #DC2626;
            border-radius: 0.5rem;
            padding: 2rem;
            z-index: 10000;
            box-shadow: 0 0 40px rgba(220, 38, 38, 0.6);
            text-align: center;
            animation: slideIn 0.5s ease;
        `;

        message.innerHTML = `
            <div style="transform: skewY(2deg);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎮</div>
                <h2 class="onboarding-title" style="font-size: 2rem; margin-bottom: 1rem;">
                    TOUR COMPLETE!
                </h2>
                <p style="color: #D1D5DB; font-size: 1.125rem; margin-bottom: 1.5rem;">
                    You're ready to dominate!
                </p>
            </div>
        `;

        document.body.appendChild(message);

        setTimeout(() => {
            message.style.animation = 'fadeOut 0.5s ease';
            setTimeout(() => message.remove(), 500);
        }, 2000);
    }

    end() {
        this.isActive = false;

        // Remove highlights
        document.querySelectorAll('.onboarding-highlight').forEach(el => {
            el.classList.remove('onboarding-highlight');
        });

        // Remove overlay and tooltip
        if (this.overlay) {
            this.overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => this.overlay.remove(), 300);
        }

        if (this.tooltip) {
            this.tooltip.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => this.tooltip.remove(), 300);
        }
    }

    reset() {
        localStorage.removeItem(this.config.storageKey);
    }

    restart() {
        this.reset();
        this.start();
    }
}

// Auto-initialize and expose globally
window.DashboardOnboarding = DashboardOnboarding;

document.addEventListener('DOMContentLoaded', () => {
    // Only auto-start for new users on dashboard
    if (window.location.pathname.includes('/dashboard/')) {
        window.onboardingTour = new DashboardOnboarding({
            autoStart: true
        });
    }
});

// Add fadeOut animation
const fadeOutKeyframes = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
const style = document.createElement('style');
style.textContent = fadeOutKeyframes;
document.head.appendChild(style);
