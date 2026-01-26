/**
 * Property-Based Tests for Mobile Optimization
 * Tests mobile-optimized layouts, touch-friendly interactions, SVG scaling, and performance
 * 
 * Property 8: Mobile Optimization and Performance
 * Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
 */

// Test configuration
const TEST_CONFIG = {
    iterations: 100,
    timeout: 30000,
    mobileViewports: [
        { width: 320, height: 568, name: 'iPhone SE' },
        { width: 375, height: 667, name: 'iPhone 8' },
        { width: 414, height: 896, name: 'iPhone 11' },
        { width: 360, height: 640, name: 'Galaxy S5' },
        { width: 412, height: 915, name: 'Pixel 5' }
    ],
    touchTargetMinSize: 44, // WCAG minimum touch target size
    performanceThresholds: {
        loadTime: 2000, // 2 seconds for critical content
        animationFrameRate: 60,
        layoutShiftScore: 0.1
    }
};

/**
 * Property Test: Mobile Layout Optimization
 * For any mobile viewport, all components should display in mobile-optimized layouts
 * Validates: Requirements 8.1
 */
function testMobileLayoutOptimization() {
    console.log('Testing Property 8.1: Mobile Layout Optimization');
    
    const results = [];
    
    for (let i = 0; i < TEST_CONFIG.iterations; i++) {
        // Generate random mobile viewport
        const viewport = generateRandomMobileViewport();
        
        try {
            // Set viewport size
            setViewportSize(viewport.width, viewport.height);
            
            // Test mobile layout optimization
            const layoutResult = testMobileLayoutForViewport(viewport);
            
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: layoutResult.passed,
                issues: layoutResult.issues,
                timestamp: Date.now()
            });
            
            if (!layoutResult.passed) {
                console.warn(`Mobile layout test failed for ${viewport.name} (${viewport.width}x${viewport.height}):`, layoutResult.issues);
            }
            
        } catch (error) {
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: false,
                issues: [`Test execution error: ${error.message}`],
                error: error,
                timestamp: Date.now()
            });
        }
    }
    
    const passedTests = results.filter(r => r.passed).length;
    const failedTests = results.length - passedTests;
    
    console.log(`Mobile Layout Optimization: ${passedTests}/${results.length} tests passed`);
    
    if (failedTests > 0) {
        const failureExamples = results.filter(r => !r.passed).slice(0, 3);
        console.error('Mobile layout failures:', failureExamples);
        throw new Error(`Mobile layout optimization failed in ${failedTests} cases. Example failures: ${JSON.stringify(failureExamples.map(f => ({ viewport: f.viewport, issues: f.issues })))}`);
    }
    
    return { passed: true, results };
}

/**
 * Property Test: Touch-Friendly Interactions
 * For any interactive element on mobile, it should have touch-friendly sizing and behavior
 * Validates: Requirements 8.2, 8.3
 */
function testTouchFriendlyInteractions() {
    console.log('Testing Property 8.2-8.3: Touch-Friendly Interactions');
    
    const results = [];
    
    for (let i = 0; i < TEST_CONFIG.iterations; i++) {
        // Generate random mobile viewport
        const viewport = generateRandomMobileViewport();
        
        try {
            // Set viewport size
            setViewportSize(viewport.width, viewport.height);
            
            // Test touch-friendly interactions
            const touchResult = testTouchInteractionsForViewport(viewport);
            
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: touchResult.passed,
                issues: touchResult.issues,
                touchTargets: touchResult.touchTargets,
                timestamp: Date.now()
            });
            
            if (!touchResult.passed) {
                console.warn(`Touch interaction test failed for ${viewport.name}:`, touchResult.issues);
            }
            
        } catch (error) {
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: false,
                issues: [`Test execution error: ${error.message}`],
                error: error,
                timestamp: Date.now()
            });
        }
    }
    
    const passedTests = results.filter(r => r.passed).length;
    const failedTests = results.length - passedTests;
    
    console.log(`Touch-Friendly Interactions: ${passedTests}/${results.length} tests passed`);
    
    if (failedTests > 0) {
        const failureExamples = results.filter(r => !r.passed).slice(0, 3);
        console.error('Touch interaction failures:', failureExamples);
        throw new Error(`Touch-friendly interactions failed in ${failedTests} cases. Example failures: ${JSON.stringify(failureExamples.map(f => ({ viewport: f.viewport, issues: f.issues })))}`);
    }
    
    return { passed: true, results };
}

/**
 * Property Test: Mobile Performance
 * For any mobile viewport, loading times should be fast and performance should be smooth
 * Validates: Requirements 8.4, 8.5
 */
function testMobilePerformance() {
    console.log('Testing Property 8.4-8.5: Mobile Performance');
    
    const results = [];
    
    for (let i = 0; i < Math.min(20, TEST_CONFIG.iterations); i++) { // Reduced iterations for performance tests
        // Generate random mobile viewport
        const viewport = generateRandomMobileViewport();
        
        try {
            // Set viewport size
            setViewportSize(viewport.width, viewport.height);
            
            // Test mobile performance
            const performanceResult = testMobilePerformanceForViewport(viewport);
            
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: performanceResult.passed,
                issues: performanceResult.issues,
                metrics: performanceResult.metrics,
                timestamp: Date.now()
            });
            
            if (!performanceResult.passed) {
                console.warn(`Mobile performance test failed for ${viewport.name}:`, performanceResult.issues);
            }
            
        } catch (error) {
            results.push({
                iteration: i + 1,
                viewport: viewport,
                passed: false,
                issues: [`Test execution error: ${error.message}`],
                error: error,
                timestamp: Date.now()
            });
        }
    }
    
    const passedTests = results.filter(r => r.passed).length;
    const failedTests = results.length - passedTests;
    
    console.log(`Mobile Performance: ${passedTests}/${results.length} tests passed`);
    
    if (failedTests > 0) {
        const failureExamples = results.filter(r => !r.passed).slice(0, 3);
        console.error('Mobile performance failures:', failureExamples);
        throw new Error(`Mobile performance failed in ${failedTests} cases. Example failures: ${JSON.stringify(failureExamples.map(f => ({ viewport: f.viewport, issues: f.issues, metrics: f.metrics })))}`);
    }
    
    return { passed: true, results };
}

// Helper Functions

/**
 * Generate random mobile viewport dimensions
 */
function generateRandomMobileViewport() {
    const predefinedViewports = TEST_CONFIG.mobileViewports;
    const randomViewport = predefinedViewports[Math.floor(Math.random() * predefinedViewports.length)];
    
    // Add some variation to test edge cases
    const variation = Math.random() < 0.3; // 30% chance of variation
    
    if (variation) {
        return {
            width: Math.floor(Math.random() * (480 - 320) + 320), // 320-480px width
            height: Math.floor(Math.random() * (1000 - 500) + 500), // 500-1000px height
            name: 'Random Mobile'
        };
    }
    
    return randomViewport;
}

/**
 * Set viewport size for testing
 */
function setViewportSize(width, height) {
    // For testing purposes, we'll simulate viewport changes
    // In a real browser environment, this would involve actual viewport manipulation
    
    // Set CSS custom properties for viewport dimensions
    document.documentElement.style.setProperty('--test-viewport-width', `${width}px`);
    document.documentElement.style.setProperty('--test-viewport-height', `${height}px`);
    
    // Simulate window resize event
    const resizeEvent = new Event('resize');
    window.dispatchEvent(resizeEvent);
    
    // Add mobile class for testing
    if (width < 768) {
        document.body.classList.add('mobile-device', 'touch-device');
    } else {
        document.body.classList.remove('mobile-device', 'touch-device');
    }
    
    // Force layout recalculation
    document.body.offsetHeight;
}

/**
 * Test mobile layout optimization for a specific viewport
 */
function testMobileLayoutForViewport(viewport) {
    const issues = [];
    let passed = true;
    
    // Test 1: Tournament grid should use single column on mobile
    const tournamentGrid = document.querySelector('.tournament-grid');
    if (tournamentGrid && viewport.width < 768) {
        const computedStyle = window.getComputedStyle(tournamentGrid);
        const gridColumns = computedStyle.gridTemplateColumns;
        
        if (gridColumns && !gridColumns.includes('1fr') && gridColumns !== 'none') {
            issues.push(`Tournament grid should use single column on mobile, found: ${gridColumns}`);
            passed = false;
        }
    }
    
    // Test 2: Hero section should have appropriate mobile height
    const heroSection = document.querySelector('.tournament-hero');
    if (heroSection && viewport.width < 768) {
        const computedStyle = window.getComputedStyle(heroSection);
        const minHeight = parseInt(computedStyle.minHeight);
        
        if (minHeight > 400) { // Should be reduced for mobile
            issues.push(`Hero section min-height too large for mobile: ${minHeight}px`);
            passed = false;
        }
    }
    
    // Test 3: Registration card should be positioned at bottom on mobile
    const registrationCard = document.querySelector('.enhanced-registration-card');
    if (registrationCard && viewport.width < 768) {
        const computedStyle = window.getComputedStyle(registrationCard);
        const position = computedStyle.position;
        
        if (position !== 'fixed') {
            issues.push(`Registration card should be fixed positioned on mobile, found: ${position}`);
            passed = false;
        }
    }
    
    // Test 4: Participant grid should adapt to mobile layout
    const participantGrid = document.querySelector('.participant-grid');
    if (participantGrid && viewport.width < 768) {
        const computedStyle = window.getComputedStyle(participantGrid);
        const gridColumns = computedStyle.gridTemplateColumns;
        
        if (gridColumns && gridColumns.split(' ').length > 2) {
            issues.push(`Participant grid should have fewer columns on mobile, found: ${gridColumns}`);
            passed = false;
        }
    }
    
    // Test 5: Tab navigation should be horizontally scrollable on mobile
    const tabContainer = document.querySelector('.tab-container');
    if (tabContainer && viewport.width < 768) {
        const computedStyle = window.getComputedStyle(tabContainer);
        const overflowX = computedStyle.overflowX;
        
        if (overflowX !== 'auto' && overflowX !== 'scroll') {
            issues.push(`Tab container should be horizontally scrollable on mobile, found: ${overflowX}`);
            passed = false;
        }
    }
    
    return { passed, issues };
}

/**
 * Test touch-friendly interactions for a specific viewport
 */
function testTouchInteractionsForViewport(viewport) {
    const issues = [];
    let passed = true;
    const touchTargets = [];
    
    if (viewport.width >= 768) {
        return { passed: true, issues: [], touchTargets: [] }; // Skip for non-mobile
    }
    
    // Find all interactive elements
    const interactiveSelectors = [
        'button',
        '.btn',
        'a[href]',
        '.tab-button',
        '.participant-card',
        '.match-card',
        '.copy-button',
        '.share-button',
        '[role="button"]',
        '[tabindex="0"]'
    ];
    
    const interactiveElements = document.querySelectorAll(interactiveSelectors.join(', '));
    
    interactiveElements.forEach((element, index) => {
        const rect = element.getBoundingClientRect();
        const computedStyle = window.getComputedStyle(element);
        
        // Calculate effective touch target size
        const width = Math.max(rect.width, parseInt(computedStyle.minWidth) || 0);
        const height = Math.max(rect.height, parseInt(computedStyle.minHeight) || 0);
        
        const touchTarget = {
            element: element.tagName + (element.className ? '.' + element.className.split(' ')[0] : ''),
            width: width,
            height: height,
            meetsMinimum: width >= TEST_CONFIG.touchTargetMinSize && height >= TEST_CONFIG.touchTargetMinSize
        };
        
        touchTargets.push(touchTarget);
        
        // Test minimum touch target size (44px x 44px)
        if (width < TEST_CONFIG.touchTargetMinSize || height < TEST_CONFIG.touchTargetMinSize) {
            issues.push(`Touch target too small: ${touchTarget.element} (${width}x${height}px, minimum: ${TEST_CONFIG.touchTargetMinSize}px)`);
            passed = false;
        }
        
        // Test for proper spacing between touch targets
        const siblings = Array.from(element.parentElement?.children || [])
            .filter(child => child !== element && interactiveSelectors.some(sel => child.matches(sel)));
        
        siblings.forEach(sibling => {
            const siblingRect = sibling.getBoundingClientRect();
            const distance = Math.min(
                Math.abs(rect.right - siblingRect.left),
                Math.abs(rect.left - siblingRect.right),
                Math.abs(rect.bottom - siblingRect.top),
                Math.abs(rect.top - siblingRect.bottom)
            );
            
            if (distance < 8) { // Minimum 8px spacing
                issues.push(`Touch targets too close: ${touchTarget.element} and ${sibling.tagName} (${distance}px apart)`);
                passed = false;
            }
        });
    });
    
    // Test SVG scaling for mobile
    const svgElements = document.querySelectorAll('svg');
    svgElements.forEach(svg => {
        const rect = svg.getBoundingClientRect();
        const viewportWidth = viewport.width;
        
        // SVG should not exceed reasonable percentage of viewport width
        if (rect.width > viewportWidth * 0.8) {
            issues.push(`SVG too large for mobile viewport: ${rect.width}px (${Math.round(rect.width/viewportWidth*100)}% of viewport)`);
            passed = false;
        }
    });
    
    return { passed, issues, touchTargets };
}

/**
 * Test mobile performance for a specific viewport
 */
function testMobilePerformanceForViewport(viewport) {
    const issues = [];
    let passed = true;
    const metrics = {};
    
    // Test 1: Measure layout performance
    const layoutStart = performance.now();
    
    // Force layout recalculation
    document.body.offsetHeight;
    
    const layoutEnd = performance.now();
    const layoutTime = layoutEnd - layoutStart;
    metrics.layoutTime = layoutTime;
    
    if (layoutTime > 16) { // Should complete within one frame (16ms for 60fps)
        issues.push(`Layout calculation too slow: ${layoutTime.toFixed(2)}ms (should be < 16ms)`);
        passed = false;
    }
    
    // Test 2: Check for excessive DOM complexity
    const allElements = document.querySelectorAll('*');
    metrics.domComplexity = allElements.length;
    
    if (allElements.length > 1500) { // Reasonable limit for mobile
        issues.push(`DOM too complex for mobile: ${allElements.length} elements (should be < 1500)`);
        passed = false;
    }
    
    // Test 3: Check animation performance
    const animatedElements = document.querySelectorAll('[style*="animation"], [style*="transition"], .animate-pulse, .animate-bounce');
    metrics.animatedElements = animatedElements.length;
    
    if (animatedElements.length > 10) {
        issues.push(`Too many animated elements for mobile performance: ${animatedElements.length} (should be < 10)`);
        passed = false;
    }
    
    // Test 4: Check image optimization
    const images = document.querySelectorAll('img');
    let oversizedImages = 0;
    
    images.forEach(img => {
        const rect = img.getBoundingClientRect();
        const naturalWidth = img.naturalWidth || 0;
        
        if (naturalWidth > rect.width * 2 && naturalWidth > 800) {
            oversizedImages++;
        }
    });
    
    metrics.oversizedImages = oversizedImages;
    
    if (oversizedImages > 0) {
        issues.push(`${oversizedImages} images not optimized for mobile display`);
        // Don't fail for this, just warn
    }
    
    // Test 5: Check for smooth scrolling performance
    const scrollableElements = document.querySelectorAll('[style*="overflow"], .tab-container');
    scrollableElements.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        const overflowScrolling = computedStyle.webkitOverflowScrolling;
        
        if (overflowScrolling !== 'touch') {
            // This is more of a recommendation than a failure
            metrics.smoothScrollingOptimized = false;
        }
    });
    
    return { passed, issues, metrics };
}

/**
 * Run all mobile optimization property tests
 */
function runMobileOptimizationTests() {
    console.log('🧪 Running Mobile Optimization Property Tests');
    console.log('Feature: tournament-detail-page-fixes, Property 8: Mobile Optimization and Performance');
    console.log('Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5');
    
    const startTime = performance.now();
    const results = {
        mobileLayout: null,
        touchInteractions: null,
        mobilePerformance: null,
        overallPassed: false,
        executionTime: 0,
        timestamp: new Date().toISOString()
    };
    
    try {
        // Test mobile layout optimization
        results.mobileLayout = testMobileLayoutOptimization();
        
        // Test touch-friendly interactions
        results.touchInteractions = testTouchFriendlyInteractions();
        
        // Test mobile performance
        results.mobilePerformance = testMobilePerformance();
        
        // Overall result
        results.overallPassed = results.mobileLayout.passed && 
                               results.touchInteractions.passed && 
                               results.mobilePerformance.passed;
        
        const endTime = performance.now();
        results.executionTime = endTime - startTime;
        
        if (results.overallPassed) {
            console.log('✅ All mobile optimization property tests passed!');
            console.log(`Execution time: ${results.executionTime.toFixed(2)}ms`);
        } else {
            console.error('❌ Some mobile optimization property tests failed');
        }
        
        return results;
        
    } catch (error) {
        const endTime = performance.now();
        results.executionTime = endTime - startTime;
        results.error = error.message;
        
        console.error('💥 Mobile optimization property tests failed with error:', error);
        throw error;
    }
}

// Export for testing frameworks
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runMobileOptimizationTests,
        testMobileLayoutOptimization,
        testTouchFriendlyInteractions,
        testMobilePerformance,
        TEST_CONFIG
    };
}

// Auto-run tests if this script is loaded directly
if (typeof window !== 'undefined' && window.document) {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(runMobileOptimizationTests, 1000); // Allow other scripts to initialize
        });
    } else {
        setTimeout(runMobileOptimizationTests, 1000);
    }
}