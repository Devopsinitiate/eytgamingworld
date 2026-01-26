# Game Stats and Match History Redesign Implementation Plan

## Task Overview

Transform the Game Stats (Tournament History) and Match History (Team Membership) pages to match EYTGaming's modern brand design with dark theme, consistent typography, and proper component styling.

## Implementation Tasks

- [ ] 1. Redesign Tournament History Page (Game Stats)
  - Update page header with consistent styling and Material Symbols icons
  - Redesign statistics summary cards using dark theme and EYT brand colors
  - Modernize filter section with consistent form styling
  - Update tournament table with dark theme and proper hover states
  - Implement branded pagination controls
  - Add empty state design with appropriate messaging
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.4, 5.1, 5.3, 5.4, 5.5_

- [ ] 2. Redesign Team Membership Page (Match History)  
  - Update page header to match dashboard styling standards
  - Redesign team statistics cards with dark theme and proper spacing
  - Modernize pending invitations section with visual emphasis
  - Update team information display with consistent typography
  - Implement branded action buttons with EYT primary colors
  - Add Material Symbols icons throughout the interface
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 5.1, 5.2, 5.3_

- [ ] 3. Implement Consistent Component Styling
  - Apply unified card layouts across both pages
  - Ensure consistent button styling and hover states
  - Standardize form element appearance and behavior
  - Implement proper responsive breakpoints
  - Add consistent loading and empty states
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Add Material Symbols Icons Integration
  - Replace existing icons with Material Symbols throughout both pages
  - Ensure consistent icon sizing and positioning
  - Add appropriate icons for status indicators and actions
  - Implement icon-text pairing patterns from other dashboard pages
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 5. Implement Brand Color Consistency
  - Apply EYTGaming primary color (#b91c1c) to all interactive elements
  - Ensure proper dark theme background colors throughout
  - Update text colors for optimal contrast and readability
  - Implement consistent focus states and visual feedback
  - _Requirements: 1.1, 2.1, 4.1, 4.4_

- [ ] 6. Final Integration and Testing
  - Verify visual consistency across all dashboard pages
  - Test responsive behavior on various screen sizes
  - Validate accessibility compliance and keyboard navigation
  - Ensure proper integration with existing dashboard navigation
  - _Requirements: All requirements validation_

## Technical Implementation Notes

### Tournament History Page Updates
- Extend `layouts/dashboard_base.html` for consistent navigation
- Use established CSS classes from `dashboard.css`
- Implement Material Symbols icon integration
- Apply dark theme color palette throughout

### Team Membership Page Updates  
- Update template inheritance and styling approach
- Modernize team card layouts with proper visual hierarchy
- Implement consistent action button styling
- Add proper empty states and loading indicators

### Shared Styling Patterns
- Statistics cards: `bg-white dark:bg-[#111318] p-6 rounded-xl border border-gray-200 dark:border-gray-800`
- Primary buttons: `bg-primary text-white rounded-lg hover:bg-red-700 transition-colors`
- Form elements: Consistent with other dashboard forms
- Icons: Material Symbols with `text-primary` coloring for brand elements

## Validation Criteria

Each task completion should result in:
- Visual consistency with existing dashboard pages
- Proper dark theme implementation
- EYTGaming brand color usage (#b91c1c)
- Material Symbols icon integration
- Responsive design functionality
- Accessibility compliance maintenance