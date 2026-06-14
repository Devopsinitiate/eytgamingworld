class DashboardOnboarding {
    constructor(options = {}) {
        this.config = Object.assign({
            storageKey: 'eyt_dashboard_tour_completed',
            autoStart: options.autoStart !== false,
            steps: this.getDefaultSteps()
        }, options);
        this.currentStep = 0;
        this.overlay = null;
        this.tooltip = null;
        this.completionMsg = null;
        this.isActive = false;
        this._positionHandler = null;
        this._keyHandler = this._keyHandler.bind(this);
        this._transitioning = false;
        if (this.config.autoStart && !this.isLocallyCompleted()) {
            this.deferredStart();
        }
    }

    findNavByLabel(labelText) {
        const labels = document.querySelectorAll('.nav-label');
        for (const label of labels) {
            if (label.textContent.trim() === labelText) {
                const link = label.closest('a');
                if (link) return link;
            }
        }
        return null;
    }

    getDefaultSteps() {
        return [
            {
                target: '.sidebar-gaming > div > a.flex.items-center',
                title: 'WELCOME TO EYTGAMING',
                icon: 'stadia_controller',
                content: 'This is your command center. Use the sidebar to navigate tournaments, teams, coaching, and more.',
                position: 'right',
                highlight: true
            },
            {
                findTarget: () => this.findNavByLabel('Dashboard'),
                title: 'DASHBOARD',
                icon: 'dashboard',
                content: 'Your personal dashboard shows key stats, activity feed, quick actions, and recommendations.',
                position: 'right',
                highlight: true
            },
            {
                findTarget: () => this.findNavByLabel('Events'),
                title: 'EVENTS',
                icon: 'emoji_events',
                content: 'Browse, register, and track all gaming tournaments. View brackets, standings, and match schedules.',
                position: 'right',
                highlight: true
            },
            {
                findTarget: () => this.findNavByLabel('Teams'),
                title: 'TEAMS',
                icon: 'groups',
                content: 'Create or join teams, manage members, and compete together in team-based events.',
                position: 'right',
                highlight: true
            },
            {
                findTarget: () => this.findNavByLabel('Coach'),
                title: 'COACH',
                icon: 'school',
                content: 'Book one-on-one coaching sessions with expert players to level up your skills.',
                position: 'right',
                highlight: true
            },
            {
                findTarget: () => this.findNavByLabel('Store'),
                title: 'STORE',
                icon: 'shopping_bag',
                content: 'Shop for gaming gear, merchandise, and digital products to enhance your setup.',
                position: 'right',
                highlight: true
            },
            {
                target: '.stat-card-gaming',
                title: 'YOUR STATS',
                icon: 'monitoring',
                content: 'Track your tournament count, win rate, teams, and unread alerts at a glance.',
                position: 'bottom',
                highlight: true
            },
            {
                target: '#notif-bell-btn',
                title: 'STAY UPDATED',
                icon: 'notifications',
                content: 'Never miss important updates. Check notifications for tournament alerts, team invites, and more.',
                position: 'bottom',
                highlight: true
            }
        ];
    }

    resolveTarget(step) {
        if (step.findTarget) return step.findTarget();
        if (step.target) return document.querySelector(step.target);
        return null;
    }

    isLocallyCompleted() {
        return localStorage.getItem(this.config.storageKey) === 'true';
    }

    markLocallyCompleted() {
        localStorage.setItem(this.config.storageKey, 'true');
    }

    async checkServerCompleted() {
        try {
            const r = await fetch('/api/onboarding-status/', { method: 'GET', headers: { 'Accept': 'application/json' } });
            const d = await r.json();
            return d.completed === true;
        } catch {
            return false;
        }
    }

    async deferredStart() {
        await new Promise(r => setTimeout(r, 600));
        if (await this.checkServerCompleted()) {
            this.markLocallyCompleted();
            return;
        }
        for (let i = 0; i < 8; i++) {
            await new Promise(r => setTimeout(r, 500));
            if (this.config.steps.some(s => this.resolveTarget(s))) break;
        }
        this.start();
    }

    start() {
        if (this.isActive) return;
        const idx = this.findFirstValidStep();
        if (idx === -1) return;
        this.isActive = true;
        this.currentStep = idx;
        this.createOverlay();
        document.addEventListener('keydown', this._keyHandler);
        this.showStep(idx);
    }

    findFirstValidStep() {
        for (let i = 0; i < this.config.steps.length; i++) {
            if (this.resolveTarget(this.config.steps[i])) return i;
        }
        return -1;
    }

    createOverlay() {
        document.body.style.overflow = 'hidden';

        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        this.overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:99998;backdrop-filter:blur(3px);animation:onboardFadeIn 0.3s ease;';
        this.overlay.addEventListener('click', () => this.end());

        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        this.tooltip.setAttribute('role', 'status');
        this.tooltip.setAttribute('aria-live', 'polite');
        this.tooltip.style.cssText = 'position:fixed;z-index:199999;background:linear-gradient(135deg,#0A0A0A 0%,#1F1F1F 100%);border:2px solid #DC2626;border-radius:10px;padding:1.25rem;max-width:380px;box-shadow:0 0 30px rgba(220,38,38,0.4),0 20px 40px rgba(0,0,0,0.5);visibility:hidden;';

        this.tooltip.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const action = btn.dataset.action;
            if (action === 'skip') this.end();
            else if (action === 'prev') this.showStep(this.currentStep - 1);
            else if (action === 'next') this.showStep(this.currentStep + 1);
            else if (action === 'finish') this.complete();
        });

        document.body.appendChild(this.overlay);
        document.body.appendChild(this.tooltip);
        this.injectStyles();
    }

    injectStyles() {
        if (document.getElementById('onboarding-styles')) return;
        const s = document.createElement('style');
        s.id = 'onboarding-styles';
        s.textContent = `
@keyframes onboardFadeIn{from{opacity:0}to{opacity:1}}
@keyframes onboardFadeOut{from{opacity:1}to{opacity:0}}
@keyframes onboardSlideIn{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:translateY(0)}}
@keyframes onboardSlideOut{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(16px)}}
.onboarding-highlight{position:relative;z-index:199999!important;box-shadow:0 0 0 9999px rgba(0,0,0,0.5);outline:3px solid #DC2626;outline-offset:2px;border-radius:8px;animation:onboardPulse 2s ease-in-out infinite}
@keyframes onboardPulse{0%,100%{box-shadow:0 0 0 9999px rgba(0,0,0,0.5),0 0 20px rgba(220,38,38,0.5);outline-color:#DC2626}50%{box-shadow:0 0 0 9999px rgba(0,0,0,0.5),0 0 40px rgba(220,38,38,0.8);outline-color:#ef4444}}
.onboarding-title{color:#DC2626;font-family:'Barlow Condensed',sans-serif;font-size:1.4rem;font-weight:900;text-transform:uppercase;font-style:italic;}
.onboarding-content{color:#D1D5DB;font-family:'Inter',sans-serif;font-size:0.9rem;line-height:1.6;margin-bottom:1.25rem;}
.onboarding-progress{display:flex;align-items:center;gap:6px;margin-bottom:0.75rem;}
.onboarding-progress-dot{width:8px;height:8px;border-radius:50%;background:rgba(220,38,38,0.25);transition:all 0.3s ease;}
.onboarding-progress-dot.active{background:#DC2626;box-shadow:0 0 8px rgba(220,38,38,0.7);transform:scale(1.3);}
.onboarding-step-count{color:#6B7280;font-family:'Inter',sans-serif;font-size:0.7rem;margin-left:auto;letter-spacing:0.03em;}
.onboarding-actions{display:flex;justify-content:space-between;align-items:center;gap:0.5rem;}
.onboarding-btn-group{display:flex;gap:0.5rem;}
.onboarding-btn{padding:0.65rem 1.25rem;border:none;border-radius:6px;font-family:'Barlow Condensed',sans-serif;font-size:0.9rem;font-weight:700;text-transform:uppercase;cursor:pointer;transition:all 0.2s ease;min-height:40px;}
.onboarding-btn-primary{background:linear-gradient(135deg,#DC2626 0%,#B91C1C 100%);color:#fff;box-shadow:0 0 16px rgba(220,38,38,0.3);}
.onboarding-btn-primary:hover{box-shadow:0 0 24px rgba(220,38,38,0.5);}
.onboarding-btn-secondary{background:transparent;color:#9CA3AF;border:1px solid rgba(220,38,38,0.3);}
.onboarding-btn-secondary:hover{color:#fff;border-color:#DC2626;}
.onboarding-tooltip-arrow{position:absolute;width:12px;height:12px;background:#1F1F1F;border-left:2px solid #DC2626;border-top:2px solid #DC2626;transform:rotate(-45deg);z-index:199998;}
@media(max-width:768px){
.onboarding-tooltip{max-width:88vw;left:50%!important;transform:translateX(-50%)!important;bottom:calc(env(safe-area-inset-bottom) + 90px)!important;top:auto!important;}
}`;
        document.head.appendChild(s);
    }

    showStep(stepIndex) {
        if (this._transitioning) return;
        const step = this.config.steps[stepIndex];
        if (!step) { this.end(); return; }

        document.querySelectorAll('.onboarding-highlight').forEach(el => el.classList.remove('onboarding-highlight'));
        document.querySelectorAll('.onboarding-tooltip-arrow').forEach(el => el.remove());

        const target = this.resolveTarget(step);
        if (!target) { this.showStep(stepIndex + 1); return; }

        target.scrollIntoView({ block: 'nearest', behavior: 'smooth' });

        if (step.highlight) target.classList.add('onboarding-highlight');

        const total = this.config.steps.length;
        const isFirst = stepIndex === 0;
        const isLast = stepIndex === total - 1;

        this.tooltip.innerHTML = `
<div class="onboarding-progress">
    ${this.config.steps.map((_, i) => `<div class="onboarding-progress-dot ${i === stepIndex ? 'active' : ''}"></div>`).join('')}
    <span class="onboarding-step-count">${stepIndex + 1} / ${total}</span>
</div>
<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
${step.icon ? `<span class="material-symbols-outlined" style="font-size:1.8rem;color:#DC2626;">${step.icon}</span>` : ''}
<h3 class="onboarding-title" style="margin-bottom:0;">${step.title}</h3>
</div>
<p class="onboarding-content">${step.content}</p>
<div class="onboarding-actions">
    <button class="onboarding-btn onboarding-btn-secondary" data-action="skip">SKIP TOUR</button>
    <div class="onboarding-btn-group">
        ${!isFirst ? '<button class="onboarding-btn onboarding-btn-secondary" data-action="prev">PREV</button>' : ''}
        <button class="onboarding-btn onboarding-btn-primary" data-action="${isLast ? 'finish' : 'next'}">${isLast ? 'FINISH' : 'NEXT'}</button>
    </div>
</div>`;
        this.tooltip.style.visibility = 'hidden';

        this.addTooltipArrow(target, step.position || 'right');

        requestAnimationFrame(() => {
            this.positionTooltip(target, step.position || 'right');
            this.tooltip.style.visibility = 'visible';
        });

        if (this._positionHandler) {
            window.removeEventListener('resize', this._positionHandler);
            window.removeEventListener('scroll', this._positionHandler, true);
        }
        this._positionHandler = () => {
            const t = this.resolveTarget(step);
            if (t) this.positionTooltip(t, step.position || 'right');
        };
        window.addEventListener('resize', this._positionHandler);
        window.addEventListener('scroll', this._positionHandler, true);
        this.currentStep = stepIndex;
    }

    addTooltipArrow(target, position) {
        const arrow = document.createElement('div');
        arrow.className = 'onboarding-tooltip-arrow';
        const tr = target.getBoundingClientRect();
        const pr = this.tooltip.getBoundingClientRect();
        let top, left;
        switch (position) {
            case 'right':
                top = tr.top + tr.height / 2 - 6;
                left = pr.left - 7;
                break;
            case 'left':
                top = tr.top + tr.height / 2 - 6;
                left = pr.right - 5;
                arrow.style.transform = 'rotate(135deg)';
                break;
            case 'bottom':
                top = pr.top - 7;
                left = tr.left + tr.width / 2 - 6;
                arrow.style.transform = 'rotate(-45deg)';
                break;
            case 'top':
                top = pr.bottom - 7;
                left = tr.left + tr.width / 2 - 6;
                arrow.style.transform = 'rotate(135deg)';
                break;
        }
        arrow.style.top = top + 'px';
        arrow.style.left = left + 'px';
        document.body.appendChild(arrow);
    }

    positionTooltip(target, position) {
        const rect = target.getBoundingClientRect();
        const tr = this.tooltip.getBoundingClientRect();
        const gap = 16;
        let top, left;
        switch (position) {
            case 'right':
                top = rect.top + rect.height / 2 - tr.height / 2;
                left = rect.right + gap;
                break;
            case 'left':
                top = rect.top + rect.height / 2 - tr.height / 2;
                left = rect.left - tr.width - gap;
                break;
            case 'top':
                top = rect.top - tr.height - gap;
                left = rect.left + rect.width / 2 - tr.width / 2;
                break;
            case 'bottom':
                top = rect.bottom + gap;
                left = rect.left + rect.width / 2 - tr.width / 2;
                break;
            default:
                top = rect.top;
                left = rect.right + gap;
        }
        top = Math.max(12, Math.min(top, window.innerHeight - tr.height - 12));
        left = Math.max(12, Math.min(left, window.innerWidth - tr.width - 12));
        this.tooltip.style.top = top + 'px';
        this.tooltip.style.left = left + 'px';
    }

    complete() {
        this.markLocallyCompleted();
        this.syncToServer();
        this.end();
        this.showCompletionMessage();
    }

    syncToServer() {
        const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        const token = input ? input.value : '';
        fetch('/api/complete-onboarding/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
            body: JSON.stringify({ completed: true })
        }).catch(() => {});
    }

    showCompletionMessage() {
        if (this.completionMsg) return;
        const msg = document.createElement('div');
        this.completionMsg = msg;
        msg.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:linear-gradient(135deg,#0A0A0A 0%,#1F1F1F 100%);border:3px solid #DC2626;border-radius:12px;padding:2rem;z-index:200000;box-shadow:0 0 40px rgba(220,38,38,0.5);text-align:center;animation:onboardSlideIn 0.4s ease;';
        msg.innerHTML = '<div style="font-size:3rem;margin-bottom:0.75rem;">🎮</div><h2 style="color:#DC2626;font-family:\'Barlow Condensed\',sans-serif;font-size:1.8rem;font-weight:900;text-transform:uppercase;font-style:italic;margin-bottom:0.5rem;">TOUR COMPLETE!</h2><p style="color:#D1D5DB;font-size:1rem;">You\'re ready to dominate!</p>';
        document.body.appendChild(msg);
        setTimeout(() => {
            msg.style.animation = 'onboardFadeOut 0.4s ease';
            setTimeout(() => { msg.remove(); this.completionMsg = null; }, 400);
        }, 2500);
    }

    _keyHandler(e) {
        if (!this.isActive) return;
        if (e.key === 'Escape') {
            e.preventDefault();
            this.end();
        } else if (e.key === 'Enter') {
            const step = this.config.steps[this.currentStep];
            if (!step) return;
            if (this.currentStep === this.config.steps.length - 1) {
                this.complete();
            } else {
                this.showStep(this.currentStep + 1);
            }
        }
    }

    end() {
        this.isActive = false;
        document.removeEventListener('keydown', this._keyHandler);
        document.body.style.overflow = '';
        if (this._positionHandler) {
            window.removeEventListener('resize', this._positionHandler);
            window.removeEventListener('scroll', this._positionHandler, true);
            this._positionHandler = null;
        }
        document.querySelectorAll('.onboarding-highlight').forEach(el => el.classList.remove('onboarding-highlight'));
        document.querySelectorAll('.onboarding-tooltip-arrow').forEach(el => el.remove());
        if (this.overlay) { const o = this.overlay; o.style.animation = 'onboardFadeOut 0.25s ease'; setTimeout(() => o.remove(), 250); this.overlay = null; }
        if (this.tooltip) { const t = this.tooltip; t.style.animation = 'onboardFadeOut 0.25s ease'; setTimeout(() => t.remove(), 250); this.tooltip = null; }
    }

    reset() { localStorage.removeItem(this.config.storageKey); }
    restart() { this.reset(); this.start(); }
}

window.DashboardOnboarding = DashboardOnboarding;

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('/dashboard/')) {
        window.onboardingTour = new DashboardOnboarding({ autoStart: true });
    }
});
