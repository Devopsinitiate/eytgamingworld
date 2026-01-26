# Team Leave Bug Fix Requirements

## Introduction

This specification addresses a critical bug in the team leave functionality where the system fails when a team captain attempts to leave a team. The error occurs due to incorrect Django ORM syntax when trying to prioritize co-captains for captaincy transfer. The system currently crashes with an AttributeError: 'Q' object has no attribute 'desc'.

## Glossary

- **Team Captain**: The team leader with full management permissions
- **Co-Captain**: A team member with elevated permissions who should be prioritized for captaincy transfer
- **Captaincy Transfer**: The process of assigning captain role to another member when the current captain leaves
- **TeamMember**: A database record representing a user's membership in a team
- **Q Object**: Django's query object for complex database queries

## Requirements

### Requirement 1: Captain Leave Functionality

**User Story:** As a team captain, I want to leave my team, so that I can join other teams or play independently without breaking the team structure.

#### Acceptance Criteria

1. WHEN a captain clicks leave team THEN the system SHALL display a confirmation dialog
2. WHEN a captain confirms leaving THEN the system SHALL transfer captaincy to the most suitable member
3. WHEN transferring captaincy THEN the system SHALL prioritize co-captains over regular members
4. WHEN no co-captain exists THEN the system SHALL transfer captaincy to the oldest active member
5. WHEN no other active members exist THEN the system SHALL disband the team

### Requirement 2: Captaincy Transfer Logic

**User Story:** As a system administrator, I want the captaincy transfer to follow a clear priority order, so that teams maintain proper leadership structure.

#### Acceptance Criteria

1. WHEN selecting a new captain THEN the system SHALL use co-captain role as the highest priority
2. WHEN multiple co-captains exist THEN the system SHALL select the one who joined earliest
3. WHEN no co-captains exist THEN the system SHALL select the member who joined earliest
4. WHEN the captain is the only member THEN the system SHALL disband the team
5. WHEN captaincy is transferred THEN the system SHALL update both the team captain field and the member role

### Requirement 3: Database Query Correctness

**User Story:** As a developer, I want the database queries to use correct Django ORM syntax, so that the system operates without errors.

#### Acceptance Criteria

1. WHEN ordering by role priority THEN the system SHALL use Django Case/When expressions for conditional ordering
2. WHEN executing the captaincy transfer query THEN the system SHALL not use invalid Q object methods
3. WHEN the query executes THEN the system SHALL return the correct member based on priority rules
4. WHEN no suitable member is found THEN the system SHALL handle the empty result gracefully
5. WHEN the query completes THEN the system SHALL proceed with the leave operation without errors

### Requirement 4: Error Handling and User Feedback

**User Story:** As a team captain, I want clear feedback when leaving a team, so that I understand what happened to the team leadership.

#### Acceptance Criteria

1. WHEN captaincy is transferred THEN the system SHALL display the name of the new captain
2. WHEN the team is disbanded THEN the system SHALL inform the user that they were the last member
3. WHEN the leave operation completes THEN the system SHALL redirect to the teams list page
4. WHEN an error occurs THEN the system SHALL display an appropriate error message
5. WHEN the operation succeeds THEN the system SHALL display a success message confirming the leave action

### Requirement 5: Data Integrity

**User Story:** As a system administrator, I want the leave operation to maintain data consistency, so that the team and member records remain accurate.

#### Acceptance Criteria

1. WHEN a captain leaves THEN the system SHALL set their member status to inactive
2. WHEN captaincy is transferred THEN the system SHALL update the new captain's role to captain
3. WHEN captaincy is transferred THEN the system SHALL update the team's captain field
4. WHEN the team is disbanded THEN the system SHALL set the team status to disbanded
5. WHEN the operation completes THEN the system SHALL record the leave timestamp