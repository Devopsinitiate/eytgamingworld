# Tabbed Navigation System Implementation Guide

## Status: READY FOR IMPLEMENTATION

Task 9 from the tournament detail UI enhancement spec requires a complete tabbed navigation system. This document provides the complete implementation guide.

## Requirements (from task 9)

- Create smooth scrolling tab navigation
- Implement URL hash updates for direct linking
- Add proper typography and formatting for rules section
- Build format-specific information display
- Create responsive tab behavior for mobile
- _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

## Implementation Components

### 1. HTML Template Addition

**Location**: Add after the social sharing section in `templates/tournaments/tournament_detail_enhanced.html`

```html
<!-- Enhanced Tabbed Navigation System -->
<section class="tournament-card" id="tabbed-content" aria-labelledby="tabs-heading">
    <h2 id="tabs-heading" class="sr-only">Tournament Information Tabs</h2>
    
    <div class="tab-navigation" role="tablist" aria-label="Tournament information tabs">
        <div class="tab-container" id="tab-container">
            <button class="tab-button active" 
                    data-tab="details" 
                    role="tab" 
                    aria-selected="true" 
                    aria-controls="details-tab"
                    id="details-tab-button"
                    tabindex="0">
                <svg class="tab-icon w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path>
                </svg>
                <span class="tab-text">Details</span>
            </button>
            
            {% if tournament.status == 'in_progress' or tournament.status == 'completed' %}
            <button class="tab-button" 
                    data-tab="bracket" 
                    role="tab" 
                    aria-selected="false" 
                    aria-controls="bracket-tab"
                    id="bracket-tab-button"
                    tabindex="-1">
                <svg class="tab-icon w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"></path>
                </svg>
                <span class="tab-text">Bracket</span>
            </button>
            {% endif %}
            
            <button class="tab-button" 
                    data-tab="rules" 
                    role="tab" 
                    aria-selected="false" 
                    aria-controls="rules-tab"
                    id="rules-tab-button"
                    tabindex="-1">
                <svg class="tab-icon w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fill-rule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clip-rule="evenodd"></path>
                    <path fill-rule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clip-rule="evenodd"></path>
                </svg>
                <span class="tab-text">Rules</span>
            </button>
            
            <button class="tab-button" 
                    data-tab="prizes" 
                    role="tab" 
                    aria-selected="false" 
                    aria-controls="prizes-tab"
                    id="prizes-tab-button"
                    tabindex="-1">
                <svg class="tab-icon w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9.5 9.293 8.207a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L11 9.586z" clip-rule="evenodd"></path>
                </svg>
                <span class="tab-text">Prizes</span>
            </button>
            
            <button class="tab-button" 
                    data-tab="participants" 
                    role="tab" 
                    aria-selected="false" 
                    aria-controls="participants-tab"
                    id="participants-tab-button"
                    tabindex="-1">
                <svg class="tab-icon w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"></path>
                </svg>
                <span class="tab-text">Participants</span>
                <span class="tab-badge">{{ tournament.total_registered }}</span>
            </button>
        </div>
        
        <!-- Mobile Tab Scroll Indicators -->
        <div class="tab-scroll-indicators">
            <button class="scroll-indicator left" id="scroll-left" aria-label="Scroll tabs left">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
            </button>
            <button class="scroll-indicator right" id="scroll-right" aria-label="Scroll tabs right">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
            </button>
        </div>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
        <!-- Details Tab -->
        <div id="details-tab" 
             class="tab-pane active" 
             role="tabpanel" 
             aria-labelledby="details-tab-button"
             tabindex="0">
            <div class="tab-content-header">
                <h3 class="text-2xl font-bold text-white mb-2">About the Tournament</h3>
                <p class="text-gray-400 text-sm">
                    Learn more about this tournament, its format, and what to expect.
                </p>
            </div>
            
            <div class="tournament-details-content mt-6">
                {% if tournament.description %}
                <div class="description-section mb-8">
                    <h4 class="text-lg font-semibold text-white mb-4">Description</h4>
                    <div class="prose prose-invert max-w-none">
                        <div class="text-gray-300 leading-relaxed space-y-4 bg-gray-800/30 p-6 rounded-lg border border-white/10">
                            {{ tournament.description|linebreaks }}
                        </div>
                    </div>
                </div>
                {% endif %}
                
                <!-- Tournament Format Information -->
                <div class="format-section mb-8">
                    <h4 class="text-lg font-semibold text-white mb-4">Tournament Format</h4>
                    <div class="format-info bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 rounded-lg p-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="format-detail">
                                <div class="text-sm text-gray-400 mb-1">Format Type</div>
                                <div class="text-lg font-semibold text-white">{{ tournament.get_format_display }}</div>
                            </div>
                            
                            <div class="format-detail">
                                <div class="text-sm text-gray-400 mb-1">Tournament Type</div>
                                <div class="text-lg font-semibold text-white">{{ tournament.get_tournament_type_display }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bracket Tab -->
        {% if tournament.status == 'in_progress' or tournament.status == 'completed' %}
        <div id="bracket-tab" 
             class="tab-pane" 
             role="tabpanel" 
             aria-labelledby="bracket-tab-button"
             tabindex="0">
            <div class="tab-content-header">
                <h3 class="text-2xl font-bold text-white mb-2">Tournament Bracket</h3>
                <p class="text-gray-400 text-sm">
                    View the complete tournament bracket and match results.
                </p>
            </div>
            
            <div class="bracket-content mt-6">
                <div class="text-center py-8">
                    <a href="{% url 'tournaments:bracket' tournament.slug %}" 
                       class="inline-flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition">
                        View Full Bracket
                        <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- Rules Tab -->
        <div id="rules-tab" 
             class="tab-pane" 
             role="tabpanel" 
             aria-labelledby="rules-tab-button"
             tabindex="0">
            <div class="tab-content-header">
                <h3 class="text-2xl font-bold text-white mb-2">Tournament Rules</h3>
                <p class="text-gray-400 text-sm">
                    Important rules and guidelines that all participants must follow.
                </p>
            </div>
            
            <div class="rules-content mt-6">
                {% if tournament.rules %}
                <div class="rules-text bg-gray-800/50 p-6 rounded-lg border border-white/10">
                    <div class="prose prose-invert max-w-none">
                        <div class="text-gray-300 leading-relaxed space-y-4">
                            {{ tournament.rules|linebreaks }}
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="text-center py-12">
                    <p class="text-gray-400">No specific rules have been set for this tournament.</p>
                    <p class="text-sm text-gray-500 mt-2">Standard game rules apply.</p>
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Prizes Tab -->
        <div id="prizes-tab" 
             class="tab-pane" 
             role="tabpanel" 
             aria-labelledby="prizes-tab-button"
             tabindex="0">
            <div class="tab-content-header">
                <h3 class="text-2xl font-bold text-white mb-2">Prize Pool</h3>
                <p class="text-gray-400 text-sm">
                    Prize distribution and rewards for tournament placements.
                </p>
            </div>
            
            <div class="prizes-content mt-6">
                {% if tournament.prize_pool > 0 %}
                <div class="text-center mb-6">
                    <div class="text-4xl font-bold text-yellow-400">${{ tournament.prize_pool }}</div>
                    <div class="text-sm text-gray-400">Total Prize Pool</div>
                </div>
                {% else %}
                <div class="text-center py-12">
                    <p class="text-gray-400">No prize pool for this tournament.</p>
                    <p class="text-sm text-yellow-400 mt-2">Compete for Glory & Bragging Rights!</p>
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Participants Tab -->
        <div id="participants-tab" 
             class="tab-pane" 
             role="tabpanel" 
             aria-labelledby="participants-tab-button"
             tabindex="0">
            <div class="tab-content-header">
                <h3 class="text-2xl font-bold text-white mb-2">
                    Registered Participants ({{ tournament.total_registered }}/{{ tournament.max_participants }})
                </h3>
                <p class="text-gray-400 text-sm">
                    View all registered participants for this tournament.
                </p>
            </div>
            
            <div class="participants-content mt-6">
                <p class="text-gray-400 text-center py-8">
                    Participant list will be displayed here.
                </p>
            </div>
        </div>
    </div>
</section>
```

### 2. CSS Styles Addition

**Location**: Add to `static/css/tournament-detail.scss`

```scss
// Enhanced Tabbed Navigation System Styles
.tab-navigation {
  position: relative;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 2rem;
  
  .tab-container {
    display: flex;
    gap: 0.5rem;
    overflow-x: auto;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
    padding: 0 1rem 1rem;
    
    // Hide scrollbar
    -ms-overflow-style: none;
    scrollbar-width: none;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }
  
  .tab-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: transparent;
    border: 2px solid transparent;
    border-radius: 0.75rem 0.75rem 0 0;
    color: #9ca3af;
    font-weight: 500;
    font-size: 0.875rem;
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    
    &:hover:not(.active) {
      color: #d1d5db;
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.1);
    }
    
    &.active {
      color: #ffffff;
      background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%);
      border-color: #dc2626;
      box-shadow: 0 4px 12px rgba(185, 28, 28, 0.3);
      
      .tab-badge {
        background: rgba(255, 255, 255, 0.2);
        color: #ffffff;
      }
    }
    
    &:focus {
      outline: none;
      border-color: #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .tab-icon {
      flex-shrink: 0;
    }
    
    .tab-badge {
      margin-left: 0.5rem;
      padding: 0.125rem 0.5rem;
      background: rgba(156, 163, 175, 0.2);
      color: #9ca3af;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      transition: all 0.3s ease;
    }
  }
  
  .tab-scroll-indicators {
    display: none;
    
    @media (max-width: 768px) {
      display: block;
    }
    
    .scroll-indicator {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 2rem;
      height: 2rem;
      background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-center;
      color: #9ca3af;
      cursor: pointer;
      transition: all 0.3s ease;
      z-index: 10;
      
      &:hover {
        color: #ffffff;
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
        border-color: rgba(255, 255, 255, 0.2);
      }
      
      &.left {
        left: 0;
      }
      
      &.right {
        right: 0;
      }
      
      &:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }
    }
  }
}

.tab-content {
  .tab-pane {
    display: none;
    opacity: 0;
    transform: translateY(10px);
    transition: all 0.3s ease;
    
    &.active {
      display: block;
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .tab-content-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 1rem;
    margin-bottom: 2rem;
  }
}

// Responsive design
@media (max-width: 768px) {
  .tab-navigation {
    .tab-container {
      padding: 0 2rem 1rem;
    }
    
    .tab-button {
      padding: 0.625rem 1rem;
      font-size: 0.8rem;
      
      .tab-icon {
        width: 1rem;
        height: 1rem;
      }
    }
  }
}
```

### 3. JavaScript Implementation

**Location**: Add to `static/js/tournament-detail.js`

```javascript
// Enhanced Tabbed Navigation System Component
class TabbedNavigation {
    constructor() {
        this.tabContainer = document.getElementById('tabbed-content');
        this.tabButtons = null;
        this.tabPanes = null;
        this.scrollContainer = null;
        this.scrollIndicators = null;
        this.currentTab = 'details';
        this.init();
    }

    init() {
        if (!this.tabContainer) return;
        
        this.tabButtons = this.tabContainer.querySelectorAll('.tab-button');
        this.tabPanes = this.tabContainer.querySelectorAll('.tab-pane');
        this.scrollContainer = document.getElementById('tab-container');
        this.scrollIndicators = {
            left: document.getElementById('scroll-left'),
            right: document.getElementById('scroll-right')
        };
        
        this.setupTabSwitching();
        this.setupKeyboardNavigation();
        this.setupURLHashHandling();
        this.setupMobileScrolling();
        this.handleInitialHash();
        
        console.log('Enhanced Tabbed Navigation initialized');
    }

    setupTabSwitching() {
        this.tabButtons.forEach((button) => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = button.dataset.tab;
                this.switchTab(targetTab);
            });
        });
    }

    setupKeyboardNavigation() {
        this.tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                let targetIndex = index;
                
                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        targetIndex = index > 0 ? index - 1 : this.tabButtons.length - 1;
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        targetIndex = index < this.tabButtons.length - 1 ? index + 1 : 0;
                        break;
                    case 'Home':
                        e.preventDefault();
                        targetIndex = 0;
                        break;
                    case 'End':
                        e.preventDefault();
                        targetIndex = this.tabButtons.length - 1;
                        break;
                    default:
                        return;
                }
                
                this.tabButtons[targetIndex].focus();
                this.scrollTabIntoView(this.tabButtons[targetIndex]);
            });
        });
    }

    setupURLHashHandling() {
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.substring(1);
            if (hash && this.isValidTab(hash)) {
                this.switchTab(hash, false);
            }
        });
    }

    setupMobileScrolling() {
        if (!this.scrollContainer || !this.scrollIndicators.left || !this.scrollIndicators.right) return;
        
        this.scrollIndicators.left.addEventListener('click', () => {
            this.scrollTabs('left');
        });
        
        this.scrollIndicators.right.addEventListener('click', () => {
            this.scrollTabs('right');
        });
        
        this.scrollContainer.addEventListener('scroll', () => {
            this.updateScrollIndicators();
        });
        
        this.updateScrollIndicators();
    }

    switchTab(targetTab, updateURL = true) {
        if (targetTab === this.currentTab) return;
        
        const targetButton = this.tabContainer.querySelector(`[data-tab="${targetTab}"]`);
        const targetPane = document.getElementById(`${targetTab}-tab`);
        
        if (!targetButton || !targetPane) return;
        
        this.currentTab = targetTab;
        
        // Update button states
        this.tabButtons.forEach(btn => {
            btn.classList.remove('active');
            btn.setAttribute('aria-selected', 'false');
            btn.setAttribute('tabindex', '-1');
        });
        
        // Update pane states
        this.tabPanes.forEach(pane => {
            pane.classList.remove('active');
            pane.setAttribute('aria-hidden', 'true');
        });
        
        // Activate target
        targetButton.classList.add('active');
        targetButton.setAttribute('aria-selected', 'true');
        targetButton.setAttribute('tabindex', '0');
        
        targetPane.classList.add('active');
        targetPane.setAttribute('aria-hidden', 'false');
        
        // Update URL
        if (updateURL) {
            window.history.pushState(null, null, `#${targetTab}`);
        }
        
        // Scroll tab into view
        this.scrollTabIntoView(targetButton);
        
        // Focus pane
        targetPane.focus();
    }

    scrollTabs(direction) {
        if (!this.scrollContainer) return;
        
        const scrollAmount = 200;
        const currentScroll = this.scrollContainer.scrollLeft;
        
        if (direction === 'left') {
            this.scrollContainer.scrollTo({
                left: currentScroll - scrollAmount,
                behavior: 'smooth'
            });
        } else {
            this.scrollContainer.scrollTo({
                left: currentScroll + scrollAmount,
                behavior: 'smooth'
            });
        }
    }

    scrollTabIntoView(button) {
        if (!this.scrollContainer || !button) return;
        
        const containerRect = this.scrollContainer.getBoundingClientRect();
        const buttonRect = button.getBoundingClientRect();
        
        const isVisible = buttonRect.left >= containerRect.left && 
                         buttonRect.right <= containerRect.right;
        
        if (!isVisible) {
            const scrollLeft = button.offsetLeft - (this.scrollContainer.offsetWidth / 2) + (button.offsetWidth / 2);
            
            this.scrollContainer.scrollTo({
                left: scrollLeft,
                behavior: 'smooth'
            });
        }
    }

    updateScrollIndicators() {
        if (!this.scrollContainer || !this.scrollIndicators.left || !this.scrollIndicators.right) return;
        
        const { scrollLeft, scrollWidth, clientWidth } = this.scrollContainer;
        const maxScroll = scrollWidth - clientWidth;
        
        this.scrollIndicators.left.disabled = scrollLeft <= 0;
        this.scrollIndicators.right.disabled = scrollLeft >= maxScroll - 1;
    }

    handleInitialHash() {
        const hash = window.location.hash.substring(1);
        if (hash && this.isValidTab(hash)) {
            this.switchTab(hash, false);
        }
    }

    isValidTab(tabName) {
        return Array.from(this.tabButtons).some(button => button.dataset.tab === tabName);
    }

    handleResize() {
        this.updateScrollIndicators();
        
        const activeButton = this.tabContainer.querySelector('.tab-button.active');
        if (activeButton) {
            setTimeout(() => {
                this.scrollTabIntoView(activeButton);
            }, 100);
        }
    }
}

// Initialize in main controller
// Add to TournamentDetailPage.init():
// this.components.tabs = new TabbedNavigation();
```

### 4. Template Filters Addition

**Location**: Add to `tournaments/templatetags/tournament_extras.py`

```python
@register.filter
def tournament_rounds(participants):
    """Calculate number of rounds for single elimination tournament"""
    try:
        import math
        return math.ceil(math.log2(int(participants)))
    except (ValueError, TypeError):
        return 1

@register.filter
def round_robin_matches(participants):
    """Calculate total matches for round robin tournament"""
    try:
        n = int(participants)
        return (n * (n - 1)) // 2
    except (ValueError, TypeError):
        return 0
```

## Implementation Steps

1. **Add HTML Template**: Insert the tabbed navigation HTML after the social sharing section
2. **Add CSS Styles**: Append the SCSS styles to the tournament-detail.scss file
3. **Add JavaScript**: Add the TabbedNavigation class to tournament-detail.js
4. **Initialize Component**: Add `this.components.tabs = new TabbedNavigation();` to the main controller
5. **Add Template Filters**: Add the helper filters to tournament_extras.py
6. **Test**: Verify all tabs work, URL hashing functions, and mobile scrolling works

## Testing Checklist

- [ ] All tabs switch correctly when clicked
- [ ] URL hash updates when switching tabs
- [ ] Direct links with hash work (e.g., #rules)
- [ ] Keyboard navigation works (Arrow keys, Home, End)
- [ ] Mobile scroll indicators appear and function
- [ ] Touch/swipe works on mobile
- [ ] ARIA attributes are correct
- [ ] Focus management works properly
- [ ] Smooth animations on tab transitions
- [ ] Responsive design works on all screen sizes

## Completion Criteria

Task 9 will be considered complete when:
1. All HTML, CSS, and JavaScript components are added
2. All tabs are functional and accessible
3. URL hash routing works correctly
4. Mobile responsive behavior is implemented
5. All testing checklist items pass

---

**Status**: Ready for implementation
**Priority**: High
**Estimated Time**: 2-3 hours for full implementation and testing
