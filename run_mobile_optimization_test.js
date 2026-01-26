/**
 * Mobile Optimization Property Test Runner
 * Runs property-based tests for mobile optimization features
 */

const puppeteer = require('puppeteer');
const path = require('path');

async function runMobileOptimizationTests() {
    console.log('🚀 Starting Mobile Optimization Property Tests');
    
    let browser;
    let results = {
        passed: false,
        error: null,
        testResults: null,
        executionTime: 0
    };
    
    const startTime = Date.now();
    
    try {
        // Launch browser in mobile mode
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps'
            ]
        });
        
        const page = await browser.newPage();
        
        // Set mobile viewport initially
        await page.setViewport({
            width: 375,
            height: 667,
            isMobile: true,
            hasTouch: true,
            deviceScaleFactor: 2
        });
        
        // Enable mobile emulation
        await page.emulate({
            name: 'iPhone 8',
            userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            viewport: {
                width: 375,
                height: 667,
                deviceScaleFactor: 2,
                isMobile: true,
                hasTouch: true,
                isLandscape: false
            }
        });
        
        // Create a test HTML page with tournament detail components
        const testHTML = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Mobile Optimization Test</title>
            <style>
                /* Include essential mobile styles for testing */
                :root {
                    --mobile: 768px;
                    --tablet: 1024px;
                    --touch-target-min: 44px;
                }
                
                body {
                    margin: 0;
                    padding: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #111827;
                    color: white;
                }
                
                .tournament-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 1rem;
                    padding: 1rem;
                }
                
                @media (min-width: 768px) {
                    .tournament-grid {
                        grid-template-columns: 2fr 1fr;
                    }
                }
                
                .tournament-hero {
                    min-height: 350px;
                    background: linear-gradient(135deg, #1f2937, #111827);
                    display: flex;
                    align-items: flex-end;
                    padding: 2rem;
                    position: relative;
                }
                
                @media (min-width: 768px) {
                    .tournament-hero {
                        min-height: 500px;
                    }
                }
                
                .enhanced-registration-card {
                    background: #1f2937;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 1rem;
                    padding: 1rem;
                    position: sticky;
                    top: 2rem;
                }
                
                @media (max-width: 767px) {
                    .enhanced-registration-card {
                        position: fixed;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        top: auto;
                        z-index: 50;
                        border-radius: 1rem 1rem 0 0;
                        margin: 0;
                    }
                }
                
                .participant-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 1rem;
                }
                
                @media (min-width: 480px) {
                    .participant-grid {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
                
                @media (min-width: 768px) {
                    .participant-grid {
                        grid-template-columns: repeat(3, 1fr);
                    }
                }
                
                .participant-card {
                    background: #374151;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    min-height: 44px;
                    cursor: pointer;
                    transition: transform 0.2s ease;
                }
                
                .participant-card:hover {
                    transform: translateY(-2px);
                }
                
                .tab-container {
                    display: flex;
                    gap: 0.5rem;
                    overflow-x: auto;
                    padding: 0 1rem;
                    scroll-behavior: smooth;
                    -webkit-overflow-scrolling: touch;
                }
                
                .tab-button {
                    background: transparent;
                    border: 2px solid transparent;
                    border-radius: 0.5rem;
                    color: #9ca3af;
                    padding: 0.75rem 1.5rem;
                    white-space: nowrap;
                    cursor: pointer;
                    min-height: 44px;
                    min-width: fit-content;
                    flex-shrink: 0;
                }
                
                .tab-button.active {
                    background: #b91c1c;
                    color: white;
                    border-color: #dc2626;
                }
                
                .btn {
                    background: #b91c1c;
                    color: white;
                    border: none;
                    border-radius: 0.5rem;
                    padding: 0.75rem 1.5rem;
                    cursor: pointer;
                    min-height: 44px;
                    font-weight: 600;
                }
                
                .copy-button {
                    background: #374151;
                    color: white;
                    border: 1px solid #4b5563;
                    border-radius: 0.5rem;
                    padding: 0.5rem 1rem;
                    cursor: pointer;
                    min-height: 44px;
                }
                
                svg {
                    max-width: 100%;
                    height: auto;
                }
                
                .mobile-device .enhanced-registration-card {
                    position: fixed !important;
                    bottom: 0 !important;
                    left: 0 !important;
                    right: 0 !important;
                }
                
                .touch-device button:active,
                .touch-device .btn:active,
                .touch-device .participant-card:active {
                    transform: scale(0.98);
                }
            </style>
        </head>
        <body>
            <div class="tournament-grid">
                <main>
                    <div class="tournament-hero">
                        <div class="hero-content">
                            <h1>Test Tournament</h1>
                            <p>Mobile optimization test page</p>
                        </div>
                    </div>
                    
                    <div class="tab-container">
                        <button class="tab-button active">Details</button>
                        <button class="tab-button">Participants</button>
                        <button class="tab-button">Bracket</button>
                        <button class="tab-button">Rules</button>
                        <button class="tab-button">Statistics</button>
                    </div>
                    
                    <div class="participant-grid">
                        <div class="participant-card">Player 1</div>
                        <div class="participant-card">Player 2</div>
                        <div class="participant-card">Player 3</div>
                        <div class="participant-card">Player 4</div>
                        <div class="participant-card">Player 5</div>
                        <div class="participant-card">Player 6</div>
                    </div>
                    
                    <div style="margin: 2rem 0;">
                        <button class="btn">Register Now</button>
                        <button class="copy-button">Copy Link</button>
                    </div>
                    
                    <svg width="200" height="100" viewBox="0 0 200 100">
                        <rect width="200" height="100" fill="#374151"/>
                        <text x="100" y="50" text-anchor="middle" fill="white">Test SVG</text>
                    </svg>
                </main>
                
                <aside class="enhanced-registration-card">
                    <h3>Tournament Registration</h3>
                    <p>Join this tournament</p>
                    <button class="btn">Register</button>
                </aside>
            </div>
            
            <script src="/static/js/test_mobile_optimization_properties.js"></script>
        </body>
        </html>
        `;
        
        // Set page content
        await page.setContent(testHTML, { waitUntil: 'networkidle0' });
        
        // Wait for any dynamic content to load
        await page.waitForTimeout(2000);
        
        // Run the property tests
        console.log('📱 Running mobile optimization property tests...');
        
        const testResults = await page.evaluate(() => {
            // Ensure the test functions are available
            if (typeof runMobileOptimizationTests === 'undefined') {
                throw new Error('Mobile optimization test functions not loaded');
            }
            
            // Run the tests
            return runMobileOptimizationTests();
        });
        
        results.testResults = testResults;
        results.passed = testResults.overallPassed;
        
        if (results.passed) {
            console.log('✅ Mobile optimization property tests passed!');
            console.log(`📊 Test Summary:`);
            console.log(`   - Mobile Layout: ${testResults.mobileLayout.passed ? 'PASS' : 'FAIL'}`);
            console.log(`   - Touch Interactions: ${testResults.touchInteractions.passed ? 'PASS' : 'FAIL'}`);
            console.log(`   - Mobile Performance: ${testResults.mobilePerformance.passed ? 'PASS' : 'FAIL'}`);
        } else {
            console.error('❌ Mobile optimization property tests failed');
            console.error('Test results:', JSON.stringify(testResults, null, 2));
        }
        
    } catch (error) {
        console.error('💥 Error running mobile optimization tests:', error);
        results.error = error.message;
        results.passed = false;
    } finally {
        if (browser) {
            await browser.close();
        }
        
        results.executionTime = Date.now() - startTime;
        console.log(`⏱️  Total execution time: ${results.executionTime}ms`);
    }
    
    return results;
}

// Run tests if this script is executed directly
if (require.main === module) {
    runMobileOptimizationTests()
        .then(results => {
            if (results.passed) {
                console.log('🎉 All mobile optimization tests completed successfully!');
                process.exit(0);
            } else {
                console.error('💔 Mobile optimization tests failed');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('🚨 Fatal error:', error);
            process.exit(1);
        });
}

module.exports = { runMobileOptimizationTests };