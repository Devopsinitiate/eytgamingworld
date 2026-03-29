/**
 * SeedingManager - Manages manual seeding interface for tournaments
 * 
 * Provides functionality for:
 * - Loading and displaying participants
 * - Drag-and-drop reordering
 * - Manual seed input
 * - Saving seed assignments
 * - Auto-seeding by registration order
 */
export class SeedingManager {
  /**
   * Initialize the SeedingManager
   * @param {string} tournamentSlug - The tournament slug identifier
   * @param {string} tournamentStatus - The tournament status (draft, registration, check_in, in_progress, completed)
   */
  constructor(tournamentSlug, tournamentStatus = 'draft') {
    this.tournamentSlug = tournamentSlug;
    this.tournamentStatus = tournamentStatus;
    this.participants = [];
    this.hasChanges = false;
    this.draggedElement = null;
    this.isLocked = this.tournamentStatus === 'in_progress' || this.tournamentStatus === 'completed';
    this.init();
  }
  
  /**
   * Initialize the seeding manager
   * Orchestrates setup of all components
   */
  async init() {
    await this.loadParticipants();
    this.setupDragAndDrop();
    this.setupEventListeners();
    this.render();
  }
  
  /**
   * Load participants from API
   * Fetches all confirmed participants for the tournament
   */
  async loadParticipants() {
    try {
      // Fetch all confirmed participants (no pagination needed for seeding)
      const response = await fetch(
        `/tournaments/${this.tournamentSlug}/api/participants/?status=confirmed&per_page=100`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Filter to only confirmed participants (double-check)
      this.participants = data.participants.filter(p => p.status === 'confirmed');
      
      console.log(`Loaded ${this.participants.length} confirmed participants`);
    } catch (error) {
      console.error('Failed to load participants:', error);
      this.showError('Failed to load participants. Please refresh the page.');
      this.participants = [];
    }
  }
  
  /**
   * Set up HTML5 drag and drop event handlers
   * Enables drag-and-drop reordering of seeded participants
   * Skips setup if tournament is locked (in_progress or completed)
   */
  setupDragAndDrop() {
    // Skip drag-and-drop setup if tournament is locked
    if (this.isLocked) {
      console.log('Tournament is locked, drag-and-drop disabled');
      return;
    }
    
    const seededList = document.getElementById('seeded-list');
    
    if (!seededList) {
      console.warn('Seeded list element not found, skipping drag-and-drop setup');
      return;
    }
    
    // Dragstart: Set the dragged element and add visual feedback
    seededList.addEventListener('dragstart', (e) => {
      if (e.target.classList.contains('participant-row')) {
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
      }
    });
    
    // Dragend: Remove visual feedback and clear dragged element
    seededList.addEventListener('dragend', (e) => {
      if (e.target.classList.contains('participant-row')) {
        e.target.classList.remove('dragging');
        this.draggedElement = null;
      }
    });
    
    // Dragover: Prevent default and position the dragged element
    seededList.addEventListener('dragover', (e) => {
      e.preventDefault();
      
      if (!this.draggedElement) {
        return;
      }
      
      const afterElement = this.getDragAfterElement(seededList, e.clientY);
      
      if (afterElement == null) {
        seededList.appendChild(this.draggedElement);
      } else {
        seededList.insertBefore(this.draggedElement, afterElement);
      }
    });
    
    // Drop: Trigger seed recalculation
    seededList.addEventListener('drop', (e) => {
      e.preventDefault();
      this.recalculateSeeds();
      this.hasChanges = true;
      this.render();
    });
  }
  
  /**
   * Get the element that the dragged item should be inserted before
   * Calculates drop position based on mouse Y coordinate
   * @param {HTMLElement} container - The container element
   * @param {number} y - Mouse Y coordinate
   * @returns {HTMLElement|null} Element to insert before, or null to append
   */
  getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.participant-row:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }
  
  /**
   * Recalculate seeds based on current DOM order
   * Assigns seeds 1, 2, 3... based on visual order from top to bottom
   * Updates participant objects with new seed values
   * Sets hasChanges flag to true
   */
  recalculateSeeds() {
    const seededList = document.getElementById('seeded-list');
    
    if (!seededList) {
      console.warn('Seeded list element not found, cannot recalculate seeds');
      return;
    }
    
    const rows = seededList.querySelectorAll('.participant-row');
    
    rows.forEach((row, index) => {
      const participantId = row.dataset.participantId;
      const participant = this.participants.find(p => p.id === participantId);
      
      if (participant) {
        participant.seed = index + 1;
      }
    });
    
    this.hasChanges = true;
  }
  
  /**
   * Set up event listeners for UI interactions
   */
  setupEventListeners() {
    // Save button
    const saveBtn = document.getElementById('save-seeds-btn');
    if (saveBtn) {
      if (this.isLocked) {
        saveBtn.disabled = true;
        saveBtn.title = 'Seeding is locked - tournament has started';
      } else {
        saveBtn.addEventListener('click', () => this.saveSeeds());
      }
    }
    
    // Auto-seed button
    const autoSeedBtn = document.getElementById('auto-seed-btn');
    if (autoSeedBtn) {
      if (this.isLocked) {
        autoSeedBtn.disabled = true;
        autoSeedBtn.title = 'Seeding is locked - tournament has started';
      } else {
        autoSeedBtn.addEventListener('click', () => this.autoSeed());
      }
    }
    
    // Seed input changes (using event delegation)
    // Only set up if tournament is not locked
    if (!this.isLocked) {
      document.addEventListener('input', (e) => {
        if (e.target.classList.contains('seed-input')) {
          this.handleSeedInput(e);
        }
      });
    }
  }
  
  /**
   * Handle seed input changes
   * @param {Event} e - Input event
   */
  handleSeedInput(e) {
    const participantId = e.target.closest('.participant-row').dataset.participantId;
    const participant = this.participants.find(p => p.id === participantId);
    const value = parseInt(e.target.value);
    
    if (participant) {
      if (value > 0 || e.target.value === '') {
        participant.seed = value > 0 ? value : null;
        this.hasChanges = true;
        this.detectConflicts();
      } else {
        // Invalid value, reset to previous
        e.target.value = participant.seed || '';
      }
    }
  }
  
  /**
   * Detect and display seed conflicts (duplicate seeds)
   */
  detectConflicts() {
    const seededParticipants = this.participants.filter(p => p.seed !== null);
    const seedCounts = {};
    
    seededParticipants.forEach(p => {
      seedCounts[p.seed] = (seedCounts[p.seed] || 0) + 1;
    });
    
    const duplicates = Object.keys(seedCounts).filter(seed => seedCounts[seed] > 1);
    
    const conflictsDiv = document.getElementById('seed-conflicts');
    const conflictDetails = document.getElementById('conflict-details');
    
    if (duplicates.length > 0) {
      conflictsDiv.style.display = 'flex';
      conflictDetails.textContent = duplicates.join(', ');
    } else {
      conflictsDiv.style.display = 'none';
    }
  }
  
  /**
   * Get CSRF token for API requests
   * @returns {string} CSRF token
   */
  getCSRFToken() {
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (tokenInput) {
      return tokenInput.value;
    }
    
    const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
    return cookieMatch ? cookieMatch[1] : '';
  }
  
  /**
   * Show success message to user
   * @param {string} message - Success message
   */
  showSuccess(message) {
    // TODO: Implement toast notification system
    alert(message);
  }
  
  /**
   * Show error message to user
   * @param {string} message - Error message
   */
  showError(message) {
    // TODO: Implement toast notification system
    alert('Error: ' + message);
  }
  
  /**
   * Render the seeding interface
   * Updates DOM with current participant state
   * Shows lock message if tournament has started
   */
  render() {
    // Show/hide lock message based on tournament status
    this.renderLockMessage();
    
    // Separate participants into seeded and unseeded
    const seededParticipants = this.participants
      .filter(p => p.seed !== null)
      .sort((a, b) => a.seed - b.seed);
    
    const unseededParticipants = this.participants
      .filter(p => p.seed === null);
    
    // Update counts
    const seededCount = document.getElementById('seeded-count');
    const unseededCount = document.getElementById('unseeded-count');
    
    if (seededCount) {
      seededCount.textContent = seededParticipants.length;
    }
    
    if (unseededCount) {
      unseededCount.textContent = unseededParticipants.length;
    }
    
    // Render seeded list (not draggable if locked)
    const seededList = document.getElementById('seeded-list');
    if (seededList) {
      seededList.innerHTML = seededParticipants
        .map(p => this.renderParticipantRow(p, !this.isLocked))
        .join('');
    }
    
    // Render unseeded list (never draggable)
    const unseededList = document.getElementById('unseeded-list');
    if (unseededList) {
      unseededList.innerHTML = unseededParticipants
        .map(p => this.renderParticipantRow(p, false))
        .join('');
    }
    
    // Detect conflicts after rendering (only if not locked)
    if (!this.isLocked) {
      this.detectConflicts();
    }
  }
  
  /**
   * Render lock message if tournament has started
   * Shows informational message indicating seeding is locked
   */
  renderLockMessage() {
    // Check if lock message already exists
    let lockMessage = document.getElementById('seeding-lock-message');
    
    if (this.isLocked) {
      // Create lock message if it doesn't exist
      if (!lockMessage) {
        lockMessage = document.createElement('div');
        lockMessage.id = 'seeding-lock-message';
        lockMessage.className = 'alert alert-info';
        lockMessage.innerHTML = `
          <span class="material-symbols-outlined">lock</span>
          <div class="alert-content">
            <strong>Seeding Locked:</strong> The tournament has started. Seed assignments can no longer be modified.
          </div>
        `;
        
        // Insert after the header
        const header = document.querySelector('.seeding-header');
        if (header) {
          header.after(lockMessage);
        }
      }
    } else {
      // Remove lock message if it exists and tournament is not locked
      if (lockMessage) {
        lockMessage.remove();
      }
    }
  }
  
  /**
   * Render a single participant row
   * @param {Object} participant - Participant data
   * @param {boolean} draggable - Whether the row should be draggable
   * @returns {string} HTML string for participant row
   */
  renderParticipantRow(participant, draggable = true) {
    const seedValue = participant.seed !== null ? participant.seed : '';
    const dragHandle = draggable ? '<span class="drag-handle">⋮⋮</span>' : '';
    const draggableAttr = draggable ? 'draggable="true"' : '';
    const disabledAttr = !draggable ? 'disabled' : '';
    
    return `
      <div class="participant-row" data-participant-id="${participant.id}" ${draggableAttr}>
        ${dragHandle}
        <input type="number" class="seed-input" value="${seedValue}" min="1" ${disabledAttr} />
        <span class="participant-name">${this.escapeHtml(participant.display_name)}</span>
        <span class="participant-status">${participant.status}</span>
      </div>
    `;
  }
  
  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  /**
   * Save seed assignments to the server
   * Collects seed assignments from participant state and POSTs to API
   */
  async saveSeeds() {
    if (!this.hasChanges) {
      this.showSuccess('No changes to save.');
      return;
    }
    
    try {
      // Collect seed assignments from participant state
      const seeds = this.participants.map(p => ({
        participant_id: p.id,
        seed: p.seed
      }));
      
      // POST to API endpoint
      const response = await fetch(
        `/api/tournaments/${this.tournamentSlug}/participants/seed/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify({ seeds })
        }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        // Handle error response
        const errorMessage = data.error || 'Failed to save seeds';
        const details = data.details ? JSON.stringify(data.details) : '';
        this.showError(`${errorMessage}${details ? ': ' + details : ''}`);
        return;
      }
      
      // Handle success response
      if (data.success) {
        this.showSuccess(data.message || 'Seeds saved successfully');
        
        // Update state with response data if provided
        if (data.participants) {
          this.participants = data.participants;
        }
        
        // Reset hasChanges flag
        this.hasChanges = false;
        
        // Re-render interface
        this.render();
      }
    } catch (error) {
      console.error('Failed to save seeds:', error);
      this.showError('Failed to save seeds. Please try again.');
    }
  }
  
  /**
   * Auto-seed participants by registration order
   * Shows confirmation dialog before proceeding
   */
  async autoSeed() {
    // Show confirmation dialog before proceeding
    const confirmed = confirm(
      'This will automatically assign seeds based on registration order. ' +
      'Any existing seed assignments will be overwritten. Continue?'
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      // POST to auto-seed API endpoint
      const response = await fetch(
        `/api/tournaments/${this.tournamentSlug}/participants/auto-seed/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify({ method: 'registration_order' })
        }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        // Handle error response
        const errorMessage = data.error || 'Failed to auto-seed participants';
        this.showError(errorMessage);
        return;
      }
      
      // Handle success response
      if (data.success) {
        this.showSuccess(data.message || 'Auto-seeding completed successfully');
        
        // Update participants with new seed values
        if (data.participants) {
          this.participants = data.participants;
        }
        
        // Reset hasChanges flag
        this.hasChanges = false;
        
        // Re-render interface with new seed values
        this.render();
      }
    } catch (error) {
      console.error('Failed to auto-seed:', error);
      this.showError('Failed to auto-seed participants. Please try again.');
    }
  }
}
