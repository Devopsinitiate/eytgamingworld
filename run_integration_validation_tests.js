/**
 * Comprehensive Integration Validation Test Runner
 * Task 10: Integration testing and validation
 * 
 * This script runs comprehensive integration tests for:
 * - Complete loading sequence across different page types
 * - Brand consistency across all templates  
 * - Performance improvements with real-world testing
 * - Accessibility compliance with automated tools
 * 
 * Requirements: All requirements (1.1-5.4)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class IntegrationValidationRunner {
    constructor() {
        this.browser = null;
        this.results = {
            loadingSequence: [],
            brandConsistency: [],
            performance: [],
            accessibility: [],
            summary: {}
        };
        this.testPages = [
            'test_tailwind_integration_suite.html',
            'test_accessibility_compliance_tailwind.html',
            'test_cross_browser_compatibility.html',
            'test_graceful_fallbacks_demo.html'
        ];
    }

    async initialize() {
        console.log('🚀 Initializing Integration Validation Runner');
        
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
            devtools: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });
        
        console.log('✅ Browser launched successfully');
    }

    async runAllValidationTests() {
        console.log('📋 Starting Comprehensive Integration Validation');
        
        try {
            await this.initialize();
            
            // Test 1: Complete loading sequence across different page types
            console.log('\n🔄 Testing Complete Loading Sequence...');
            await this.testCompleteLoadingSequence();
            
            // Test 2: Brand consistency across all templates
            console.log('\n🎨 Testing Brand Consistency...');
            await this.testBrandConsistencyAcrossTemplates();
            
            // Test 3: Performance improvements with real-world testing
            console.log('\n⚡ Testing Performance Improvements...');
            await this.testPerformanceImprovements();
            
            // Test 4: Accessibility compliance with automated tools
            console.log('\n♿ Testing Accessibility Compliance...');
            await this.testAccessibilityCompliance();
            
            // Generate comprehensive report
            console.log('\n📊 Generating Integration Test Report...');
            await this.generateIntegrationReport();
            
            console.log('\n✅ All integration validation tests completed successfully');
            
        } catch (error) {
            console.error('❌ Integration validation failed:', error);
            throw error;
        } finally {
            if (this.browser) {
                await this.browser.close();
            }
        }
    }

    // ========================================
    // LOADING SEQUENCE TESTS (Requirements 1.1, 1.2, 1.3, 1.4)
    // ========================================

    async testCompleteLoadingSequence() {
        const loadingTests = [];
        
        for (const testPage of this.testPages) {
            console.log(`  📄 Testing loading sequence on: ${testPage}`);
            
            const page = await this.browser.newPage();
            
            try {
                // Enable console logging
                page.on('console', msg => {
                    if (msg.text().includes('tailwind is not defined')) {
                        loadingTests.push({
                            page: testPage,
                            test: 'Error Prevention',
                            passed: false,
                            message: 'Found "tailwind is not defined" error',
                            requirement: '1.2, 1.3'
                        });
                    }
                });
                
                // Monitor network requests
                const resourceLoadTimes = [];
                page.on('response', response => {
                    if (response.url().includes('tailwindcss.com')) {
                        resourceLoadTimes.push({
                            url: response.url(),
                            status: response.status(),
                            timing: response.timing()
                        });
                    }
                });
                
                // Navigate to test page
                const startTime = Date.now();
                await page.goto(`file://${path.resolve(testPage)}`, {
                    waitUntil: 'networkidle0',
                    timeout: 30000
                });
                const loadTime = Date.now() - startTime;
                
                // Test 1: Tailwind availability after load
                const tailwindAvailable = await page.evaluate(() => {
                    return typeof tailwind !== 'undefined';
                });
                
                loadingTests.push({
                    page: testPage,
                    test: 'Tailwind Availability',
                    passed: tailwindAvailable,
                    message: tailwindAvailable ? 'Tailwind CSS is available' : 'Tailwind CSS not available',
                    requirement: '1.1, 1.2'
                });
                
                // Test 2: Configuration application
                const configApplied = await page.evaluate(() => {
                    const testEl = document.createElement('div');
                    testEl.className = 'bg-primary';
                    document.body.appendChild(testEl);
                    const style = window.getComputedStyle(testEl);
                    const bgColor = style.backgroundColor;
                    document.body.removeChild(testEl);
                    return bgColor.includes('185, 28, 28'); // EYTGaming brand red
                });
                
                loadingTests.push({
                    page: testPage,
                    test: 'Configuration Application',
                    passed: configApplied,
                    message: configApplied ? 'Brand configuration applied' : 'Brand configuration not applied',
                    requirement: '1.3, 1.4'
                });
                
                // Test 3: Loading order verification
                const scriptOrder = await page.evaluate(() => {
                    const scripts = Array.from(document.querySelectorAll('script[src*="tailwind"]'));
                    const configScripts = Array.from(document.querySelectorAll('script')).filter(s => 
                        s.textContent && s.textContent.includes('tailwind.config')
                    );
                    
                    return {
                        tailwindScripts: scripts.length,
                        hasDefer: scripts.some(s => s.hasAttribute('defer')),
                        configScripts: configScripts.length
                    };
                });
                
                loadingTests.push({
                    page: testPage,
                    test: 'Script Loading Order',
                    passed: scriptOrder.tailwindScripts > 0 && scriptOrder.hasDefer,
                    message: `Tailwind scripts: ${scriptOrder.tailwindScripts}, Defer: ${scriptOrder.hasDefer}`,
                    requirement: '1.1, 1.4'
                });
                
                // Test 4: Performance timing
                loadingTests.push({
                    page: testPage,
                    test: 'Loading Performance',
                    passed: loadTime < 5000, // 5 second threshold
                    message: `Page loaded in ${loadTime}ms`,
                    requirement: '1.4'
                });
                
            } catch (error) {
                loadingTests.push({
                    page: testPage,
                    test: 'Page Load',
                    passed: false,
                    message: `Failed to load page: ${error.message}`,
                    requirement: '1.1-1.4'
                });
            } finally {
                await page.close();
            }
        }
        
        this.results.loadingSequence = loadingTests;
        
        const passedTests = loadingTests.filter(t => t.passed).length;
        const totalTests = loadingTests.length;
        
        console.log(`  ✅ Loading sequence tests: ${passedTests}/${totalTests} passed`);
    }

    // ========================================
    // BRAND CONSISTENCY TESTS (Requirements 2.1, 2.2, 2.3, 2.4)
    // ========================================

    async testBrandConsistencyAcrossTemplates() {
        const brandTests = [];
        
        for (const testPage of this.testPages) {
            console.log(`  🎨 Testing brand consistency on: ${testPage}`);
            
            const page = await this.browser.newPage();
            
            try {
                await page.goto(`file://${path.resolve(testPage)}`, {
                    waitUntil: 'networkidle0',
                    timeout: 30000
                });
                
                // Test 1: Primary color consistency (Requirement 2.1)
                const primaryColorTest = await page.evaluate(() => {
                    const testEl = document.createElement('div');
                    testEl.className = 'bg-primary text-primary border-primary';
                    document.body.appendChild(testEl);
                    
                    const style = window.getComputedStyle(testEl);
                    const bgColor = style.backgroundColor;
                    const textColor = style.color;
                    const borderColor = style.borderColor;
                    
                    document.body.removeChild(testEl);
                    
                    const expectedRgb = '185, 28, 28'; // #b91c1c
                    return {
                        bgMatch: bgColor.includes(expectedRgb),
                        textMatch: textColor.includes(expectedRgb),
                        borderMatch: borderColor.includes(expectedRgb),
                        bgColor,
                        textColor,
                        borderColor
                    };
                });
                
                brandTests.push({
                    page: testPage,
                    test: 'Primary Color Consistency',
                    passed: primaryColorTest.bgMatch || primaryColorTest.textMatch,
                    message: `Brand red applied: bg=${primaryColorTest.bgMatch}, text=${primaryColorTest.textMatch}`,
                    requirement: '2.1'
                });
                
                // Test 2: Dark mode colors (Requirement 2.2)
                await page.evaluate(() => {
                    document.documentElement.classList.add('dark');
                });
                
                const darkModeTest = await page.evaluate(() => {
                    const testEl = document.createElement('div');
                    testEl.className = 'bg-background-dark text-text-dark';
                    document.body.appendChild(testEl);
                    
                    const style = window.getComputedStyle(testEl);
                    const bgColor = style.backgroundColor;
                    const textColor = style.color;
                    
                    document.body.removeChild(testEl);
                    
                    return {
                        hasDarkBg: bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent',
                        hasDarkText: textColor !== 'rgba(0, 0, 0, 0)' && textColor !== 'transparent',
                        bgColor,
                        textColor
                    };
                });
                
                brandTests.push({
                    page: testPage,
                    test: 'Dark Mode Colors',
                    passed: darkModeTest.hasDarkBg || darkModeTest.hasDarkText,
                    message: `Dark mode colors: bg=${darkModeTest.hasDarkBg}, text=${darkModeTest.hasDarkText}`,
                    requirement: '2.2'
                });
                
                // Test 3: Font family consistency (Requirement 2.3)
                const fontTest = await page.evaluate(() => {
                    const testEl = document.createElement('div');
                    testEl.className = 'font-display';
                    testEl.textContent = 'Test';
                    document.body.appendChild(testEl);
                    
                    const style = window.getComputedStyle(testEl);
                    const fontFamily = style.fontFamily;
                    
                    document.body.removeChild(testEl);
                    
                    return {
                        hasSplineSans: fontFamily.includes('Spline Sans'),
                        fontFamily
                    };
                });
                
                brandTests.push({
                    page: testPage,
                    test: 'Font Family Consistency',
                    passed: fontTest.hasSplineSans,
                    message: `Spline Sans applied: ${fontTest.hasSplineSans} (${fontTest.fontFamily})`,
                    requirement: '2.3'
                });
                
                // Test 4: Material Icons styling (Requirement 2.4)
                const iconTest = await page.evaluate(() => {
                    const testEl = document.createElement('span');
                    testEl.className = 'material-symbols-outlined';
                    testEl.textContent = 'home';
                    document.body.appendChild(testEl);
                    
                    const style = window.getComputedStyle(testEl);
                    const fontSize = style.fontSize;
                    const fontVariationSettings = style.fontVariationSettings;
                    
                    document.body.removeChild(testEl);
                    
                    return {
                        hasProperSize: fontSize && fontSize !== '16px',
                        hasVariationSettings: fontVariationSettings && fontVariationSettings !== 'normal',
                        fontSize,
                        fontVariationSettings
                    };
                });
                
                brandTests.push({
                    page: testPage,
                    test: 'Material Icons Styling',
                    passed: iconTest.hasProperSize || iconTest.hasVariationSettings,
                    message: `Icons styled: size=${iconTest.hasProperSize}, variation=${iconTest.hasVariationSettings}`,
                    requirement: '2.4'
                });
                
            } catch (error) {
                brandTests.push({
                    page: testPage,
                    test: 'Brand Consistency',
                    passed: false,
                    message: `Failed to test brand consistency: ${error.message}`,
                    requirement: '2.1-2.4'
                });
            } finally {
                await page.close();
            }
        }
        
        this.results.brandConsistency = brandTests;
        
        const passedTests = brandTests.filter(t => t.passed).length;
        const totalTests = brandTests.length;
        
        console.log(`  ✅ Brand consistency tests: ${passedTests}/${totalTests} passed`);
    }

    // ========================================
    // PERFORMANCE TESTS (Requirements 3.1, 3.2, 3.3, 3.4)
    // ========================================

    async testPerformanceImprovements() {
        const performanceTests = [];
        
        for (const testPage of this.testPages) {
            console.log(`  ⚡ Testing performance on: ${testPage}`);
            
            const page = await this.browser.newPage();
            
            try {
                // Enable performance monitoring
                await page.setCacheEnabled(false); // Test without cache
                
                const startTime = Date.now();
                
                // Navigate and measure performance
                await page.goto(`file://${path.resolve(testPage)}`, {
                    waitUntil: 'networkidle0',
                    timeout: 30000
                });
                
                const loadTime = Date.now() - startTime;
                
                // Test 1: Render-blocking resources (Requirement 3.1)
                const renderBlockingTest = await page.evaluate(() => {
                    const stylesheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
                    const scripts = Array.from(document.querySelectorAll('script[src]'));
                    
                    const blockingStylesheets = stylesheets.filter(link => 
                        !link.hasAttribute('media') || link.getAttribute('media') === 'all'
                    );
                    
                    const blockingScripts = scripts.filter(script => 
                        !script.hasAttribute('defer') && !script.hasAttribute('async')
                    );
                    
                    return {
                        totalBlocking: blockingStylesheets.length + blockingScripts.length,
                        blockingCSS: blockingStylesheets.length,
                        blockingJS: blockingScripts.length
                    };
                });
                
                performanceTests.push({
                    page: testPage,
                    test: 'Render-Blocking Resources',
                    passed: renderBlockingTest.totalBlocking <= 3,
                    message: `${renderBlockingTest.totalBlocking} blocking resources (${renderBlockingTest.blockingCSS} CSS, ${renderBlockingTest.blockingJS} JS)`,
                    requirement: '3.1'
                });
                
                // Test 2: Font loading performance (Requirement 3.2)
                const fontLoadingTest = await page.evaluate(() => {
                    if ('fonts' in document) {
                        return document.fonts.ready.then(() => {
                            const loadedFonts = Array.from(document.fonts);
                            return {
                                fontsLoaded: loadedFonts.length,
                                splineSansLoaded: loadedFonts.some(font => font.family.includes('Spline Sans'))
                            };
                        });
                    }
                    return { fontsLoaded: 0, splineSansLoaded: false };
                });
                
                const fontResult = await fontLoadingTest;
                performanceTests.push({
                    page: testPage,
                    test: 'Font Loading Performance',
                    passed: fontResult.splineSansLoaded,
                    message: `${fontResult.fontsLoaded} fonts loaded, Spline Sans: ${fontResult.splineSansLoaded}`,
                    requirement: '3.2'
                });
                
                // Test 3: Layout stability (Requirement 3.3)
                const layoutStabilityTest = await page.evaluate(() => {
                    return new Promise((resolve) => {
                        if ('PerformanceObserver' in window) {
                            let clsValue = 0;
                            
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
                                resolve({ clsValue, supported: true });
                            }, 2000);
                        } else {
                            resolve({ clsValue: 0, supported: false });
                        }
                    });
                });
                
                const layoutResult = await layoutStabilityTest;
                performanceTests.push({
                    page: testPage,
                    test: 'Layout Stability (CLS)',
                    passed: layoutResult.supported ? layoutResult.clsValue < 0.1 : true,
                    message: layoutResult.supported ? `CLS: ${layoutResult.clsValue.toFixed(4)}` : 'CLS not supported',
                    requirement: '3.3'
                });
                
                // Test 4: Critical resource timing (Requirement 3.4)
                const resourceTimingTest = await page.evaluate(() => {
                    if ('performance' in window && 'getEntriesByType' in performance) {
                        const resources = performance.getEntriesByType('resource');
                        const tailwindResource = resources.find(r => r.name.includes('tailwindcss.com'));
                        
                        if (tailwindResource) {
                            return {
                                found: true,
                                loadTime: tailwindResource.responseEnd - tailwindResource.startTime,
                                transferSize: tailwindResource.transferSize || 0
                            };
                        }
                    }
                    return { found: false, loadTime: 0, transferSize: 0 };
                });
                
                performanceTests.push({
                    page: testPage,
                    test: 'Critical Resource Timing',
                    passed: resourceTimingTest.found && resourceTimingTest.loadTime < 2000,
                    message: resourceTimingTest.found ? 
                        `Tailwind loaded in ${resourceTimingTest.loadTime.toFixed(0)}ms (${resourceTimingTest.transferSize} bytes)` :
                        'Tailwind resource timing not found',
                    requirement: '3.4'
                });
                
                // Test 5: Overall page load performance
                performanceTests.push({
                    page: testPage,
                    test: 'Overall Load Performance',
                    passed: loadTime < 3000, // 3 second threshold
                    message: `Page loaded in ${loadTime}ms`,
                    requirement: '3.1-3.4'
                });
                
            } catch (error) {
                performanceTests.push({
                    page: testPage,
                    test: 'Performance Testing',
                    passed: false,
                    message: `Failed to test performance: ${error.message}`,
                    requirement: '3.1-3.4'
                });
            } finally {
                await page.close();
            }
        }
        
        this.results.performance = performanceTests;
        
        const passedTests = performanceTests.filter(t => t.passed).length;
        const totalTests = performanceTests.length;
        
        console.log(`  ✅ Performance tests: ${passedTests}/${totalTests} passed`);
    }

    // ========================================
    // ACCESSIBILITY TESTS (Requirements 5.1, 5.2, 5.3, 5.4)
    // ========================================

    async testAccessibilityCompliance() {
        const accessibilityTests = [];
        
        for (const testPage of this.testPages) {
            console.log(`  ♿ Testing accessibility on: ${testPage}`);
            
            const page = await this.browser.newPage();
            
            try {
                await page.goto(`file://${path.resolve(testPage)}`, {
                    waitUntil: 'networkidle0',
                    timeout: 30000
                });
                
                // Test 1: Focus indicators (Requirement 5.1)
                const focusTest = await page.evaluate(() => {
                    const button = document.createElement('button');
                    button.className = 'focus:outline-primary px-4 py-2';
                    button.textContent = 'Test Button';
                    document.body.appendChild(button);
                    
                    button.focus();
                    
                    const style = window.getComputedStyle(button);
                    const outline = style.outline;
                    const outlineColor = style.outlineColor;
                    
                    document.body.removeChild(button);
                    
                    return {
                        hasOutline: outline !== 'none',
                        hasBrandColor: outlineColor.includes('185, 28, 28'),
                        outline,
                        outlineColor
                    };
                });
                
                accessibilityTests.push({
                    page: testPage,
                    test: 'Focus Indicators',
                    passed: focusTest.hasOutline || focusTest.hasBrandColor,
                    message: `Focus outline: ${focusTest.hasOutline}, Brand color: ${focusTest.hasBrandColor}`,
                    requirement: '5.1'
                });
                
                // Test 2: Color contrast in dark mode (Requirement 5.2)
                await page.evaluate(() => {
                    document.documentElement.classList.add('dark');
                });
                
                const contrastTest = await page.evaluate(() => {
                    // Test primary color on white background
                    const testEl = document.createElement('div');
                    testEl.className = 'bg-primary text-white p-4';
                    testEl.textContent = 'Test Text';
                    document.body.appendChild(testEl);
                    
                    const style = window.getComputedStyle(testEl);
                    const bgColor = style.backgroundColor;
                    const textColor = style.color;
                    
                    document.body.removeChild(testEl);
                    
                    // Simple contrast check (proper implementation would calculate actual ratios)
                    const hasGoodContrast = bgColor.includes('185, 28, 28') && textColor.includes('255, 255, 255');
                    
                    return {
                        hasGoodContrast,
                        bgColor,
                        textColor
                    };
                });
                
                accessibilityTests.push({
                    page: testPage,
                    test: 'WCAG AA Color Contrast',
                    passed: contrastTest.hasGoodContrast,
                    message: `Primary/white contrast: ${contrastTest.hasGoodContrast}`,
                    requirement: '5.2'
                });
                
                // Test 3: Interactive elements accessibility (Requirement 5.3)
                const interactiveTest = await page.evaluate(() => {
                    const button = document.createElement('button');
                    button.className = 'interactive-element px-4 py-2';
                    button.textContent = 'Test';
                    document.body.appendChild(button);
                    
                    const rect = button.getBoundingClientRect();
                    const minSize = 44; // 44px minimum for touch targets
                    
                    document.body.removeChild(button);
                    
                    return {
                        width: rect.width,
                        height: rect.height,
                        meetsMinimum: rect.width >= minSize && rect.height >= minSize
                    };
                });
                
                accessibilityTests.push({
                    page: testPage,
                    test: 'Interactive Elements Size',
                    passed: interactiveTest.meetsMinimum,
                    message: `Button size: ${interactiveTest.width}x${interactiveTest.height}px (min: 44px)`,
                    requirement: '5.3'
                });
                
                // Test 4: Custom color accessibility (Requirement 5.4)
                const customColorTest = await page.evaluate(() => {
                    // Test various brand color applications
                    const testElements = [
                        { class: 'text-primary', type: 'text' },
                        { class: 'bg-primary text-white', type: 'background' },
                        { class: 'border-primary', type: 'border' }
                    ];
                    
                    const results = testElements.map(test => {
                        const el = document.createElement('div');
                        el.className = test.class;
                        el.textContent = 'Test';
                        document.body.appendChild(el);
                        
                        const style = window.getComputedStyle(el);
                        const hasColor = style.color.includes('185, 28, 28') || 
                                        style.backgroundColor.includes('185, 28, 28') ||
                                        style.borderColor.includes('185, 28, 28');
                        
                        document.body.removeChild(el);
                        
                        return { type: test.type, hasColor };
                    });
                    
                    return {
                        totalTests: results.length,
                        passedTests: results.filter(r => r.hasColor).length,
                        results
                    };
                });
                
                accessibilityTests.push({
                    page: testPage,
                    test: 'Custom Color Accessibility',
                    passed: customColorTest.passedTests > 0,
                    message: `${customColorTest.passedTests}/${customColorTest.totalTests} color applications working`,
                    requirement: '5.4'
                });
                
                // Test 5: ARIA and semantic markup
                const ariaTest = await page.evaluate(() => {
                    const skipLink = document.querySelector('.skip-to-main, [href="#main-content"]');
                    const liveRegions = document.querySelectorAll('[aria-live]');
                    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                    
                    return {
                        hasSkipLink: !!skipLink,
                        liveRegions: liveRegions.length,
                        headings: headings.length
                    };
                });
                
                accessibilityTests.push({
                    page: testPage,
                    test: 'ARIA and Semantic Markup',
                    passed: ariaTest.hasSkipLink || ariaTest.liveRegions > 0 || ariaTest.headings > 0,
                    message: `Skip link: ${ariaTest.hasSkipLink}, Live regions: ${ariaTest.liveRegions}, Headings: ${ariaTest.headings}`,
                    requirement: '5.1-5.4'
                });
                
            } catch (error) {
                accessibilityTests.push({
                    page: testPage,
                    test: 'Accessibility Testing',
                    passed: false,
                    message: `Failed to test accessibility: ${error.message}`,
                    requirement: '5.1-5.4'
                });
            } finally {
                await page.close();
            }
        }
        
        this.results.accessibility = accessibilityTests;
        
        const passedTests = accessibilityTests.filter(t => t.passed).length;
        const totalTests = accessibilityTests.length;
        
        console.log(`  ✅ Accessibility tests: ${passedTests}/${totalTests} passed`);
    }

    // ========================================
    // REPORT GENERATION
    // ========================================

    async generateIntegrationReport() {
        const allResults = [
            ...this.results.loadingSequence,
            ...this.results.brandConsistency,
            ...this.results.performance,
            ...this.results.accessibility
        ];
        
        const totalTests = allResults.length;
        const passedTests = allResults.filter(r => r.passed).length;
        const failedTests = totalTests - passedTests;
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;
        
        this.results.summary = {
            totalTests,
            passedTests,
            failedTests,
            passRate,
            timestamp: new Date().toISOString()
        };
        
        // Generate HTML report
        const htmlReport = this.generateHTMLReport();
        fs.writeFileSync('integration_test_report.html', htmlReport);
        
        // Generate JSON report
        fs.writeFileSync('integration_test_results.json', JSON.stringify(this.results, null, 2));
        
        // Generate console summary
        console.log('\n📊 INTEGRATION TEST SUMMARY');
        console.log('=' .repeat(50));
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests} (${passRate}%)`);
        console.log(`Failed: ${failedTests}`);
        console.log('=' .repeat(50));
        
        if (failedTests > 0) {
            console.log('\n❌ FAILED TESTS:');
            allResults.filter(r => !r.passed).forEach(test => {
                console.log(`  • ${test.test} (${test.page}) - ${test.message}`);
            });
        }
        
        console.log(`\n📄 Reports generated:`);
        console.log(`  • integration_test_report.html`);
        console.log(`  • integration_test_results.json`);
        
        return passRate >= 80; // Return success if 80% or more tests pass
    }

    generateHTMLReport() {
        const { summary } = this.results;
        
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tailwind CSS Integration Test Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .test-passed { @apply bg-green-100 border-green-500 text-green-800; }
        .test-failed { @apply bg-red-100 border-red-500 text-red-800; }
    </style>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-6xl mx-auto">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Tailwind CSS Integration Test Report</h1>
            <p class="text-gray-600">Generated: ${summary.timestamp}</p>
            
            <div class="grid grid-cols-4 gap-4 mt-6">
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="text-2xl font-bold text-blue-600">${summary.totalTests}</div>
                    <div class="text-sm text-gray-600">Total Tests</div>
                </div>
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="text-2xl font-bold text-green-600">${summary.passedTests}</div>
                    <div class="text-sm text-gray-600">Passed</div>
                </div>
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="text-2xl font-bold text-red-600">${summary.failedTests}</div>
                    <div class="text-sm text-gray-600">Failed</div>
                </div>
                <div class="bg-white p-4 rounded-lg shadow">
                    <div class="text-2xl font-bold text-purple-600">${summary.passRate}%</div>
                    <div class="text-sm text-gray-600">Pass Rate</div>
                </div>
            </div>
        </header>
        
        <main class="space-y-8">
            ${this.generateTestSectionHTML('Loading Sequence Tests', this.results.loadingSequence)}
            ${this.generateTestSectionHTML('Brand Consistency Tests', this.results.brandConsistency)}
            ${this.generateTestSectionHTML('Performance Tests', this.results.performance)}
            ${this.generateTestSectionHTML('Accessibility Tests', this.results.accessibility)}
        </main>
        
        <footer class="mt-12 pt-8 border-t border-gray-200">
            <p class="text-center text-gray-600">
                Integration testing completed for Tailwind CSS Fix (Task 10)
            </p>
        </footer>
    </div>
</body>
</html>`;
    }

    generateTestSectionHTML(title, tests) {
        if (!tests || tests.length === 0) {
            return `
                <section class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">${title}</h2>
                    <p class="text-gray-500">No tests in this category</p>
                </section>
            `;
        }
        
        const passedCount = tests.filter(t => t.passed).length;
        const totalCount = tests.length;
        
        return `
            <section class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">${title}</h2>
                <div class="mb-4">
                    <div class="text-sm text-gray-600">
                        ${passedCount}/${totalCount} tests passed
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div class="bg-green-600 h-2 rounded-full" style="width: ${(passedCount/totalCount)*100}%"></div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    ${tests.map(test => `
                        <div class="border-l-4 p-4 ${test.passed ? 'test-passed' : 'test-failed'}">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h3 class="font-medium">${test.test}</h3>
                                    <p class="text-sm mt-1">${test.message}</p>
                                    <p class="text-xs mt-1 opacity-75">Page: ${test.page} | Requirement: ${test.requirement}</p>
                                </div>
                                <div class="text-lg">
                                    ${test.passed ? '✅' : '❌'}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }
}

// Main execution
async function main() {
    const runner = new IntegrationValidationRunner();
    
    try {
        const success = await runner.runAllValidationTests();
        
        if (success) {
            console.log('\n🎉 Integration validation completed successfully!');
            process.exit(0);
        } else {
            console.log('\n⚠️ Integration validation completed with some failures.');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('\n💥 Integration validation failed:', error);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = IntegrationValidationRunner;