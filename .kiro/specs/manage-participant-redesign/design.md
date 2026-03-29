# Design Document: Manage Participant Page Gaming Redesign

## Overview

This design document outlines the technical approach for redesigning the Manage Participant page to match the gaming/esports aesthetic established in the homepage and venue system. The redesign transforms the current basic Tailwind-styled interface into an immersive gaming experience featuring neon glows, skewed elements, animated gradients, and cinematic typography.

The redesign focuses on three core areas:
1. **Visual Enhancement**: Applying gaming-style CSS with neon effects, skewed transforms, and animated gradients
2. **Component Redesign**: Transforming stat cards, tables, buttons, and modals with gaming aesthetics
3. **Performance & Accessibility**: Ensuring smooth animations while maintaining WCAG 2.1 AA compliance

The implementation will be CSS-focused, leveraging existing HTML structure with minimal template modifications. All gaming styles will be consolidated into a dedicated CSS file that can be applied to the existing `participant_list.html` template.

## Architecture

### Design Principles

1. **CSS-First Approach**: Maximize use of CSS for visual effects to minimize JavaScript overhead
2. **Progressive Enhancement**: Core functionality works without advanced CSS, gaming effects enhance the experience
3. **GPU Acceleration**: Use CSS transforms and will-change for smooth animations
4. **Responsive Gaming**: Gaming aesthetic adapts gracefully across all viewport sizes
5. **Accessibility First**: Visual enhancements never compromise keyboard navigation or screen reader support

### File Structure

```
static/css/
├── manage-participant-gaming.css    # New gaming styles for participant management
└── venues.css                        # Existing gaming styles (reference)

templates/tournaments/
└── participant_list.html             # Existing template (minimal modifications)
```

### CSS Architecture

The gaming styles will be organized into logical sections:

1. **CSS Variables**: Color palette, spacing, timing functions
2. **Base Styles**: Background, typography, layout foundations
3. **Component Styles**: Stat cards, tables, buttons, modals
4. **Animation Definitions**: Keyframes for glows, gradients, transitions
5. **Responsive Overrides**: Mobile and tablet adaptations
6. **Accessibility Overrides**: Reduced motion and high contrast support

## Components and Interfaces

### 1. Gaming Foundation Layer

**Purpose**: Establish the visual foundation with background, typography, and color system.

**CSS Variables**:
```css
:root {
  --color-deep-black: #0A0A0A;
  --color-gunmetal-gray: #1F2937;
  --color-electric-red: #DC2626;
  --color-neon-cyan: #06B6D4;
  --color-neon-green: #10B981;
  --color-neon-yellow: #F59E0B;
  
  --glow-red: 0 0 20px rgba(220, 38, 38, 0.3);
  --glow-cyan: 0 0 20px rgba(6, 182, 212, 0.3);
  --glow-green: 0 0 20px rgba(16, 185, 129, 0.3);
  
  --font-gaming: 'Barlow Condensed', sans-serif;
  --font-numeric: 'Space Grotesk', sans-serif;
  
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}
```

**Background Pattern**:
- Deep black base (#0A0A0A)
- Subtle grid pattern using CSS gradients
- Optional scanline effect for retro gaming feel

### 2. Stat Cards Component

**Purpose**: Display tournament metrics with gaming-style visual effects.

**Structure**: Four cards showing Total Registered, Checked In, Pending Check-in, Spots Remaining

**Gaming Effects**:
- Skewed transform (skewY -1deg) at rest
- Neon red border with glow effect
- Animated gradient top border on hover
- Transform to skewY 0deg on hover with elevation
- Large numeric values using Space Grotesk font
- Subtle background transparency

**CSS Classes**:
- `.gaming-stat-card`: Base card styling
- `.gaming-stat-card:hover`: Hover state with transform
- `.gaming-stat-value`: Large numeric display
- `.gaming-stat-label`: Descriptive text

**Responsive Behavior**:
- Desktop: 4 cards in horizontal row
- Tablet: 2x2 grid
- Mobile: Vertical stack, full width

### 3. Participant Table Component

**Purpose**: Display participant data with gaming-style enhancements.

**Gaming Effects**:
- Dark semi-transparent background (rgba(31, 41, 55, 0.6))
- Neon red border (2px solid rgba(220, 38, 38, 0.3))
- Row hover: Red glow background (rgba(220, 38, 38, 0.08))
- Column headers: Barlow Condensed uppercase
- Status indicators: Colored dots with neon glow
- Seed badges: Circular with red background and glow

**Status Indicator Styles**:
- Checked In: Green dot with green glow
- Pending: Yellow/amber dot with yellow glow
- Confirmed: Cyan dot with cyan glow
- Withdrawn: Gray dot, no glow
- Disqualified: Red dot with red glow

**Seed Badge**:
- Circular badge (32px diameter)
- Red background with opacity
- White text, bold
- Neon red glow effect
- Pulse animation for emphasis

**Responsive Behavior**:
- Desktop: Full table display
- Tablet: Horizontal scroll enabled
- Mobile: Horizontal scroll with sticky first column

### 4. Search Bar and Toolbar

**Purpose**: Provide filtering and action controls with gaming aesthetics.

**Search Bar Gaming Effects**:
- Dark background (rgba(31, 31, 31, 0.8))
- Neon red border (1px solid rgba(220, 38, 38, 0.3))
- Focus state: Enhanced glow (box-shadow: 0 0 20px rgba(220, 38, 38, 0.3))
- Icon with red accent color
- Smooth transition on focus

**Action Buttons**:
- Primary button (Add Participant): Skewed transform (skewX -12deg)
- Hover: Transform to skewX 0deg with enhanced glow
- Barlow Condensed font, uppercase, italic
- Ripple effect on click
- Icon-only buttons: Gaming ghost style with hover glow

**Button Variants**:
- `.gaming-btn-primary`: Red background, skewed
- `.gaming-btn-ghost`: Transparent with border, icon-only
- `.gaming-btn-action`: Small action buttons (Check In, Seed)

### 5. Modal Components

**Purpose**: Seed assignment and participant action modals with gaming styling.

**Gaming Effects**:
- Dark background (#1F2937) with neon red border
- Backdrop blur (backdrop-filter: blur(20px))
- Fade-in animation with scale transform
- Input fields: Gaming style with neon borders
- Focus state: Enhanced glow on inputs
- Action buttons: Gaming button styles

**Modal Structure**:
- Header: Title with close button
- Body: Form inputs with gaming styling
- Footer: Action buttons (Cancel, Confirm)

**Animations**:
- Open: Fade in + scale from 0.95 to 1
- Close: Fade out + scale to 0.95
- Duration: 0.3s ease

### 6. Animation System

**Purpose**: Provide smooth, performant animations for interactive elements.

**Keyframe Animations**:

1. **Neon Pulse**: Subtle glow intensity variation
2. **Gradient Flow**: Animated gradient for borders
3. **Fade In Up**: Page load animation
4. **Ripple Effect**: Button click feedback
5. **Scanline**: Optional retro effect

**Performance Optimizations**:
- Use `transform` and `opacity` for GPU acceleration
- Apply `will-change` to animated elements
- Remove animations when `prefers-reduced-motion` is enabled
- Limit animations to visible viewport elements

## Data Models

### CSS Class Naming Convention

The design uses a consistent naming pattern for gaming-styled elements:

**Pattern**: `gaming-{component}-{variant}`

**Examples**:
- `gaming-stat-card`
- `gaming-table-row`
- `gaming-btn-primary`
- `gaming-modal-backdrop`
- `gaming-status-indicator`

### Component State Classes

**Hover States**: `.gaming-{component}:hover`
**Focus States**: `.gaming-{component}:focus`
**Active States**: `.gaming-{component}.active`
**Disabled States**: `.gaming-{component}.disabled`

### Responsive Breakpoints

```css
/* Mobile: < 768px */
@media (max-width: 767px) { }

/* Tablet: 768px - 1023px */
@media (min-width: 768px) and (max-width: 1023px) { }

/* Desktop: >= 1024px */
@media (min-width: 1024px) { }
```

### Accessibility Classes

**Reduced Motion**:
```css
@media (prefers-reduced-motion: reduce) {
  .gaming-animated { animation: none; }
  .gaming-transition { transition: none; }
}
```

**High Contrast**:
```css
@media (prefers-contrast: high) {
  .gaming-glow { box-shadow: none; }
  .gaming-border { border-width: 2px; }
}
```

### Color Mapping

| Element | Color | Glow |
|---------|-------|------|
| Primary Accent | Electric Red (#DC2626) | Red Glow |
| Secondary Accent | Neon Cyan (#06B6D4) | Cyan Glow |
| Success State | Neon Green (#10B981) | Green Glow |
| Warning State | Neon Yellow (#F59E0B) | Yellow Glow |
| Background | Deep Black (#0A0A0A) | None |
| Card Background | Gunmetal Gray (#1F2937) | None |


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:
- Criteria 8.4 duplicates 5.6 (minimum 44px touch targets)
- Criteria 9.5 duplicates 5.5 (reduced motion support)

These redundant properties will be consolidated into single comprehensive properties.

### Property 1: Heading Typography Consistency

*For all* heading elements on the Manage Participant page, the computed font-family should be 'Barlow Condensed' and text-transform should be 'uppercase'.

**Validates: Requirements 1.2**

### Property 2: Interactive Element Color Consistency

*For all* interactive elements (buttons, links, inputs), the primary accent color should use electric red (#DC2626) in either color, background-color, or border-color properties.

**Validates: Requirements 1.3**

### Property 3: Status Indicator Color Consistency

*For all* status indicator elements, the secondary accent color should use neon cyan (#06B6D4) for confirmed/active states.

**Validates: Requirements 1.4**

### Property 4: Card Element Gaming Style

*For all* card elements with the gaming-card class, the computed transform should include a skew function and border should include rgba color with glow effect.

**Validates: Requirements 1.6**

### Property 5: Stat Card Hover Transform

*For any* stat card element, when hover state is simulated, the transform should change from skewY(-1deg) to skewY(0deg) and box-shadow should increase in intensity.

**Validates: Requirements 2.2**

### Property 6: Stat Card Gradient Animation on Hover

*For any* stat card element, when hover state is simulated, an animated gradient should appear on the top border or pseudo-element.

**Validates: Requirements 2.5**

### Property 7: Table Row Hover Behavior

*For any* table row in the participant table, when hover state is simulated, the background-color should be rgba(220, 38, 38, 0.08) and transition duration should be present.

**Validates: Requirements 3.3**

### Property 8: Status Indicator Visual Effects

*For all* status indicator elements, they should display colored dots with appropriate neon glow effects based on status type (green for checked-in, yellow for pending, cyan for confirmed, red for disqualified).

**Validates: Requirements 3.5**

### Property 9: Seed Badge Styling

*For all* seed badge elements, they should have circular border-radius, red background color, and neon red box-shadow glow effect.

**Validates: Requirements 3.6**

### Property 10: Action Button Transform

*For all* action buttons with gaming-btn class, the computed transform should include skewX(-12deg) at rest state.

**Validates: Requirements 4.3**

### Property 11: Action Button Hover Transform

*For any* action button with gaming-btn class, when hover state is simulated, the transform should change to skewX(0deg) and box-shadow should enhance.

**Validates: Requirements 4.4**

### Property 12: Action Button Typography

*For all* action buttons with gaming-btn class, the font-family should be 'Barlow Condensed', text-transform should be 'uppercase', and font-style should be 'italic'.

**Validates: Requirements 4.5**

### Property 13: Button Ripple Effect

*For any* button element, when click event is simulated, a ripple effect animation should be triggered (visible through animation property or pseudo-element creation).

**Validates: Requirements 5.1**

### Property 14: Card Hover Transition

*For any* card element, when hover state is simulated, the transition property should be set with duration of 0.3s and easing function.

**Validates: Requirements 5.2**

### Property 15: Modal Animation Behavior

*For any* modal element, when opened, the backdrop should have backdrop-filter blur effect and the modal should have fade-in animation.

**Validates: Requirements 5.4**

### Property 16: Touch Target Minimum Size

*For all* interactive elements (buttons, links, inputs, checkboxes), the computed width and height should be at least 44px to meet touch target accessibility requirements.

**Validates: Requirements 5.6, 8.4**

### Property 17: Modal Input Field Gaming Style

*For all* input fields within modal elements, they should have gaming-style borders with neon effects, and when focus is simulated, box-shadow glow should enhance.

**Validates: Requirements 6.3**

### Property 18: Modal Button Transform

*For all* action buttons within modal elements, the computed transform should include skew function consistent with gaming button styling.

**Validates: Requirements 6.4**

### Property 19: Modal Close Animation

*For any* modal element, when close action is triggered, the modal should animate out with fade transition effect.

**Validates: Requirements 6.5**

### Property 20: Status Indicator Pulse Animation

*For all* status indicators in active states (checked-in, pending), the animation property should include a pulse effect with appropriate timing.

**Validates: Requirements 7.5**

### Property 21: Focus Indicator Visibility

*For any* focusable interactive element, when focus state is simulated, the outline property should display a visible neon red indicator.

**Validates: Requirements 9.6**

### Property 22: Color Contrast Compliance

*For all* text elements on the page, the contrast ratio between text color and background color should meet or exceed WCAG 2.1 AA standards (4.5:1 for normal text, 3:1 for large text).

**Validates: Requirements 9.1**

### Property 23: GPU-Accelerated Animations

*For all* animated elements, the animation keyframes should use CSS transform or opacity properties (not layout properties like width, height, top, left) to leverage GPU acceleration.

**Validates: Requirements 10.1**

### Property 24: Will-Change Optimization

*For all* elements with animations or transitions, the will-change property should be applied to optimize rendering performance.

**Validates: Requirements 10.2**

## Error Handling

### CSS Fallbacks

The gaming design includes graceful degradation for browsers that don't support modern CSS features:

1. **Backdrop Filter Fallback**: If backdrop-filter is not supported, modals will use solid background with higher opacity
2. **Transform Fallback**: If CSS transforms are not supported, elements will display without skew effects but maintain functionality
3. **Custom Properties Fallback**: If CSS variables are not supported, fallback values are provided inline

### Missing Font Handling

If custom fonts (Barlow Condensed, Space Grotesk) fail to load:
- System font stack provides fallback: `system-ui, -apple-system, sans-serif`
- Font loading is monitored with `font-display: swap` to prevent invisible text

### Animation Performance Issues

If animations cause performance problems:
- Animations are automatically disabled when `prefers-reduced-motion` is detected
- Will-change property is removed after animations complete to free GPU resources
- Complex animations are simplified on mobile devices through media queries

### Color Contrast Issues

If neon glow effects reduce text readability:
- High contrast mode automatically removes decorative glows
- Text always maintains minimum contrast ratio against backgrounds
- Focus indicators use solid outlines in addition to glows

### Browser Compatibility

The design targets modern browsers (last 2 versions):
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers with equivalent versions

Older browsers receive simplified styling without advanced effects but maintain full functionality.

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and individual component styling
**Property Tests**: Verify universal properties across all elements of a given type

### Unit Testing Focus

Unit tests will verify:
1. Specific color values for key elements (background, primary buttons, status indicators)
2. Exact transform values for skewed elements at rest state
3. Presence of required CSS classes on gaming-styled components
4. Responsive breakpoint behavior at specific viewport widths
5. Reduced motion media query disables animations
6. Modal backdrop blur effect values
7. Font loading and fallback behavior

Example unit tests:
- Page background is #0A0A0A
- Stat cards have skewY(-1deg) transform at rest
- Search bar focus state has specific box-shadow value
- Mobile viewport (<768px) stacks stat cards vertically
- Seed assignment modal has #1F2937 background

### Property-Based Testing Focus

Property tests will verify universal rules across multiple elements using randomized inputs:

**Test Configuration**:
- Minimum 100 iterations per property test
- Use CSS selector queries to find all elements of a type
- Simulate user interactions (hover, focus, click) programmatically
- Measure computed CSS properties using getComputedStyle()

**Property Test Implementation**:

Each property test will:
1. Query all elements matching a selector (e.g., all buttons, all cards)
2. For each element, verify the property holds true
3. Simulate interactions when testing hover/focus states
4. Use assertion libraries to check computed CSS values

**Tag Format**: Each property test must include a comment tag:
```javascript
// Feature: manage-participant-redesign, Property 1: For all heading elements, font-family should be 'Barlow Condensed' and text-transform should be 'uppercase'
```

### Testing Tools

**Recommended Testing Stack**:
- **Test Framework**: Jest or Vitest for JavaScript testing
- **DOM Testing**: jsdom or happy-dom for simulating browser environment
- **Property Testing Library**: fast-check for JavaScript property-based testing
- **CSS Testing**: getComputedStyle() for verifying applied styles
- **Accessibility Testing**: axe-core for WCAG compliance verification
- **Visual Regression**: Percy or Chromatic for visual diff testing (optional)

### Test Organization

```
tests/
├── unit/
│   ├── gaming-styles.test.js          # Specific value tests
│   ├── responsive-behavior.test.js    # Breakpoint tests
│   └── accessibility.test.js          # A11y specific tests
└── property/
    ├── typography-properties.test.js  # Font and text properties
    ├── color-properties.test.js       # Color consistency properties
    ├── transform-properties.test.js   # Transform and animation properties
    ├── interaction-properties.test.js # Hover, focus, click properties
    └── accessibility-properties.test.js # Touch targets, contrast, focus
```

### Coverage Goals

- **CSS Coverage**: 100% of gaming-style classes tested
- **Component Coverage**: All gaming components (cards, buttons, modals, table) tested
- **Interaction Coverage**: All hover, focus, and click states tested
- **Responsive Coverage**: All breakpoints tested
- **Accessibility Coverage**: All WCAG 2.1 AA criteria verified

### Continuous Integration

Tests should run:
- On every commit to feature branch
- Before merging to main branch
- After CSS file modifications
- On schedule (nightly) for regression detection

### Performance Testing

While not part of unit/property tests, performance should be monitored:
- Lighthouse CI for performance metrics
- First Contentful Paint target: <1.5s on 3G
- Animation frame rate: 60fps on desktop, 30fps minimum on mobile
- CSS file size: <50KB minified and gzipped

