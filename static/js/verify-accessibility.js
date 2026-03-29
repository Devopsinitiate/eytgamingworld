/**
 * WCAG 2.1 AA Accessibility Verification Script
 * Tests color contrast ratios and touch target sizes
 * 
 * Requirements: 9.1, 9.4, 5.6, 8.4
 */

// Utility function to calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio between two colors
function getContrastRatio(rgb1, rgb2) {
  const l1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const l2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Parse RGB color string to object
function parseRGB(rgbString) {
  const match = rgbString.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) return null;
  return {
    r: parseInt(match[1]),
    g: parseInt(match[2]),
    b: parseInt(match[3])
  };
}

// Get background color of element (including inherited backgrounds)
function getEffectiveBackgroundColor(element) {
  let current = element;
  while (current) {
    const bg = window.getComputedStyle(current).backgroundColor;
    const rgb = parseRGB(bg);
    if (rgb && (rgb.r !== 0 || rgb.g !== 0 || rgb.b !== 0)) {
      return rgb;
    }
    current = current.parentElement;
  }
  // Default to deep black background
  return { r: 10, g: 10, b: 10 };
}

// Test color contrast for an element
function testContrast(element, description, isLargeText = false) {
  if (!element) {
    return {
      pass: false,
      description,
      message: `${description}: Element not found - SKIP`
    };
  }
  
  const color = window.getComputedStyle(element).color;
  const textRGB = parseRGB(color);
  const bgRGB = getEffectiveBackgroundColor(element);
  
  if (!textRGB || !bgRGB) {
    return {
      pass: false,
      description,
      message: `${description}: Could not parse colors - FAIL`
    };
  }
  
  const ratio = getContrastRatio(textRGB, bgRGB);
  const requiredRatio = isLargeText ? 3.0 : 4.5;
  const pass = ratio >= requiredRatio;
  
  return {
    pass,
    description,
    ratio: ratio.toFixed(2),
    required: requiredRatio,
    message: `${description}: ${ratio.toFixed(2)}:1 (required: ${requiredRatio}:1) - ${pass ? 'PASS' : 'FAIL'}`
  };
}

// Test touch target size
function testTouchTarget(element, description) {
  if (!element) {
    return {
      pass: false,
      description,
      message: `${description}: Element not found - SKIP`
    };
  }
  
  const rect = element.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  const minSize = 44;
  
  const pass = width >= minSize && height >= minSize;
  
  return {
    pass,
    description,
    width: Math.round(width),
    height: Math.round(height),
    message: `${description}: ${Math.round(width)}px × ${Math.round(height)}px (required: ${minSize}px × ${minSize}px) - ${pass ? 'PASS' : 'FAIL'}`
  };
}

// Test ARIA support for screen reader announcements
function testARIASupport() {
  const results = [];
  
  // Check for ARIA live regions
  const liveRegions = document.querySelectorAll('[aria-live]');
  results.push({
    pass: liveRegions.length > 0,
    description: 'ARIA Live Regions',
    message: `ARIA Live Regions: ${liveRegions.length} found - ${liveRegions.length > 0 ? 'PASS' : 'FAIL'}`
  });
  
  // Check for proper role attributes on status elements
  const statusElements = document.querySelectorAll('[role="status"]');
  results.push({
    pass: statusElements.length > 0,
    description: 'Status Role Elements',
    message: `Status Role Elements: ${statusElements.length} found - ${statusElements.length > 0 ? 'PASS' : 'FAIL'}`
  });
  
  // Check for aria-atomic on live regions
  const atomicRegions = document.querySelectorAll('[aria-atomic="true"]');
  results.push({
    pass: atomicRegions.length > 0,
    description: 'ARIA Atomic Regions',
    message: `ARIA Atomic Regions: ${atomicRegions.length} found - ${atomicRegions.length > 0 ? 'PASS' : 'FAIL'}`
  });
  
  return results;
}

// Main verification function
function verifyAccessibility() {
  console.log('='.repeat(60));
  console.log('WCAG 2.1 AA ACCESSIBILITY VERIFICATION');
  console.log('='.repeat(60));
  console.log('');
  
  const contrastResults = [];
  const touchTargetResults = [];
  
  // Color Contrast Tests
  console.log('COLOR CONTRAST TESTS');
  console.log('-'.repeat(60));
  
  const testElements = [
    { selector: '.gaming-stat-value', description: 'Stat Card Value (large text)', isLarge: true },
    { selector: '.gaming-stat-label', description: 'Stat Card Label', isLarge: false },
    { selector: '.gaming-btn-primary', description: 'Primary Button Text', isLarge: false },
    { selector: '.gaming-btn-ghost', description: 'Ghost Button Text', isLarge: false },
    { selector: '.gaming-btn-action', description: 'Action Button Text', isLarge: false },
    { selector: '.gaming-search-bar', description: 'Search Bar Text', isLarge: false },
    { selector: '.gaming-table th', description: 'Table Header Text', isLarge: false },
    { selector: '.gaming-table td', description: 'Table Cell Text', isLarge: false },
    { selector: '.gaming-status-indicator span:not(.gaming-status-dot)', description: 'Status Indicator Text', isLarge: false },
    { selector: '.gaming-label', description: 'Form Label Text', isLarge: false },
    { selector: '.gaming-input', description: 'Input Field Text', isLarge: false },
    { selector: '.gaming-seed-badge', description: 'Seed Badge Text', isLarge: false },
    { selector: '.gaming-heading-primary', description: 'Primary Heading (large text)', isLarge: true },
    { selector: '.gaming-heading-secondary', description: 'Secondary Heading (large text)', isLarge: true }
  ];
  
  testElements.forEach(({ selector, description, isLarge }) => {
    const element = document.querySelector(selector);
    const result = testContrast(element, description, isLarge);
    contrastResults.push(result);
    console.log(result.message);
  });
  
  console.log('');
  console.log('TOUCH TARGET TESTS');
  console.log('-'.repeat(60));
  
  const touchElements = [
    { selector: '.gaming-btn-primary', description: 'Primary Button' },
    { selector: '.gaming-btn-ghost', description: 'Ghost Button' },
    { selector: '.gaming-btn-action', description: 'Action Button' },
    { selector: '.gaming-search-bar', description: 'Search Bar' },
    { selector: '.gaming-input', description: 'Input Field' },
    { selector: '.gaming-modal-close', description: 'Modal Close Button' },
    { selector: 'input[type="checkbox"]', description: 'Checkbox' },
    { selector: 'input[type="radio"]', description: 'Radio Button' },
    { selector: 'a', description: 'Link' },
    { selector: 'button', description: 'Generic Button' }
  ];
  
  touchElements.forEach(({ selector, description }) => {
    const element = document.querySelector(selector);
    const result = testTouchTarget(element, description);
    touchTargetResults.push(result);
    console.log(result.message);
  });
  
  console.log('');
  console.log('SCREEN READER SUPPORT TESTS');
  console.log('-'.repeat(60));
  
  const ariaResults = testARIASupport();
  ariaResults.forEach(result => {
    console.log(result.message);
  });
  
  console.log('');
  console.log('='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));
  
  const contrastPassed = contrastResults.filter(r => r.pass).length;
  const contrastTotal = contrastResults.filter(r => !r.message.includes('SKIP')).length;
  const touchPassed = touchTargetResults.filter(r => r.pass).length;
  const touchTotal = touchTargetResults.filter(r => !r.message.includes('SKIP')).length;
  const ariaPassed = ariaResults.filter(r => r.pass).length;
  const ariaTotal = ariaResults.length;
  
  console.log(`Color Contrast: ${contrastPassed}/${contrastTotal} tests passed`);
  console.log(`Touch Targets: ${touchPassed}/${touchTotal} tests passed`);
  console.log(`ARIA Support: ${ariaPassed}/${ariaTotal} tests passed`);
  console.log('');
  
  const allPassed = (contrastPassed === contrastTotal) && 
                    (touchPassed === touchTotal) && 
                    (ariaPassed === ariaTotal);
  
  if (allPassed) {
    console.log('✓ WCAG 2.1 AA COMPLIANT');
  } else {
    console.log('✗ COMPLIANCE ISSUES FOUND');
    console.log('');
    console.log('Failed Tests:');
    
    contrastResults.filter(r => !r.pass && !r.message.includes('SKIP')).forEach(r => {
      console.log(`  - ${r.description}: ${r.ratio}:1 (required: ${r.required}:1)`);
    });
    
    touchTargetResults.filter(r => !r.pass && !r.message.includes('SKIP')).forEach(r => {
      console.log(`  - ${r.description}: ${r.width}px × ${r.height}px (required: 44px × 44px)`);
    });
    
    ariaResults.filter(r => !r.pass).forEach(r => {
      console.log(`  - ${r.description}`);
    });
  }
  
  console.log('='.repeat(60));
  
  return {
    contrastResults,
    touchTargetResults,
    ariaResults,
    summary: {
      contrastPassed,
      contrastTotal,
      touchPassed,
      touchTotal,
      ariaPassed,
      ariaTotal,
      allPassed
    }
  };
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    verifyAccessibility,
    testContrast,
    testTouchTarget,
    testARIASupport,
    getContrastRatio,
    parseRGB
  };
}

// Auto-run if loaded in browser
if (typeof window !== 'undefined') {
  window.verifyAccessibility = verifyAccessibility;
  console.log('Accessibility verification script loaded.');
  console.log('Run verifyAccessibility() to test the current page.');
}
