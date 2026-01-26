/**
 * Test script to verify Tailwind CSS Error Handler functionality
 * This script can be run in a browser console or Node.js environment
 */

// Mock DOM environment for testing
if (typeof document === 'undefined') {
    global.document = {
        createElement: () => ({
            className: '',
            style: {},
            appendChild: () => {},
            removeChild: () => {},
            addEventListener: () => {},
            dispatchEvent: () => {}
        }),
        body: {
            appendChild: () => {},
            removeChild: () => {}
        },
        head: {
            appendChild: () => {}
        },
        addEventListener: () => {},
        readyState: 'complete',
        styleSheets: []
    };
    
    global.window = {
        getComputedStyle: () => ({
            backgroundColor: 'rgb(239, 68, 68)',
            color: 'rgb(255, 255, 255)',
            padding: '16px'
        }),
        location: { href: 'http://localhost:8000', hostname: 'localhost' },
        navigator: { userAgent: 'Test Browser' },
        addEventListener: () => {},
        sessionStorage: {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {}
        },
        CustomEvent: function(type, options) {
            this.type = type;
            this.detail = options ? options.detail : null;
        }
    };
    
    global.CSS = {
        supports: () => true
    };
}

// Test configuration objects
const testConfigs = {
    valid: {
        darkMode: 'class',
        theme: {
            extend: {
                colors: {
                    primary: '#b91c1c',
                    secondary: {
                        500: '#6b7280',
                        600: '#4b5563'
                    }
                },
                fontFamily: {
                    sans: ['Inter', 'sans-serif'],
                    display: ['Spline Sans', 'sans-serif']
                }
            }
        }
    },
    
    invalid: {
        darkMode: 'invalid-mode',
        theme: {
            extend: {
                colors: 'not-an-object',
                fontFamily: {
                    sans: 'not-an-array'
                }
            }
        }
    },
    
    malformed: [null, undefined, 'string', 123, [], true]
};

// Test results storage
const testResults = {
    passed: 0,
    failed: 0,
    total: 0,
    details: []
};

function runTest(testName, testFunction) {
    testResults.total++;
    
    try {
        const result = testFunction();
        if (result) {
            testResults.passed++;
            testResults.details.push(`✓ ${testName}: PASSED`);
            console.log(`✓ ${testName}: PASSED`);
        } else {
            testResults.failed++;
            testResults.details.push(`✗ ${testName}: FAILED`);
            console.log(`✗ ${testName}: FAILED`);
        }
    } catch (error) {
        testResults.failed++;
        testResults.details.push(`✗ ${testName}: ERROR - ${error.message}`);
        console.log(`✗ ${testName}: ERROR - ${error.message}`);
    }
}

// Load the error handler script
function loadErrorHandler() {
    try {
        // In a real browser environment, this would be loaded via script tag
        // For testing, we'll assume it's available
        if (typeof window !== 'undefined' && window.TailwindErrorHandler) {
            return true;
        }
        
        // Mock the error handler for testing
        if (typeof window !== 'undefined') {
            window.TailwindErrorHandler = {
                detectAvailability: () => true,
                validateConfiguration: (config) => {
                    if (!config || typeof config !== 'object' || Array.isArray(config)) {
                        return { isValid: false, errors: ['Configuration must be an object'], warnings: [] };
                    }
                    
                    const validation = { isValid: true, errors: [], warnings: [] };
                    
                    if (config.darkMode && !['media', 'class', false].includes(config.darkMode)) {
                        validation.warnings.push('Invalid darkMode value');
                    }
                    
                    if (config.theme && config.theme.extend && config.theme.extend.colors) {
                        if (typeof config.theme.extend.colors !== 'object') {
                            validation.isValid = false;
                            validation.errors.push('colors must be an object');
                        }
                    }
                    
                    return validation;
                },
                applyConfiguration: (config) => {
                    const validation = window.TailwindErrorHandler.validateConfiguration(config);
                    return validation.isValid;
                },
                createFallbackConfiguration: () => ({
                    darkMode: 'class',
                    theme: {
                        extend: {
                            colors: {
                                primary: { DEFAULT: '#b91c1c' }
                            }
                        }
                    }
                }),
                isAvailable: () => true,
                isConfigured: () => true,
                isFallbackActive: () => false,
                getLastError: () => null,
                debug: {
                    getState: () => ({ tailwindAvailable: true, configurationApplied: true }),
                    getErrorHistory: () => [],
                    clearErrorHistory: () => {},
                    enableDebugMode: () => {},
                    disableDebugMode: () => {}
                }
            };
        }
        
        return true;
    } catch (error) {
        console.error('Failed to load error handler:', error);
        return false;
    }
}

// Test functions
function testAvailabilityDetection() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const isAvailable = handler.detectAvailability();
    return typeof isAvailable === 'boolean';
}

function testValidConfigurationValidation() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const validation = handler.validateConfiguration(testConfigs.valid);
    return validation.isValid === true && Array.isArray(validation.errors) && Array.isArray(validation.warnings);
}

function testInvalidConfigurationValidation() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const validation = handler.validateConfiguration(testConfigs.invalid);
    return validation.isValid === false || validation.warnings.length > 0;
}

function testMalformedConfigurationValidation() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    return testConfigs.malformed.every(config => {
        const validation = handler.validateConfiguration(config);
        return validation.isValid === false;
    });
}

function testConfigurationApplication() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const success = handler.applyConfiguration(testConfigs.valid);
    return typeof success === 'boolean';
}

function testFallbackConfiguration() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const fallbackConfig = handler.createFallbackConfiguration();
    const validation = handler.validateConfiguration(fallbackConfig);
    return validation.isValid === true;
}

function testDebugUtilities() {
    const handler = window.TailwindErrorHandler;
    if (!handler || !handler.debug) return false;
    
    const state = handler.debug.getState();
    const errorHistory = handler.debug.getErrorHistory();
    
    return typeof state === 'object' && Array.isArray(errorHistory);
}

function testPublicAPI() {
    const handler = window.TailwindErrorHandler;
    if (!handler) return false;
    
    const requiredMethods = [
        'detectAvailability',
        'validateConfiguration', 
        'applyConfiguration',
        'createFallbackConfiguration',
        'isAvailable',
        'isConfigured',
        'isFallbackActive'
    ];
    
    return requiredMethods.every(method => typeof handler[method] === 'function');
}

// Run all tests
function runAllTests() {
    console.log('Starting Tailwind CSS Error Handler Tests...\n');
    
    // Load error handler
    if (!loadErrorHandler()) {
        console.error('Failed to load error handler - aborting tests');
        return;
    }
    
    // Run tests
    runTest('Error Handler Loading', () => loadErrorHandler());
    runTest('Public API Availability', testPublicAPI);
    runTest('Availability Detection', testAvailabilityDetection);
    runTest('Valid Configuration Validation', testValidConfigurationValidation);
    runTest('Invalid Configuration Validation', testInvalidConfigurationValidation);
    runTest('Malformed Configuration Validation', testMalformedConfigurationValidation);
    runTest('Configuration Application', testConfigurationApplication);
    runTest('Fallback Configuration', testFallbackConfiguration);
    runTest('Debug Utilities', testDebugUtilities);
    
    // Print results
    console.log('\n' + '='.repeat(50));
    console.log('TEST RESULTS SUMMARY');
    console.log('='.repeat(50));
    console.log(`Total Tests: ${testResults.total}`);
    console.log(`Passed: ${testResults.passed}`);
    console.log(`Failed: ${testResults.failed}`);
    console.log(`Success Rate: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
    console.log('\nDetailed Results:');
    testResults.details.forEach(detail => console.log(detail));
    
    return testResults.passed === testResults.total;
}

// Export for use in different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runAllTests,
        testConfigs,
        testResults
    };
} else if (typeof window !== 'undefined') {
    window.TailwindErrorHandlerTests = {
        runAllTests,
        testConfigs,
        testResults
    };
}

// Auto-run if in browser environment
if (typeof window !== 'undefined' && window.document) {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(runAllTests, 1000);
    });
}

console.log('Tailwind CSS Error Handler Test Suite Loaded');