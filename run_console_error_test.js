/**
 * Console Error Property Test Runner
 * Executes property-based tests for console error-free operation
 * 
 * **Feature: tournament-detail-page-fixes, Property 7: Console Error-Free Operation**
 * **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_CONFIG = {
    testFile: 'static/js/test_console_error_properties.js',
    iterations: 100,
    timeout: 20000,
    verbose: true
};

class ConsoleErrorTestRunner {
    constructor(config = {}) {
        this.config = { ...TEST_CONFIG, ...config };
        this.results = {
            totalTests: 0,
            passedTests: 0,
            failedTests: 0,
            errors: [],
            startTime: null,
            endTime: null
        };
    }
    
    async runTests() {
        console.log('🧪 Starting Console Error Property Tests...');
        console.log(`📁 Test file: ${this.config.testFile}`);
        console.log(`🔄 Iterations: ${this.config.iterations}`);
        console.log(`⏱️  Timeout: ${this.config.timeout}ms`);
        console.log('─'.repeat(60));
        
        this.results.startTime = Date.now();
        
        try {
            // Check if test file exists
            if (!fs.existsSync(this.config.testFile)) {
                throw new Error(`Test file not found: ${this.config.testFile}`);
            }
            
            // Run the property tests
            await this.executePropertyTests();
            
            this.results.endTime = Date.now();
            this.printResults();
            
        } catch (error) {
            this.results.endTime = Date.now();
            this.results.errors.push(error.message);
            console.error('❌ Test execution failed:', error.message);
            this.printResults();
            process.exit(1);
        }
    }
    
    async executePropertyTests() {
        console.log('🔍 Executing Console Error Property Tests...\n');
        
        // Load and execute the test file
        const testModule = require(path.resolve(this.config.testFile));
        const { ConsoleErrorHandler, ConsoleErrorTestGenerators } = testModule;
        
        // Test 1: Console Error-Free Operation Property
        await this.runPropertyTest(
            'Console Error-Free Operation',
            async () => {
                return await this.testConsoleErrorFreeOperation(ConsoleErrorHandler, ConsoleErrorTestGenerators);
            }
        );
        
        // Test 2: Error Suppression Property
        await this.runPropertyTest(
            'Error Suppression Consistency',
            async () => {
                return await this.testErrorSuppression(ConsoleErrorHandler);
            }
        );
        
        // Test 3: Logging Level Property
        await this.runPropertyTest(
            'Logging Level Compliance',
            async () => {
                return await this.testLoggingLevels(ConsoleErrorHandler);
            }
        );
        
        // Test 4: Network Error Handling Property
        await this.runPropertyTest(
            'Network Error Handling',
            async () => {
                return await this.testNetworkErrorHandling(ConsoleErrorHandler, ConsoleErrorTestGenerators);
            }
        );
        
        // Test 5: Module Loading Error Property
        await this.runPropertyTest(
            'Module Loading Error Handling',
            async () => {
                return await this.testModuleLoadingErrors(ConsoleErrorHandler, ConsoleErrorTestGenerators);
            }
        );
    }
    
    async runPropertyTest(testName, testFunction) {
        console.log(`🧪 Running: ${testName}`);
        this.results.totalTests++;
        
        try {
            const startTime = Date.now();
            const result = await testFunction();
            const duration = Date.now() - startTime;
            
            if (result.success) {
                console.log(`✅ ${testName} - PASSED (${duration}ms)`);
                if (this.config.verbose && result.details) {
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
            console.log(`💥 ${testName} - ERROR`);
            console.log(`   🚨 ${error.message}`);
            this.results.failedTests++;
            this.results.errors.push(`${testName}: ${error.message}`);
        }
        
        console.log('');
    }
    
    async testConsoleErrorFreeOperation(ConsoleErrorHandler, ConsoleErrorTestGenerators) {
        const iterations = Math.min(this.config.iterations, 50); // Limit for performance
        let successfulOperations = 0;
        let totalVisibleErrors = 0;
        let totalHandledErrors = 0;
        
        for (let i = 0; i < iterations; i++) {
            const consoleErrorHandler = new ConsoleErrorHandler({
                suppressErrors: true,
                logLevel: 'info'
            });
            
            try {
                // Generate random operation
                const operationType = Math.floor(Math.random() * 4);
                
                switch (operationType) {
                    case 0: // JavaScript operation
                        const jsOp = ConsoleErrorTestGenerators.generateJavaScriptOperation();
                        try { jsOp(); } catch (e) { /* Expected */ }
                        break;
                        
                    case 1: // Network operation (simulated)
                        const networkReq = ConsoleErrorTestGenerators.generateNetworkRequest();
                        consoleErrorHandler.handleNetworkError(new Error(`Network: ${networkReq.url}`));
                        break;
                        
                    case 2: // Module operation (simulated)
                        const moduleScenario = ConsoleErrorTestGenerators.generateModuleLoadScenario();
                        if (moduleScenario.shouldFail) {
                            consoleErrorHandler.handleResourceError({
                                target: { src: moduleScenario.path }
                            });
                        }
                        break;
                        
                    case 3: // Promise operation
                        const promiseOp = ConsoleErrorTestGenerators.generatePromiseOperation();
                        try { await promiseOp(); } catch (e) { /* Expected */ }
                        break;
                }
                
                // Check console state
                const consoleErrors = consoleErrorHandler.getConsoleErrors();
                const visibleErrors = consoleErrors.filter(log => 
                    log.level === 'error' && !log.message.includes('handled')
                );
                
                totalVisibleErrors += visibleErrors.length;
                totalHandledErrors += consoleErrors.length;
                
                if (visibleErrors.length === 0) {
                    successfulOperations++;
                }
                
            } finally {
                consoleErrorHandler.destroy();
            }
        }
        
        const successRate = (successfulOperations / iterations) * 100;
        
        return {
            success: totalVisibleErrors === 0 && successfulOperations === iterations,
            error: totalVisibleErrors > 0 ? 
                `Found ${totalVisibleErrors} visible console errors` : 
                successfulOperations < iterations ? 
                    `Only ${successfulOperations}/${iterations} operations succeeded` : null,
            details: `${successfulOperations}/${iterations} operations clean (${successRate.toFixed(1)}%), ${totalHandledErrors} errors handled`
        };
    }
    
    async testErrorSuppression(ConsoleErrorHandler) {
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
    
    async testLoggingLevels(ConsoleErrorHandler) {
        const logLevels = ['debug', 'info', 'warn', 'error'];
        let successfulLevels = 0;
        
        for (const level of logLevels) {
            const consoleErrorHandler = new ConsoleErrorHandler({ 
                logLevel: level,
                suppressErrors: true 
            });
            
            try {
                // Generate logs at different levels
                consoleErrorHandler.log('Debug message', 'debug');
                consoleErrorHandler.log('Info message', 'info');
                consoleErrorHandler.log('Warning message', 'warn');
                consoleErrorHandler.log('Error message', 'error');
                
                const allLogs = consoleErrorHandler.getInterceptedLogs();
                const levelIndex = logLevels.indexOf(level);
                
                // Count appropriate logs
                const appropriateLogs = allLogs.filter(log => {
                    const logLevelIndex = logLevels.indexOf(log.level);
                    return logLevelIndex >= levelIndex;
                });
                
                if (appropriateLogs.length > 0) {
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
    
    async testNetworkErrorHandling(ConsoleErrorHandler, ConsoleErrorTestGenerators) {
        const consoleErrorHandler = new ConsoleErrorHandler({ suppressErrors: true });
        let handledRequests = 0;
        const iterations = 15;
        
        try {
            for (let i = 0; i < iterations; i++) {
                const networkRequest = ConsoleErrorTestGenerators.generateNetworkRequest();
                
                // Simulate network error handling
                if (networkRequest.shouldFail) {
                    consoleErrorHandler.handleNetworkError(new Error(`Network error: ${networkRequest.url}`));
                }
                
                // Check that no visible errors appeared
                const consoleErrors = consoleErrorHandler.getConsoleErrors();
                const visibleErrors = consoleErrors.filter(log => 
                    log.level === 'error' && !log.message.includes('handled')
                );
                
                if (visibleErrors.length === 0) {
                    handledRequests++;
                }
            }
            
            return {
                success: handledRequests === iterations,
                error: handledRequests !== iterations ? 
                    `Only ${handledRequests}/${iterations} network errors handled cleanly` : null,
                details: `${handledRequests}/${iterations} network errors handled`
            };
            
        } finally {
            consoleErrorHandler.destroy();
        }
    }
    
    async testModuleLoadingErrors(ConsoleErrorHandler, ConsoleErrorTestGenerators) {
        const consoleErrorHandler = new ConsoleErrorHandler({ suppressErrors: true });
        let handledModules = 0;
        const iterations = 10;
        
        try {
            for (let i = 0; i < iterations; i++) {
                const moduleScenario = ConsoleErrorTestGenerators.generateModuleLoadScenario();
                
                if (moduleScenario.shouldFail) {
                    // Simulate module loading error
                    consoleErrorHandler.handleResourceError({
                        target: { src: moduleScenario.path }
                    });
                }
                
                // Check that no visible errors appeared
                const consoleErrors = consoleErrorHandler.getConsoleErrors();
                const visibleErrors = consoleErrors.filter(log => 
                    log.level === 'error' && !log.message.includes('handled')
                );
                
                if (visibleErrors.length === 0) {
                    handledModules++;
                }
            }
            
            return {
                success: handledModules === iterations,
                error: handledModules !== iterations ? 
                    `Only ${handledModules}/${iterations} module errors handled cleanly` : null,
                details: `${handledModules}/${iterations} module errors handled`
            };
            
        } finally {
            consoleErrorHandler.destroy();
        }
    }
    
    printResults() {
        const duration = this.results.endTime - this.results.startTime;
        
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
        
        const successRate = (this.results.passedTests / this.results.totalTests) * 100;
        console.log(`\n📈 Success Rate: ${successRate.toFixed(1)}%`);
        
        if (this.results.failedTests === 0) {
            console.log('\n🎉 ALL CONSOLE ERROR PROPERTY TESTS PASSED!');
            console.log('✨ Console error-free operation property validated');
        } else {
            console.log('\n⚠️  Some tests failed - console error handling needs attention');
        }
        
        console.log('═'.repeat(60));
    }
}

// Mock Jest functions if not available
if (typeof global === 'undefined') {
    global = {};
}

// Run tests if called directly
if (require.main === module) {
    const runner = new ConsoleErrorTestRunner();
    runner.runTests().catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
}

module.exports = ConsoleErrorTestRunner;