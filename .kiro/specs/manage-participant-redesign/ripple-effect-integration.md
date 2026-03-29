# Ripple Effect Integration Guide

## Overview

The gaming ripple effect has been implemented for the Manage Participant page redesign. This document explains how to integrate the JavaScript ripple effect into the participant_list.html template.

## Files Created

1. **static/js/gaming-ripple-effect.js** - JavaScript module that creates ripple effects on button clicks
2. **static/js/test-ripple-effect.html** - Test page to verify ripple effect functionality
3. **static/css/manage-participant-gaming.css** - Updated with ripple effect CSS (already exists)

## Implementation Details

### JavaScript Functionality

The `gaming-ripple-effect.js` file:
- Automatically detects all gaming-styled buttons on the page
- Adds click event listeners to create ripple effects
- Calculates ripple position based on click coordinates
- Removes ripple elements after animation completes
- Provides a `reinitRippleEffect()` function for dynamically added buttons

### CSS Styling

The ripple effect uses:
- `.ripple-effect` class for the animated element
- `@keyframes ripple` animation (scale from 0 to 4, fade out)
- `position: relative` and `overflow: hidden` on button containers

## Integration Steps

### Step 1: Add JavaScript File to Template

Add the following line to the `participant_list.html` template, just before the closing `</body>` tag or in the existing `<script>` section:

```html
<script src="{% static 'js/gaming-ripple-effect.js' %}"></script>
```

**Recommended placement:** After the existing inline JavaScript in the template, before `{% endblock %}`.

### Step 2: Apply Gaming CSS Classes (Optional)

If you want to apply the full gaming aesthetic to the participant page, add the gaming CSS file to the `{% block extra_css %}` section:

```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/manage-participant-gaming.css' %}">
<!-- existing styles -->
{% endblock %}
```

Then update button classes in the template to use gaming styles:
- Replace `bg-[#b91c1c]` buttons with `gaming-btn-primary` class
- Replace ghost/outline buttons with `gaming-btn-ghost` class
- Replace small action buttons with `gaming-btn-action` class

### Step 3: Test the Implementation

1. Open the test page: `static/js/test-ripple-effect.html` in a browser
2. Click buttons to verify ripple effect appears at click position
3. Verify ripple animation completes and element is removed

## Button Selectors

The ripple effect automatically applies to:
- `.gaming-btn-primary`
- `.gaming-btn-ghost`
- `.gaming-btn-action`
- Any button with `class*="gaming-btn"`
- Buttons with `onclick` attributes (e.g., `onclick="assignSeed(...)"`)
- Submit buttons (`button[type="submit"]`)

## Dynamic Buttons

If buttons are added to the page after initial load (e.g., via AJAX), call:

```javascript
window.reinitRippleEffect();
```

This will re-scan the page and add ripple effects to new buttons.

## Browser Compatibility

The ripple effect works in all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers with equivalent versions

## Accessibility

The ripple effect:
- Does not interfere with keyboard navigation
- Respects `prefers-reduced-motion` media query (animation duration reduced)
- Uses `pointer-events: none` to prevent interaction with ripple element
- Does not affect button functionality or form submission

## Performance

The implementation is optimized for performance:
- Uses CSS transforms (GPU accelerated)
- Removes ripple elements after animation completes
- No memory leaks from event listeners
- Minimal DOM manipulation

## Troubleshooting

### Ripple not appearing
- Verify JavaScript file is loaded (check browser console)
- Ensure button has `position: relative` or `overflow: hidden`
- Check that button selector matches in JavaScript

### Ripple position incorrect
- Verify button has proper positioning context
- Check that click event coordinates are calculated correctly

### Multiple ripples appearing
- The script removes existing ripples before creating new ones
- If issue persists, check for duplicate event listeners

## Example Integration

Here's a complete example of integrating the ripple effect into participant_list.html:

```html
{% extends 'base.html' %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/manage-participant-gaming.css' %}">
<!-- other styles -->
{% endblock %}

{% block body %}
<!-- page content -->

<!-- Add Participant Button with Gaming Style -->
<button onclick="showAddParticipantModal()" class="gaming-btn-primary">
    <span class="material-symbols-outlined">add</span>
    <span>Add Participant</span>
</button>

<!-- Seed Assignment Button -->
<button onclick="assignSeed({{ participant.id }})" class="gaming-btn-action">
    <span class="material-symbols-outlined">tag</span>
    Seed
</button>

<script>
    // Existing JavaScript functions
    function assignSeed(participantId) { /* ... */ }
    function showAddParticipantModal() { /* ... */ }
    // ... other functions
</script>

<!-- Add Ripple Effect Script -->
<script src="{% static 'js/gaming-ripple-effect.js' %}"></script>

{% endblock %}
```

## Next Steps

1. Integrate the JavaScript file into participant_list.html
2. Test ripple effect on all button types
3. Optionally apply full gaming CSS classes for complete aesthetic
4. Verify accessibility and performance
5. Run property-based tests to validate ripple effect behavior

## Related Requirements

- **Requirement 5.1**: Button ripple effect animation on click
- **Property 13**: Button Ripple Effect validation
