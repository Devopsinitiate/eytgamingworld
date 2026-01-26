/**
 * Timeline Animations Module for Tournament Detail Page
 * Provides interactive timeline with smooth animations and progressive reveal
 */

class TimelineAnimationsManager {
    constructor() {
        this.timelineContainer = document.querySelector('.tournament-timeline, .timeline-container, [data-timeline]');
        this.animationController = new AnimationController();
        this.currentPhase = null;
        this.isAnimating = false;
        this.respectsReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        this.init();
    }
    
    init() {
        if (!this.timelineContainer) {
            this.log('No timeline container found');
            return;
        }
        
        this.setupTimelineStructure();
        this.setupInteractions();
        this.setupProgressiveReveal();
        this.setupResponsiveHandling();
        this.detectCurrentPhase();
        
        this.log('Timeline Animations Manager initialized');
    }
    
    setupTimelineStructure() {
        // Ensure timeline has proper structure for animations
        const timelineItems = this.timelineContainer.querySelectorAll('.timeline-item, .phase-item, [data-phase]');
        
        timelineItems.forEach((item, index) => {
            // Add animation classes
            item.classList.add('timeline-item-animated');
            item.setAttribute('data-timeline-index', index);
            
            // Add intersection observer for scroll-based animations
            this.observeTimelineItem(item);
            
            // Setup hover effects
            this.setupItemHoverEffects(item);
        });
    }
    
    setupInteractions() {
        const timelineItems = this.timelineContainer.querySelectorAll('.timeline-item-animated');
        
        timelineItems.forEach(item => {
            // Click interactions
            item.addEventListener('click', (e) => {
                if (!item.classList.contains('clickable')) return;
                
                e.preventDefault();
                this.highlightPhase(item);
            });
            
            // Keyboard navigation
            item.addEventListener('keydown', (e) => {
                this.handleKeyboardNavigation(e, item);
            });
            
            // Make items focusable if they're interactive
            if (item.classList.contains('clickable') || item.dataset.phase) {
                item.setAttribute('tabindex', '0');
                item.setAttribute('role', 'button');
            }
        });
    }
    
    setupItemHoverEffects(item) {
        if (this.respectsReducedMotion) return;
        
        item.addEventListener('mouseenter', () => {
            if (!this.isAnimating) {
                this.animateItemHover(item, true);
            }
        });
        
        item.addEventListener('mouseleave', () => {
            if (!this.isAnimating) {
                this.animateItemHover(item, false);
            }
        });
    }
    
    animateItemHover(item, isHovering) {
        const duration = this.respectsReducedMotion ? 0 : 200;
        
        if (isHovering) {
            item.style.transition = `transform ${duration}ms ease-out, box-shadow ${duration}ms ease-out`;
            item.style.transform = 'scale(1.02) translateY(-2px)';
            item.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
        } else {
            item.style.transform = '';
            item.style.boxShadow = '';
        }
    }
    
    setupProgressiveReveal() {
        if (this.respectsReducedMotion) {
            // Show all items immediately if motion is reduced
            this.timelineContainer.querySelectorAll('.timeline-item-animated').forEach(item => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            });
            return;
        }
        
        // Initially hide items for progressive reveal
        this.timelineContainer.querySelectorAll('.timeline-item-animated').forEach(item => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        });
        
        // Start progressive reveal
        this.startProgressiveReveal();
    }
    
    startProgressiveReveal() {
        const items = this.timelineContainer.querySelectorAll('.timeline-item-animated');
        
        items.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 150); // Stagger by 150ms
        });
    }
    
    observeTimelineItem(item) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateItemIntoView(entry.target);
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '50px'
        });
        
        observer.observe(item);
    }
    
    animateItemIntoView(item) {
        if (this.respectsReducedMotion) return;
        
        // Add entrance animation
        item.classList.add('timeline-item-visible');
        
        // Animate any child elements
        const childElements = item.querySelectorAll('.phase-title, .phase-description, .phase-date');
        childElements.forEach((child, index) => {
            setTimeout(() => {
                child.style.opacity = '1';
                child.style.transform = 'translateX(0)';
            }, index * 100);
        });
    }
    
    detectCurrentPhase() {
        // Try to detect current phase from data attributes or classes
        const currentPhaseElement = this.timelineContainer.querySelector('.current-phase, .active-phase, [data-current="true"]');
        
        if (currentPhaseElement) {
            this.currentPhase = currentPhaseElement;
            this.highlightCurrentPhase();
        } else {
            // Try to detect from tournament status
            const tournamentStatus = document.querySelector('[data-tournament-status]')?.dataset.tournamentStatus;
            if (tournamentStatus) {
                this.highlightPhaseByStatus(tournamentStatus);
            }
        }
    }
    
    highlightCurrentPhase() {
        if (!this.currentPhase) return;
        
        this.currentPhase.classList.add('current-phase-highlighted');
        
        if (!this.respectsReducedMotion) {
            // Add pulsing animation for current phase
            this.currentPhase.style.animation = 'pulse-glow 2s ease-in-out infinite';
        }
        
        // Scroll current phase into view
        this.scrollToPhase(this.currentPhase);
    }
    
    highlightPhaseByStatus(status) {
        const statusPhaseMap = {
            'registration': 'registration',
            'check_in': 'check-in',
            'in_progress': 'tournament',
            'completed': 'results'
        };
        
        const phaseId = statusPhaseMap[status];
        if (phaseId) {
            const phaseElement = this.timelineContainer.querySelector(`[data-phase="${phaseId}"]`);
            if (phaseElement) {
                this.currentPhase = phaseElement;
                this.highlightCurrentPhase();
            }
        }
    }
    
    highlightPhase(phaseElement) {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        
        // Remove previous highlights
        this.timelineContainer.querySelectorAll('.phase-highlighted').forEach(el => {
            el.classList.remove('phase-highlighted');
        });
        
        // Add highlight to selected phase
        phaseElement.classList.add('phase-highlighted');
        
        if (!this.respectsReducedMotion) {
            // Animate highlight
            phaseElement.style.transform = 'scale(1.05)';
            phaseElement.style.zIndex = '10';
            
            setTimeout(() => {
                phaseElement.style.transform = '';
                phaseElement.style.zIndex = '';
                this.isAnimating = false;
            }, 300);
        } else {
            this.isAnimating = false;
        }
        
        // Scroll to highlighted phase
        this.scrollToPhase(phaseElement);
        
        // Announce to screen readers
        this.announcePhaseChange(phaseElement);
    }
    
    scrollToPhase(phaseElement) {
        const behavior = this.respectsReducedMotion ? 'auto' : 'smooth';
        
        phaseElement.scrollIntoView({
            behavior,
            block: 'center',
            inline: 'nearest'
        });
    }
    
    handleKeyboardNavigation(e, currentItem) {
        const items = Array.from(this.timelineContainer.querySelectorAll('.timeline-item-animated'));
        const currentIndex = items.indexOf(currentItem);
        
        let targetIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowDown':
            case 'ArrowRight':
                e.preventDefault();
                targetIndex = Math.min(currentIndex + 1, items.length - 1);
                break;
            case 'ArrowUp':
            case 'ArrowLeft':
                e.preventDefault();
                targetIndex = Math.max(currentIndex - 1, 0);
                break;
            case 'Home':
                e.preventDefault();
                targetIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                targetIndex = items.length - 1;
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                this.highlightPhase(currentItem);
                return;
        }
        
        if (targetIndex !== currentIndex) {
            items[targetIndex].focus();
            this.highlightPhase(items[targetIndex]);
        }
    }
    
    setupResponsiveHandling() {
        // Handle responsive layout changes
        const mediaQuery = window.matchMedia('(max-width: 768px)');
        
        const handleResponsiveChange = (e) => {
            if (e.matches) {
                // Mobile layout
                this.timelineContainer.classList.add('timeline-mobile');
                this.adjustMobileAnimations();
            } else {
                // Desktop layout
                this.timelineContainer.classList.remove('timeline-mobile');
                this.adjustDesktopAnimations();
            }
        };
        
        mediaQuery.addListener(handleResponsiveChange);
        handleResponsiveChange(mediaQuery);
    }
    
    adjustMobileAnimations() {
        // Reduce animation complexity on mobile
        const items = this.timelineContainer.querySelectorAll('.timeline-item-animated');
        items.forEach(item => {
            item.style.transition = 'opacity 0.3s ease-out';
        });
    }
    
    adjustDesktopAnimations() {
        // Full animations on desktop
        const items = this.timelineContainer.querySelectorAll('.timeline-item-animated');
        items.forEach(item => {
            if (!this.respectsReducedMotion) {
                item.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            }
        });
    }
    
    updateTimelineData(newData) {
        if (!newData || !newData.phases) return;
        
        this.log('Updating timeline with new data');
        
        // Animate data transitions
        this.animateDataUpdate(newData);
    }
    
    animateDataUpdate(data) {
        if (this.respectsReducedMotion) {
            this.updateTimelineContent(data);
            return;
        }
        
        // Fade out current content
        this.timelineContainer.style.opacity = '0.5';
        
        setTimeout(() => {
            this.updateTimelineContent(data);
            
            // Fade back in
            this.timelineContainer.style.opacity = '1';
        }, 200);
    }
    
    updateTimelineContent(data) {
        data.phases.forEach(phase => {
            const phaseElement = this.timelineContainer.querySelector(`[data-phase="${phase.id}"]`);
            if (phaseElement) {
                // Update phase content
                const titleElement = phaseElement.querySelector('.phase-title');
                const descElement = phaseElement.querySelector('.phase-description');
                const dateElement = phaseElement.querySelector('.phase-date');
                
                if (titleElement) titleElement.textContent = phase.title;
                if (descElement) descElement.textContent = phase.description;
                if (dateElement) dateElement.textContent = this.formatDate(phase.date);
                
                // Update status classes
                phaseElement.className = phaseElement.className.replace(/status-\w+/g, '');
                phaseElement.classList.add(`status-${phase.status}`);
            }
        });
        
        // Update current phase if changed
        if (data.currentPhase && data.currentPhase !== this.currentPhase?.dataset.phase) {
            const newCurrentPhase = this.timelineContainer.querySelector(`[data-phase="${data.currentPhase}"]`);
            if (newCurrentPhase) {
                this.currentPhase = newCurrentPhase;
                this.highlightCurrentPhase();
            }
        }
    }
    
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    }
    
    announcePhaseChange(phaseElement) {
        const phaseName = phaseElement.querySelector('.phase-title')?.textContent || 'Phase';
        const announcement = `${phaseName} selected`;
        
        // Use existing live region or create one
        let liveRegion = document.getElementById('timeline-announcements');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'timeline-announcements';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.style.position = 'absolute';
            liveRegion.style.left = '-10000px';
            liveRegion.style.width = '1px';
            liveRegion.style.height = '1px';
            liveRegion.style.overflow = 'hidden';
            document.body.appendChild(liveRegion);
        }
        
        liveRegion.textContent = announcement;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
    
    log(...args) {
        console.log('[TimelineAnimations]', ...args);
    }
    
    destroy() {
        // Remove event listeners
        const items = this.timelineContainer?.querySelectorAll('.timeline-item-animated') || [];
        items.forEach(item => {
            item.replaceWith(item.cloneNode(true));
        });
        
        // Remove created elements
        const liveRegion = document.getElementById('timeline-announcements');
        if (liveRegion) {
            liveRegion.remove();
        }
        
        // Clear animations
        if (this.timelineContainer) {
            this.timelineContainer.style.animation = '';
            this.timelineContainer.querySelectorAll('*').forEach(el => {
                el.style.animation = '';
                el.style.transition = '';
                el.style.transform = '';
            });
        }
        
        this.log('Timeline Animations Manager destroyed');
    }
}

/**
 * Animation Controller for managing complex animations
 */
class AnimationController {
    constructor() {
        this.activeAnimations = new Set();
        this.animationQueue = [];
    }
    
    animate(element, keyframes, options = {}) {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return Promise.resolve();
        }
        
        const animation = element.animate(keyframes, {
            duration: 300,
            easing: 'ease-out',
            fill: 'forwards',
            ...options
        });
        
        this.activeAnimations.add(animation);
        
        animation.addEventListener('finish', () => {
            this.activeAnimations.delete(animation);
        });
        
        return animation.finished;
    }
    
    stopAll() {
        this.activeAnimations.forEach(animation => {
            animation.cancel();
        });
        this.activeAnimations.clear();
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.TimelineAnimationsManager = new TimelineAnimationsManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.TimelineAnimationsManager) {
        window.TimelineAnimationsManager.destroy();
    }
});

// Make available globally instead of using ES6 export
window.TimelineAnimationsManager = TimelineAnimationsManager;