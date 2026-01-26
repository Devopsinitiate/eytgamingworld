/**
 * Property-Based Tests for Copy Link Handler
 * Tests Property 4: Copy Link Cross-Browser Functionality
 * Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
 */

// Import the CopyLinkHandler module
import CopyLinkHandler from './modules/copy-link-handler.js';

class CopyLinkPropertyTests {
    constructor() {
        this.testResults = [];
        this.iterations = 100;
        this.currentIteration = 0;
    }
    
    // Property test generators
    generateRandomURL() {
        const protocols = ['http://', 'https://'];
        const domains = ['example.com', 'test.org', 'localhost:8000', 'eytgaming.com'];
        const paths = ['', '/tournaments', '/tournaments/test-tournament', '/tournaments/test-tournament-123'];
        const queries = ['', '?param=value', '?utm_source=test&utm_medium=copy'];
        const fragments = ['', '#section', '#details', '#participants'];
        
        const protocol = protocols[Math.floor(Math.random() * protocols.length)];
        const domain = domains[Math.floor(Math.random() * domains.length)];
        const path = paths[Math.floor(Math.random() * paths.length)];
        const query = queries[Math.floor(Math.random() * queries.length)];
        const fragment = fragments[Math.floor(Math.random() * fragments.length)];
        
        return protocol + domain + path + query + fragment;
    }
    
    generateRandomBrowserEnvironment() {
        const environments = [
            {
                name: 'Modern Chrome',
                hasClipboardAPI: true,
                hasExecCommand: true,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            {
                name: 'Modern Firefox',
                hasClipboardAPI: true,
                hasExecCommand: true,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
            },
            {
                name: 'Safari',
                hasClipboardAPI: true,
                hasExecCommand: true,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
            },
            {
                name: 'Edge',
                hasClipboardAPI: true,
                hasExecCommand: true,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
            },
            {
                name: 'Legacy Browser',
                hasClipboardAPI: false,
                hasExecCommand: true,
                isSecureContext: false,
                userAgent: 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
            },
            {
                name: 'Insecure Context',
                hasClipboardAPI: false,
                hasExecCommand: true,
                isSecureContext: false,
                userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            {
                name: 'Mobile Safari',
                hasClipboardAPI: true,
                hasExecCommand: false,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
            },
            {
                name: 'Mobile Chrome',
                hasClipboardAPI: true,
                hasExecCommand: true,
                isSecureContext: true,
                userAgent: 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
            }
        ];
        
        return environments[Math.floor(Math.random() * environments.length)];
    }
    
    generateRandomButtonElement() {
        const buttonTypes = [
            '<button class="copy-button">Copy Link</button>',
            '<button class="copy-link" data-copy-link>Share</button>',
            '<button data-action="copy-link">btn-copy-link</button>',
            '<a href="#" class="copy-button">class="btn btn-copy"</a>',
            '<button class="copy-link"></button>', // Empty text
            '<button class="copy-button">Copy Tournament Link</button>'
        ];
        
        const buttonHTML = buttonTypes[Math.floor(Math.random() * buttonTypes.length)];
        const div = document.createElement('div');
        div.innerHTML = buttonHTML;
        return div.firstElementChild;
    }
    
    // Mock browser environment
    mockBrowserEnvironment(env) {
        // Store original values
        const originalNavigator = { ...navigator };
        const originalDocument = { ...document };
        const originalWindow = { ...window };
        
        // Mock navigator.clipboard
        if (env.hasClipboardAPI) {
            Object.defineProperty(navigator, 'clipboard', {
                value: {
                    writeText: async (text) => {
                        if (!env.isSecureContext) {
                            throw new Error('Clipboard API requires secure context');
                        }
                        return Promise.resolve();
                    }
                },
                configurable: true
            });
        } else {
            Object.defineProperty(navigator, 'clipboard', {
                value: undefined,
                configurable: true
            });
        }
        
        // Mock document.execCommand
        if (env.hasExecCommand) {
            document.execCommand = () => true;
        } else {
            document.execCommand = undefined;
        }
        
        // Mock window.isSecureContext
        Object.defineProperty(window, 'isSecureContext', {
            value: env.isSecureContext,
            configurable: true
        });
        
        // Mock navigator.userAgent
        Object.defineProperty(navigator, 'userAgent', {
            value: env.userAgent,
            configurable: true
        });
        
        return () => {
            // Restore original values
            Object.defineProperty(navigator, 'clipboard', {
                value: originalNavigator.clipboard,
                configurable: true
            });
            document.execCommand = originalDocument.execCommand;
            Object.defineProperty(window, 'isSecureContext', {
                value: originalWindow.isSecureContext,
                configurable: true
            });
            Object.defineProperty(navigator, 'userAgent', {
                value: originalNavigator.userAgent,
                configurable: true
            });
        };
    }
    
    // Property 4: Copy Link Cross-Browser Functionality
    async testCopyLinkCrossBrowserFunctionality() {
        console.log('Testing Property 4: Copy Link Cross-Browser Functionality');
        
        for (let i = 0; i < this.iterations; i++) {
            this.currentIteration = i + 1;
            
            try {
                // Generate random test data
                const url = this.generateRandomURL();
                const browserEnv = this.generateRandomBrowserEnvironment();
                const buttonElement = this.generateRandomButtonElement();
                
                // Mock browser environment
                const restoreEnv = this.mockBrowserEnvironment(browserEnv);
                
                try {
                    // Add button to DOM
                    document.body.appendChild(buttonElement);
                    
                    // Create CopyLinkHandler instance
                    const handler = new CopyLinkHandler(buttonElement);
                    
                    // Test 1: Button text should be properly displayed (no HTML class names)
                    const buttonText = buttonElement.textContent || buttonElement.innerText;
                    const hasProperText = !buttonText.includes('class=') && 
                                        !buttonText.includes('btn-') && 
                                        buttonText.trim() !== '';
                    
                    if (!hasProperText) {
                        throw new Error(`Button text contains HTML class names or is empty: "${buttonText}"`);
                    }
                    
                    // Test 2: Copy functionality should work or provide fallback
                    let copySucceeded = false;
                    let fallbackProvided = false;
                    let feedbackShown = false;
                    
                    // Mock feedback system to detect if feedback was shown
                    const originalShowFeedback = handler.showFeedback;
                    handler.showFeedback = (message, type) => {
                        feedbackShown = true;
                        return originalShowFeedback.call(handler, message, type);
                    };
                    
                    try {
                        await handler.copyToClipboard(url);
                        copySucceeded = true;
                    } catch (error) {
                        // Check if a fallback method was attempted
                        const modals = document.querySelectorAll('.copy-link-modal');
                        fallbackProvided = modals.length > 0;
                        
                        // Clean up modals
                        modals.forEach(modal => modal.remove());
                    }
                    
                    // Test 3: Either copy succeeded or fallback was provided
                    if (!copySucceeded && !fallbackProvided) {
                        throw new Error(`Copy failed and no fallback provided in ${browserEnv.name}`);
                    }
                    
                    // Test 4: User feedback should be displayed
                    if (!feedbackShown) {
                        throw new Error(`No user feedback shown in ${browserEnv.name}`);
                    }
                    
                    // Test 5: Browser compatibility - should work across different environments
                    const support = handler.checkBrowserSupport();
                    if (!support.clipboardAPI && !support.execCommand) {
                        // Should still provide modal fallback
                        if (!fallbackProvided) {
                            throw new Error(`No fallback method available in ${browserEnv.name}`);
                        }
                    }
                    
                    // Clean up
                    handler.destroy();
                    document.body.removeChild(buttonElement);
                    
                    this.testResults.push({
                        iteration: i + 1,
                        url,
                        browserEnv: browserEnv.name,
                        success: true,
                        copySucceeded,
                        fallbackProvided,
                        feedbackShown
                    });
                    
                } finally {
                    // Always restore environment
                    restoreEnv();
                }
                
            } catch (error) {
                this.testResults.push({
                    iteration: i + 1,
                    success: false,
                    error: error.message,
                    browserEnv: browserEnv?.name || 'unknown'
                });
                
                console.error(`Property test failed at iteration ${i + 1}:`, error);
                throw error; // Re-throw to fail the test
            }
        }
        
        return this.testResults;
    }
    
    // Run all property tests
    async runAllTests() {
        console.log(`Starting Copy Link Property Tests (${this.iterations} iterations)`);
        
        try {
            const results = await this.testCopyLinkCrossBrowserFunctionality();
            
            const successCount = results.filter(r => r.success).length;
            const failureCount = results.filter(r => !r.success).length;
            
            console.log(`\nProperty Test Results:`);
            console.log(`✓ Successful iterations: ${successCount}/${this.iterations}`);
            console.log(`✗ Failed iterations: ${failureCount}/${this.iterations}`);
            
            if (failureCount > 0) {
                console.log('\nFailures:');
                results.filter(r => !r.success).forEach(result => {
                    console.log(`  Iteration ${result.iteration}: ${result.error} (${result.browserEnv})`);
                });
            }
            
            // Summary statistics
            const browserStats = {};
            results.filter(r => r.success).forEach(result => {
                if (!browserStats[result.browserEnv]) {
                    browserStats[result.browserEnv] = { total: 0, copySucceeded: 0, fallbackUsed: 0 };
                }
                browserStats[result.browserEnv].total++;
                if (result.copySucceeded) browserStats[result.browserEnv].copySucceeded++;
                if (result.fallbackProvided) browserStats[result.browserEnv].fallbackUsed++;
            });
            
            console.log('\nBrowser Environment Statistics:');
            Object.entries(browserStats).forEach(([browser, stats]) => {
                console.log(`  ${browser}: ${stats.total} tests, ${stats.copySucceeded} direct copy, ${stats.fallbackUsed} fallback`);
            });
            
            return failureCount === 0;
            
        } catch (error) {
            console.error('Property tests failed:', error);
            return false;
        }
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CopyLinkPropertyTests;
}

// Auto-run if loaded directly
if (typeof window !== 'undefined' && window.location) {
    document.addEventListener('DOMContentLoaded', async () => {
        const tester = new CopyLinkPropertyTests();
        const success = await tester.runAllTests();
        
        if (success) {
            console.log('🎉 All copy link property tests passed!');
        } else {
            console.error('❌ Some copy link property tests failed!');
        }
    });
}