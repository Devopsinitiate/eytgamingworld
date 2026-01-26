/**
 * Accessibility Compliance Module
 * Ensures comprehensive accessibility support for tournament detail page
 * Addresses Requirements 12.1, 12.2, 12.3, 12.4, 12.5
 */

class AccessibilityCompliance {
    constructor() {
        this.focusIndicators = new Map();
        this.ariaLiveRegions = new Map();
        this.motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.contrastPreference = window.matchMedia('(prefers-contrast: high)').matches;
        this.colorSchemePreference = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Bind methods to preserve context
        this.handleMotionPreferenceChange = this.handleMotionPreferenceChange.bind(this);
        this.handleContrastPreferenceChange = this.handleContrastPreferenceChange.bind(this);
        this.handleKeyboardNavigation = this.handleKeyboardNavigation.bind(this);
        this.handleFocusManagement = this.handleFocusManagement.bind(this);
        
        this.init();
    }
    
    init() {
        this.setupFocusIndicators();
        this.setupAriaLabels();
        this.setupMotionPreferences();
        this.setupNonColorIndicators();
        this.setupKeyboardNavigation();
        this.setupLiveRegions();
        this.setupContrastSupport();
        this.setupScreenReaderSupport();
        this.setupTouchTargets();
        
        this.log('Accessibility Compliance initialized');
    }
    
    /**
     * Setup visible focus indicators for all interactive elements
     * Requirement 12.1: Visible focus indicators for keyboard navigation
     */
    setupFocusIndicators() {
        const interactiveElements = document.querySelectorAll(`
            button, 
            a, 
            input, 
            select, 
            textarea, 
            [tabindex]:not([tabindex="-1"]),
            [role="button"],
            [role="tab"],
            [role="menuitem"],
            .timeline-item-interactive,
            .participant-card,
            .match-card,
            .stat-card,
            .share-button,
            .copy-button,
            .tab-button
        `);
        
        interactiveElements.forEach(element => {
            this.enhanceFocusIndicator(element);
        });
        
        // Setup focus trap for modals
        this.setupFocusTraps();
        
        this.log(`Enhanced focus indicators for ${interactiveElements.length} elements`);
    }
    
    enhanceFocusIndicator(element) {
        // Remove default outline
        element.style.outline = 'none';
        
        // Add enhanced focus handling
        element.addEventListener('focus', (e) => {
            this.showFocusIndicator(e.target);
        });
        
        element.addEventListener('blur', (e) => {
            this.hideFocusIndicator(e.target);
        });
        
        // Handle keyboard vs mouse focus
        element.addEventListener('mousedown', (e) => {
            e.target.classList.add('mouse-focus');
        });
        
        element.addEventListener('keydown', (e) => {
            e.target.classList.remove('mouse-focus');
        });
    }
    
    showFocusIndicator(element) {
        if (element.classList.contains('mouse-focus')) {
            return; // Don't show focus indicator for mouse interactions
        }
        
        // Create or update focus indicator
        const indicator = this.createFocusIndicator(element);
        this.focusIndicators.set(element, indicator);
        
        // Position the indicator
        this.positionFocusIndicator(element, indicator);
        
        // Add to DOM
        document.body.appendChild(indicator);
        
        // Animate in
        requestAnimationFrame(() => {
            indicator.style.opacity = '1';
            indicator.style.transform = 'scale(1)';
        });
    }
    
    hideFocusIndicator(element) {
        const indicator = this.focusIndicators.get(element);
        if (indicator && indicator.parentNode) {
            indicator.style.opacity = '0';
            indicator.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 200);
        }
        this.focusIndicators.delete(element);
    }
    
    createFocusIndicator(element) {
        const indicator = document.createElement('div');
        indicator.className = 'accessibility-focus-indicator';
        indicator.style.cssText = `
            position: absolute;
            pointer-events: none;
            z-index: 9999;
            border: 2px solid #3b82f6;
            border-radius: 4px;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2), 0 0 8px rgba(59, 130, 246, 0.3);
            opacity: 0;
            transform: scale(0.95);
            transition: all 0.2s ease-out;
            background: rgba(59, 130, 246, 0.1);
        `;
        
        // Add animation for high visibility
        if (!this.motionPreference) {
            indicator.style.animation = 'accessibility-focus-pulse 2s ease-in-out infinite';
        }
        
        return indicator;
    }
    
    positionFocusIndicator(element, indicator) {
        const rect = element.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        indicator.style.top = `${rect.top + scrollTop - 4}px`;
        indicator.style.left = `${rect.left + scrollLeft - 4}px`;
        indicator.style.width = `${rect.width + 8}px`;
        indicator.style.height = `${rect.height + 8}px`;
    }
    
    setupFocusTraps() {
        // Setup focus traps for modals and dialogs
        const modals = document.querySelectorAll('[role="dialog"], .modal, .copy-link-modal');
        
        modals.forEach(modal => {
            this.setupModalFocusTrap(modal);
        });
    }
    
    setupModalFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(`
            button:not([disabled]),
            [href]:not([disabled]),
            input:not([disabled]),
            select:not([disabled]),
            textarea:not([disabled]),
            [tabindex]:not([tabindex="-1"]):not([disabled])
        `);
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    // Shift + Tab
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    // Tab
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
            
            if (e.key === 'Escape') {
                this.closeModal(modal);
            }
        });
        
        // Focus first element when modal opens
        setTimeout(() => {
            firstElement.focus();
        }, 100);
    }
    
    closeModal(modal) {
        // Find and trigger close button or remove modal
        const closeButton = modal.querySelector('[aria-label*="close"], .close-btn, .cancel-btn');
        if (closeButton) {
            closeButton.click();
        } else {
            modal.remove();
        }
    }
    
    /**
     * Setup descriptive ARIA labels and announcements
     * Requirement 12.2: Descriptive ARIA labels and screen reader support
     */
    setupAriaLabels() {
        // Tournament status indicators
        this.setupStatusAriaLabels();
        
        // Interactive elements
        this.setupInteractiveAriaLabels();
        
        // Progress indicators
        this.setupProgressAriaLabels();
        
        // Navigation elements
        this.setupNavigationAriaLabels();
        
        // Form elements
        this.setupFormAriaLabels();
        
        this.log('ARIA labels configured');
    }
    
    setupStatusAriaLabels() {
        const statusElements = document.querySelectorAll('.status-badge, [data-status], .tournament-status');
        
        statusElements.forEach(element => {
            const status = element.textContent?.trim() || 
                          element.dataset.status || 
                          element.className.match(/status-(\w+)/)?.[1];
            
            if (status) {
                const ariaLabel = this.getStatusAriaLabel(status);
                element.setAttribute('aria-label', ariaLabel);
                element.setAttribute('role', 'status');
                
                // Add live region for status changes
                if (!element.hasAttribute('aria-live')) {
                    element.setAttribute('aria-live', 'polite');
                }
            }
        });
    }
    
    getStatusAriaLabel(status) {
        const statusLabels = {
            'registration': 'Tournament registration is open',
            'in-progress': 'Tournament is currently in progress',
            'completed': 'Tournament has been completed',
            'cancelled': 'Tournament has been cancelled',
            'check-in': 'Check-in period is active',
            'upcoming': 'Tournament is scheduled for the future'
        };
        
        return statusLabels[status.toLowerCase()] || `Tournament status: ${status}`;
    }
    
    setupInteractiveAriaLabels() {
        // Timeline items
        const timelineItems = document.querySelectorAll('.timeline-item, [data-phase]');
        timelineItems.forEach(item => {
            if (!item.getAttribute('aria-label')) {
                const phase = item.querySelector('h4, .phase-title')?.textContent?.trim();
                const status = item.classList.contains('active') ? 'current' : 
                              item.classList.contains('completed') ? 'completed' : 'upcoming';
                
                if (phase) {
                    item.setAttribute('aria-label', `${phase} phase, ${status}. Click to view details.`);
                    item.setAttribute('role', 'button');
                    item.setAttribute('tabindex', '0');
                }
            }
        });
        
        // Participant cards
        const participantCards = document.querySelectorAll('.participant-card');
        participantCards.forEach(card => {
            const name = card.querySelector('.participant-name, .player-name')?.textContent?.trim();
            const team = card.querySelector('.team-name')?.textContent?.trim();
            const seed = card.querySelector('.seed-badge')?.textContent?.trim();
            
            let ariaLabel = name ? `Participant: ${name}` : 'Tournament participant';
            if (team) ariaLabel += `, Team: ${team}`;
            if (seed) ariaLabel += `, Seed: ${seed}`;
            
            card.setAttribute('aria-label', ariaLabel);
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
        });
        
        // Share buttons
        const shareButtons = document.querySelectorAll('.share-button, [data-share]');
        shareButtons.forEach(button => {
            const platform = button.dataset.share || 
                           button.className.match(/share-(\w+)/)?.[1] || 
                           'social media';
            
            button.setAttribute('aria-label', `Share tournament on ${platform}`);
        });
    }
    
    setupProgressAriaLabels() {
        const progressBars = document.querySelectorAll('.progress-bar, [role="progressbar"]');
        
        progressBars.forEach(bar => {
            bar.setAttribute('role', 'progressbar');
            
            // Calculate progress value
            const progress = this.calculateProgress(bar);
            bar.setAttribute('aria-valuenow', progress.current);
            bar.setAttribute('aria-valuemin', progress.min);
            bar.setAttribute('aria-valuemax', progress.max);
            bar.setAttribute('aria-label', `Tournament progress: ${progress.current} of ${progress.max} completed`);
        });
    }
    
    calculateProgress(progressBar) {
        // Try to extract progress from various sources
        const progressText = progressBar.textContent?.match(/(\d+).*?(\d+)/);
        const dataProgress = progressBar.dataset.progress;
        const styleWidth = progressBar.style.width?.match(/(\d+)%/);
        
        if (progressText) {
            return {
                current: parseInt(progressText[1]),
                min: 0,
                max: parseInt(progressText[2])
            };
        } else if (dataProgress) {
            return {
                current: parseInt(dataProgress),
                min: 0,
                max: 100
            };
        } else if (styleWidth) {
            return {
                current: parseInt(styleWidth[1]),
                min: 0,
                max: 100
            };
        }
        
        return { current: 0, min: 0, max: 100 };
    }
    
    setupNavigationAriaLabels() {
        // Breadcrumb navigation
        const breadcrumbs = document.querySelectorAll('.breadcrumbs, nav[aria-label*="breadcrumb"]');
        breadcrumbs.forEach(nav => {
            if (!nav.getAttribute('aria-label')) {
                nav.setAttribute('aria-label', 'Breadcrumb navigation');
            }
            
            const list = nav.querySelector('ol, ul');
            if (list && !list.getAttribute('role')) {
                list.setAttribute('role', 'list');
            }
            
            const items = nav.querySelectorAll('li');
            items.forEach((item, index) => {
                item.setAttribute('role', 'listitem');
                
                const link = item.querySelector('a');
                const current = item.querySelector('[aria-current]');
                
                if (current) {
                    current.setAttribute('aria-current', 'page');
                } else if (link && index === items.length - 1) {
                    // Last item without explicit current marker
                    item.setAttribute('aria-current', 'page');
                }
            });
        });
        
        // Tab navigation
        const tabLists = document.querySelectorAll('.tab-navigation, [role="tablist"]');
        tabLists.forEach(tabList => {
            tabList.setAttribute('role', 'tablist');
            
            const tabs = tabList.querySelectorAll('.tab-button, [role="tab"]');
            tabs.forEach((tab, index) => {
                tab.setAttribute('role', 'tab');
                tab.setAttribute('aria-selected', tab.classList.contains('active') ? 'true' : 'false');
                tab.setAttribute('tabindex', tab.classList.contains('active') ? '0' : '-1');
                
                const panelId = tab.dataset.target || `panel-${index}`;
                tab.setAttribute('aria-controls', panelId);
                
                // Find corresponding panel
                const panel = document.querySelector(`#${panelId}, [data-panel="${panelId}"]`);
                if (panel) {
                    panel.setAttribute('role', 'tabpanel');
                    panel.setAttribute('aria-labelledby', tab.id || `tab-${index}`);
                    if (!tab.id) tab.id = `tab-${index}`;
                }
            });
        });
    }
    
    setupFormAriaLabels() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                // Associate labels
                const label = form.querySelector(`label[for="${input.id}"]`) ||
                             input.closest('label') ||
                             form.querySelector(`label:has(input[name="${input.name}"])`);
                
                if (label && !input.getAttribute('aria-labelledby')) {
                    if (!label.id) label.id = `label-${input.name || Math.random().toString(36).substr(2, 9)}`;
                    input.setAttribute('aria-labelledby', label.id);
                }
                
                // Add required indicators
                if (input.required && !input.getAttribute('aria-required')) {
                    input.setAttribute('aria-required', 'true');
                }
                
                // Add error associations
                const errorElement = form.querySelector(`[data-error-for="${input.name}"], .error-${input.name}`);
                if (errorElement) {
                    if (!errorElement.id) errorElement.id = `error-${input.name}`;
                    input.setAttribute('aria-describedby', errorElement.id);
                    input.setAttribute('aria-invalid', 'true');
                }
            });
        });
    }
    
    /**
     * Setup motion preference handling
     * Requirement 12.3: Respect prefers-reduced-motion setting
     */
    setupMotionPreferences() {
        // Listen for motion preference changes
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.addListener(this.handleMotionPreferenceChange);
        
        // Apply initial motion preferences
        this.applyMotionPreferences();
        
        this.log(`Motion preferences applied. Reduced motion: ${this.motionPreference}`);
    }
    
    handleMotionPreferenceChange(e) {
        this.motionPreference = e.matches;
        this.applyMotionPreferences();
        this.log(`Motion preference changed. Reduced motion: ${this.motionPreference}`);
    }
    
    applyMotionPreferences() {
        if (this.motionPreference) {
            this.disableAnimations();
        } else {
            this.enableAnimations();
        }
    }
    
    disableAnimations() {
        // Add CSS class to disable animations
        document.documentElement.classList.add('reduce-motion');
        
        // Disable specific animations
        const animatedElements = document.querySelectorAll(`
            .animate-pulse,
            .animate-bounce,
            .animate-spin,
            [style*="animation"],
            .timeline-item-interactive,
            .participant-card,
            .share-button
        `);
        
        animatedElements.forEach(element => {
            element.style.animation = 'none';
            element.style.transition = 'none';
        });
        
        // Disable scroll animations
        document.documentElement.style.scrollBehavior = 'auto';
    }
    
    enableAnimations() {
        document.documentElement.classList.remove('reduce-motion');
        document.documentElement.style.scrollBehavior = 'smooth';
        
        // Re-enable animations by removing inline styles
        const elements = document.querySelectorAll('[style*="animation: none"], [style*="transition: none"]');
        elements.forEach(element => {
            element.style.animation = '';
            element.style.transition = '';
        });
    }
    
    /**
     * Setup non-color information indicators
     * Requirement 12.4: Provide non-color indicators for information
     */
    setupNonColorIndicators() {
        this.addStatusIcons();
        this.addProgressPatterns();
        this.addTextualIndicators();
        
        this.log('Non-color indicators configured');
    }
    
    addStatusIcons() {
        const statusElements = document.querySelectorAll('.status-badge, [data-status]');
        
        statusElements.forEach(element => {
            const status = element.textContent?.trim().toLowerCase() || 
                          element.dataset.status?.toLowerCase() ||
                          element.className.match(/status-(\w+)/)?.[1];
            
            const icon = this.getStatusIcon(status);
            if (icon && !element.querySelector('.status-icon')) {
                const iconElement = document.createElement('span');
                iconElement.className = 'status-icon';
                iconElement.setAttribute('aria-hidden', 'true');
                iconElement.textContent = icon;
                
                element.insertBefore(iconElement, element.firstChild);
            }
        });
    }
    
    getStatusIcon(status) {
        const statusIcons = {
            'registration': '📝',
            'open': '🟢',
            'in-progress': '🔴',
            'active': '🔴',
            'completed': '✅',
            'finished': '✅',
            'cancelled': '❌',
            'postponed': '⏸️',
            'check-in': '📋',
            'upcoming': '⏰',
            'pending': '⏳'
        };
        
        return statusIcons[status] || '●';
    }
    
    addProgressPatterns() {
        const progressBars = document.querySelectorAll('.progress-bar, [role="progressbar"]');
        
        progressBars.forEach(bar => {
            // Add pattern or texture to progress bars
            const progress = this.calculateProgress(bar);
            const percentage = Math.round((progress.current / progress.max) * 100);
            
            // Add textual progress indicator
            if (!bar.querySelector('.progress-text')) {
                const progressText = document.createElement('span');
                progressText.className = 'progress-text sr-only';
                progressText.textContent = `${percentage}% complete`;
                bar.appendChild(progressText);
            }
            
            // Add visual pattern for different progress levels
            bar.classList.remove('progress-low', 'progress-medium', 'progress-high');
            if (percentage < 33) {
                bar.classList.add('progress-low');
            } else if (percentage < 66) {
                bar.classList.add('progress-medium');
            } else {
                bar.classList.add('progress-high');
            }
        });
    }
    
    addTextualIndicators() {
        // Add text alternatives for color-coded information
        const colorCodedElements = document.querySelectorAll(`
            .text-red-500,
            .text-green-500,
            .text-yellow-500,
            .text-blue-500,
            .bg-red-500,
            .bg-green-500,
            .bg-yellow-500,
            .bg-blue-500
        `);
        
        colorCodedElements.forEach(element => {
            const colorClass = Array.from(element.classList).find(cls => 
                cls.includes('red') || cls.includes('green') || 
                cls.includes('yellow') || cls.includes('blue')
            );
            
            if (colorClass && !element.querySelector('.color-indicator')) {
                const indicator = this.getColorIndicator(colorClass);
                if (indicator) {
                    const indicatorElement = document.createElement('span');
                    indicatorElement.className = 'color-indicator';
                    indicatorElement.setAttribute('aria-hidden', 'true');
                    indicatorElement.textContent = indicator;
                    
                    element.insertBefore(indicatorElement, element.firstChild);
                }
            }
        });
    }
    
    getColorIndicator(colorClass) {
        if (colorClass.includes('red')) return '🔴';
        if (colorClass.includes('green')) return '🟢';
        if (colorClass.includes('yellow')) return '🟡';
        if (colorClass.includes('blue')) return '🔵';
        return null;
    }
    
    /**
     * Setup keyboard navigation enhancements
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', this.handleKeyboardNavigation);
        
        // Setup roving tabindex for complex widgets
        this.setupRovingTabindex();
        
        // Setup skip links
        this.setupSkipLinks();
        
        this.log('Keyboard navigation configured');
    }
    
    handleKeyboardNavigation(e) {
        // Handle escape key for modals
        if (e.key === 'Escape') {
            const modal = document.querySelector('.modal:not([style*="display: none"]), [role="dialog"]');
            if (modal) {
                this.closeModal(modal);
                return;
            }
        }
        
        // Handle arrow keys for tab navigation
        if (e.target.getAttribute('role') === 'tab') {
            this.handleTabNavigation(e);
        }
        
        // Handle arrow keys for timeline navigation
        if (e.target.classList.contains('timeline-item-interactive')) {
            this.handleTimelineNavigation(e);
        }
    }
    
    handleTabNavigation(e) {
        const tabList = e.target.closest('[role="tablist"]');
        if (!tabList) return;
        
        const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
        const currentIndex = tabs.indexOf(e.target);
        
        let targetIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                targetIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                targetIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                break;
            case 'Home':
                e.preventDefault();
                targetIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                targetIndex = tabs.length - 1;
                break;
        }
        
        if (targetIndex !== currentIndex) {
            this.activateTab(tabs[targetIndex]);
        }
    }
    
    activateTab(tab) {
        const tabList = tab.closest('[role="tablist"]');
        const tabs = tabList.querySelectorAll('[role="tab"]');
        
        // Update tab states
        tabs.forEach(t => {
            t.setAttribute('aria-selected', 'false');
            t.setAttribute('tabindex', '-1');
        });
        
        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');
        tab.focus();
        
        // Activate corresponding panel
        const panelId = tab.getAttribute('aria-controls');
        if (panelId) {
            const panels = document.querySelectorAll('[role="tabpanel"]');
            panels.forEach(panel => {
                panel.hidden = true;
            });
            
            const activePanel = document.getElementById(panelId);
            if (activePanel) {
                activePanel.hidden = false;
            }
        }
        
        // Trigger click event for existing functionality
        tab.click();
    }
    
    handleTimelineNavigation(e) {
        const timeline = e.target.closest('.tournament-timeline, [data-timeline]');
        if (!timeline) return;
        
        const items = Array.from(timeline.querySelectorAll('.timeline-item-interactive'));
        const currentIndex = items.indexOf(e.target);
        
        let targetIndex = currentIndex;
        
        switch (e.key) {
            case 'ArrowUp':
            case 'ArrowLeft':
                e.preventDefault();
                targetIndex = Math.max(0, currentIndex - 1);
                break;
            case 'ArrowDown':
            case 'ArrowRight':
                e.preventDefault();
                targetIndex = Math.min(items.length - 1, currentIndex + 1);
                break;
            case 'Home':
                e.preventDefault();
                targetIndex = 0;
                break;
            case 'End':
                e.preventDefault();
                targetIndex = items.length - 1;
                break;
        }
        
        if (targetIndex !== currentIndex) {
            items[targetIndex].focus();
        }
    }
    
    setupRovingTabindex() {
        // Setup roving tabindex for participant grids
        const participantGrids = document.querySelectorAll('.participant-grid');
        
        participantGrids.forEach(grid => {
            const cards = grid.querySelectorAll('.participant-card');
            if (cards.length === 0) return;
            
            // Set initial tabindex
            cards.forEach((card, index) => {
                card.setAttribute('tabindex', index === 0 ? '0' : '-1');
            });
            
            // Handle arrow key navigation
            grid.addEventListener('keydown', (e) => {
                if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;
                
                e.preventDefault();
                
                const currentCard = e.target;
                const currentIndex = Array.from(cards).indexOf(currentCard);
                const gridCols = this.getGridColumns(grid);
                
                let targetIndex = currentIndex;
                
                switch (e.key) {
                    case 'ArrowLeft':
                        targetIndex = Math.max(0, currentIndex - 1);
                        break;
                    case 'ArrowRight':
                        targetIndex = Math.min(cards.length - 1, currentIndex + 1);
                        break;
                    case 'ArrowUp':
                        targetIndex = Math.max(0, currentIndex - gridCols);
                        break;
                    case 'ArrowDown':
                        targetIndex = Math.min(cards.length - 1, currentIndex + gridCols);
                        break;
                }
                
                if (targetIndex !== currentIndex) {
                    currentCard.setAttribute('tabindex', '-1');
                    cards[targetIndex].setAttribute('tabindex', '0');
                    cards[targetIndex].focus();
                }
            });
        });
    }
    
    getGridColumns(grid) {
        const computedStyle = window.getComputedStyle(grid);
        const gridTemplateColumns = computedStyle.gridTemplateColumns;
        
        if (gridTemplateColumns && gridTemplateColumns !== 'none') {
            return gridTemplateColumns.split(' ').length;
        }
        
        // Fallback: estimate based on viewport
        const width = grid.offsetWidth;
        if (width < 480) return 1;
        if (width < 768) return 2;
        if (width < 1024) return 3;
        return 4;
    }
    
    setupSkipLinks() {
        // Create skip links if they don't exist
        if (!document.querySelector('.skip-link')) {
            const skipLinks = document.createElement('div');
            skipLinks.className = 'skip-links';
            skipLinks.innerHTML = `
                <a href="#main-content" class="skip-link">Skip to main content</a>
                <a href="#tournament-navigation" class="skip-link">Skip to navigation</a>
                <a href="#tournament-participants" class="skip-link">Skip to participants</a>
            `;
            
            document.body.insertBefore(skipLinks, document.body.firstChild);
        }
        
        // Ensure target elements have IDs
        this.ensureSkipTargets();
    }
    
    ensureSkipTargets() {
        const targets = [
            { selector: 'main, .main-content, .tournament-content', id: 'main-content' },
            { selector: '.tab-navigation, nav', id: 'tournament-navigation' },
            { selector: '.participant-grid, .participants', id: 'tournament-participants' }
        ];
        
        targets.forEach(({ selector, id }) => {
            const element = document.querySelector(selector);
            if (element && !element.id) {
                element.id = id;
            }
        });
    }
    
    /**
     * Setup ARIA live regions for dynamic content
     */
    setupLiveRegions() {
        // Create global live region if it doesn't exist
        if (!document.getElementById('accessibility-live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'accessibility-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            liveRegion.style.cssText = `
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            `;
            document.body.appendChild(liveRegion);
            
            this.ariaLiveRegions.set('global', liveRegion);
        }
        
        // Setup specific live regions for different content types
        this.setupStatusLiveRegion();
        this.setupProgressLiveRegion();
        
        this.log('ARIA live regions configured');
    }
    
    setupStatusLiveRegion() {
        const statusRegion = document.createElement('div');
        statusRegion.id = 'status-live-region';
        statusRegion.setAttribute('aria-live', 'assertive');
        statusRegion.setAttribute('aria-atomic', 'true');
        statusRegion.className = 'sr-only';
        statusRegion.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(statusRegion);
        
        this.ariaLiveRegions.set('status', statusRegion);
    }
    
    setupProgressLiveRegion() {
        const progressRegion = document.createElement('div');
        progressRegion.id = 'progress-live-region';
        progressRegion.setAttribute('aria-live', 'polite');
        progressRegion.setAttribute('aria-atomic', 'false');
        progressRegion.className = 'sr-only';
        progressRegion.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(progressRegion);
        
        this.ariaLiveRegions.set('progress', progressRegion);
    }
    
    /**
     * Announce message to screen readers
     */
    announceToScreenReader(message, type = 'global', priority = 'polite') {
        const liveRegion = this.ariaLiveRegions.get(type) || this.ariaLiveRegions.get('global');
        
        if (liveRegion) {
            // Set priority
            liveRegion.setAttribute('aria-live', priority);
            
            // Clear previous message
            liveRegion.textContent = '';
            
            // Add new message
            setTimeout(() => {
                liveRegion.textContent = message;
                
                // Clear after announcement
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }, 100);
        }
    }
    
    /**
     * Setup contrast support
     */
    setupContrastSupport() {
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');
        contrastQuery.addListener(this.handleContrastPreferenceChange);
        
        this.applyContrastPreferences();
        
        this.log(`Contrast preferences applied. High contrast: ${this.contrastPreference}`);
    }
    
    handleContrastPreferenceChange(e) {
        this.contrastPreference = e.matches;
        this.applyContrastPreferences();
        this.log(`Contrast preference changed. High contrast: ${this.contrastPreference}`);
    }
    
    applyContrastPreferences() {
        if (this.contrastPreference) {
            document.documentElement.classList.add('high-contrast');
        } else {
            document.documentElement.classList.remove('high-contrast');
        }
    }
    
    /**
     * Setup screen reader support
     */
    setupScreenReaderSupport() {
        // Add landmark roles
        this.setupLandmarkRoles();
        
        // Setup heading hierarchy
        this.validateHeadingHierarchy();
        
        // Setup table accessibility
        this.setupTableAccessibility();
        
        this.log('Screen reader support configured');
    }
    
    setupLandmarkRoles() {
        // Main content
        const main = document.querySelector('main');
        if (main && !main.getAttribute('role')) {
            main.setAttribute('role', 'main');
        }
        
        // Navigation
        const navs = document.querySelectorAll('nav');
        navs.forEach(nav => {
            if (!nav.getAttribute('role')) {
                nav.setAttribute('role', 'navigation');
            }
        });
        
        // Complementary content (sidebars)
        const sidebars = document.querySelectorAll('.sidebar, aside');
        sidebars.forEach(sidebar => {
            if (!sidebar.getAttribute('role')) {
                sidebar.setAttribute('role', 'complementary');
            }
        });
        
        // Content info (footers)
        const footers = document.querySelectorAll('footer');
        footers.forEach(footer => {
            if (!footer.getAttribute('role')) {
                footer.setAttribute('role', 'contentinfo');
            }
        });
    }
    
    validateHeadingHierarchy() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        
        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            
            // Check for skipped levels
            if (level > previousLevel + 1) {
                this.log(`Warning: Heading hierarchy skip detected at ${heading.tagName} (index ${index})`);
                
                // Add ARIA level to maintain semantic structure
                heading.setAttribute('aria-level', Math.min(level, previousLevel + 1));
            }
            
            previousLevel = level;
        });
    }
    
    setupTableAccessibility() {
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            // Add table role if missing
            if (!table.getAttribute('role')) {
                table.setAttribute('role', 'table');
            }
            
            // Setup headers
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                if (!header.id) {
                    header.id = `table-header-${index}`;
                }
                header.setAttribute('role', 'columnheader');
            });
            
            // Setup cells
            const cells = table.querySelectorAll('td');
            cells.forEach(cell => {
                cell.setAttribute('role', 'cell');
                
                // Associate with headers
                const headerIds = Array.from(headers).map(h => h.id).join(' ');
                if (headerIds) {
                    cell.setAttribute('headers', headerIds);
                }
            });
            
            // Add caption if missing
            if (!table.querySelector('caption')) {
                const caption = document.createElement('caption');
                caption.textContent = 'Tournament data table';
                caption.className = 'sr-only';
                table.insertBefore(caption, table.firstChild);
            }
        });
    }
    
    /**
     * Setup touch targets for mobile accessibility
     */
    setupTouchTargets() {
        const interactiveElements = document.querySelectorAll(`
            button,
            a,
            input,
            select,
            textarea,
            [tabindex]:not([tabindex="-1"]),
            [role="button"],
            .participant-card,
            .share-button,
            .tab-button
        `);
        
        interactiveElements.forEach(element => {
            this.ensureMinimumTouchTarget(element);
        });
        
        this.log(`Touch targets configured for ${interactiveElements.length} elements`);
    }
    
    ensureMinimumTouchTarget(element) {
        const rect = element.getBoundingClientRect();
        const minSize = 44; // WCAG minimum touch target size
        
        if (rect.width < minSize || rect.height < minSize) {
            // Add padding to reach minimum size
            const currentPadding = parseInt(window.getComputedStyle(element).padding) || 0;
            const neededPadding = Math.max(0, (minSize - Math.min(rect.width, rect.height)) / 2);
            
            if (neededPadding > currentPadding) {
                element.style.padding = `${neededPadding}px`;
                element.style.minWidth = `${minSize}px`;
                element.style.minHeight = `${minSize}px`;
            }
        }
    }
    
    /**
     * Public API methods
     */
    updateStatus(element, status, message) {
        // Update element status and announce to screen readers
        element.setAttribute('aria-label', message || this.getStatusAriaLabel(status));
        this.announceToScreenReader(message || `Status changed to ${status}`, 'status', 'assertive');
    }
    
    updateProgress(element, current, max, label) {
        // Update progress element and announce to screen readers
        element.setAttribute('aria-valuenow', current);
        element.setAttribute('aria-valuemax', max);
        
        const percentage = Math.round((current / max) * 100);
        const message = label ? `${label}: ${percentage}% complete` : `${percentage}% complete`;
        
        element.setAttribute('aria-label', message);
        this.announceToScreenReader(message, 'progress');
    }
    
    focusElement(element, options = {}) {
        // Focus element with enhanced accessibility
        if (element && typeof element.focus === 'function') {
            element.focus(options);
            
            // Ensure focus indicator is visible
            this.showFocusIndicator(element);
            
            // Announce focus change if requested
            if (options.announce) {
                const label = element.getAttribute('aria-label') || 
                             element.textContent?.trim() || 
                             'Element focused';
                this.announceToScreenReader(`Focused: ${label}`);
            }
        }
    }
    
    log(...args) {
        console.log('[AccessibilityCompliance]', ...args);
    }
    
    destroy() {
        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeyboardNavigation);
        
        const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        motionQuery.removeListener(this.handleMotionPreferenceChange);
        
        const contrastQuery = window.matchMedia('(prefers-contrast: high)');
        contrastQuery.removeListener(this.handleContrastPreferenceChange);
        
        // Clean up focus indicators
        this.focusIndicators.forEach(indicator => {
            if (indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        });
        this.focusIndicators.clear();
        
        // Clean up live regions
        this.ariaLiveRegions.forEach(region => {
            if (region.parentNode) {
                region.parentNode.removeChild(region);
            }
        });
        this.ariaLiveRegions.clear();
        
        // Remove added classes
        document.documentElement.classList.remove('reduce-motion', 'high-contrast');
        
        this.log('Accessibility Compliance destroyed');
    }
}

// Add CSS for accessibility enhancements
const accessibilityCSS = `
/* Accessibility Focus Indicators */
@keyframes accessibility-focus-pulse {
    0%, 100% { box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2), 0 0 8px rgba(59, 130, 246, 0.3); }
    50% { box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4), 0 0 12px rgba(59, 130, 246, 0.5); }
}

/* Skip Links */
.skip-links {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 10000;
}

.skip-link {
    position: absolute;
    top: -40px;
    left: 6px;
    background: #1f2937;
    color: white;
    padding: 8px 12px;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 600;
    transition: top 0.3s ease;
}

.skip-link:focus {
    top: 6px;
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}

/* Screen Reader Only */
.sr-only {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}

/* Reduced Motion Support */
.reduce-motion *,
.reduce-motion *::before,
.reduce-motion *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
}

/* High Contrast Support */
.high-contrast {
    --border-white-10: rgba(255, 255, 255, 0.3);
    --border-white-20: rgba(255, 255, 255, 0.5);
}

.high-contrast .card,
.high-contrast .bg-gray-800,
.high-contrast .status-badge {
    border-width: 2px !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
}

.high-contrast button,
.high-contrast .btn {
    border: 2px solid currentColor !important;
}

/* Progress Indicators */
.progress-low::before { content: "🔴"; margin-right: 8px; }
.progress-medium::before { content: "🟡"; margin-right: 8px; }
.progress-high::before { content: "🟢"; margin-right: 8px; }

/* Status Icons */
.status-icon {
    margin-right: 4px;
    font-size: 0.875em;
}

/* Color Indicators */
.color-indicator {
    margin-right: 4px;
    font-size: 0.75em;
}

/* Touch Target Improvements */
@media (pointer: coarse) {
    button,
    a,
    [role="button"],
    [tabindex]:not([tabindex="-1"]) {
        min-height: 44px;
        min-width: 44px;
    }
}

/* Focus Management */
.accessibility-focus-indicator {
    pointer-events: none;
    z-index: 9999;
}

/* Print Accessibility */
@media print {
    .skip-links,
    .accessibility-focus-indicator {
        display: none !important;
    }
    
    .sr-only {
        position: static !important;
        width: auto !important;
        height: auto !important;
        padding: inherit !important;
        margin: inherit !important;
        overflow: visible !important;
        clip: auto !important;
        white-space: normal !important;
        border: inherit !important;
    }
}
`;

// Inject CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = accessibilityCSS;
document.head.appendChild(styleSheet);

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.AccessibilityCompliance) {
        window.AccessibilityCompliance = new AccessibilityCompliance();
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.AccessibilityCompliance && window.AccessibilityCompliance.destroy) {
        window.AccessibilityCompliance.destroy();
    }
});

export default AccessibilityCompliance;