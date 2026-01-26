# Game Stats and Match History Redesign Requirements

## Introduction

This specification covers the redesign of the Game Stats and Match History sections to ensure consistent styling with the EYTGaming brand design. Currently, these sections use outdated styling that doesn't match the modern, dark-themed design used throughout the rest of the platform.

## Glossary

- **Game Stats**: Tournament history page showing user's tournament participation and performance statistics
- **Match History**: Team membership page showing user's team affiliations and team-based match statistics  
- **EYTGaming Brand**: The company's design system using #b91c1c (red) as primary color with dark theme
- **Dashboard Base Layout**: The consistent layout template used across dashboard pages
- **Material Symbols**: The icon system used throughout the platform

## Requirements

### Requirement 1

**User Story:** As a user viewing my game statistics, I want the page to match the modern EYTGaming brand design, so that I have a consistent visual experience across the platform.

#### Acceptance Criteria

1. WHEN a user navigates to Game Stats THEN the system SHALL display the page using the dark theme with EYTGaming brand colors
2. WHEN tournament statistics are shown THEN the system SHALL use modern card-based layouts with proper spacing and typography
3. WHEN filters are displayed THEN the system SHALL style form elements consistently with other dashboard pages
4. WHEN tournament data is presented THEN the system SHALL use the same visual hierarchy as other dashboard components
5. WHEN pagination is shown THEN the system SHALL use EYTGaming brand styling for navigation controls

### Requirement 2

**User Story:** As a user viewing my match history, I want the team membership page to use consistent styling, so that the interface feels cohesive and professional.

#### Acceptance Criteria

1. WHEN a user navigates to Match History THEN the system SHALL display the page using the dark theme background colors
2. WHEN team statistics are shown THEN the system SHALL use card-based layouts with proper borders and shadows
3. WHEN team information is displayed THEN the system SHALL use consistent typography and spacing
4. WHEN pending invitations are shown THEN the system SHALL style them with appropriate visual emphasis
5. WHEN action buttons are displayed THEN the system SHALL use EYTGaming primary color and hover states

### Requirement 3

**User Story:** As a user, I want both Game Stats and Match History to use Material Symbols icons, so that the iconography is consistent across the platform.

#### Acceptance Criteria

1. WHEN icons are displayed THEN the system SHALL use Material Symbols with consistent sizing and styling
2. WHEN status indicators are shown THEN the system SHALL use appropriate icons with proper color coding
3. WHEN navigation elements include icons THEN the system SHALL maintain consistent icon placement and sizing
4. WHEN empty states are displayed THEN the system SHALL use relevant Material Symbols icons
5. WHEN action buttons include icons THEN the system SHALL follow the established icon-text pairing patterns

### Requirement 4

**User Story:** As a user, I want the statistics cards to follow the same design patterns as other dashboard components, so that the interface feels unified.

#### Acceptance Criteria

1. WHEN statistics are displayed THEN the system SHALL use the same card styling as profile view statistics
2. WHEN numerical data is shown THEN the system SHALL use consistent typography hierarchy and color coding
3. WHEN progress indicators are needed THEN the system SHALL use EYTGaming brand colors for visual feedback
4. WHEN hover states are triggered THEN the system SHALL provide consistent interactive feedback
5. WHEN responsive breakpoints are reached THEN the system SHALL maintain proper layout and readability

### Requirement 5

**User Story:** As a user, I want the page headers and navigation to match other dashboard pages, so that I can navigate intuitively.

#### Acceptance Criteria

1. WHEN page headers are displayed THEN the system SHALL use consistent typography and spacing with other dashboard pages
2. WHEN breadcrumb navigation is shown THEN the system SHALL follow established navigation patterns
3. WHEN page descriptions are included THEN the system SHALL use consistent text styling and color
4. WHEN back navigation is provided THEN the system SHALL use the same styling as other dashboard pages
5. WHEN page titles are displayed THEN the system SHALL maintain the established font hierarchy