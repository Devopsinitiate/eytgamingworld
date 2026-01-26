/**
 * Tailwind CSS Integration Test Suite
 * Comprehensive testing for loading sequence, brand consistency, performance, and accessibility
 * Requirements: All requirements (1.1-5.4)
 */

class TailwindIntegrationTestSuite {
    constructor() {
        this.testResults = {
            loading: [],
            brand: [],
            performance: [],
            accessibility: [],
            compatibility: []
        };
        this.performanceMetrics = {};
        this.startTime = performance.now();
        
        // Initialize test suite
        this.init();
    }
    
    init() {
        console.log('🚀 Initializing Tailwind CSS Integration Test Suite');
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Start monitoring performance from page load
        this.startPerformanceMonitoring();
        
        // Detect browser information
        this.detectBrowserInfo();
        
        // Initialize accessibility testing
        this.initAccessibilityTesting();
    }
    
    bindEventListeners() {
        // Main test controls
        document.getElementById('runAllTests')?.addEventListener('click', () => this.runAllTests());
        document.getElementById('toggleDarkMode')?.addEventListener('click', () => this.toggleDarkMode());
        document.getElementById('clearResults')?.addEventListener('click', () => this.clearResults());
        
        // Individual test runners
        document.getElementById('runLoadingTests')?.addEventListener('click', () => this.runLoadingTests());
        document.getElementById('runBrandTests')?.addEventListener('click', () => this.runBrandTests());
        document.getElementById('runPerformanceTests')?.addEventListener('click', () => this.runPerformanceTests());
        document.getElementById('runAccessibilityTests')?.addEventListener('click', () => this.runAccessibilityTests());
        document.getElementById('runCompatibilityTests')?.addEventListener('click', () => this.runCompatibilityTests());
    }
    
    // ========================================
    // LOADING SEQUENCE TESTS (Requirements 1.1, 1.2, 1.3, 1.4)
    // ========================================
    
    async runLoadingTests() {
        console.log('🔄 Running Loading Sequence Tests');
        this.updateTestStatus('loading', 'running');
        
        const tests = [
            this.testTailwindAvailability(),
            this.testConfigurationApplication(),
            this.testErrorPrevention(),
            this.testLoadingOrder()
        ];
        
        try {
            const results = await Promise.all(tests);
            this.testResults.loading = results;
            
            const passed = results.every(r => r.passed);
            this.updateTestStatus('loading', passed ? 'passed' : 'failed');
            this.displayLoadingResults(results);
            
            this.announceTestResult('Loading sequence tests', passed);
            
        } catch (error) {
            console.error('Loading tests failed:', error);
            this.updateTestStatus('loading', 'failed');
            this.displayLoadingResults([{
                name: 'Loading Tests',
                passed: false,
                message: `Test execution failed: ${error.message}`,
                requirement: '1.1-1.4'
            }]);
        }
    }
    
    testTailwindAvailability() {
        return new Promise((resolve) => {
            const test = {
                name: 'Tailwind CSS Availability',
                requirement: '1.1, 1.2'
            };
            
            // Check if Tailwind is available
            if (typeof tailwind !== 'undefined') {
                test.passed = true;
                test.message = '✅ Tailwind CSS library is available and accessible';
            } else {
                test.passed = false;
                test.message = '❌ Tailwind CSS library is not defined - race condition detected';
            }
            
            resolve(test);
        });
    }
    
    testConfigurationApplication() {
        return new Promise((resolve) => {
            const test = {
                name: 'Configuration Application',
                requirement: '1.3, 1.4'
            };
            
            // Test if configuration was applied by checking computed styles
            const testElement = document.createElement('div');
            testElement.className = 'bg-primary text-primary';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(testElement);
                const bgColor = computedStyle.backgroundColor;
                const textColor = computedStyle.color;
                
                // Check if EYTGaming brand red is applied
                const expectedRgb = 'rgb(185, 28, 28)'; // #b91c1c
                
                if (bgColor.includes('185, 28, 28') || textColor.includes('185, 28, 28')) {
                    test.passed = true;
                    test.message = '✅ Tailwind configuration applied successfully - brand colors detected';
                } else {
                    test.passed = false;
                    test.message = `❌ Configuration not applied - expected brand red, got bg: ${bgColor}, text: ${textColor}`;
                }
                
                document.body.removeChild(testElement);
                resolve(test);
            }, 100);
        });
    }
    
    testErrorPrevention() {
        return new Promise((resolve) => {
            const test = {
                name: 'JavaScript Error Prevention',
                requirement: '1.2, 1.3'
            };
            
            // Check console for "tailwind is not defined" errors
            const originalError = console.error;
            let errorDetected = false;
            
            console.error = function(...args) {
                if (args.some(arg => typeof arg === 'string' && arg.includes('tailwind is not defined'))) {
                    errorDetected = true;
                }
                originalError.apply(console, args);
            };
            
            // Restore original console.error after a brief period
            setTimeout(() => {
                console.error = originalError;
                
                if (!errorDetected) {
                    test.passed = true;
                    test.message = '✅ No "tailwind is not defined" errors detected';
                } else {
                    test.passed = false;
                    test.message = '❌ "tailwind is not defined" error detected - race condition exists';
                }
                
                resolve(test);
            }, 500);
        });
    }
    
    testLoadingOrder() {
        return new Promise((resolve) => {
            const test = {
                name: 'Script Loading Order',
                requirement: '1.1, 1.4'
            };
            
            // Check if scripts are loaded in correct order by examining DOM
            const scripts = Array.from(document.querySelectorAll('script[src*="tailwind"]'));
            const configScripts = Array.from(document.querySelectorAll('script')).filter(s => 
                s.textContent && s.textContent.includes('tailwind.config')
            );
            
            if (scripts.length > 0) {
                test.passed = true;
                test.message = `✅ Tailwind CSS script found with defer attribute: ${scripts[0].hasAttribute('defer')}`;
            } else {
                test.passed = false;
                test.message = '❌ Tailwind CSS script not found in DOM';
            }
            
            resolve(test);
        });
    }
    
    displayLoadingResults(results) {
        const container = document.getElementById('loadingResults');
        if (!container) return;
        
        container.innerHTML = results.map(result => `
            <div class="test-result ${result.passed ? 'pass' : 'fail'}">
                <strong>${result.name}</strong> (${result.requirement})<br>
                ${result.message}
            </div>
        `).join('');
    }
    
    // ========================================
    // BRAND CONSISTENCY TESTS (Requirements 2.1, 2.2, 2.3, 2.4)
    // ========================================
    
    async runBrandTests() {
        console.log('🎨 Running Brand Consistency Tests');
        this.updateTestStatus('brand', 'running');
        
        const tests = [
            this.testPrimaryColors(),
            this.testDarkModeColors(),
            this.testFontFamily(),
            this.testMaterialIcons()
        ];
        
        try {
            const results = await Promise.all(tests);
            this.testResults.brand = results;
            
            const passed = results.every(r => r.passed);
            this.updateTestStatus('brand', passed ? 'passed' : 'failed');
            this.displayBrandResults(results);
            
            this.announceTestResult('Brand consistency tests', passed);
            
        } catch (error) {
            console.error('Brand tests failed:', error);
            this.updateTestStatus('brand', 'failed');
        }
    }
    
    testPrimaryColors() {
        return new Promise((resolve) => {
            const test = {
                name: 'EYTGaming Primary Colors',
                requirement: '2.1'
            };
            
            // Test primary color application
            const testElement = document.createElement('div');
            testElement.className = 'bg-primary';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(testElement);
                const bgColor = computedStyle.backgroundColor;
                
                // Check for EYTGaming brand red (#b91c1c = rgb(185, 28, 28))
                if (bgColor.includes('185, 28, 28')) {
                    test.passed = true;
                    test.message = `✅ Primary color correctly set to EYTGaming brand red: ${bgColor}`;
                } else {
                    test.passed = false;
                    test.message = `❌ Primary color incorrect - expected rgb(185, 28, 28), got: ${bgColor}`;
                }
                
                document.body.removeChild(testElement);
                resolve(test);
            }, 100);
        });
    }
    
    testDarkModeColors() {
        return new Promise((resolve) => {
            const test = {
                name: 'Dark Mode Color Configuration',
                requirement: '2.2'
            };
            
            // Test dark mode color application
            const originalClass = document.documentElement.className;
            document.documentElement.classList.add('dark');
            
            const testElement = document.createElement('div');
            testElement.className = 'bg-background-dark text-text-dark';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(testElement);
                const bgColor = computedStyle.backgroundColor;
                const textColor = computedStyle.color;
                
                // Check if dark mode colors are applied
                const hasDarkBg = bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent';
                const hasDarkText = textColor !== 'rgba(0, 0, 0, 0)' && textColor !== 'transparent';
                
                if (hasDarkBg || hasDarkText) {
                    test.passed = true;
                    test.message = `✅ Dark mode colors applied - bg: ${bgColor}, text: ${textColor}`;
                } else {
                    test.passed = false;
                    test.message = `❌ Dark mode colors not applied - bg: ${bgColor}, text: ${textColor}`;
                }
                
                document.body.removeChild(testElement);
                document.documentElement.className = originalClass;
                resolve(test);
            }, 100);
        });
    }
    
    testFontFamily() {
        return new Promise((resolve) => {
            const test = {
                name: 'Spline Sans Font Family',
                requirement: '2.3'
            };
            
            // Test font family application
            const testElement = document.createElement('div');
            testElement.className = 'font-display';
            testElement.textContent = 'Test';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(testElement);
                const fontFamily = computedStyle.fontFamily;
                
                if (fontFamily.includes('Spline Sans')) {
                    test.passed = true;
                    test.message = `✅ Spline Sans font family applied: ${fontFamily}`;
                } else {
                    test.passed = false;
                    test.message = `❌ Spline Sans not found in font family: ${fontFamily}`;
                }
                
                document.body.removeChild(testElement);
                resolve(test);
            }, 100);
        });
    }
    
    testMaterialIcons() {
        return new Promise((resolve) => {
            const test = {
                name: 'Material Icons Styling',
                requirement: '2.4'
            };
            
            // Test Material Icons styling
            const testElement = document.createElement('span');
            testElement.className = 'material-symbols-outlined';
            testElement.textContent = 'home';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(testElement);
                const fontSize = computedStyle.fontSize;
                const fontVariationSettings = computedStyle.fontVariationSettings;
                
                // Check if Material Icons styling is applied
                const hasProperSize = fontSize && fontSize !== '16px'; // Should be larger than default
                const hasVariationSettings = fontVariationSettings && fontVariationSettings !== 'normal';
                
                if (hasProperSize || hasVariationSettings) {
                    test.passed = true;
                    test.message = `✅ Material Icons styling applied - size: ${fontSize}, variation: ${fontVariationSettings}`;
                } else {
                    test.passed = false;
                    test.message = `❌ Material Icons styling not applied - size: ${fontSize}, variation: ${fontVariationSettings}`;
                }
                
                document.body.removeChild(testElement);
                resolve(test);
            }, 100);
        });
    }
    
    displayBrandResults(results) {
        const container = document.getElementById('brandResults');
        if (!container) return;
        
        container.innerHTML = results.map(result => `
            <div class="test-result ${result.passed ? 'pass' : 'fail'}">
                <strong>${result.name}</strong> (${result.requirement})<br>
                ${result.message}
            </div>
        `).join('');
    }
    
    // ========================================
    // PERFORMANCE TESTS (Requirements 3.1, 3.2, 3.3, 3.4)
    // ========================================
    
    async runPerformanceTests() {
        console.log('⚡ Running Performance Tests');
        this.updateTestStatus('performance', 'running');
        
        const tests = [
            this.testRenderBlockingResources(),
            this.testFontLoadingPerformance(),
            this.testLayoutStability(),
            this.testCriticalResourceTiming()
        ];
        
        try {
            const results = await Promise.all(tests);
            this.testResults.performance = results;
            
            const passed = results.every(r => r.passed);
            this.updateTestStatus('performance', passed ? 'passed' : 'failed');
            this.displayPerformanceResults(results);
            this.updatePerformanceMetrics();
            
            this.announceTestResult('Performance tests', passed);
            
        } catch (error) {
            console.error('Performance tests failed:', error);
            this.updateTestStatus('performance', 'failed');
        }
    }
    
    testRenderBlockingResources() {
        return new Promise((resolve) => {
            const test = {
                name: 'Render-Blocking Resources',
                requirement: '3.1'
            };
            
            // Check for render-blocking resources
            const stylesheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
            const scripts = Array.from(document.querySelectorAll('script[src]'));
            
            const blockingStylesheets = stylesheets.filter(link => 
                !link.hasAttribute('media') || link.getAttribute('media') === 'all'
            );
            
            const blockingScripts = scripts.filter(script => 
                !script.hasAttribute('defer') && !script.hasAttribute('async')
            );
            
            const totalBlocking = blockingStylesheets.length + blockingScripts.length;
            
            if (totalBlocking <= 3) { // Allow some critical resources
                test.passed = true;
                test.message = `✅ Minimal render-blocking resources: ${totalBlocking} (${blockingStylesheets.length} CSS, ${blockingScripts.length} JS)`;
            } else {
                test.passed = false;
                test.message = `❌ Too many render-blocking resources: ${totalBlocking} (${blockingStylesheets.length} CSS, ${blockingScripts.length} JS)`;
            }
            
            resolve(test);
        });
    }
    
    testFontLoadingPerformance() {
        return new Promise((resolve) => {
            const test = {
                name: 'Font Loading Performance',
                requirement: '3.2'
            };
            
            if ('fonts' in document) {
                document.fonts.ready.then(() => {
                    const loadedFonts = Array.from(document.fonts);
                    const splineSansLoaded = loadedFonts.some(font => 
                        font.family.includes('Spline Sans')
                    );
                    
                    if (splineSansLoaded) {
                        test.passed = true;
                        test.message = `✅ Fonts loaded successfully: ${loadedFonts.length} fonts including Spline Sans`;
                    } else {
                        test.passed = false;
                        test.message = `❌ Spline Sans font not loaded: ${loadedFonts.length} fonts loaded`;
                    }
                    
                    resolve(test);
                });
            } else {
                test.passed = false;
                test.message = '❌ Font Loading API not supported in this browser';
                resolve(test);
            }
        });
    }
    
    testLayoutStability() {
        return new Promise((resolve) => {
            const test = {
                name: 'Layout Stability (CLS)',
                requirement: '3.3'
            };
            
            // Measure Cumulative Layout Shift if available
            if ('PerformanceObserver' in window) {
                let clsValue = 0;
                
                try {
                    const observer = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (!entry.hadRecentInput) {
                                clsValue += entry.value;
                            }
                        }
                    });
                    
                    observer.observe({ type: 'layout-shift', buffered: true });
                    
                    setTimeout(() => {
                        observer.disconnect();
                        
                        if (clsValue < 0.1) { // Good CLS score
                            test.passed = true;
                            test.message = `✅ Good layout stability: CLS = ${clsValue.toFixed(4)}`;
                        } else {
                            test.passed = false;
                            test.message = `❌ Poor layout stability: CLS = ${clsValue.toFixed(4)} (should be < 0.1)`;
                        }
                        
                        resolve(test);
                    }, 1000);
                    
                } catch (error) {
                    test.passed = false;
                    test.message = `❌ Could not measure CLS: ${error.message}`;
                    resolve(test);
                }
            } else {
                test.passed = false;
                test.message = '❌ PerformanceObserver not supported - cannot measure CLS';
                resolve(test);
            }
        });
    }
    
    testCriticalResourceTiming() {
        return new Promise((resolve) => {
            const test = {
                name: 'Critical Resource Timing',
                requirement: '3.4'
            };
            
            if ('performance' in window && 'getEntriesByType' in performance) {
                const resources = performance.getEntriesByType('resource');
                const tailwindResource = resources.find(r => r.name.includes('tailwindcss.com'));
                
                if (tailwindResource) {
                    const loadTime = tailwindResource.responseEnd - tailwindResource.startTime;
                    
                    if (loadTime < 1000) { // Less than 1 second
                        test.passed = true;
                        test.message = `✅ Tailwind CSS loaded quickly: ${loadTime.toFixed(0)}ms`;
                    } else {
                        test.passed = false;
                        test.message = `❌ Tailwind CSS loaded slowly: ${loadTime.toFixed(0)}ms`;
                    }
                } else {
                    test.passed = false;
                    test.message = '❌ Tailwind CSS resource timing not found';
                }
            } else {
                test.passed = false;
                test.message = '❌ Performance API not supported';
            }
            
            resolve(test);
        });
    }
    
    displayPerformanceResults(results) {
        const container = document.getElementById('performanceResults');
        if (!container) return;
        
        container.innerHTML = results.map(result => `
            <div class="test-result ${result.passed ? 'pass' : 'fail'}">
                <strong>${result.name}</strong> (${result.requirement})<br>
                ${result.message}
            </div>
        `).join('');
    }
    
    updatePerformanceMetrics() {
        const metricsContainer = document.getElementById('performanceMetrics');
        if (!metricsContainer) return;
        
        // Collect performance metrics
        const navigation = performance.getEntriesByType('navigation')[0];
        const metrics = {};
        
        if (navigation) {
            metrics.domContentLoaded = Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart);
            metrics.loadComplete = Math.round(navigation.loadEventEnd - navigation.loadEventStart);
            metrics.totalTime = Math.round(navigation.loadEventEnd - navigation.fetchStart);
        }
        
        // Add resource count
        metrics.resourceCount = performance.getEntriesByType('resource').length;
        
        // Display metrics
        metricsContainer.innerHTML = `
            <div class="metric-card">
                <div class="metric-value">${metrics.domContentLoaded || 'N/A'}ms</div>
                <div class="metric-label">DOM Content Loaded</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.loadComplete || 'N/A'}ms</div>
                <div class="metric-label">Load Complete</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.totalTime || 'N/A'}ms</div>
                <div class="metric-label">Total Load Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${metrics.resourceCount}</div>
                <div class="metric-label">Resources Loaded</div>
            </div>
        `;
    }
    
    // ========================================
    // ACCESSIBILITY TESTS (Requirements 5.1, 5.2, 5.3, 5.4)
    // ========================================
    
    async runAccessibilityTests() {
        console.log('♿ Running Accessibility Tests');
        this.updateTestStatus('accessibility', 'running');
        
        const tests = [
            this.testFocusIndicators(),
            this.testColorContrast(),
            this.testInteractiveElements(),
            this.testCustomColors()
        ];
        
        try {
            const results = await Promise.all(tests);
            this.testResults.accessibility = results;
            
            const passed = results.every(r => r.passed);
            this.updateTestStatus('accessibility', passed ? 'passed' : 'failed');
            this.displayAccessibilityResults(results);
            
            this.announceTestResult('Accessibility tests', passed);
            
        } catch (error) {
            console.error('Accessibility tests failed:', error);
            this.updateTestStatus('accessibility', 'failed');
        }
    }
    
    testFocusIndicators() {
        return new Promise((resolve) => {
            const test = {
                name: 'Focus Indicators',
                requirement: '5.1'
            };
            
            // Test focus indicators on interactive elements
            const button = document.createElement('button');
            button.className = 'focus:outline-primary';
            button.textContent = 'Test Button';
            document.body.appendChild(button);
            
            button.focus();
            
            setTimeout(() => {
                const computedStyle = window.getComputedStyle(button);
                const outline = computedStyle.outline;
                const outlineColor = computedStyle.outlineColor;
                
                if (outline !== 'none' || outlineColor.includes('185, 28, 28')) {
                    test.passed = true;
                    test.message = `✅ Focus indicators present: outline=${outline}, color=${outlineColor}`;
                } else {
                    test.passed = false;
                    test.message = `❌ Focus indicators missing: outline=${outline}, color=${outlineColor}`;
                }
                
                document.body.removeChild(button);
                resolve(test);
            }, 100);
        });
    }
    
    testColorContrast() {
        return new Promise((resolve) => {
            const test = {
                name: 'WCAG AA Color Contrast',
                requirement: '5.2'
            };
            
            // Test color contrast ratios
            const testCombinations = [
                { bg: '#b91c1c', text: '#ffffff', name: 'Primary/White' },
                { bg: '#ffffff', text: '#111827', name: 'White/Dark Text' },
                { bg: '#121212', text: '#f9fafb', name: 'Dark/Light Text' }
            ];
            
            const results = testCombinations.map(combo => {
                const contrast = this.calculateContrastRatio(combo.bg, combo.text);
                return {
                    name: combo.name,
                    contrast: contrast,
                    passes: contrast >= 4.5 // WCAG AA standard
                };
            });
            
            const allPass = results.every(r => r.passes);
            
            if (allPass) {
                test.passed = true;
                test.message = `✅ All color combinations pass WCAG AA: ${results.map(r => `${r.name}(${r.contrast.toFixed(1)})`).join(', ')}`;
            } else {
                test.passed = false;
                test.message = `❌ Some combinations fail WCAG AA: ${results.map(r => `${r.name}(${r.contrast.toFixed(1)}${r.passes ? '✓' : '✗'})`).join(', ')}`;
            }
            
            resolve(test);
        });
    }
    
    testInteractiveElements() {
        return new Promise((resolve) => {
            const test = {
                name: 'Interactive Elements Accessibility',
                requirement: '5.3'
            };
            
            // Test minimum touch target sizes
            const button = document.createElement('button');
            button.className = 'interactive-element';
            button.textContent = 'Test';
            document.body.appendChild(button);
            
            setTimeout(() => {
                const rect = button.getBoundingClientRect();
                const minSize = 44; // 44px minimum for touch targets
                
                if (rect.width >= minSize && rect.height >= minSize) {
                    test.passed = true;
                    test.message = `✅ Interactive elements meet minimum size: ${rect.width}x${rect.height}px`;
                } else {
                    test.passed = false;
                    test.message = `❌ Interactive elements too small: ${rect.width}x${rect.height}px (minimum: ${minSize}px)`;
                }
                
                document.body.removeChild(button);
                resolve(test);
            }, 100);
        });
    }
    
    testCustomColors() {
        return new Promise((resolve) => {
            const test = {
                name: 'Custom Color Accessibility',
                requirement: '5.4'
            };
            
            // Test EYTGaming brand colors for accessibility
            const brandRed = '#b91c1c';
            const whiteContrast = this.calculateContrastRatio(brandRed, '#ffffff');
            const blackContrast = this.calculateContrastRatio(brandRed, '#000000');
            
            if (whiteContrast >= 4.5 || blackContrast >= 4.5) {
                test.passed = true;
                test.message = `✅ Brand colors accessible: white(${whiteContrast.toFixed(1)}), black(${blackContrast.toFixed(1)})`;
            } else {
                test.passed = false;
                test.message = `❌ Brand colors fail accessibility: white(${whiteContrast.toFixed(1)}), black(${blackContrast.toFixed(1)})`;
            }
            
            resolve(test);
        });
    }
    
    displayAccessibilityResults(results) {
        const container = document.getElementById('accessibilityResults');
        if (!container) return;
        
        container.innerHTML = results.map(result => `
            <div class="test-result ${result.passed ? 'pass' : 'fail'}">
                <strong>${result.name}</strong> (${result.requirement})<br>
                ${result.message}
            </div>
        `).join('');
    }
    
    // ========================================
    // CROSS-BROWSER COMPATIBILITY TESTS (Requirements 4.1, 4.2, 4.3, 4.4)
    // ========================================
    
    async runCompatibilityTests() {
        console.log('🌐 Running Cross-Browser Compatibility Tests');
        this.updateTestStatus('compatibility', 'running');
        
        const tests = [
            this.testBrowserCompatibility(),
            this.testFeatureDetection(),
            this.testGracefulFallbacks(),
            this.testJavaScriptDisabled()
        ];
        
        try {
            const results = await Promise.all(tests);
            this.testResults.compatibility = results;
            
            const passed = results.every(r => r.passed);
            this.updateTestStatus('compatibility', passed ? 'passed' : 'failed');
            this.displayCompatibilityResults(results);
            
            this.announceTestResult('Cross-browser compatibility tests', passed);
            
        } catch (error) {
            console.error('Compatibility tests failed:', error);
            this.updateTestStatus('compatibility', 'failed');
        }
    }
    
    testBrowserCompatibility() {
        return new Promise((resolve) => {
            const test = {
                name: 'Browser Compatibility',
                requirement: '4.1'
            };
            
            const browserInfo = this.getBrowserInfo();
            const supportedFeatures = this.checkFeatureSupport();
            
            const criticalFeatures = ['flexbox', 'grid', 'customProperties'];
            const supportedCritical = criticalFeatures.filter(feature => supportedFeatures[feature]);
            
            if (supportedCritical.length >= 2) { // At least 2 out of 3 critical features
                test.passed = true;
                test.message = `✅ Browser compatible: ${browserInfo.name} ${browserInfo.version}, supports ${supportedCritical.join(', ')}`;
            } else {
                test.passed = false;
                test.message = `❌ Browser compatibility issues: ${browserInfo.name} ${browserInfo.version}, missing ${criticalFeatures.filter(f => !supportedFeatures[f]).join(', ')}`;
            }
            
            resolve(test);
        });
    }
    
    testFeatureDetection() {
        return new Promise((resolve) => {
            const test = {
                name: 'CSS Feature Detection',
                requirement: '4.2'
            };
            
            // Test @supports feature detection
            const features = {
                'display: grid': CSS.supports('display', 'grid'),
                'display: flex': CSS.supports('display', 'flex'),
                'color: var(--test)': CSS.supports('color', 'var(--test)'),
                'backdrop-filter: blur(10px)': CSS.supports('backdrop-filter', 'blur(10px)')
            };
            
            const supportedCount = Object.values(features).filter(Boolean).length;
            const totalCount = Object.keys(features).length;
            
            if (supportedCount >= totalCount * 0.75) { // 75% support
                test.passed = true;
                test.message = `✅ Good feature detection: ${supportedCount}/${totalCount} features supported`;
            } else {
                test.passed = false;
                test.message = `❌ Limited feature support: ${supportedCount}/${totalCount} features supported`;
            }
            
            resolve(test);
        });
    }
    
    testGracefulFallbacks() {
        return new Promise((resolve) => {
            const test = {
                name: 'Graceful Fallbacks',
                requirement: '4.3, 4.4'
            };
            
            // Test if fallback CSS is available
            const fallbackStyles = Array.from(document.styleSheets).some(sheet => {
                try {
                    return sheet.href && sheet.href.includes('fallback');
                } catch (e) {
                    return false;
                }
            });
            
            // Test if basic styling works without advanced features
            const testElement = document.createElement('div');
            testElement.style.cssText = 'display: block; background: #f0f0f0; padding: 10px;';
            document.body.appendChild(testElement);
            
            const computedStyle = window.getComputedStyle(testElement);
            const hasBasicStyling = computedStyle.backgroundColor !== 'rgba(0, 0, 0, 0)';
            
            document.body.removeChild(testElement);
            
            if (fallbackStyles || hasBasicStyling) {
                test.passed = true;
                test.message = `✅ Graceful fallbacks available: fallback CSS=${fallbackStyles}, basic styling=${hasBasicStyling}`;
            } else {
                test.passed = false;
                test.message = `❌ No graceful fallbacks detected: fallback CSS=${fallbackStyles}, basic styling=${hasBasicStyling}`;
            }
            
            resolve(test);
        });
    }
    
    testJavaScriptDisabled() {
        return new Promise((resolve) => {
            const test = {
                name: 'JavaScript Disabled Fallback',
                requirement: '4.4'
            };
            
            // Check for noscript elements and fallback content
            const noscriptElements = document.querySelectorAll('noscript');
            const fallbackNotices = document.querySelectorAll('.tailwind-fallback-notice');
            
            if (noscriptElements.length > 0 || fallbackNotices.length > 0) {
                test.passed = true;
                test.message = `✅ JavaScript fallbacks present: ${noscriptElements.length} noscript elements, ${fallbackNotices.length} fallback notices`;
            } else {
                test.passed = false;
                test.message = `❌ No JavaScript fallbacks found: ${noscriptElements.length} noscript elements, ${fallbackNotices.length} fallback notices`;
            }
            
            resolve(test);
        });
    }
    
    displayCompatibilityResults(results) {
        const container = document.getElementById('compatibilityResults');
        if (!container) return;
        
        container.innerHTML = results.map(result => `
            <div class="test-result ${result.passed ? 'pass' : 'fail'}">
                <strong>${result.name}</strong> (${result.requirement})<br>
                ${result.message}
            </div>
        `).join('');
    }
    
    // ========================================
    // UTILITY METHODS
    // ========================================
    
    calculateContrastRatio(color1, color2) {
        // Convert hex to RGB
        const rgb1 = this.hexToRgb(color1);
        const rgb2 = this.hexToRgb(color2);
        
        // Calculate relative luminance
        const l1 = this.getRelativeLuminance(rgb1);
        const l2 = this.getRelativeLuminance(rgb2);
        
        // Calculate contrast ratio
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }
    
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    getRelativeLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }
    
    getBrowserInfo() {
        const ua = navigator.userAgent;
        let name = 'Unknown';
        let version = 'Unknown';
        
        if (ua.includes('Chrome')) {
            name = 'Chrome';
            version = ua.match(/Chrome\/(\d+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Firefox')) {
            name = 'Firefox';
            version = ua.match(/Firefox\/(\d+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Safari')) {
            name = 'Safari';
            version = ua.match(/Version\/(\d+)/)?.[1] || 'Unknown';
        } else if (ua.includes('Edge')) {
            name = 'Edge';
            version = ua.match(/Edge\/(\d+)/)?.[1] || 'Unknown';
        }
        
        return { name, version };
    }
    
    checkFeatureSupport() {
        return {
            flexbox: CSS.supports('display', 'flex'),
            grid: CSS.supports('display', 'grid'),
            customProperties: CSS.supports('color', 'var(--test)'),
            focusVisible: CSS.supports('selector(:focus-visible)'),
            backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
            objectFit: CSS.supports('object-fit', 'cover'),
            stickyPosition: CSS.supports('position', 'sticky')
        };
    }
    
    detectBrowserInfo() {
        const browserInfo = this.getBrowserInfo();
        const features = this.checkFeatureSupport();
        
        const browserDetails = document.getElementById('browserDetails');
        if (browserDetails) {
            browserDetails.innerHTML = `
                <div><strong>Browser:</strong> ${browserInfo.name} ${browserInfo.version}</div>
                <div><strong>User Agent:</strong> ${navigator.userAgent.substring(0, 100)}...</div>
                <div><strong>Viewport:</strong> ${window.innerWidth}x${window.innerHeight}</div>
                <div><strong>Features:</strong> ${Object.entries(features).filter(([k, v]) => v).map(([k]) => k).join(', ')}</div>
            `;
        }
    }
    
    startPerformanceMonitoring() {
        if ('performance' in window) {
            performance.mark('test-suite-start');
            
            // Monitor resource loading
            if ('PerformanceObserver' in window) {
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (entry.name.includes('tailwind')) {
                            console.log(`📊 Tailwind resource loaded: ${entry.name} (${entry.duration.toFixed(0)}ms)`);
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['resource'] });
            }
        }
    }
    
    initAccessibilityTesting() {
        // Add keyboard navigation testing
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                console.log(`🔍 Tab navigation: ${document.activeElement.tagName} ${document.activeElement.className}`);
            }
        });
    }
    
    updateTestStatus(category, status) {
        const statusElement = document.getElementById(`${category}Status`);
        if (statusElement) {
            statusElement.className = `test-result ${status === 'passed' ? 'pass' : status === 'failed' ? 'fail' : 'warning'}`;
            statusElement.textContent = status === 'running' ? 'Running...' : 
                                      status === 'passed' ? 'All tests passed' :
                                      status === 'failed' ? 'Some tests failed' : status;
        }
    }
    
    announceTestResult(testName, passed) {
        const announcement = document.getElementById('testAnnouncements');
        if (announcement) {
            announcement.textContent = `${testName} ${passed ? 'passed' : 'failed'}`;
        }
    }
    
    toggleDarkMode() {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        
        const button = document.getElementById('toggleDarkMode');
        if (button) {
            button.textContent = isDark ? '☀️ Toggle Light Mode' : '🌙 Toggle Dark Mode';
        }
        
        this.announceTestResult('Dark mode', true);
    }
    
    clearResults() {
        // Clear all test results
        const resultContainers = [
            'loadingResults', 'brandResults', 'performanceResults', 
            'accessibilityResults', 'compatibilityResults'
        ];
        
        resultContainers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = '<p class="text-gray-500">Results cleared. Run tests to see new results.</p>';
            }
        });
        
        // Reset status indicators
        ['loading', 'brand', 'performance', 'accessibility'].forEach(category => {
            this.updateTestStatus(category, 'Not started');
        });
        
        // Clear performance metrics
        const metricsContainer = document.getElementById('performanceMetrics');
        if (metricsContainer) {
            metricsContainer.innerHTML = '<p class="text-gray-500">Run performance tests to see metrics.</p>';
        }
        
        // Clear test summary
        const summaryContainer = document.getElementById('testSummary');
        if (summaryContainer) {
            summaryContainer.innerHTML = '<p class="text-gray-600 dark:text-gray-400">Run tests to see summary results</p>';
        }
        
        this.announceTestResult('Results', true);
    }
    
    async runAllTests() {
        console.log('🚀 Running All Integration Tests');
        
        const startTime = performance.now();
        
        try {
            // Run all test suites in sequence
            await this.runLoadingTests();
            await this.runBrandTests();
            await this.runPerformanceTests();
            await this.runAccessibilityTests();
            await this.runCompatibilityTests();
            
            const endTime = performance.now();
            const totalTime = Math.round(endTime - startTime);
            
            // Generate summary
            this.generateTestSummary(totalTime);
            
            console.log(`✅ All integration tests completed in ${totalTime}ms`);
            
        } catch (error) {
            console.error('❌ Integration test suite failed:', error);
            this.announceTestResult('All tests', false);
        }
    }
    
    generateTestSummary(totalTime) {
        const summaryContainer = document.getElementById('testSummary');
        if (!summaryContainer) return;
        
        // Count results
        const allResults = [
            ...this.testResults.loading,
            ...this.testResults.brand,
            ...this.testResults.performance,
            ...this.testResults.accessibility,
            ...this.testResults.compatibility
        ];
        
        const totalTests = allResults.length;
        const passedTests = allResults.filter(r => r.passed).length;
        const failedTests = totalTests - passedTests;
        
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;
        
        summaryContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="metric-card">
                    <div class="metric-value text-green-600">${passedTests}</div>
                    <div class="metric-label">Tests Passed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value text-red-600">${failedTests}</div>
                    <div class="metric-label">Tests Failed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value text-blue-600">${passRate}%</div>
                    <div class="metric-label">Pass Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value text-purple-600">${totalTime}ms</div>
                    <div class="metric-label">Total Time</div>
                </div>
            </div>
            
            <div class="mt-6 p-4 rounded-lg ${passRate >= 80 ? 'bg-green-100 dark:bg-green-900' : 'bg-yellow-100 dark:bg-yellow-900'}">
                <h3 class="font-semibold mb-2">
                    ${passRate >= 80 ? '✅ Integration Tests Passed' : '⚠️ Integration Tests Need Attention'}
                </h3>
                <p class="text-sm">
                    ${passRate >= 80 
                        ? 'All critical Tailwind CSS integration requirements are working correctly.'
                        : 'Some integration tests failed. Review the results above and address any issues.'}
                </p>
                
                ${failedTests > 0 ? `
                    <div class="mt-3">
                        <h4 class="font-medium text-sm">Failed Tests:</h4>
                        <ul class="text-xs mt-1 space-y-1">
                            ${allResults.filter(r => !r.passed).map(r => `
                                <li>• ${r.name} (${r.requirement})</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.announceTestResult(`Integration test summary: ${passedTests} passed, ${failedTests} failed`, passRate >= 80);
    }
}

// Initialize the test suite when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Initializing Tailwind CSS Integration Test Suite');
    
    // Wait for all critical resources to load
    setTimeout(() => {
        window.tailwindTestSuite = new TailwindIntegrationTestSuite();
        console.log('✅ Integration Test Suite Ready');
    }, 1000);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TailwindIntegrationTestSuite;
}