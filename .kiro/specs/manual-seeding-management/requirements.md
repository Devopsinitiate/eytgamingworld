# Requirements Document

## Introduction

This document specifies requirements for the Manual Seeding Management feature. Tournament organizers can configure tournaments to use manual seeding, but currently lack any interface to actually assign or modify seed positions for participants. This feature adds seeding management capabilities to both the Django Admin interface and the organizer frontend dashboard, enabling organizers to control participant seeding when manual seeding is selected.

## Glossary

- **Tournament**: A competitive event with participants, brackets, and matches
- **Participant**: A user or team registered for a tournament
- **Seed**: An integer value (1, 2, 3, etc.) that determines a participant's initial position in the tournament bracket
- **Manual_Seeding**: A seeding method where the organizer explicitly assigns seed positions to participants
- **Organizer**: The user who created and manages a tournament
- **Django_Admin**: The Django administrative interface accessible at /admin
- **Organizer_Dashboard**: The frontend interface where organizers manage their tournaments
- **Seeding_Method**: The tournament configuration field that determines how participants are seeded (random, skill-based, manual, or registration order)

## Requirements

### Requirement 1: Display Seed Values in Admin Interface

**User Story:** As a tournament organizer using Django Admin, I want to see participant seed values in the participant list, so that I can quickly review the current seeding order.

#### Acceptance Criteria

1. WHEN viewing the Participant inline in Tournament Admin, THE Django_Admin SHALL display the seed field for each participant
2. WHEN viewing the Participant list page, THE Django_Admin SHALL display the seed column in the list view
3. THE Django_Admin SHALL allow sorting participants by seed value
4. WHEN a participant has no seed assigned, THE Django_Admin SHALL display the seed field as empty or null

### Requirement 2: Edit Seeds in Admin Interface

**User Story:** As a tournament organizer using Django Admin, I want to edit participant seed values directly, so that I can manually assign seeding positions.

#### Acceptance Criteria

1. WHEN editing a Tournament with manual seeding, THE Django_Admin SHALL allow editing the seed field for each participant in the inline
2. WHEN editing a Participant directly, THE Django_Admin SHALL allow editing the seed field
3. WHEN saving a seed value, THE Django_Admin SHALL validate that the seed is a positive integer
4. IF duplicate seed values are assigned within the same tournament, THEN THE Django_Admin SHALL display a validation warning

### Requirement 3: Bulk Seed Assignment in Admin

**User Story:** As a tournament organizer using Django Admin, I want to assign seeds to multiple participants at once, so that I can efficiently seed large tournaments.

#### Acceptance Criteria

1. WHEN selecting multiple participants in the Participant Admin, THE Django_Admin SHALL provide a bulk action to assign sequential seeds
2. WHEN the bulk seed assignment action is executed, THE Django_Admin SHALL assign seeds starting from 1 in the order participants are selected
3. WHEN bulk seed assignment completes, THE Django_Admin SHALL display a success message showing how many participants were seeded
4. THE Django_Admin SHALL preserve existing seeds for participants not included in the bulk action

### Requirement 4: Display Seeding Interface in Organizer Dashboard

**User Story:** As a tournament organizer, I want to access seeding management from my organizer dashboard, so that I can manage seeds without using Django Admin.

#### Acceptance Criteria

1. WHEN the seeding_method is set to 'manual', THE Organizer_Dashboard SHALL display a seeding management interface
2. WHEN the seeding_method is not 'manual', THE Organizer_Dashboard SHALL NOT display the seeding management interface
3. WHEN viewing the seeding interface, THE Organizer_Dashboard SHALL display all confirmed participants with their current seed values
4. THE Organizer_Dashboard SHALL display participants ordered by their seed value (nulls last)

### Requirement 5: Drag-and-Drop Seed Reordering

**User Story:** As a tournament organizer, I want to reorder participants by dragging and dropping them, so that I can intuitively adjust seeding positions.

#### Acceptance Criteria

1. WHEN viewing the seeding interface, THE Organizer_Dashboard SHALL provide drag-and-drop functionality for participant rows
2. WHEN a participant is dragged to a new position, THE Organizer_Dashboard SHALL visually update the order immediately
3. WHEN drag-and-drop reordering occurs, THE Organizer_Dashboard SHALL automatically recalculate seed numbers based on the new order
4. THE Organizer_Dashboard SHALL provide visual feedback during drag operations (e.g., highlighting drop zones)

### Requirement 6: Manual Seed Input

**User Story:** As a tournament organizer, I want to type seed numbers directly for participants, so that I can precisely assign specific seed positions.

#### Acceptance Criteria

1. WHEN viewing the seeding interface, THE Organizer_Dashboard SHALL provide an input field for each participant's seed value
2. WHEN a seed value is entered, THE Organizer_Dashboard SHALL validate that it is a positive integer
3. WHEN an invalid seed value is entered, THE Organizer_Dashboard SHALL display an error message
4. WHEN a valid seed value is entered, THE Organizer_Dashboard SHALL update the participant's seed upon saving

### Requirement 7: Save Seeding Changes

**User Story:** As a tournament organizer, I want to save my seeding changes, so that the seed assignments are persisted to the database.

#### Acceptance Criteria

1. WHEN seeding changes are made, THE Organizer_Dashboard SHALL provide a save button
2. WHEN the save button is clicked, THE Organizer_Dashboard SHALL send seed assignments to the backend API
3. WHEN the API receives seed assignments, THE Backend SHALL validate that the user is the tournament organizer
4. WHEN validation passes, THE Backend SHALL update participant seed values in the database
5. WHEN the save operation completes successfully, THE Organizer_Dashboard SHALL display a success message
6. IF the save operation fails, THEN THE Organizer_Dashboard SHALL display an error message with details

### Requirement 8: Prevent Seeding Changes After Tournament Start

**User Story:** As a tournament organizer, I want seeding to be locked once the tournament starts, so that bracket integrity is maintained.

#### Acceptance Criteria

1. WHEN the tournament status is 'in_progress' or 'completed', THE Organizer_Dashboard SHALL display seeding as read-only
2. WHEN the tournament status is 'in_progress' or 'completed', THE Backend SHALL reject any seed modification requests
3. WHEN attempting to modify seeds for a started tournament, THE Backend SHALL return an error indicating seeding is locked
4. WHEN the tournament status is 'draft', 'registration', or 'check_in', THE Organizer_Dashboard SHALL allow seed modifications

### Requirement 9: Auto-Seed Functionality

**User Story:** As a tournament organizer, I want to automatically assign seeds based on registration order, so that I can quickly establish an initial seeding.

#### Acceptance Criteria

1. WHEN viewing the seeding interface, THE Organizer_Dashboard SHALL provide an "Auto-Seed" button
2. WHEN the Auto-Seed button is clicked, THE Organizer_Dashboard SHALL prompt for confirmation
3. WHEN auto-seed is confirmed, THE Backend SHALL assign seeds sequentially based on participant registration timestamp
4. WHEN auto-seed completes, THE Organizer_Dashboard SHALL refresh the participant list with new seed values
5. THE Backend SHALL assign seed 1 to the earliest registered participant, seed 2 to the second earliest, and so on

### Requirement 10: Seed Conflict Detection

**User Story:** As a tournament organizer, I want to be warned about duplicate seed assignments, so that I can correct conflicts before saving.

#### Acceptance Criteria

1. WHEN multiple participants have the same seed value, THE Organizer_Dashboard SHALL highlight the conflicting participants
2. WHEN seed conflicts exist, THE Organizer_Dashboard SHALL display a warning message listing the conflicting seed numbers
3. WHEN attempting to save with seed conflicts, THE Organizer_Dashboard SHALL prompt for confirmation
4. THE Backend SHALL allow saving duplicate seeds but log a warning for audit purposes

### Requirement 11: Unseeded Participant Handling

**User Story:** As a tournament organizer, I want to see which participants lack seed assignments, so that I can ensure all participants are seeded before starting the tournament.

#### Acceptance Criteria

1. WHEN participants have null seed values, THE Organizer_Dashboard SHALL display them in a separate "Unseeded" section
2. WHEN viewing the seeding interface, THE Organizer_Dashboard SHALL display a count of unseeded participants
3. WHEN all participants are seeded, THE Organizer_Dashboard SHALL display a confirmation indicator
4. THE Organizer_Dashboard SHALL allow dragging unseeded participants into the seeded list

### Requirement 12: Seeding API Endpoint

**User Story:** As a frontend developer, I want a dedicated API endpoint for seeding operations, so that the organizer dashboard can manage seeds efficiently.

#### Acceptance Criteria

1. THE Backend SHALL provide a POST endpoint at /api/tournaments/{slug}/participants/seed/
2. WHEN the endpoint receives a request, THE Backend SHALL verify the user is the tournament organizer or admin
3. WHEN the endpoint receives seed assignments, THE Backend SHALL validate the tournament seeding_method is 'manual'
4. WHEN validation passes, THE Backend SHALL update participant seeds in a single transaction
5. WHEN the update succeeds, THE Backend SHALL return HTTP 200 with updated participant data
6. IF authorization fails, THEN THE Backend SHALL return HTTP 403
7. IF validation fails, THEN THE Backend SHALL return HTTP 400 with error details

### Requirement 13: Seeding Change Audit Log

**User Story:** As a tournament administrator, I want seeding changes to be logged, so that I can track who modified seeds and when.

#### Acceptance Criteria

1. WHEN participant seeds are modified, THE Backend SHALL log the change with timestamp, user, and old/new values
2. WHEN viewing a participant in Django Admin, THE Backend SHALL display a history of seed changes
3. THE Backend SHALL log seed changes through Django's built-in admin logging system
4. THE Backend SHALL include the tournament name and participant name in log entries
