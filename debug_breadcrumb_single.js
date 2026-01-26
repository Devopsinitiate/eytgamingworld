/**
 * Debug single breadcrumb test case
 */

const { JSDOM } = require('jsdom');

// Set up JSDOM environment
const dom = new JSDOM(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Breadcrumb Test</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
    </style>
</head>
<body>
    <div id="test-container"></div>
</body>
</html>
`, {
    url: 'http://localhost',
    pretendToBeVisual: true,
    resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Load the modules
require('./static/js/modules/layout-manager.js');
require('./static/js/test_breadcrumb_layout_properties.js');

async function debugSingleTest() {
    console.log('🔍 Debugging single breadcrumb test case...');
    
    // Create test instance
    const tester = new window.BreadcrumbPropertyTester({
        iterations: 1,
        debug: true
    });
    
    // Set up test environment
    tester.setup();
    
    try {
        // Test mobile-medium viewport with long breadcrumb
        const viewport = { width: 375, height: 667, name: 'mobile-medium' };
        const breadcrumbItems = [
            'Home',
            'User Profile', 
            'Settings',
            'Notifications',
            'Email Preferences',
            'Advanced Settings'
        ];
        
        console.log(`Testing: ${viewport.name} (${viewport.width}x${viewport.height})`);
        console.log(`Breadcrumb items: ${breadcrumbItems.length}`);
        
        // Set viewport
        await window.BreadcrumbTestUtils.setViewportSize(viewport.width, viewport.height);
        console.log(`Viewport set to: ${window.innerWidth}x${window.innerHeight}`);
        
        // Create breadcrumb
        const breadcrumb = window.BreadcrumbTestUtils.createTestBreadcrumb(breadcrumbItems);
        tester.testContainer.appendChild(breadcrumb);
        console.log('Breadcrumb created and added to DOM');
        
        // Apply layout manager
        const layoutManager = new window.LayoutManager({ debug: true });
        layoutManager.addComponent(breadcrumb, 'breadcrumb');
        console.log('Layout manager applied');
        
        // Wait for layout
        await new Promise(resolve => setTimeout(resolve, 200));
        breadcrumb.offsetHeight; // Force reflow
        
        // Get elements for testing
        const ol = breadcrumb.querySelector('ol');
        const listItems = Array.from(ol.querySelectorAll('li'));
        const links = Array.from(ol.querySelectorAll('a'));
        const separators = Array.from(ol.querySelectorAll('span'));
        
        console.log(`\nElements found:`);
        console.log(`- List items: ${listItems.length}`);
        console.log(`- Links: ${links.length}`);
        console.log(`- Separators: ${separators.length}`);
        
        // Test alignment
        console.log('\n🧪 Testing alignment...');
        const alignmentTest = window.BreadcrumbTestUtils.checkAlignment([...links, ...separators]);
        console.log(`Alignment test: ${alignmentTest ? '✅ PASS' : '❌ FAIL'}`);
        
        if (!alignmentTest) {
            console.log('Link positions:');
            links.forEach((link, i) => {
                const rect = link.getBoundingClientRect();
                console.log(`  Link ${i}: top=${rect.top}, height=${rect.height}`);
            });
            console.log('Separator positions:');
            separators.forEach((sep, i) => {
                const rect = sep.getBoundingClientRect();
                console.log(`  Separator ${i}: top=${rect.top}, height=${rect.height}`);
            });
        }
        
        // Test spacing
        console.log('\n🧪 Testing spacing...');
        const spacingTest = window.BreadcrumbTestUtils.checkSpacing(listItems, 8);
        console.log(`Spacing test: ${spacingTest ? '✅ PASS' : '❌ FAIL'}`);
        
        if (!spacingTest) {
            console.log('List item spacing:');
            listItems.forEach((li, i) => {
                const rect = li.getBoundingClientRect();
                const style = window.getComputedStyle(li);
                console.log(`  Item ${i}: left=${rect.left}, right=${rect.right}, marginRight=${style.marginRight}`);
            });
        }
        
        // Test responsive layout
        console.log('\n🧪 Testing responsive layout...');
        const measurements = window.BreadcrumbTestUtils.measureElement(breadcrumb);
        console.log(`Breadcrumb width: ${measurements.width}, viewport: ${viewport.width}`);
        const responsiveTest = measurements.width <= viewport.width;
        console.log(`Responsive test: ${responsiveTest ? '✅ PASS' : '❌ FAIL'}`);
        
        // Test wrapping
        console.log('\n🧪 Testing wrapping...');
        const wrappingTest = window.BreadcrumbTestUtils.checkWrapping(ol, listItems);
        console.log(`Wrapping test: ${wrappingTest ? '✅ PASS' : '❌ FAIL'}`);
        
        // Test separator alignment
        console.log('\n🧪 Testing separator alignment...');
        const separatorAlignmentTest = tester.testSeparatorAlignment(links, separators);
        console.log(`Separator alignment test: ${separatorAlignmentTest ? '✅ PASS' : '❌ FAIL'}`);
        
        if (!separatorAlignmentTest) {
            console.log('Link centers vs Separator centers:');
            for (let i = 0; i < Math.min(links.length, separators.length); i++) {
                const linkRect = links[i].getBoundingClientRect();
                const separatorRect = separators[i].getBoundingClientRect();
                const linkCenter = linkRect.top + linkRect.height / 2;
                const separatorCenter = separatorRect.top + separatorRect.height / 2;
                const diff = Math.abs(linkCenter - separatorCenter);
                console.log(`  Pair ${i}: link center=${linkCenter}, separator center=${separatorCenter}, diff=${diff}`);
            }
        }
        
        const overallResult = alignmentTest && spacingTest && responsiveTest && wrappingTest && separatorAlignmentTest;
        console.log(`\n🎯 Overall result: ${overallResult ? '✅ PASS' : '❌ FAIL'}`);
        
    } catch (error) {
        console.error('❌ Test failed with error:', error);
    } finally {
        tester.teardown();
    }
}

debugSingleTest().then(() => {
    console.log('\n✅ Debug test completed');
}).catch(error => {
    console.error('❌ Debug test failed:', error);
});