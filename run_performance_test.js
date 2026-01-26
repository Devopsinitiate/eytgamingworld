/**
 * Performance Property Test Runner
 * Runs property-based tests for performance optimization
 */

const puppeteer = require('puppeteer');
const path = require('path');

async function runPerformancePropertyTests() {
    console.log('Starting Performance Property Tests...');
    
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    try {
        const page = await browser.newPage();
        
        // Enable performance monitoring
        await page.setCacheEnabled(false);
        
        // Create test HTML page
        const testHTML = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Performance Property Tests</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .test-container { margin: 20px 0; }
                .test-result { margin: 10px 0; padding: 10px; border-radius: 4px; }
                .passed { background-color: #d4edda; color: #155724; }
                .failed { background-color: #f8d7da; color: #721c24; }
                .animate { transition: transform 0.3s ease; }
                .reduced-animations .animate { transition: none; }
            </style>
        </head>
        <body>
            <h1>Performance Property Tests</h1>
            <div id="test-results"></div>
            
            <script src="static/js/modules/performance-optimizer.js"></script>
            <script src="static/js/test_performance_properties.js"></script>
            
            <script>
                async function runTests() {
                    const testSuite = new PerformancePropertyTests();
                    
                    try {
                        const report = await testSuite.runAllTests();
                        
                        // Display results
                        const resultsDiv = document.getElementById('test-results');
                        resultsDiv.innerHTML = generateResultsHTML(report);
                        
                        // Return results for Node.js
                        window.testResults = report;
                        
                        console.log('All performance property tests completed');
                        return report;
                    } catch (error) {
                        console.error('Performance tests failed:', error);
                        window.testResults = { error: error.message };
                        throw error;
                    } finally {
                        testSuite.cleanup();
                    }
                }
                
                function generateResultsHTML(report) {
                    let html = '<div class="test-container">';
                    html += '<h2>Overall Results</h2>';
                    html += '<div class="test-result ' + (report.overall.allPropertiesPass ? 'passed' : 'failed') + '">';
                    html += 'Total Tests: ' + report.totalTests + ' | ';
                    html += 'Passed: ' + report.overall.passed + ' | ';
                    html += 'Failed: ' + report.overall.failed + ' | ';
                    html += 'Pass Rate: ' + report.overall.passRate;
                    html += '</div>';
                    
                    html += '<h2>Property Results</h2>';
                    Object.entries(report.properties).forEach(([property, results]) => {
                        html += '<div class="test-result ' + (results.failed === 0 ? 'passed' : 'failed') + '">';
                        html += '<strong>' + property + '</strong>: ';
                        html += results.passed + '/' + results.total + ' passed (' + results.passRate + ')';
                        if (results.failures.length > 0) {
                            html += '<br>Sample failures: ' + results.failures.length;
                        }
                        html += '</div>';
                    });
                    
                    html += '</div>';
                    return html;
                }
                
                // Auto-run tests when page loads
                window.addEventListener('load', runTests);
            </script>
        </body>
        </html>
        `;
        
        // Set content and wait for tests to complete
        await page.setContent(testHTML, { waitUntil: 'networkidle0' });
        
        // Wait for tests to complete (with timeout)
        await page.waitForFunction(
            () => window.testResults !== undefined,
            { timeout: 60000 }
        );
        
        // Get test results
        const results = await page.evaluate(() => window.testResults);
        
        if (results.error) {
            throw new Error(results.error);
        }
        
        // Log results
        console.log('\n=== Performance Property Test Results ===');
        console.log(`Total Tests: ${results.totalTests}`);
        console.log(`Properties Tested: ${results.propertiesTested}`);
        console.log(`Overall Pass Rate: ${results.overall.passRate}`);
        console.log(`All Properties Pass: ${results.overall.allPropertiesPass}`);
        
        console.log('\nProperty Breakdown:');
        Object.entries(results.properties).forEach(([property, data]) => {
            console.log(`  ${property}: ${data.passed}/${data.total} (${data.passRate})`);
            if (data.failed > 0) {
                console.log(`    Failures: ${data.failed}`);
            }
        });
        
        if (!results.overall.allPropertiesPass) {
            console.log('\nSample Failures:');
            Object.entries(results.properties).forEach(([property, data]) => {
                if (data.failures.length > 0) {
                    console.log(`  ${property}:`);
                    data.failures.slice(0, 2).forEach(failure => {
                        console.log(`    - Iteration ${failure.iteration}: ${JSON.stringify(failure, null, 2)}`);
                    });
                }
            });
        }
        
        return results;
        
    } finally {
        await browser.close();
    }
}

// Run tests if called directly
if (require.main === module) {
    runPerformancePropertyTests()
        .then(results => {
            if (results.overall.allPropertiesPass) {
                console.log('\n✅ All performance property tests passed!');
                process.exit(0);
            } else {
                console.log('\n❌ Some performance property tests failed.');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('\n💥 Performance property tests crashed:', error.message);
            process.exit(1);
        });
}

module.exports = runPerformancePropertyTests;