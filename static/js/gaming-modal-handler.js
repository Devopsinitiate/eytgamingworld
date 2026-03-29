/**
 * Gaming Modal Handler
 * Handles modal interactions with gaming-style animations
 * Includes fade-out animations, keyboard handlers, background click handlers,
 * and screen reader announcements for accessibility
 */

(function() {
  'use strict';

  // Animation duration (should match CSS transition-normal)
  const ANIMATION_DURATION = 300; // milliseconds

  /**
   * Create ARIA live region for screen reader announcements
   * Requirements: 9.4 - Screen reader announcements for status changes
   */
  function createARIALiveRegion() {
    let liveRegion = document.getElementById('aria-live-announcer');
    
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'aria-live-announcer';
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.style.position = 'absolute';
      liveRegion.style.left = '-10000px';
      liveRegion.style.width = '1px';
      liveRegion.style.height = '1px';
      liveRegion.style.overflow = 'hidden';
      document.body.appendChild(liveRegion);
    }
    
    return liveRegion;
  }

  /**
   * Announce message to screen readers
   * @param {string} message - The message to announce
   */
  function announceToScreenReader(message) {
    const liveRegion = createARIALiveRegion();
    
    // Clear previous message
    liveRegion.textContent = '';
    
    // Set new message after a brief delay to ensure screen readers detect the change
    setTimeout(() => {
      liveRegion.textContent = message;
    }, 100);
    
    // Clear message after it's been announced
    setTimeout(() => {
      liveRegion.textContent = '';
    }, 3000);
  }

  /**
   * Close modal with fade-out animation
   * @param {HTMLElement} modalElement - The modal element to close
   */
  function closeModalWithAnimation(modalElement) {
    if (!modalElement || modalElement.classList.contains('hidden')) {
      return;
    }

    // Add closing class to trigger fade-out animation
    modalElement.classList.add('closing');
    
    // Find the modal content inside the backdrop
    const modalContent = modalElement.querySelector('.gaming-modal, [class*="bg-[#1F2937]"]');
    if (modalContent) {
      modalContent.classList.add('closing');
    }

    // Wait for animation to complete before hiding
    setTimeout(() => {
      modalElement.classList.add('hidden');
      modalElement.classList.remove('closing');
      if (modalContent) {
        modalContent.classList.remove('closing');
      }
      
      // Reset form if present
      const form = modalElement.querySelector('form');
      if (form) {
        form.reset();
      }
    }, ANIMATION_DURATION);
  }

  /**
   * Open modal with fade-in animation
   * @param {HTMLElement} modalElement - The modal element to open
   */
  function openModalWithAnimation(modalElement) {
    if (!modalElement) {
      return;
    }

    // Remove hidden class to trigger fade-in animation
    modalElement.classList.remove('hidden');
  }

  /**
   * Initialize status change observers for screen reader announcements
   */
  function initializeStatusChangeObserver() {
    // Create ARIA live region on initialization
    createARIALiveRegion();
    
    // Observe status changes in the participant table
    const participantTable = document.querySelector('.gaming-table tbody');
    if (participantTable) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' || mutation.type === 'characterData') {
            // Check if a status indicator changed
            const statusIndicators = mutation.target.querySelectorAll('.gaming-status-indicator');
            statusIndicators.forEach((indicator) => {
              const statusText = indicator.textContent.trim();
              if (statusText && mutation.oldValue !== statusText) {
                announceToScreenReader(`Participant status changed to ${statusText}`);
              }
            });
          }
        });
      });
      
      observer.observe(participantTable, {
        childList: true,
        subtree: true,
        characterData: true,
        characterDataOldValue: true
      });
    }
  }

  /**
   * Initialize modal handlers
   */
  function initializeModalHandlers() {
    // Get all modal elements
    const seedModal = document.getElementById('seed-modal');
    const addParticipantModal = document.getElementById('add-participant-modal');

    // Keyboard handler - Close modals on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        if (seedModal && !seedModal.classList.contains('hidden')) {
          closeModalWithAnimation(seedModal);
        }
        if (addParticipantModal && !addParticipantModal.classList.contains('hidden')) {
          closeModalWithAnimation(addParticipantModal);
        }
      }
    });

    // Background click handler for seed modal
    if (seedModal) {
      seedModal.addEventListener('click', function(e) {
        // Only close if clicking the backdrop (not the modal content)
        if (e.target === seedModal) {
          closeModalWithAnimation(seedModal);
        }
      });
    }

    // Background click handler for add participant modal
    if (addParticipantModal) {
      addParticipantModal.addEventListener('click', function(e) {
        // Only close if clicking the backdrop (not the modal content)
        if (e.target === addParticipantModal) {
          closeModalWithAnimation(addParticipantModal);
        }
      });
    }

    // Override existing close functions with animated versions
    window.closeSeedModal = function() {
      closeModalWithAnimation(seedModal);
    };

    window.closeAddParticipantModal = function() {
      closeModalWithAnimation(addParticipantModal);
    };

    // Override existing open functions to use animation-aware version
    const originalAssignSeed = window.assignSeed;
    window.assignSeed = function(participantId) {
      if (originalAssignSeed) {
        originalAssignSeed(participantId);
      } else {
        document.getElementById('participant-id').value = participantId;
        openModalWithAnimation(seedModal);
      }
    };

    const originalShowAddParticipantModal = window.showAddParticipantModal;
    window.showAddParticipantModal = function() {
      if (originalShowAddParticipantModal) {
        originalShowAddParticipantModal();
      } else {
        openModalWithAnimation(addParticipantModal);
      }
    };
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initializeModalHandlers();
      initializeStatusChangeObserver();
    });
  } else {
    initializeModalHandlers();
    initializeStatusChangeObserver();
  }

  // Export announce function for use by other scripts
  window.announceToScreenReader = announceToScreenReader;

})();
