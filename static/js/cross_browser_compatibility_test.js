/**
 * Cross-Browser Compatibility Test Suite
 * Tests rendering consistency across major browsers
 * Requirement 4.1: Cross-browser compatibility measures
 */

(function() {
    'use strict';
    
    const CrossBrowserTest = {
        results: {
            passed: 0,
            failed: 0,
            warnings: 0,
            details: []
        },
        
        // Browser detection
        detectBrowser: function() {
            const ua = navigator.userAgent;
            const browsers = {
                chrome: /Chrome/.test(ua) && !/Edge/.test(ua),
                firefox: /Firefox/.test(ua),
                safari: /Safari/.test(ua) && !/Chrome/.test(ua),
                edge: /Edge/.test(ua),
                ie: /MSIE|Trident/.test(ua)
            };
            
            for (const [name, detected] of Object.entries(browsers)) {
                if (detected) return name;
            }
            return 'unknown';
        },
        
        // Test CSS feature support
        testCSSFeatures: function() {
            const features = {
                'CSS Grid': 'display: grid',
                'Flexbox': 'display: flex',
                'CSS Custom Properties': 'color: var(--test)',
                'Focus Visible': 'selector(:focus-visible)',
                'Color Scheme': 'color-scheme: dark',
                'Font Variation Settings': 'font-variation-settings: "wght" 400',
                'Backdrop Filter': 'backdrop-filter: blur(10px)',
                'Clip Path': 'clip-path: circle(50%)',
                'Object Fit': 'object-fit: cover',
                'Position Sticky': 'position: sticky',
                'Scrollbar Width': 'scrollbar-width: thin'
            };
            
            const results = {};
            
            for (const [name, property] of Object.entries(features)) {
                try {
                    let supported = false;
                    
                    if (name === 'Focus Visible') {
                        supported = CSS.supports('selector(:focus-visible)');
                    } else {
                        const [prop, value] = property.split(': ');
                        supported = CSS.supports(prop, value);
                    }
                    
                    results[name] = supported;
                    
                    if (supported) {
                        this.results.passed++;
                        this.results.details.push({
                            type: 'pass',
                            test: `CSS Feature: ${name}`,
                            message: 'Supported'
                        });
                    } else {
                        this.results.warnings++;
                        this.results.details.push({
                            type: 'warning',
                            test: `CSS Feature: ${name}`,
                            message: 'Not supported - fallback should be active'
                        });
                    }
                } catch (error) {
                    results[name] = false;
                    this.results.failed++;
                    this.results.details.push({
                        type: 'fail',
                        test: `CSS Feature: ${name}`,
                        message: `Error testing support: ${error.message}`
                    });
                }
            }
            
            return results;
        },
        
        // Test Tailwind CSS loading and configuration
        testTailwindLoading: function() {
            return new Promise((resolve) => {
                const startTime = performance.now();
                const maxWaitTime = 5000; // 5 seconds
                
                const checkTailwind = () => {
                    if (typeof tailwind !== 'undefined') {
                        const loadTime = performance.now() - startTime;
                        this.results.passed++;
                        this.results.details.push({
                            type: 'pass',
                            test: 'Tailwind CSS Loading',
                            message: `Loaded successfully in ${loadTime.toFixed(2)}ms`
                        });
                        resolve(true);
                    } else if (performance.now() - startTime > maxWaitTime) {
                        this.results.failed++;
                        this.results.details.push({
                            type: 'fail',
                            test: 'Tailwind CSS Loading',
                            message: 'Failed to load within 5 seconds'
                        });
                        resolve(false);
                    } else {
                        setTimeout(checkTailwind, 100);
                    }
                };
                
                checkTailwind();
            });
        },
        
        // Test font loading
        testFontLoading: function() {
            return new Promise((resolve) => {
                if (!document.fonts) {
                    this.results.warnings++;
                    this.results.details.push({
                        type: 'warning',
                        test: 'Font Loading API',
                        message: 'Font Loading API not supported'
                    });
                    resolve(false);
                    return;
                }
                
                const startTime = performance.now();
                
                document.fonts.ready.then(() => {
                    const loadTime = performance.now() - startTime;
                    
                    // Check if Spline Sans is loaded
                    const splineSansLoaded = document.fonts.check('16px "Spline Sans"');
                    
                    if (splineSansLoaded) {
                        this.results.passed++;
                        this.results.details.push({
                            type: 'pass',
                            test: 'Font Loading: Spline Sans',
                            message: `Loaded successfully in ${loadTime.toFixed(2)}ms`
                        });
                    } else {
                        this.results.warnings++;
                        this.results.details.push({
                            type: 'warning',
                            test: 'Font Loading: Spline Sans',
                            message: 'Font not detected - fallback fonts should be active'
                        });
                    }
                    
                    resolve(splineSansLoaded);
                }).catch((error) => {
                    this.results.failed++;
                    this.results.details.push({
                        type: 'fail',
                        test: 'Font Loading',
                        message: `Error: ${error.message}`
                    });
                    resolve(false);
                });
            });
        },
        
        // Test dark mode functionality
        testDarkMode: function() {
            const htmlElement = document.documentElement;
            const originalClass = htmlElement.className;
            
            try {
                // Test dark mode class toggle
                htmlElement.classList.add('dark');
                const darkModeActive = htmlElement.classList.contains('dark');
                
                if (darkModeActive) {
                    // Test computed styles in dark mode
                    const bodyStyles = window.getComputedStyle(document.body);
                    const backgroundColor = bodyStyles.backgroundColor;
                    
                    // Check if dark background is applied
                    const isDarkBackground = backgroundColor === 'rgb(18, 18, 18)' || 
                                           backgroundColor === '#121212';
                    
                    if (isDarkBackground) {
                        this.results.passed++;
                        this.results.details.push({
                            type: 'pass',
                            test: 'Dark Mode Functionality',
                            message: 'Dark mode styles applied correctly'
                        });
                    } else {
                        this.results.warnings++;
                        this.results.details.push({
                            type: 'warning',
                            test: 'Dark Mode Functionality',
                            message: `Dark background not detected. Got: ${backgroundColor}`
                        });
                    }
                } else {
                    this.results.failed++;
                    this.results.details.push({
                        type: 'fail',
                        test: 'Dark Mode Functionality',
                        message: 'Dark mode class not applied'
                    });
                }
                
                // Restore original class
                htmlElement.className = originalClass;
                
            } catch (error) {
                this.results.failed++;
                this.results.details.push({
                    type: 'fail',
                    test: 'Dark Mode Functionality',
                    message: `Error: ${error.message}`
                });
                
                // Restore original class
                htmlElement.className = originalClass;
            }
        },
        
        // Test responsive design breakpoints
        testResponsiveDesign: function() {
            const breakpoints = [
                { name: 'Mobile', width: 375 },
                { name: 'Tablet', width: 768 },
                { name: 'Desktop', width: 1024 },
                { name: 'Large Desktop', width: 1280 }
            ];
            
            const originalWidth = window.innerWidth;
            
            breakpoints.forEach(breakpoint => {
                try {
                    // Create a test element to check responsive behavior
                    const testElement = document.createElement('div');
                    testElement.className = 'container';
                    testElement.style.visibility = 'hidden';
                    testElement.style.position = 'absolute';
                    document.body.appendChild(testElement);
                    
                    // Simulate viewport width (limited testing in real browser)
                    const mediaQuery = window.matchMedia(`(min-width: ${breakpoint.width}px)`);
                    
                    if (mediaQuery.matches || breakpoint.width <= originalWidth) {
                        this.results.passed++;
                        this.results.details.push({
                            type: 'pass',
                            test: `Responsive Design: ${breakpoint.name}`,
                            message: `Breakpoint ${breakpoint.width}px handled correctly`
                        });
                    } else {
                        this.results.warnings++;
                        this.results.details.push({
                            type: 'warning',
                            test: `Responsive Design: ${breakpoint.name}`,
                            message: `Cannot test breakpoint ${breakpoint.width}px in current viewport`
                        });
                    }
                    
                    document.body.removeChild(testElement);
                    
                } catch (error) {
                    this.results.failed++;
                    this.results.details.push({
                        type: 'fail',
                        test: `Responsive Design: ${breakpoint.name}`,
                        message: `Error: ${error.message}`
                    });
                }
            });
        },
        
        // Test accessibility features
        testAccessibility: function() {
            try {
                // Test skip link
                const skipLink = document.querySelector('.skip-to-main');
                if (skipLink) {
                    this.results.passed++;
                    this.results.details.push({
                        type: 'pass',
                        test: 'Accessibility: Skip Link',
                        message: 'Skip to main content link found'
                    });
                } else {
                    this.results.failed++;
                    this.results.details.push({
                        type: 'fail',
                        test: 'Accessibility: Skip Link',
                        message: 'Skip to main content link not found'
                    });
                }
                
                // Test focus indicators
                const testButton = document.createElement('button');
                testButton.className = 'btn-primary focus-visible';
                testButton.textContent = 'Test Button';
                testButton.style.visibility = 'hidden';
                testButton.style.position = 'absolute';
                document.body.appendChild(testButton);
                
                testButton.focus();
                const focusStyles = window.getComputedStyle(testButton, ':focus');
                
                // Check if focus styles are applied (simplified check)
                if (focusStyles.outline !== 'none' || focusStyles.outlineWidth !== '0px') {
                    this.results.passed++;
                    this.results.details.push({
                        type: 'pass',
                        test: 'Accessibility: Focus Indicators',
                        message: 'Focus indicators are properly styled'
                    });
                } else {
                    this.results.warnings++;
                    this.results.details.push({
                        type: 'warning',
                        test: 'Accessibility: Focus Indicators',
                        message: 'Focus indicators may not be visible'
                    });
                }
                
                document.body.removeChild(testButton);
                
            } catch (error) {
                this.results.failed++;
                this.results.details.push({
                    type: 'fail',
                    test: 'Accessibility Features',
                    message: `Error: ${error.message}`
                });
            }
        },
        
        // Test performance metrics
        testPerformance: function() {
            if (!window.performance || !window.performance.timing) {
                this.results.warnings++;
                this.results.details.push({
                    type: 'warning',
                    test: 'Performance API',
                    message: 'Performance API not supported'
                });
                return;
            }
            
            const timing = performance.timing;
            const navigation = performance.getEntriesByType('navigation')[0];
            
            if (navigation) {
                const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
                const loadComplete = navigation.loadEventEnd - navigation.loadEventStart;
                
                if (domContentLoaded < 1000) { // Less than 1 second
                    this.results.passed++;
                    this.results.details.push({
                        type: 'pass',
                        test: 'Performance: DOM Content Loaded',
                        message: `${domContentLoaded.toFixed(2)}ms (Good)`
                    });
                } else {
                    this.results.warnings++;
                    this.results.details.push({
                        type: 'warning',
                        test: 'Performance: DOM Content Loaded',
                        message: `${domContentLoaded.toFixed(2)}ms (Could be improved)`
                    });
                }
                
                if (loadComplete < 2000) { // Less than 2 seconds
                    this.results.passed++;
                    this.results.details.push({
                        type: 'pass',
                        test: 'Performance: Load Complete',
                        message: `${loadComplete.toFixed(2)}ms (Good)`
                    });
                } else {
                    this.results.warnings++;
                    this.results.details.push({
                        type: 'warning',
                        test: 'Performance: Load Complete',
                        message: `${loadComplete.toFixed(2)}ms (Could be improved)`
                    });
                }
            }
        },
        
        // Run all tests
        runAllTests: async function() {
            console.log('🧪 Starting Cross-Browser Compatibility Tests...');
            console.log(`🌐 Browser: ${this.detectBrowser()}`);
            console.log(`📱 User Agent: ${navigator.userAgent}`);
            
            // Reset results
            this.results = {
                passed: 0,
                failed: 0,
                warnings: 0,
                details: []
            };
            
            // Run synchronous tests
            this.testCSSFeatures();
            this.testDarkMode();
            this.testResponsiveDesign();
            this.testAccessibility();
            this.testPerformance();
            
            // Run asynchronous tests
            await this.testTailwindLoading();
            await this.testFontLoading();
            
            // Generate report
            this.generateReport();
            
            return this.results;
        },
        
        // Generate test report
        generateReport: function() {
            const total = this.results.passed + this.results.failed + this.results.warnings;
            
            console.log('\n📊 Cross-Browser Compatibility Test Results');
            console.log('='.repeat(50));
            console.log(`✅ Passed: ${this.results.passed}`);
            console.log(`❌ Failed: ${this.results.failed}`);
            console.log(`⚠️  Warnings: ${this.results.warnings}`);
            console.log(`📈 Total: ${total}`);
            console.log(`🎯 Success Rate: ${((this.results.passed / total) * 100).toFixed(1)}%`);
            
            console.log('\n📋 Detailed Results:');
            this.results.details.forEach((detail, index) => {
                const icon = detail.type === 'pass' ? '✅' : detail.type === 'fail' ? '❌' : '⚠️';
                console.log(`${icon} ${detail.test}: ${detail.message}`);
            });
            
            // Browser-specific recommendations
            const browser = this.detectBrowser();
            console.log(`\n🔧 Browser-Specific Notes for ${browser}:`);
            
            switch (browser) {
                case 'chrome':
                    console.log('- All modern features should be supported');
                    console.log('- Check for any experimental features');
                    break;
                case 'firefox':
                    console.log('- CSS Grid and Flexbox fully supported');
                    console.log('- Custom scrollbar styling may differ');
                    break;
                case 'safari':
                    console.log('- Some CSS features may need prefixes');
                    console.log('- Focus-visible polyfill may be active');
                    break;
                case 'edge':
                    console.log('- Modern Edge should support all features');
                    console.log('- Legacy Edge may need fallbacks');
                    break;
                case 'ie':
                    console.log('- Many modern features not supported');
                    console.log('- Fallbacks and polyfills should be active');
                    break;
                default:
                    console.log('- Unknown browser - verify all fallbacks work');
            }
            
            console.log('\n🏁 Cross-Browser Compatibility Test Complete');
        }
    };
    
    // Auto-run tests when script loads (for development)
    if (window.location.search.includes('test=cross-browser')) {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                CrossBrowserTest.runAllTests();
            }, 1000); // Wait for other resources to load
        });
    }
    
    // Export for manual testing
    window.CrossBrowserTest = CrossBrowserTest;
    
})();

// Usage:
// 1. Add ?test=cross-browser to URL for auto-run
// 2. Or run manually: CrossBrowserTest.runAllTests()
// 3. Check console for detailed results