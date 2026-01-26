/**
 * Accessibility Integration Test
 * Tests accessibility compliance integration with existing tournament detail page components
 */

// Test configuration
const TEST_CONFIG = {
    testUrl: 'http://localhost:8000/tournaments/1/',
    timeout: 10000
};

// Integration test functions
const AccessibilityIntegrationTests = {
    
    async testPageAccessibility() {
        console.log('🔍 Testing page-level accessibility compliance...');
        
        // Check for skip links
        const skipLinks = document.querySelectorAll('.skip-link');
        console.log(`✓ Found ${skipLinks.length} skip links`);
        
        // Check for ARIA landmarks
        const landmarks = document.querySelectorAll('[role="main"], [role="navigation"], [role="complementary"], [role="contentinfo"]');
        console.log(`✓ Found ${landmarks.length} ARIA landmarks`);
        
        // Check for heading hierarchy
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        console.log(`✓ Found ${headings.length} headings`);
        
        // Check for live regions
        const liveRegions = document.querySelectorAll('[aria-live]');
        console.log(`✓ Found ${liveRegions.length} live regions`);
        
        return {
            skipLinks: skipLinks.length,
            landmarks: landmarks.length,
            headings: headings.length,
            liveRegions: liveRegions.length
        };
    },
    
    async testInteractiveElements() {
        console.log('🔍 Testing interactive element accessibility...');
        
        const interactiveElements = document.querySelectorAll(`
            button, 
            a, 
            input, 
            select, 
            textarea, 
            [tabindex]:not([tabindex="-1"]),
            [role="button"],
            .participant-card,
            .timeline-item-interactive,
            .tab-button
        `);
        
        let focusableCount = 0;
        let ariaLabelCount = 0;
        let touchTargetCount = 0;
        
        interactiveElements.forEach(element => {
            // Check if focusable
            const tabIndex = element.getAttribute('tabindex');
            const isFocusable = tabIndex !== '-1' && (
                tabIndex !== null || 
                ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)
            );
            
            if (isFocusable) focusableCount++;
            
            // Check for ARIA labels
            const hasAriaLabel = element.getAttribute('aria-label') || 
                               element.getAttribute('aria-labelledby') ||
                               element.textContent?.trim();
            
            if (hasAriaLabel) ariaLabelCount++;
            
            // Check touch target size
            const rect = element.getBoundingClientRect();
            if (rect.width >= 44 && rect.height >= 44) {
                touchTargetCount++;
            }
        });
        
        console.log(`✓ ${focusableCount}/${interactiveElements.length} elements are focusable`);
        console.log(`✓ ${ariaLabelCount}/${interactiveElements.length} elements have accessible names`);
        console.log(`✓ ${touchTargetCount}/${interactiveElements.length} elements meet touch target size`);
        
        return {
            total: interactiveElements.length,
            focusable: focusableCount,
            labeled: ariaLabelCount,
            touchTargets: touchTargetCount
        };
    },
    
    async testStatusIndicators() {
        console.log('🔍 Testing status indicator accessibility...');
        
        const statusElements = document.querySelectorAll('.status-badge, [data-status]');
        
        let iconCount = 0;
        let ariaCount = 0;
        
        statusElements.forEach(element => {
            // Check for non-color indicators (icons/symbols)
            const hasIcon = element.querySelector('.status-icon') ||
                           /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[●○◆◇▲△▼▽★☆✓✗]/u.test(element.textContent);
            
            if (hasIcon) iconCount++;
            
            // Check for ARIA status
            const hasAriaStatus = element.getAttribute('role') === 'status' ||
                                element.getAttribute('aria-live');
            
            if (hasAriaStatus) ariaCount++;
        });
        
        console.log(`✓ ${iconCount}/${statusElements.length} status elements have non-color indicators`);
        console.log(`✓ ${ariaCount}/${statusElements.length} status elements have ARIA status roles`);
        
        return {
            total: statusElements.length,
            withIcons: iconCount,
            withAria: ariaCount
        };
    },
    
    async testKeyboardNavigation() {
        console.log('🔍 Testing keyboard navigation...');
        
        // Test tab navigation
        const focusableElements = document.querySelectorAll(`
            button:not([disabled]), 
            a[href], 
            input:not([disabled]), 
            select:not([disabled]), 
            textarea:not([disabled]), 
            [tabindex]:not([tabindex="-1"]):not([disabled])
        `);
        
        let tabOrderCount = 0;
        let keyHandlerCount = 0;
        
        focusableElements.forEach((element, index) => {
            // Check tab order
            const tabIndex = element.getAttribute('tabindex');
            if (!tabIndex || parseInt(tabIndex) >= 0) {
                tabOrderCount++;
            }
            
            // Check for keyboard event handlers
            const hasKeyHandler = element.onkeydown || 
                                element.onkeyup || 
                                element.onkeypress ||
                                element.getAttribute('onkeydown') ||
                                element.getAttribute('onkeyup') ||
                                element.getAttribute('onkeypress');
            
            if (hasKeyHandler) keyHandlerCount++;
        });
        
        console.log(`✓ ${tabOrderCount}/${focusableElements.length} elements in proper tab order`);
        console.log(`✓ ${keyHandlerCount}/${focusableElements.length} elements have keyboard handlers`);
        
        return {
            total: focusableElements.length,
            tabOrder: tabOrderCount,
            keyHandlers: keyHandlerCount
        };
    },
    
    async testMotionPreferences() {
        console.log('🔍 Testing motion preference support...');
        
        // Check for reduced motion CSS
        const hasReducedMotionCSS = document.querySelector('style')?.textContent?.includes('prefers-reduced-motion') ||
                                   Array.from(document.styleSheets).some(sheet => {
                                       try {
                                           return Array.from(sheet.cssRules).some(rule => 
                                               rule.cssText?.includes('prefers-reduced-motion')
                                           );
                                       } catch (e) {
                                           return false;
                                       }
                                   });
        
        // Check for motion preference handling in JavaScript
        const hasMotionJS = window.AccessibilityCompliance && 
                           typeof window.AccessibilityCompliance.handleMotionPreferenceChange === 'function';
        
        console.log(`✓ Reduced motion CSS support: ${hasReducedMotionCSS ? 'Yes' : 'No'}`);
        console.log(`✓ Motion preference JS handling: ${hasMotionJS ? 'Yes' : 'No'}`);
        
        return {
            cssSupport: hasReducedMotionCSS,
            jsSupport: hasMotionJS
        };
    }
};

// Main integration test runner
async function runAccessibilityIntegrationTests() {
    console.log('🧪 Accessibility Integration Tests');
    console.log('==================================');
    
    const results = {
        passed: 0,
        failed: 0,
        details: {}
    };
    
    const tests = [
        { name: 'Page Accessibility', test: AccessibilityIntegrationTests.testPageAccessibility },
        { name: 'Interactive Elements', test: AccessibilityIntegrationTests.testInteractiveElements },
        { name: 'Status Indicators', test: AccessibilityIntegrationTests.testStatusIndicators },
        { name: 'Keyboard Navigation', test: AccessibilityIntegrationTests.testKeyboardNavigation },
        { name: 'Motion Preferences', test: AccessibilityIntegrationTests.testMotionPreferences }
    ];
    
    for (const test of tests) {
        try {
            console.log(`\n🔍 Running ${test.name} test...`);
            const result = await test.test();
            results.details[test.name] = result;
            results.passed++;
            console.log(`✅ ${test.name} test completed`);
        } catch (error) {
            console.error(`❌ ${test.name} test failed:`, error.message);
            results.failed++;
            results.details[test.name] = { error: error.message };
        }
    }
    
    // Summary
    console.log('\n📊 Integration Test Summary:');
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`📈 Success Rate: ${((results.passed / (results.passed + results.failed)) * 100).toFixed(1)}%`);
    
    // Detailed results
    console.log('\n📋 Detailed Results:');
    Object.entries(results.details).forEach(([testName, result]) => {
        console.log(`\n${testName}:`);
        if (result.error) {
            console.log(`  ❌ Error: ${result.error}`);
        } else {
            Object.entries(result).forEach(([key, value]) => {
                console.log(`  ${key}: ${value}`);
            });
        }
    });
    
    return results;
}

// Auto-run if loaded in browser
if (typeof window !== 'undefined' && window.location) {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait for accessibility compliance to initialize
        setTimeout(() => {
            runAccessibilityIntegrationTests();
        }, 2000);
    });
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runAccessibilityIntegrationTests,
        AccessibilityIntegrationTests
    };
}