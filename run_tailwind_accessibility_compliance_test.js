/**
 * Tailwind CSS Accessibility Compliance Test Runner
 * Requirements: 5.1, 5.2, 5.3, 5.4
 * Automated testing for WCAG AA compliance
 */

const fs = require('fs');
const path = require('path');

/**
 * Test Configuration
 */
const TEST_CONFIG = {
    testFile: 'test_accessibility_compliance_tailwind.html',
    requirements: ['5.1', '5.2', '5.3', '5.4'],
    wcagLevel: 'AA',
    minimumContrastRatio: {
        normal: 4.5,
        large: 3.0,
        focus: 3.0
    }
};

/**
 * Color Contrast Calculator (Node.js version)
 */
class ColorContrastCalculator {
    static hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }

    static getRelativeLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }

    static getContrastRatio(color1, color2) {
        const lum1 = this.getRelativeLuminance(color1);
        const lum2 = this.getRelativeLuminance(color2);
        const brightest = Math.max(lum1, lum2);
        const darkest = Math.min(lum1, lum2);
        return (brightest + 0.05) / (darkest + 0.05);
    }

    static meetsWCAGAA(contrastRatio, isLargeText = false) {
        return isLargeText ? contrastRatio >= 3 : contrastRatio >= 4.5;
    }
}

/**
 * Accessibility Test Suite
 */
class AccessibilityTestSuite {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            tests: []
        };
    }

    /**
     * Test EYTGaming brand colors for WCAG AA compliance
     */
    testBrandColors() {
        console.log('\n🎨 Testing EYTGaming Brand Colors (Requirement 5.4)...');
        
        const brandColors = {
            primary: '#b91c1c',
            primaryDark: '#dc2626',
            white: '#ffffff',
            darkBackground: '#1a1a1a',
            lightBackground: '#ffffff'
        };

        const tests = [
            {
                name: 'Primary red on white background',
                foreground: brandColors.primary,
                background: brandColors.white,
                expected: 'pass'
            },
            {
                name: 'Primary red (dark mode) on dark background',
                foreground: '#ef4444', // Updated to match CSS
                background: brandColors.darkBackground,
                expected: 'pass'
            },
            {
                name: 'White text on primary red background',
                foreground: brandColors.white,
                background: brandColors.primary,
                expected: 'pass'
            },
            {
                name: 'White text on primary red (dark mode) background',
                foreground: brandColors.white,
                background: '#dc2626', // Use a darker shade for better contrast
                expected: 'pass'
            }
        ];

        tests.forEach(test => {
            const fg = ColorContrastCalculator.hexToRgb(test.foreground);
            const bg = ColorContrastCalculator.hexToRgb(test.background);
            const ratio = ColorContrastCalculator.getContrastRatio(fg, bg);
            const passes = ColorContrastCalculator.meetsWCAGAA(ratio);
            
            const result = {
                test: test.name,
                requirement: '5.4',
                contrastRatio: ratio.toFixed(2),
                passes: passes,
                expected: test.expected === 'pass'
            };

            if (passes === result.expected) {
                console.log(`  ✅ ${test.name}: ${ratio.toFixed(2)}:1`);
                this.results.passed++;
            } else {
                console.log(`  ❌ ${test.name}: ${ratio.toFixed(2)}:1 (Expected: ${test.expected})`);
                this.results.failed++;
            }

            this.results.tests.push(result);
        });
    }

    /**
     * Test status colors for WCAG AA compliance
     */
    testStatusColors() {
        console.log('\n🚦 Testing Status Colors (Requirement 5.4)...');
        
        const statusColors = {
            success: '#047857',
            warning: '#b45309',
            error: '#dc2626',
            info: '#2563eb',
            white: '#ffffff',
            black: '#000000'
        };

        const tests = [
            {
                name: 'Success color on white background',
                foreground: statusColors.success,
                background: statusColors.white,
                expected: 'pass'
            },
            {
                name: 'Warning color on white background',
                foreground: statusColors.warning,
                background: statusColors.white,
                expected: 'pass'
            },
            {
                name: 'Error color on white background',
                foreground: statusColors.error,
                background: statusColors.white,
                expected: 'pass'
            },
            {
                name: 'Info color on white background',
                foreground: statusColors.info,
                background: statusColors.white,
                expected: 'pass'
            },
            {
                name: 'White text on success background',
                foreground: statusColors.white,
                background: statusColors.success,
                expected: 'pass'
            },
            {
                name: 'White text on warning background',
                foreground: statusColors.white,
                background: statusColors.warning,
                expected: 'pass'
            },
            {
                name: 'White text on error background',
                foreground: statusColors.white,
                background: statusColors.error,
                expected: 'pass'
            },
            {
                name: 'White text on info background',
                foreground: statusColors.white,
                background: statusColors.info,
                expected: 'pass'
            }
        ];

        tests.forEach(test => {
            const fg = ColorContrastCalculator.hexToRgb(test.foreground);
            const bg = ColorContrastCalculator.hexToRgb(test.background);
            const ratio = ColorContrastCalculator.getContrastRatio(fg, bg);
            const passes = ColorContrastCalculator.meetsWCAGAA(ratio);
            
            const result = {
                test: test.name,
                requirement: '5.4',
                contrastRatio: ratio.toFixed(2),
                passes: passes,
                expected: test.expected === 'pass'
            };

            if (passes === result.expected) {
                console.log(`  ✅ ${test.name}: ${ratio.toFixed(2)}:1`);
                this.results.passed++;
            } else {
                console.log(`  ❌ ${test.name}: ${ratio.toFixed(2)}:1 (Expected: ${test.expected})`);
                this.results.failed++;
            }

            this.results.tests.push(result);
        });
    }

    /**
     * Test focus indicator contrast ratios
     */
    testFocusIndicators() {
        console.log('\n🎯 Testing Focus Indicators (Requirement 5.1)...');
        
        const focusTests = [
            {
                name: 'Primary focus indicator on white background',
                foreground: '#b91c1c',
                background: '#ffffff',
                expected: 'pass'
            },
            {
                name: 'Primary focus indicator (dark mode) on dark background',
                foreground: '#ef4444', // Updated to match CSS
                background: '#1a1a1a',
                expected: 'pass'
            },
            {
                name: 'White focus indicator on primary background',
                foreground: '#ffffff',
                background: '#b91c1c',
                expected: 'pass'
            }
        ];

        focusTests.forEach(test => {
            const fg = ColorContrastCalculator.hexToRgb(test.foreground);
            const bg = ColorContrastCalculator.hexToRgb(test.background);
            const ratio = ColorContrastCalculator.getContrastRatio(fg, bg);
            const passes = ratio >= TEST_CONFIG.minimumContrastRatio.focus;
            
            const result = {
                test: test.name,
                requirement: '5.1',
                contrastRatio: ratio.toFixed(2),
                passes: passes,
                expected: test.expected === 'pass'
            };

            if (passes === result.expected) {
                console.log(`  ✅ ${test.name}: ${ratio.toFixed(2)}:1`);
                this.results.passed++;
            } else {
                console.log(`  ❌ ${test.name}: ${ratio.toFixed(2)}:1 (Expected: ${test.expected})`);
                this.results.failed++;
            }

            this.results.tests.push(result);
        });
    }

    /**
     * Test dark mode contrast ratios
     */
    testDarkModeContrast() {
        console.log('\n🌙 Testing Dark Mode Contrast (Requirement 5.2)...');
        
        const darkModeTests = [
            {
                name: 'Primary text on dark background',
                foreground: '#f9fafb',
                background: '#1a1a1a',
                expected: 'pass'
            },
            {
                name: 'Secondary text on dark background',
                foreground: '#d1d5db',
                background: '#1a1a1a',
                expected: 'pass'
            },
            {
                name: 'Muted text on dark background',
                foreground: '#9ca3af',
                background: '#1a1a1a',
                expected: 'pass'
            },
            {
                name: 'Primary brand color on dark background',
                foreground: '#ef4444', // Updated to match CSS
                background: '#1a1a1a',
                expected: 'pass'
            },
            {
                name: 'White text on card background (dark mode)',
                foreground: '#f9fafb',
                background: '#2a2a2a',
                expected: 'pass'
            }
        ];

        darkModeTests.forEach(test => {
            const fg = ColorContrastCalculator.hexToRgb(test.foreground);
            const bg = ColorContrastCalculator.hexToRgb(test.background);
            const ratio = ColorContrastCalculator.getContrastRatio(fg, bg);
            const passes = ColorContrastCalculator.meetsWCAGAA(ratio);
            
            const result = {
                test: test.name,
                requirement: '5.2',
                contrastRatio: ratio.toFixed(2),
                passes: passes,
                expected: test.expected === 'pass'
            };

            if (passes === result.expected) {
                console.log(`  ✅ ${test.name}: ${ratio.toFixed(2)}:1`);
                this.results.passed++;
            } else {
                console.log(`  ❌ ${test.name}: ${ratio.toFixed(2)}:1 (Expected: ${test.expected})`);
                this.results.failed++;
            }

            this.results.tests.push(result);
        });
    }

    /**
     * Validate CSS file structure and content
     */
    validateCSSImplementation() {
        console.log('\n📄 Validating CSS Implementation...');
        
        const cssFile = 'static/css/tailwind-accessibility-compliance.css';
        
        if (!fs.existsSync(cssFile)) {
            console.log(`  ❌ CSS file not found: ${cssFile}`);
            this.results.failed++;
            return;
        }

        const cssContent = fs.readFileSync(cssFile, 'utf8');
        
        const requiredRules = [
            '.focus\\:outline-primary:focus',
            '.dark .text-primary',
            '.interactive-element',
            '.text-brand-red',
            '@media (prefers-contrast: high)',
            '@media (prefers-reduced-motion: reduce)',
            '[aria-live="polite"]'
        ];

        requiredRules.forEach(rule => {
            if (cssContent.includes(rule)) {
                console.log(`  ✅ Found required CSS rule: ${rule}`);
                this.results.passed++;
            } else {
                console.log(`  ❌ Missing required CSS rule: ${rule}`);
                this.results.failed++;
            }
        });
    }

    /**
     * Validate JavaScript file structure and content
     */
    validateJSImplementation() {
        console.log('\n📄 Validating JavaScript Implementation...');
        
        const jsFile = 'static/js/tailwind-accessibility-compliance.js';
        
        if (!fs.existsSync(jsFile)) {
            console.log(`  ❌ JavaScript file not found: ${jsFile}`);
            this.results.failed++;
            return;
        }

        const jsContent = fs.readFileSync(jsFile, 'utf8');
        
        const requiredClasses = [
            'ColorContrastValidator',
            'AccessibilityComplianceValidator',
            'AccessibilityEnhancer'
        ];

        const requiredMethods = [
            'validateFocusIndicators',
            'validateDarkModeContrast',
            'validateInteractiveElements',
            'validateCustomColors',
            'getContrastRatio',
            'meetsWCAGAA'
        ];

        requiredClasses.forEach(className => {
            if (jsContent.includes(`class ${className}`)) {
                console.log(`  ✅ Found required class: ${className}`);
                this.results.passed++;
            } else {
                console.log(`  ❌ Missing required class: ${className}`);
                this.results.failed++;
            }
        });

        requiredMethods.forEach(method => {
            if (jsContent.includes(method)) {
                console.log(`  ✅ Found required method: ${method}`);
                this.results.passed++;
            } else {
                console.log(`  ❌ Missing required method: ${method}`);
                this.results.failed++;
            }
        });
    }

    /**
     * Run all accessibility tests
     */
    runAllTests() {
        console.log('🔍 Running Tailwind CSS Accessibility Compliance Tests...');
        console.log(`📋 Testing against WCAG ${TEST_CONFIG.wcagLevel} standards`);
        console.log(`📋 Requirements: ${TEST_CONFIG.requirements.join(', ')}`);
        
        this.testBrandColors();
        this.testStatusColors();
        this.testFocusIndicators();
        this.testDarkModeContrast();
        this.validateCSSImplementation();
        this.validateJSImplementation();
        
        return this.results;
    }

    /**
     * Generate test report
     */
    generateReport() {
        const results = this.runAllTests();
        
        console.log('\n📊 Test Results Summary:');
        console.log('═'.repeat(50));
        console.log(`✅ Passed: ${results.passed}`);
        console.log(`❌ Failed: ${results.failed}`);
        console.log(`⚠️  Warnings: ${results.warnings}`);
        console.log(`📊 Total Tests: ${results.passed + results.failed + results.warnings}`);
        
        const passRate = ((results.passed / (results.passed + results.failed)) * 100).toFixed(1);
        console.log(`📈 Pass Rate: ${passRate}%`);
        
        if (results.failed === 0) {
            console.log('\n🎉 All accessibility compliance tests passed!');
            console.log('✅ Requirements 5.1, 5.2, 5.3, 5.4 are satisfied');
        } else {
            console.log(`\n⚠️  ${results.failed} tests failed. Review implementation.`);
        }
        
        // Save detailed results to file
        const reportFile = 'tailwind_accessibility_test_report.json';
        fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));
        console.log(`\n📄 Detailed report saved to: ${reportFile}`);
        
        return results;
    }
}

/**
 * Main execution
 */
if (require.main === module) {
    const testSuite = new AccessibilityTestSuite();
    const results = testSuite.generateReport();
    
    // Exit with appropriate code
    process.exit(results.failed === 0 ? 0 : 1);
}

module.exports = {
    AccessibilityTestSuite,
    ColorContrastCalculator,
    TEST_CONFIG
};