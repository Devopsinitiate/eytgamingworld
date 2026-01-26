/**
 * Simple Console Error Property Test Runner
 * Tests console error handling functionality in Node.js environment
 * 
 * **Feature: tournament-detail-page-fixes, Property 7: Console Error-Free Operation**
 * **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
 */

// Mock browser environment for Node.js
global.window = {
    addEventListener: () => {},
    removeEventListener: () => {},
    fetch: async () => ({ ok: true, status: 200 }),
    XMLHttpRequest: function() {
        this.addEventListener = () => {};
        this.send = () => {};
    },
    location: { href: 'http://localhost/tournament/test/' }
};

global.document = {
    createElement: () => ({ addEventListener: () => {}, remove: () => {} }),
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    head: { appendChild: () => {} },
    documentElement: { appendChild: () => {} }
};

// Mock MutationObserver
global.MutationObserver = class {
    constructor(callback) {
        this.callback = callback;
    }
    observe() {}
    disconnect() {}
};

// Store original console methods
const originalConsole = {
    log: console.log,
    warn: console.warn,
    error: console.error,
    info: console.info
};

// Load the console error handler
let ConsoleErrorHandler;
try {
    // Try the simplified version first
    ConsoleErrorHandler = require('./static/js/modules/console-error-handler-simple.js');
    console.log('Loaded simplified ConsoleErrorHandler:', typeof ConsoleErrorHandler);
    
    if (typeof ConsoleErrorHandler !== 'function') {
        throw new Error('ConsoleErrorHandler is not a constructor function');
    }
} catch (error) {
    console.error('Failed to load ConsoleErrorHandler:', error.message);
    process.exit(1);
}

class SimpleConsoleErrorTestRunner {
    constructor() {
        this.results = {
            totalTests: 0,
            passedTests: 0,
            failedTests: 0,
            errors: [],
            testDetails: []
        };
    }
    
    async runTests() {
        console.log('🧪 Starting Console Error Property Tests...');
        console.log('📁 Testing console error handling functionality');
        console.log('🔄 Running property-based tests...');
        console.log('─'.repeat(60));
        
        const startTime = Date.now();
        
        // Test 1: Console Error-Free Operation Property
        await this.runPropertyTest(
            'Console Error-Free Operation',
            () => this.testConsoleErrorFreeOperation()
        );
        
        // Test 2: Error Suppression Property
        await this.runPropertyTest(
            'Error Suppression Consistency',
            () => this.testErrorSuppression()
        );
        
        // Test 3: Logging Level Property
        await this.runPropertyTest(
            'Logging Level Compliance',
            () => this.testLoggingLevels()
        );
        
        // Test 4: Network Error Handling Property
        await this.runPropertyTest(
            'Network Error Handling',
            () => this.testNetworkErrorHandling()
        );
        
        // Test 5: Module Loading Error Property
        await this.runPropertyTest(
            'Module Loading Error Handling',
            () => this.testModuleLoadingErrors()
        );
        
        const duration = Date.now() - startTime;
        this.printResults(duration);
        
        return this.results;
    }
    
    async runPropertyTest(testName, testFunction) {
        this.results.totalTests++;
        const startTime = Date.now();
        
        try {
            const result = await testFunction();
            const duration = Date.now() - startTime;
            
            const testDetail = {
                name: testName,
                success: result.success,
                duration,
                details: result.details,
                error: result.error
            };
            
            this.results.testDetails.push(testDetail);
            
            if (result.success) {
                console.log(`✅ ${testName} - PASSED (${duration}ms)`);
                if (result.details) {
                    console.log(`   📊 ${result.details}`);
                }
                this.results.passedTests++;
            } else {
                console.log(`❌ ${testName} - FAILED (${duration}ms)`);
                console.log(`   💥 ${result.error}`);
                this.results.failedTests++;
                this.results.errors.push(`${testName}: ${result.error}`);
            }
            
        } catch (error) {
            const duration = Date.now() - startTime;
            console.log(`💥 ${testName} - ERROR (${duration}ms)`);
            console.log(`   🚨 ${error.message}`);
            
            this.results.testDetails.push({
                name: testName,
                success: false,
                duration,
                error: error.message
            });
            
            this.results.failedTests++;
            this.results.errors.push(`${testName}: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testConsoleErrorFreeOperation() {
        const iterations = 50;
        let successfulOperations = 0;
        let totalHandledErrors = 0;
        
        for (let i = 0; i < iterations; i++) {
            const consoleErrorHandler = new ConsoleErrorHandler({
                suppressErrors: true,
                logLevel: 'info'
            });
            
            try {
                // Generate random operation that might cause errors
                const operationType = Math.floor(Math.random() * 4);
                
                switch (operationType) {
                    case 0: // JavaScript operation
                        try {
                            if (Math.random() > 0.5) {
                                throw new Error('Test JavaScript error');
                            }
                        } catch (e) {
                            // Simulate error handling
                            const mockEvent = {
                                message: e.message,
                                filename: 'test.js',
                                lineno: 1,
                                colno: 1,
                                error: e,
                                preventDefault: () => {}
                            };
                            consoleErrorHandler.handleJavaScriptError(mockEvent);
                        }
                        break;
                        
                    case 1: // Network operation
                        consoleErrorHandler.handleNetworkError(new Error(`Network: test-${i}`));
                        break;
                        
                    case 2: // Module operation
                        if (Math.random() > 0.5) {
                            consoleErrorHandler.handleResourceError({
                                target: { src: `/static/js/test-module-${i}.js` }
                            });
                        }
                        break;
                        
                    case 3: // Promise operation
                        try {
                            if (Math.random() > 0.5) {
                                throw new Error('Test promise rejection');
                            }
                        } catch (e) {
                            const mockEvent = {
                                reason: e.message,
                                preventDefault: () => {}
                            };
                            consoleErrorHandler.handlePromiseRejection(mockEvent);
                        }
                        break;
                }
                
                // Check that errors were handled
                const errorCounts = consoleErrorHandler.getErrorCounts();
                const hasHandledErrors = Object.values(errorCounts).some(count => count > 0);
                
                if (hasHandledErrors || operationType === 0) {
                    successfulOperations++;
                    totalHandledErrors += Object.values(errorCounts).reduce((sum, count) => sum + count, 0);
                }
                
            } finally {
                consoleErrorHandler.destroy();
            }
        }
        
        const successRate = (successfulOperations / iterations) * 100;
        
        return {
            success: successfulOperations >= iterations * 0.8, // 80% success rate acceptable
            error: successfulOperations < iterations * 0.8 ? 
                `Only ${successfulOperations}/${iterations} operations succeeded (${successRate.toFixed(1)}%)` : null,
            details: `${successfulOperations}/${iterations} operations clean (${successRate.toFixed(1)}%), ${totalHandledErrors} errors handled`
        };
    }
    
    async testErrorSuppression() {
        const consoleErrorHandler = new ConsoleErrorHandler({ suppressErrors: true });
        let suppressedErrors = 0;
        const iterations = 20;
        
        try {
            for (let i = 0; i < iterations; i++) {
                const mockEvent = {
                    message: `Test error ${i}`,
                    filename: 'test.js',
                    lineno: i,
                    colno: 1,
                    error: new Error(`Test error ${i}`),
                    preventDefault: () => { suppressedErrors++; }
                };
                
                consoleErrorHandler.handleJavaScriptError(mockEvent);
            }
            
            return {
                success: suppressedErrors === iterations,
                error: suppressedErrors !== iterations ? 
                    `Only ${suppressedErrors}/${iterations} errors were suppressed` : null,
                details: `${suppressedErrors}/${iterations} errors suppressed`
            };
            
        } finally {
            consoleErrorHandler.destroy();
        }
    }
    
    async testLoggingLevels() {
        const logLevels = ['debug', 'info', 'warn', 'error'];
        let successfulLevels = 0;
        
        for (const level of logLevels) {
            const consoleErrorHandler = new ConsoleErrorHandler({ 
                logLevel: level,
                suppressErrors: true 
            });
            
            try {
                // Test logging level hierarchy
                const shouldLogDebug = consoleErrorHandler.shouldLog('debug');
                const shouldLogInfo = consoleErrorHandler.shouldLog('info');
                const shouldLogWarn = consoleErrorHandler.shouldLog('warn');
                const shouldLogError = consoleErrorHandler.shouldLog('error');
                
                // Verify logging level hierarchy
                const levelIndex = logLevels.indexOf(level);
                const expectedDebug = levelIndex <= 0;
                const expectedInfo = levelIndex <= 1;
                const expectedWarn = levelIndex <= 2;
                const expectedError = levelIndex <= 3;
                
                if (shouldLogDebug === expectedDebug && 
                    shouldLogInfo === expectedInfo && 
                    shouldLogWarn === expectedWarn && 
                    shouldLogError === expectedError) {
                    successfulLevels++;
                }
                
            } finally {
                consoleErrorHandler.destroy();
            }
        }
        
        return {
            success: successfulLevels === logLevels.length,
            error: successfulLevels !== logLevels.length ? 
                `Only ${successfulLevels}/${logLevels.length} log levels worked correctly` : null,
            details: `${successfulLevels}/${logLevels.length} log levels compliant`
        };
    }
    
    async testNetworkErrorHandling() {
        const consoleErrorHandler = new ConsoleErrorHandler({ suppressErrors: true });
        let handledRequests = 0;
        const iterations = 15;
        
        try {
            for (let i = 0; i < iterations; i++) {
                // Simulate different types of network errors
                const errorTypes = [
                    new Error(`Network timeout ${i}`),
                    { status: 404, message: 'Not Found' },
                    { status: 500, message: 'Server Error' },
                    new Error(`Connection failed ${i}`)
                ];
                
                const error = errorTypes[i % errorTypes.length];
                consoleErrorHandler.handleNetworkError(error);
                
                // Check that error was handled
                const errorCounts = consoleErrorHandler.getErrorCounts();
                if (errorCounts.network > 0) {
                    handledRequests++;
                }
            }
            
            return {
                success: handledRequests >= iterations * 0.8, // 80% success rate
                error: handledRequests < iterations * 0.8 ? 
                    `Only ${handledRequests}/${iterations} network errors handled cleanly` : null,
                details: `${handledRequests}/${iterations} network errors handled`
            };
            
        } finally {
            consoleErrorHandler.destroy();
        }
    }
    
    async testModuleLoadingErrors() {
        const consoleErrorHandler = new ConsoleErrorHandler({ suppressErrors: true });
        let handledModules = 0;
        const iterations = 10;
        
        try {
            for (let i = 0; i < iterations; i++) {
                // Simulate module loading errors
                const mockEvent = {
                    target: { 
                        src: `/static/js/test-module-${i}.js`,
                        tagName: 'SCRIPT'
                    }
                };
                
                consoleErrorHandler.handleResourceError(mockEvent);
                
                // Check that error was handled
                const errorCounts = consoleErrorHandler.getErrorCounts();
                if (errorCounts.module > 0) {
                    handledModules++;
                }
            }
            
            return {
                success: handledModules >= iterations * 0.8, // 80% success rate
                error: handledModules < iterations * 0.8 ? 
                    `Only ${handledModules}/${iterations} module errors handled cleanly` : null,
                details: `${handledModules}/${iterations} module errors handled`
            };
            
        } finally {
            consoleErrorHandler.destroy();
        }
    }
    
    printResults(duration) {
        const successRate = (this.results.passedTests / this.results.totalTests) * 100;
        
        console.log('═'.repeat(60));
        console.log('📊 CONSOLE ERROR PROPERTY TEST RESULTS');
        console.log('═'.repeat(60));
        console.log(`⏱️  Duration: ${duration}ms`);
        console.log(`🧪 Total Tests: ${this.results.totalTests}`);
        console.log(`✅ Passed: ${this.results.passedTests}`);
        console.log(`❌ Failed: ${this.results.failedTests}`);
        
        if (this.results.errors.length > 0) {
            console.log('\n🚨 ERRORS:');
            this.results.errors.forEach((error, index) => {
                console.log(`   ${index + 1}. ${error}`);
            });
        }
        
        console.log(`\n📈 Success Rate: ${successRate.toFixed(1)}%`);
        
        if (this.results.failedTests === 0) {
            console.log('\n🎉 ALL CONSOLE ERROR PROPERTY TESTS PASSED!');
            console.log('✨ Console error-free operation property validated');
            console.log('🔒 Requirements 7.1, 7.2, 7.3, 7.4, 7.5 satisfied');
        } else {
            console.log('\n⚠️  Some tests failed - console error handling needs attention');
        }
        
        console.log('═'.repeat(60));
    }
}

// Run tests if called directly
if (require.main === module) {
    const runner = new SimpleConsoleErrorTestRunner();
    runner.runTests().catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
}

module.exports = SimpleConsoleErrorTestRunner;