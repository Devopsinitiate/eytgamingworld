# Implementation Plan: Manage Participant Gaming Redesign

## Overview

This implementation plan transforms the Manage Participant page into a gaming/esports-styled interface matching the homepage aesthetic. The approach is CSS-focused with minimal template modifications, creating a new `manage-participant-gaming.css` file that applies neon glows, skewed elements, animated gradients, and cinematic typography to the existing participant management interface.

## Tasks

- [x] 1. Set up gaming CSS foundation and variables
  - Create `static/css/manage-participant-gaming.css` file
  - Define CSS custom properties for colors, glows, fonts, and transitions
  - Implement base background styling with deep black (#0A0A0A) and grid pattern
  - Set up font imports for Barlow Condensed and Space Grotesk
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 1.1 Write property test for heading typography consistency
  - **Property 1: Heading Typography Consistency**
  - **Validates: Requirements 1.2**

- [ ]* 1.2 Write property test for interactive element color consistency
  - **Property 2: Interactive Element Color Consistency**
  - **Validates: Requirements 1.3**

- [ ]* 1.3 Write property test for card element gaming style
  - **Property 4: Card Element Gaming Style**
  - **Validates: Requirements 1.6**

- [ ] 2. Implement gaming-style stat cards
  - [x] 2.1 Create `.gaming-stat-card` base styling with skewed transform
    - Apply skewY(-1deg) transform, neon red borders, and semi-transparent backgrounds
    - Style numeric values with Space Grotesk font at 2.5rem size
    - Add subtle background transparency and border glow effects
    - _Requirements: 2.1, 2.3, 2.4_
  
  - [x] 2.2 Implement stat card hover effects and animations
    - Add hover state with skewY(0deg) transform and elevation
    - Create animated gradient top border using keyframe animation
    - Apply smooth 0.3s ease transitions
    - _Requirements: 2.2, 2.5_
  
  - [ ]* 2.3 Write property test for stat card hover transform
    - **Property 5: Stat Card Hover Transform**
    - **Validates: Requirements 2.2**
  
  - [ ]* 2.4 Write property test for stat card gradient animation
    - **Property 6: Stat Card Gradient Animation on Hover**
    - **Validates: Requirements 2.5**

- [ ] 3. Implement gaming-style participant table
  - [x] 3.1 Create table base styling with dark background and neon borders
    - Apply dark semi-transparent background (rgba(31, 41, 55, 0.6))
    - Add 2px neon red border with rgba(220, 38, 38, 0.3)
    - Style column headers with Barlow Condensed uppercase font
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [x] 3.2 Implement table row hover effects
    - Add hover state with rgba(220, 38, 38, 0.08) background
    - Apply smooth transition effects
    - _Requirements: 3.3_
  
  - [x] 3.3 Create status indicator styles with neon glows
    - Implement colored dots for each status type (checked-in, pending, confirmed, withdrawn, disqualified)
    - Add appropriate neon glow effects (green, yellow, cyan, red)
    - Include pulse animation for active states
    - _Requirements: 3.5, 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 3.4 Create seed badge styling with circular design
    - Implement circular badges (32px diameter) with red background
    - Add neon red glow effect and white bold text
    - _Requirements: 3.6_
  
  - [ ]* 3.5 Write property test for table row hover behavior
    - **Property 7: Table Row Hover Behavior**
    - **Validates: Requirements 3.3**
  
  - [ ]* 3.6 Write property test for status indicator visual effects
    - **Property 8: Status Indicator Visual Effects**
    - **Validates: Requirements 3.5**
  
  - [ ]* 3.7 Write property test for seed badge styling
    - **Property 9: Seed Badge Styling**
    - **Validates: Requirements 3.6**
  
  - [ ]* 3.8 Write property test for status indicator pulse animation
    - **Property 20: Status Indicator Pulse Animation**
    - **Validates: Requirements 7.5**

- [x] 4. Checkpoint - Verify core visual components
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement gaming-style search bar and toolbar
  - [x] 5.1 Create search bar styling with dark background and neon effects
    - Apply dark background (rgba(31, 31, 31, 0.8)) with neon red border
    - Implement focus state with enhanced glow (box-shadow: 0 0 20px rgba(220, 38, 38, 0.3))
    - Style search icon with red accent color
    - _Requirements: 4.1, 4.2_
  
  - [x] 5.2 Create gaming button styles with skewed transforms
    - Implement `.gaming-btn-primary` with skewX(-12deg) transform
    - Style with Barlow Condensed font, uppercase, and italic
    - Add hover state with skewX(0deg) transform and enhanced glow
    - Create `.gaming-btn-ghost` variant for icon-only buttons
    - _Requirements: 4.3, 4.4, 4.5, 4.6_
  
  - [x] 5.3 Implement button ripple effect animation
    - Create ripple effect using pseudo-elements and keyframe animation
    - Trigger on click event with JavaScript
    - _Requirements: 5.1_
  
  - [ ]* 5.4 Write property test for action button transform
    - **Property 10: Action Button Transform**
    - **Validates: Requirements 4.3**
  
  - [ ]* 5.5 Write property test for action button hover transform
    - **Property 11: Action Button Hover Transform**
    - **Validates: Requirements 4.4**
  
  - [ ]* 5.6 Write property test for action button typography
    - **Property 12: Action Button Typography**
    - **Validates: Requirements 4.5**
  
  - [ ]* 5.7 Write property test for button ripple effect
    - **Property 13: Button Ripple Effect**
    - **Validates: Requirements 5.1**

- [ ] 6. Implement gaming-style modals
  - [x] 6.1 Create modal base styling with backdrop blur
    - Apply dark background (#1F2937) with neon red border
    - Implement backdrop blur effect (backdrop-filter: blur(20px))
    - Add fade-in animation with scale transform
    - _Requirements: 6.1, 6.2, 5.4_
  
  - [x] 6.2 Style modal input fields with gaming effects
    - Apply gaming input styling with neon borders
    - Implement focus state with enhanced glow
    - _Requirements: 6.3_
  
  - [x] 6.3 Implement modal action buttons and close animation
    - Apply gaming button styles to modal action buttons
    - Create fade-out animation for modal close
    - Add keyboard (Escape) and background click handlers
    - _Requirements: 6.4, 6.5, 6.6_
  
  - [ ]* 6.4 Write property test for modal animation behavior
    - **Property 15: Modal Animation Behavior**
    - **Validates: Requirements 5.4**
  
  - [ ]* 6.5 Write property test for modal input field gaming style
    - **Property 17: Modal Input Field Gaming Style**
    - **Validates: Requirements 6.3**
  
  - [ ]* 6.6 Write property test for modal button transform
    - **Property 18: Modal Button Transform**
    - **Validates: Requirements 6.4**
  
  - [ ]* 6.7 Write property test for modal close animation
    - **Property 19: Modal Close Animation**
    - **Validates: Requirements 6.5**

- [ ] 7. Implement animation system and keyframes
  - [x] 7.1 Create keyframe animations for gaming effects
    - Define neon pulse animation for glowing elements
    - Create gradient flow animation for borders
    - Implement fade-in-up animation for page load
    - Add scanline effect (optional retro enhancement)
    - _Requirements: 5.2, 5.3_
  
  - [x] 7.2 Apply GPU acceleration optimizations
    - Use CSS transforms and opacity for animations
    - Add will-change property to animated elements
    - Ensure animations use transform/opacity only (not layout properties)
    - _Requirements: 10.1, 10.2_
  
  - [ ]* 7.3 Write property test for card hover transition
    - **Property 14: Card Hover Transition**
    - **Validates: Requirements 5.2**
  
  - [ ]* 7.4 Write property test for GPU-accelerated animations
    - **Property 23: GPU-Accelerated Animations**
    - **Validates: Requirements 10.1**
  
  - [ ]* 7.5 Write property test for will-change optimization
    - **Property 24: Will-Change Optimization**
    - **Validates: Requirements 10.2**

- [x] 8. Checkpoint - Verify animations and interactions
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement responsive design adaptations
  - [x] 9.1 Create mobile styles for stat cards and table
    - Stack stat cards vertically at <768px viewport
    - Enable horizontal scrolling for participant table
    - Make search bar full width on mobile
    - _Requirements: 8.1, 8.2, 8.3_
  
  - [x] 9.2 Optimize animations for mobile performance
    - Reduce animation complexity on mobile devices
    - Scale gaming visual effects appropriately for smaller viewports
    - _Requirements: 8.5, 8.6_

- [x] 10. Implement accessibility features
  - [x] 10.1 Add reduced motion support
    - Create @media (prefers-reduced-motion: reduce) rules
    - Disable decorative animations when reduced motion is enabled
    - Maintain functional transitions
    - _Requirements: 5.5, 9.5_
  
  - [x] 10.2 Implement focus indicators and keyboard navigation
    - Add visible neon red focus outlines to all interactive elements
    - Ensure keyboard navigation works for all components
    - Add ARIA labels for icon-only buttons
    - _Requirements: 9.2, 9.3, 9.6_
  
  - [x] 10.3 Verify color contrast and touch targets
    - Ensure all text meets WCAG 2.1 AA contrast ratios
    - Verify minimum 44px touch targets for all interactive elements
    - Add screen reader announcements for status changes
    - _Requirements: 9.1, 9.4, 5.6, 8.4_
  
  - [ ]* 10.4 Write property test for touch target minimum size
    - **Property 16: Touch Target Minimum Size**
    - **Validates: Requirements 5.6, 8.4**
  
  - [ ]* 10.5 Write property test for focus indicator visibility
    - **Property 21: Focus Indicator Visibility**
    - **Validates: Requirements 9.6**
  
  - [ ]* 10.6 Write property test for color contrast compliance
    - **Property 22: Color Contrast Compliance**
    - **Validates: Requirements 9.1**

- [x] 11. Implement performance optimizations
  - [x] 11.1 Add lazy loading and debouncing
    - Implement lazy loading for participant avatars with placeholders
    - Add debounce to search input (300ms delay)
    - Limit neon glow effects to visible viewport elements
    - _Requirements: 10.3, 10.4, 10.5_
  
  - [x] 11.2 Optimize CSS delivery and browser compatibility
    - Add CSS fallbacks for unsupported features (backdrop-filter, transforms)
    - Implement font-display: swap for custom fonts
    - Add high contrast mode support
    - _Requirements: 10.6_

- [x] 12. Integrate gaming CSS with participant template
  - [x] 12.1 Update participant_list.html template
    - Add link to manage-participant-gaming.css in template head
    - Apply gaming CSS classes to existing HTML elements
    - Add minimal JavaScript for ripple effects and modal interactions
    - Ensure existing functionality remains intact
    - _Requirements: All requirements_

- [x] 13. Final checkpoint - Complete testing and validation
  - Run all property-based tests and unit tests
  - Verify responsive behavior across all breakpoints
  - Test accessibility with keyboard navigation and screen readers
  - Validate performance metrics (FCP <1.5s on 3G)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties across all elements
- Unit tests validate specific examples and edge cases
- The implementation is CSS-focused with minimal JavaScript for interactions
- All gaming styles are consolidated in a single CSS file for easy maintenance
- Existing HTML structure is preserved with minimal template modifications
