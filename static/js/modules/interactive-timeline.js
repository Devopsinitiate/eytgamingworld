/**
 * Interactive Tournament Timeline Module
 * Provides interactive timeline with animation controller, progressive reveal animations,
 * phase highlighting, hover effects, and smooth transitions
 */

class InteractiveTimeline {
    constructor(container, data = null) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.data = data;
        this.currentPhase = null;
        this.animationController = new AnimationController();
        this.isAnimating = false;
        this.respectsReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.observers = new Map();
        
        // Bind methods to preserve context
        this.handleResize = this.handleResize.bind(this);
        this.handleMotionPreferenceChange = this.handleMotionPreferenceChange.bind(this);
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            this.log('No timeline container found');
            return;
        }
        
        this.setupTimelineStructure();
        this.setupProgressiveReveal();
        this.setupInteractions();
        this.setupHoverEffects();
        this.setupResponsiveHandling();
        this.detectCurrentPhase();
        this.setupAccessibility();
        this.setupMotionPreferences();
        
        this.log('Interactive Timeline initialized');
    }
    
    setupTimelineStructure() {
        // Find timeline items within the container
        const timelineItems = this.container.querySelectorAll('.timeline-item, [data-phase]');
        
        timelineItems.forEach((item, index) => {
            // Add animation classes and attributes
            item.classList.add('timeline-item-interactive');
            item.setAttribute('data-timeline-index', index);
            
            // Setup intersection observer for scroll-based animations
            this.observeTimelineItem(item);
            
            // Ensure proper structure for animations
            this.ensureItemStructure(item);
        });
        
        // Add timeline connector line if not present
        this.ensureTimelineConnector();
    }
    
    ensureItemStructure(item) {
        // Ensure each item has the necessary elements for animations
        const icon = item.querySelector('.timeline-icon');
        const content = item.querySelector('.timeline-content');
        
        if (icon && !icon.classList.contains('timeline-icon-interactive')) {
            icon.classList.add('timeline-icon-interactive');
        }
        
        if (content && !content.classList.contains('timeline-content-interactive')) {
            content.classList.add('timeline-content-interactive');
        }
    }
    
    ensureTimelineConnector() {
        // Add connecting line between timeline items if not present
        const timeline = this.container.querySelector('.timeline');
        if (timeline && !timeline.querySelector('.timeline-connector')) {
            const connector = document.createElement('div');
            connector.className = 'timeline-connector';
            connector.setAttribute('aria-hidden', 'true');
            timeline.appendChild(connector);
        }
    }
    
    setupProgressiveReveal() {
        if (this.respectsReducedMotion) {
            // Show all items immediately if motion is reduced
            this.showAllItemsImmediately();
            return;
        }
        
        // Initially hide items for progressive reveal
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(30px)';
            item.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
        });
        
        // Start progressive reveal with staggered timing
        this.startProgressiveReveal();
    }
    
    showAllItemsImmediately() {
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
            item.classList.add('timeline-item-revealed');
        });
    }
    
    startProgressiveReveal() {
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        
        items.forEach((item, index) => {
            setTimeout(() => {
                this.revealTimelineItem(item);
            }, index * 200); // Stagger by 200ms for smoother effect
        });
    }
    
    revealTimelineItem(item) {
        item.style.opacity = '1';
        item.style.transform = 'translateY(0)';
        item.classList.add('timeline-item-revealed');
        
        // Animate child elements with additional stagger
        const childElements = item.querySelectorAll('.timeline-content h4, .timeline-content p, .phase-details');
        childElements.forEach((child, index) => {
            if (!this.respectsReducedMotion) {
                child.style.opacity = '0';
                child.style.transform = 'translateX(-20px)';
                child.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
                
                setTimeout(() => {
                    child.style.opacity = '1';
                    child.style.transform = 'translateX(0)';
                }, index * 100);
            }
        });
    }
    
    setupInteractions() {
        const timelineItems = this.container.querySelectorAll('.timeline-item-interactive');
        
        timelineItems.forEach(item => {
            // Make items focusable and clickable
            item.setAttribute('tabindex', '0');
            item.setAttribute('role', 'button');
            item.setAttribute('aria-label', this.getItemAriaLabel(item));
            
            // Click interactions
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.highlightPhase(item);
            });
            
            // Keyboard navigation
            item.addEventListener('keydown', (e) => {
                this.handleKeyboardNavigation(e, item);
            });
            
            // Focus handling
            item.addEventListener('focus', () => {
                this.handleItemFocus(item);
            });
            
            item.addEventListener('blur', () => {
                this.handleItemBlur(item);
            });
        });
    }
    
    getItemAriaLabel(item) {
        const phaseTitle = item.querySelector('.timeline-content h4')?.textContent?.trim() || 'Timeline phase';
        const phaseStatus = item.classList.contains('active') ? 'currently active' : 
                           item.classList.contains('completed') ? 'completed' : 'upcoming';
        return `${phaseTitle}, ${phaseStatus}. Click to highlight this phase.`;
    }
    
    setupHoverEffects() {
        if (this.respectsReducedMotion) return;
        
        const timelineItems = this.container.querySelectorAll('.timeline-item-interactive');
        
        timelineItems.forEach(item => {
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
        });
    }
    
    animateItemHover(item, isHovering) {
        const duration = this.respectsReducedMotion ? 0 : 300;
        const icon = item.querySelector('.timeline-icon-interactive');
        const content = item.querySelector('.timeline-content-interactive');
        
        if (isHovering) {
            // Hover in animation
            item.style.transition = `transform ${duration}ms ease-out, box-shadow ${duration}ms ease-out`;
            item.style.transform = 'scale(1.02) translateY(-4px)';
            item.style.boxShadow = '0 12px 30px rgba(0, 0, 0, 0.2)';
            
            if (icon) {
                icon.style.transition = `transform ${duration}ms ease-out`;
                icon.style.transform = 'scale(1.1) rotate(5deg)';
            }
            
            if (content) {
                content.style.transition = `transform ${duration}ms ease-out`;
                content.style.transform = 'translateX(8px)';
            }
            
            // Show tooltip if present
            const tooltip = item.querySelector('.timeline-tooltip');
            if (tooltip) {
                this.showTooltip(tooltip);
            }
        } else {
            // Hover out animation
            item.style.transform = '';
            item.style.boxShadow = '';
            
            if (icon) {
                icon.style.transform = '';
            }
            
            if (content) {
                content.style.transform = '';
            }
            
            // Hide tooltip
            const tooltip = item.querySelector('.timeline-tooltip');
            if (tooltip) {
                this.hideTooltip(tooltip);
            }
        }
    }
    
    showTooltip(tooltip) {
        if (this.respectsReducedMotion) {
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
            return;
        }
        
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'visible';
        tooltip.style.transform = 'translateY(10px)';
        tooltip.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
            tooltip.style.transform = 'translateY(0)';
        });
    }
    
    hideTooltip(tooltip) {
        if (this.respectsReducedMotion) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
            return;
        }
        
        tooltip.style.opacity = '0';
        tooltip.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            tooltip.style.visibility = 'hidden';
        }, 300);
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
        this.observers.set(item, observer);
    }
    
    animateItemIntoView(item) {
        if (this.respectsReducedMotion || item.classList.contains('timeline-item-in-view')) return;
        
        item.classList.add('timeline-item-in-view');
        
        // Add entrance animation with bounce effect
        this.animationController.animate(item, [
            { transform: 'translateY(20px)', opacity: 0 },
            { transform: 'translateY(-5px)', opacity: 0.8, offset: 0.7 },
            { transform: 'translateY(0)', opacity: 1 }
        ], {
            duration: 600,
            easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
        });
    }
    
    detectCurrentPhase() {
        // Try to detect current phase from classes or data attributes
        const currentPhaseElement = this.container.querySelector('.timeline-item.active, [data-current="true"]');
        
        if (currentPhaseElement) {
            this.currentPhase = currentPhaseElement;
            this.highlightCurrentPhase();
        } else {
            // Try to detect from tournament status in the page
            this.detectPhaseFromPageData();
        }
    }
    
    detectPhaseFromPageData() {
        // Look for tournament status indicators in the page
        const statusElement = document.querySelector('[data-tournament-status]');
        if (statusElement) {
            const status = statusElement.dataset.tournamentStatus;
            this.highlightPhaseByStatus(status);
        }
    }
    
    highlightCurrentPhase() {
        if (!this.currentPhase) return;
        
        this.currentPhase.classList.add('current-phase-highlighted');
        
        if (!this.respectsReducedMotion) {
            // Add subtle pulsing animation for current phase
            this.currentPhase.style.animation = 'timeline-pulse 3s ease-in-out infinite';
        }
        
        // Scroll current phase into view smoothly
        this.scrollToPhase(this.currentPhase);
        
        // Announce to screen readers
        this.announcePhaseChange(this.currentPhase, 'Current phase');
    }
    
    highlightPhaseByStatus(status) {
        const statusPhaseMap = {
            'registration': 'registration',
            'check_in': 'checkin',
            'in_progress': 'tournament',
            'completed': 'tournament'
        };
        
        const phaseId = statusPhaseMap[status];
        if (phaseId) {
            const phaseElement = this.container.querySelector(`[data-phase="${phaseId}"]`);
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
        this.container.querySelectorAll('.phase-highlighted').forEach(el => {
            el.classList.remove('phase-highlighted');
        });
        
        // Add highlight to selected phase
        phaseElement.classList.add('phase-highlighted');
        
        if (!this.respectsReducedMotion) {
            // Animate highlight with scale and glow effect
            this.animationController.animate(phaseElement, [
                { transform: 'scale(1)', boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)' },
                { transform: 'scale(1.05)', boxShadow: '0 8px 30px rgba(59, 130, 246, 0.3)', offset: 0.5 },
                { transform: 'scale(1)', boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)' }
            ], {
                duration: 600,
                easing: 'ease-out'
            }).then(() => {
                this.isAnimating = false;
            });
        } else {
            this.isAnimating = false;
        }
        
        // Scroll to highlighted phase
        this.scrollToPhase(phaseElement);
        
        // Announce to screen readers
        this.announcePhaseChange(phaseElement, 'Selected');
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
        const items = Array.from(this.container.querySelectorAll('.timeline-item-interactive'));
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
    
    handleItemFocus(item) {
        if (!this.respectsReducedMotion) {
            item.style.outline = '2px solid #3b82f6';
            item.style.outlineOffset = '2px';
        }
    }
    
    handleItemBlur(item) {
        item.style.outline = '';
        item.style.outlineOffset = '';
    }
    
    setupResponsiveHandling() {
        // Handle responsive layout changes
        const mediaQuery = window.matchMedia('(max-width: 768px)');
        
        const handleResponsiveChange = (e) => {
            if (e.matches) {
                this.adjustForMobile();
            } else {
                this.adjustForDesktop();
            }
        };
        
        mediaQuery.addListener(handleResponsiveChange);
        handleResponsiveChange(mediaQuery);
        
        // Handle window resize
        window.addEventListener('resize', this.handleResize);
    }
    
    adjustForMobile() {
        this.container.classList.add('timeline-mobile');
        
        // Reduce animation complexity on mobile
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            if (!this.respectsReducedMotion) {
                item.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            }
        });
    }
    
    adjustForDesktop() {
        this.container.classList.remove('timeline-mobile');
        
        // Full animations on desktop
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            if (!this.respectsReducedMotion) {
                item.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
            }
        });
    }
    
    handleResize() {
        // Debounce resize handling
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.recalculateLayout();
        }, 250);
    }
    
    recalculateLayout() {
        // Recalculate any layout-dependent animations or positions
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            // Reset any transforms that might be affected by layout changes
            if (item.style.transform && !item.classList.contains('phase-highlighted')) {
                item.style.transform = '';
            }
        });
    }
    
    setupAccessibility() {
        // Add ARIA labels and live region for announcements
        this.container.setAttribute('role', 'region');
        this.container.setAttribute('aria-label', 'Tournament timeline');
        
        // Create live region for announcements
        this.createLiveRegion();
    }
    
    createLiveRegion() {
        if (document.getElementById('timeline-announcements')) return;
        
        const liveRegion = document.createElement('div');
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
    
    setupMotionPreferences() {
        // Listen for changes in motion preferences
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.addListener(this.handleMotionPreferenceChange);
    }
    
    handleMotionPreferenceChange(e) {
        this.respectsReducedMotion = e.matches;
        
        if (this.respectsReducedMotion) {
            // Disable all animations
            this.disableAnimations();
        } else {
            // Re-enable animations
            this.enableAnimations();
        }
    }
    
    disableAnimations() {
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            item.style.transition = 'none';
            item.style.animation = 'none';
            item.style.transform = '';
        });
    }
    
    enableAnimations() {
        const items = this.container.querySelectorAll('.timeline-item-interactive');
        items.forEach(item => {
            item.style.transition = '';
            // Re-setup animations if needed
        });
    }
    
    updateTimelineData(newData) {
        if (!newData || !newData.phases) {
            this.log('Invalid timeline data provided');
            return;
        }
        
        this.log('Updating timeline with new data');
        this.data = newData;
        
        // Animate data transitions
        this.animateDataUpdate(newData);
    }
    
    animateDataUpdate(data) {
        if (this.respectsReducedMotion) {
            this.updateTimelineContent(data);
            return;
        }
        
        // Fade out current content
        this.container.style.transition = 'opacity 0.4s ease-out';
        this.container.style.opacity = '0.6';
        
        setTimeout(() => {
            this.updateTimelineContent(data);
            
            // Fade back in
            this.container.style.opacity = '1';
        }, 200);
    }
    
    updateTimelineContent(data) {
        data.phases.forEach(phase => {
            const phaseElement = this.container.querySelector(`[data-phase="${phase.id}"]`);
            if (phaseElement) {
                this.updatePhaseElement(phaseElement, phase);
            }
        });
        
        // Update current phase if changed
        if (data.currentPhase && data.currentPhase !== this.currentPhase?.dataset.phase) {
            const newCurrentPhase = this.container.querySelector(`[data-phase="${data.currentPhase}"]`);
            if (newCurrentPhase) {
                this.currentPhase = newCurrentPhase;
                this.highlightCurrentPhase();
            }
        }
    }
    
    updatePhaseElement(element, phaseData) {
        // Update phase content
        const titleElement = element.querySelector('.timeline-content h4');
        const descElement = element.querySelector('.timeline-content p');
        const dateElement = element.querySelector('.phase-date');
        
        if (titleElement && phaseData.title) {
            titleElement.textContent = phaseData.title;
        }
        
        if (descElement && phaseData.description) {
            descElement.textContent = phaseData.description;
        }
        
        if (dateElement && phaseData.date) {
            dateElement.textContent = this.formatDate(phaseData.date);
        }
        
        // Update status classes
        element.className = element.className.replace(/status-\w+/g, '');
        if (phaseData.status) {
            element.classList.add(`status-${phaseData.status}`);
        }
        
        // Update ARIA label
        element.setAttribute('aria-label', this.getItemAriaLabel(element));
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
            this.log('Error formatting date:', error);
            return dateString;
        }
    }
    
    announcePhaseChange(phaseElement, action = 'Selected') {
        const phaseName = phaseElement.querySelector('.timeline-content h4')?.textContent || 'Phase';
        const announcement = `${action}: ${phaseName}`;
        
        const liveRegion = document.getElementById('timeline-announcements');
        if (liveRegion) {
            liveRegion.textContent = announcement;
            
            // Clear after announcement
            setTimeout(() => {
                liveRegion.textContent = '';
            }, 1000);
        }
    }
    
    log(...args) {
        console.log('[InteractiveTimeline]', ...args);
    }
    
    destroy() {
        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.removeListener(this.handleMotionPreferenceChange);
        
        // Clean up intersection observers
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
        
        // Remove event listeners from items
        const items = this.container?.querySelectorAll('.timeline-item-interactive') || [];
        items.forEach(item => {
            item.replaceWith(item.cloneNode(true));
        });
        
        // Remove created elements
        const liveRegion = document.getElementById('timeline-announcements');
        if (liveRegion) {
            liveRegion.remove();
        }
        
        // Clear animations
        if (this.container) {
            this.container.style.animation = '';
            this.container.querySelectorAll('*').forEach(el => {
                el.style.animation = '';
                el.style.transition = '';
                el.style.transform = '';
            });
        }
        
        // Stop animation controller
        if (this.animationController) {
            this.animationController.stopAll();
        }
        
        this.log('Interactive Timeline destroyed');
    }
}

/**
 * Animation Controller for managing complex animations
 * Handles Web Animations API with fallbacks and motion preferences
 */
class AnimationController {
    constructor() {
        this.activeAnimations = new Set();
        this.animationQueue = [];
        this.respectsReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    
    animate(element, keyframes, options = {}) {
        if (this.respectsReducedMotion) {
            // Apply final state immediately if motion is reduced
            const finalFrame = keyframes[keyframes.length - 1];
            Object.assign(element.style, finalFrame);
            return Promise.resolve();
        }
        
        // Use Web Animations API if available
        if (element.animate) {
            const animation = element.animate(keyframes, {
                duration: 400,
                easing: 'ease-out',
                fill: 'forwards',
                ...options
            });
            
            this.activeAnimations.add(animation);
            
            animation.addEventListener('finish', () => {
                this.activeAnimations.delete(animation);
            });
            
            animation.addEventListener('cancel', () => {
                this.activeAnimations.delete(animation);
            });
            
            return animation.finished;
        } else {
            // Fallback for older browsers
            return this.fallbackAnimate(element, keyframes, options);
        }
    }
    
    fallbackAnimate(element, keyframes, options) {
        return new Promise((resolve) => {
            const duration = options.duration || 400;
            const finalFrame = keyframes[keyframes.length - 1];
            
            element.style.transition = `all ${duration}ms ${options.easing || 'ease-out'}`;
            Object.assign(element.style, finalFrame);
            
            setTimeout(() => {
                resolve();
            }, duration);
        });
    }
    
    stopAll() {
        this.activeAnimations.forEach(animation => {
            animation.cancel();
        });
        this.activeAnimations.clear();
        this.animationQueue = [];
    }
    
    pause() {
        this.activeAnimations.forEach(animation => {
            if (animation.pause) {
                animation.pause();
            }
        });
    }
    
    resume() {
        this.activeAnimations.forEach(animation => {
            if (animation.play) {
                animation.play();
            }
        });
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const timelineContainer = document.querySelector('#tournament-timeline, .tournament-timeline, [data-timeline]');
    if (timelineContainer) {
        window.InteractiveTimeline = new InteractiveTimeline(timelineContainer);
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.InteractiveTimeline) {
        window.InteractiveTimeline.destroy();
    }
});

export default InteractiveTimeline;