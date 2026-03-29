# Implementation Plan: Manual Seeding Management

## Overview

This implementation plan breaks down the manual seeding management feature into discrete coding tasks. The feature adds seeding management capabilities to both Django Admin and the organizer frontend dashboard, enabling tournament organizers to assign and modify participant seed positions when manual seeding is selected.

The implementation follows a layered approach: backend API and validation first, then Django Admin enhancements, followed by frontend interface with drag-and-drop functionality, and finally integration testing.

## Tasks

- [x] 1. Set up backend API endpoints and validation
  - [x] 1.1 Create seed assignment API endpoint
    - Implement `seed_participants_api` view in `tournaments/api_views.py`
    - Add POST endpoint at `/api/tournaments/{slug}/participants/seed/`
    - Implement authorization check (organizer or superuser only)
    - Implement tournament status validation (reject if in_progress or completed)
    - Implement seeding method validation (must be 'manual')
    - Implement seed value validation (positive integers or null only)
    - Implement transactional seed updates with atomic database operations
    - Return updated participant data on success
    - Return appropriate error responses (403, 400, 409) with details
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.2, 8.3, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7_

  - [ ]* 1.2 Write property test for seed value validation
    - **Property 1: Seed Value Validation**
    - **Validates: Requirements 2.3, 6.2**
    - Test that system accepts only positive integers or null
    - Test that system rejects zero, negative integers, floats, and strings

  - [ ]* 1.3 Write property test for organizer authorization
    - **Property 8: Organizer Authorization**
    - **Validates: Requirements 7.3, 12.2**
    - Test that non-organizers and non-superusers receive 403 responses
    - Test that organizers and superusers can modify seeds

  - [ ]* 1.4 Write property test for tournament status-based locking
    - **Property 9: Tournament Status-Based Locking**
    - **Validates: Requirements 8.1, 8.2**
    - Test that tournaments with status 'in_progress' or 'completed' reject seed modifications
    - Test that appropriate error messages are returned

  - [ ]* 1.5 Write property test for transactional seed updates
    - **Property 15: Transactional Seed Updates**
    - **Validates: Requirements 12.4**
    - Test that either all seeds are updated or none are updated (atomicity)
    - Test that partial failures result in complete rollback

  - [x] 1.6 Create auto-seed API endpoint
    - Implement `auto_seed_api` view in `tournaments/api_views.py`
    - Add POST endpoint at `/api/tournaments/{slug}/participants/auto-seed/`
    - Implement same authorization and validation as seed assignment endpoint
    - Query confirmed participants ordered by `registered_at`
    - Assign seeds sequentially (1, 2, 3...) based on registration order
    - Return success message with participant count and updated data
    - _Requirements: 9.3, 9.4, 9.5_

  - [ ]* 1.7 Write property test for auto-seed registration order
    - **Property 11: Auto-Seed Registration Order**
    - **Validates: Requirements 9.3, 9.5**
    - Test that earliest registered participant gets seed 1
    - Test that seeds are assigned sequentially by registration timestamp

  - [x] 1.8 Add URL routes for seeding endpoints
    - Add routes to `tournaments/urls.py`
    - Map `/api/tournaments/<slug:slug>/participants/seed/` to `seed_participants_api`
    - Map `/api/tournaments/<slug:slug>/participants/auto-seed/` to `auto_seed_api`
    - _Requirements: 12.1_

  - [ ]* 1.9 Write unit tests for API endpoints
    - Test successful seed assignment returns 200 with updated data
    - Test non-organizer receives 403
    - Test started tournament receives 409
    - Test invalid seeding_method receives 400
    - Test invalid seed values receive 400 with error details
    - Test participant not found receives 400

- [x] 2. Implement audit logging for seed changes
  - [x] 2.1 Add audit logging to seed assignment endpoint
    - Import Django's LogEntry and ContentType models
    - Create LogEntry for each seed modification in transaction
    - Include timestamp, user, participant, old seed value, new seed value
    - Include tournament name and participant name in change message
    - _Requirements: 13.1, 13.4_

  - [x] 2.2 Add audit logging to auto-seed endpoint
    - Create LogEntry for each participant seeded during auto-seed
    - Include descriptive change message indicating auto-seed operation
    - _Requirements: 13.1, 13.4_

  - [ ]* 2.3 Write property test for seed change audit logging
    - **Property 16: Seed Change Audit Logging**
    - **Validates: Requirements 13.1, 13.4**
    - Test that every seed modification creates a log entry
    - Test that log entries contain all required fields

  - [ ]* 2.4 Write unit tests for audit logging
    - Test that LogEntry is created after seed modification
    - Test that admin history view displays seed changes
    - Test that log entries are immutable
    - _Requirements: 13.2_

- [x] 3. Enhance Django Admin interface
  - [x] 3.1 Update ParticipantInline configuration
    - Add 'seed' to fields list in `tournaments/admin.py`
    - Implement `get_readonly_fields` to make seed readonly when tournament started
    - Ensure seed field is editable for draft/registration/check_in tournaments
    - _Requirements: 1.1, 2.1, 2.2, 8.1_

  - [x] 3.2 Update ParticipantAdmin configuration
    - Add 'seed' to list_display
    - Add 'seed' to ordering (before 'registered_at')
    - Ensure seed column is sortable
    - Display null seeds as empty in list view
    - _Requirements: 1.2, 1.3, 1.4, 2.3_

  - [x] 3.3 Implement bulk seed assignment action
    - Create `assign_sequential_seeds` method in ParticipantAdmin
    - Assign seeds starting from 1 based on selection order
    - Create audit log entries for each participant
    - Display success message with count of seeded participants
    - Add action to ParticipantAdmin.actions list
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 3.4 Write property test for sequential bulk seeding
    - **Property 2: Sequential Bulk Seeding**
    - **Validates: Requirements 3.2**
    - Test that selected participants receive seeds 1, 2, 3, ... in order

  - [ ]* 3.5 Write property test for bulk action isolation
    - **Property 3: Bulk Action Isolation**
    - **Validates: Requirements 3.4**
    - Test that participants not in bulk action retain original seeds

  - [ ]* 3.6 Write unit tests for admin enhancements
    - Test seed field appears in ParticipantInline
    - Test seed field is readonly when tournament started
    - Test seed appears in ParticipantAdmin list_display
    - Test bulk action is registered and functional
    - Test validation warning for duplicate seeds

- [x] 4. Checkpoint - Ensure backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create frontend seeding interface component
  - [x] 5.1 Create seeding interface HTML template
    - Create `templates/tournaments/components/seeding_interface.html`
    - Add seeding header with stats (seeded count, unseeded count)
    - Add action buttons (Auto-Seed, Save Changes)
    - Add seeded participants section with sortable list container
    - Add unseeded participants section with list container
    - Add conflict warning banner (hidden by default)
    - _Requirements: 4.1, 4.3, 4.4, 9.1, 11.1, 11.2_

  - [x] 5.2 Integrate seeding interface into tournament detail page
    - Add conditional include in `templates/tournaments/tournament_detail.html`
    - Show interface only when seeding_method is 'manual' and user is organizer
    - Add script tag to initialize SeedingManager module
    - _Requirements: 4.1, 4.2_

  - [ ]* 5.3 Write unit tests for template rendering
    - Test interface is visible when seeding_method is 'manual' and user is organizer
    - Test interface is hidden when seeding_method is not 'manual'
    - Test interface is hidden for non-organizers
    - Test all required elements are present (buttons, sections, lists)

- [x] 6. Implement SeedingManager JavaScript module
  - [x] 6.1 Create SeedingManager class structure
    - Create `static/js/modules/seeding-manager.js`
    - Implement constructor with tournamentSlug parameter
    - Initialize state properties (participants, hasChanges, draggedElement)
    - Implement init method to orchestrate setup
    - _Requirements: 4.3, 4.4_

  - [x] 6.2 Implement participant loading
    - Implement `loadParticipants` method
    - Fetch from `/api/tournaments/{slug}/participants/`
    - Filter participants by status='confirmed'
    - Handle fetch errors with user-friendly messages
    - _Requirements: 4.3_

  - [ ]* 6.3 Write property test for confirmed participant filtering
    - **Property 4: Confirmed Participant Filtering**
    - **Validates: Requirements 4.3**
    - Test that only participants with status='confirmed' are displayed

  - [x] 6.3 Implement rendering logic
    - Implement `render` method to update DOM
    - Separate participants into seeded and unseeded lists
    - Sort seeded participants by seed value (ascending)
    - Update seeded/unseeded count displays
    - Implement `renderParticipantRow` helper method
    - _Requirements: 4.4, 11.1, 11.2_

  - [ ]* 6.4 Write property test for seed-based ordering with nulls last
    - **Property 5: Seed-Based Ordering with Nulls Last**
    - **Validates: Requirements 4.4**
    - Test that participants are ordered by seed (1, 2, 3, ...) with nulls last

  - [ ]* 6.5 Write property test for unseeded participant segregation
    - **Property 13: Unseeded Participant Segregation**
    - **Validates: Requirements 11.1, 11.2**
    - Test that participants with null seeds appear in unseeded section
    - Test that unseeded count matches number of null-seeded participants

- [x] 7. Implement drag-and-drop functionality
  - [x] 7.1 Set up HTML5 drag and drop event handlers
    - Implement `setupDragAndDrop` method
    - Add dragstart event listener to set draggedElement and add dragging class
    - Add dragend event listener to remove dragging class
    - Add dragover event listener to prevent default and position dragged element
    - Add drop event listener to trigger seed recalculation
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 7.2 Implement drag positioning helper
    - Implement `getDragAfterElement` method
    - Calculate drop position based on mouse Y coordinate
    - Return element that dragged item should be inserted before
    - _Requirements: 5.2_

  - [x] 7.3 Implement seed recalculation after drag
    - Implement `recalculateSeeds` method
    - Query current DOM order of participant rows
    - Assign seeds 1, 2, 3, ... based on visual order
    - Update participant objects with new seed values
    - Set hasChanges flag to true
    - _Requirements: 5.3_

  - [ ]* 7.4 Write property test for drag-and-drop seed recalculation
    - **Property 6: Drag-and-Drop Seed Recalculation**
    - **Validates: Requirements 5.3**
    - Test that seeds are recalculated as 1, 2, 3, ... after any reordering

  - [ ]* 7.5 Write unit tests for drag-and-drop
    - Test participant rows have draggable=true attribute
    - Test drop event updates DOM order
    - Test seed recalculation is triggered after drop
    - Test visual feedback during drag (dragging class)

- [x] 8. Implement manual seed input and validation
  - [x] 8.1 Add seed input event handlers
    - Add input event listener for seed-input fields in `setupEventListeners`
    - Parse input value as integer
    - Validate value is positive integer
    - Update participant seed value in state
    - Set hasChanges flag to true
    - Trigger conflict detection
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 8.2 Implement conflict detection
    - Implement `detectConflicts` method
    - Count occurrences of each seed value
    - Identify duplicate seeds
    - Show/hide conflict warning banner
    - Display list of conflicting seed numbers
    - _Requirements: 10.1, 10.2_

  - [ ]* 8.3 Write unit tests for manual seed input
    - Test invalid seed inputs show error messages
    - Test valid seed inputs update participant state
    - Test duplicate seeds show warning banner
    - Test conflict detection identifies duplicates correctly
    - _Requirements: 6.3_

- [x] 9. Implement save and auto-seed operations
  - [x] 9.1 Implement save seeds functionality
    - Implement `saveSeeds` method
    - Collect seed assignments from participant state
    - POST to `/api/tournaments/{slug}/participants/seed/`
    - Include CSRF token in request headers
    - Handle success response (show message, update state, re-render)
    - Handle error response (show error message with details)
    - Reset hasChanges flag on success
    - _Requirements: 7.1, 7.2, 7.5, 7.6_

  - [ ]* 9.2 Write property test for seed persistence
    - **Property 7: Seed Persistence**
    - **Validates: Requirements 6.4, 7.4**
    - Test that saved seed values are persisted to database
    - Test that subsequent queries return the saved values

  - [x] 9.3 Implement auto-seed functionality
    - Implement `autoSeed` method
    - Show confirmation dialog before proceeding
    - POST to `/api/tournaments/{slug}/participants/auto-seed/`
    - Include CSRF token in request headers
    - Handle success response (show message, update participants, re-render)
    - Handle error response (show error message)
    - Reset hasChanges flag on success
    - _Requirements: 9.1, 9.2, 9.4_

  - [x] 9.4 Implement CSRF token helper
    - Implement `getCSRFToken` method
    - Check for token in form input or cookie
    - Return token for API requests
    - _Requirements: 7.2_

  - [x] 9.5 Implement user feedback methods
    - Implement `showSuccess` method for success messages
    - Implement `showError` method for error messages
    - Use toast notifications or alerts
    - _Requirements: 7.5, 7.6_

  - [ ]* 9.6 Write unit tests for save and auto-seed
    - Test save button triggers API POST
    - Test success response shows success message
    - Test error response shows error message
    - Test auto-seed button shows confirmation dialog
    - Test auto-seed success updates participant list
    - Test unsaved changes are tracked correctly

- [x] 10. Implement tournament status-based UI controls
  - [x] 10.1 Add read-only mode for started tournaments
    - Check tournament status in render method
    - Disable seed inputs when status is 'in_progress' or 'completed'
    - Disable drag-and-drop when tournament started
    - Disable save and auto-seed buttons when tournament started
    - Show informational message indicating seeding is locked
    - _Requirements: 8.1_

  - [ ]* 10.2 Write property test for tournament status-based editing
    - **Property 10: Tournament Status-Based Editing**
    - **Validates: Requirements 8.4**
    - Test that tournaments with status 'draft', 'registration', or 'check_in' allow edits
    - Test that UI inputs are enabled for editable tournaments

  - [ ]* 10.3 Write unit tests for status-based UI controls
    - Test read-only mode when tournament status is 'in_progress'
    - Test read-only mode when tournament status is 'completed'
    - Test editable mode when tournament status is 'draft'
    - Test editable mode when tournament status is 'registration'
    - Test editable mode when tournament status is 'check_in'

- [x] 11. Add CSS styling for seeding interface
  - [x] 11.1 Create seeding interface styles
    - Add styles to appropriate CSS file or create new module
    - Style seeding header with stats and action buttons
    - Style participant rows with drag handles and seed inputs
    - Style seeded and unseeded sections
    - Style conflict warning banner
    - Add visual feedback for drag operations (hover states, dragging class)
    - Ensure responsive design for mobile devices
    - Ensure accessibility (focus indicators, color contrast)
    - _Requirements: 5.4_

- [x] 12. Checkpoint - Ensure frontend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Integration testing and edge cases
  - [ ]* 13.1 Write integration test for end-to-end seeding workflow
    - Test organizer logs in and navigates to tournament
    - Test seeding interface is visible for manual seeding tournaments
    - Test drag-and-drop reordering updates seeds
    - Test save operation persists changes to database
    - Test audit log entries are created
    - _Requirements: 1.1, 2.1, 4.1, 5.1, 7.1, 13.1_

  - [ ]* 13.2 Write integration test for admin workflow
    - Test admin opens tournament in Django Admin
    - Test seed field is visible and editable in inline
    - Test saving tournament persists seed changes
    - Test bulk action assigns sequential seeds
    - _Requirements: 1.1, 2.1, 3.1_

  - [ ]* 13.3 Write integration test for duplicate seed handling
    - Test duplicate seeds show warning in UI
    - Test duplicate seeds are accepted by backend with logging
    - Test confirmation prompt for saving with conflicts
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [ ]* 13.4 Write unit tests for edge cases
    - Test empty participant list shows appropriate message
    - Test all participants unseeded shows empty seeded section
    - Test no confirmed participants shows informational message
    - Test seed value exceeding participant count is accepted
    - Test network errors trigger retry logic
    - Test concurrent modification handling

- [x] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and integration points
- The implementation uses existing database schema (no migrations required)
- Backend uses Django's built-in admin logging for audit trail
- Frontend uses native HTML5 Drag and Drop API (no external libraries required)
- All API endpoints include proper authorization, validation, and error handling
