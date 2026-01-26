const fs = require('fs');
const { JSDOM } = require('jsdom');

// Set up DOM environment
const dom = new JSDOM('<!DOCTYPE html><html><head><style>body { margin: 0; padding: 0; }</style></head><body></body></html>', {
  url: 'http://localhost',
  pretendToBeVisual: true,
  resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Add matchMedia support for JSDOM with proper viewport simulation
global.window.matchMedia = global.window.matchMedia || function(media) {
    // Parse media query to determine if it matches current viewport
    const width = global.window.innerWidth || 1024;
    
    let matches = false;
    
    // Parse common media queries
    if (media.includes('max-width')) {
        const maxWidth = parseInt(media.match(/max-width:\s*(\d+)px/)?.[1] || '0');
        matches = width <= maxWidth;
    } else if (media.includes('min-width') && media.includes('max-width')) {
        const minWidth = parseInt(media.match(/min-width:\s*(\d+)px/)?.[1] || '0');
        const maxWidth = parseInt(media.match(/max-width:\s*(\d+)px/)?.[1] || '9999');
        matches = width >= minWidth && width <= maxWidth;
    } else if (media.includes('min-width')) {
        const minWidth = parseInt(media.match(/min-width:\s*(\d+)px/)?.[1] || '0');
        matches = width >= minWidth;
    }
    
    return {
        matches: matches,
        media: media,
        addListener: function(callback) {
            this.onchange = callback;
        },
        removeListener: function(callback) {
            this.onchange = null;
        },
        onchange: null
    };
};

// Add ResizeObserver mock
global.window.ResizeObserver = global.window.ResizeObserver || class ResizeObserver {
    constructor(callback) {
        this.callback = callback;
    }
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Load the layout manager
let layoutManagerCode = fs.readFileSync('static/js/modules/layout-manager.js', 'utf8');
// Remove ES6 export for Node.js compatibility
layoutManagerCode = layoutManagerCode.replace('export default LayoutManager;', '');

const layoutManagerWrapper = `
(function(window, document) {
${layoutManagerCode}
})
`;
eval(layoutManagerWrapper)(global.window, global.document);

// Load the test file
const testCode = fs.readFileSync('static/js/test_breadcrumb_layout_properties.js', 'utf8');

// Create a function wrapper to capture exports
const moduleExports = {};
const moduleWrapper = `
(function(module, exports, window, document) {
${testCode}
return { BreadcrumbPropertyTester, BreadcrumbTestUtils };
})
`;

// Execute the wrapped code
const testModule = eval(moduleWrapper)(moduleExports, moduleExports, global.window, global.document);

// Run the test
const tester = new testModule.BreadcrumbPropertyTester({ iterations: 100, debug: false });
tester.runProperty3Test().then(result => {
  console.log('\n' + '='.repeat(60));
  console.log('Test completed:', result ? '✅ PASSED' : '❌ FAILED');
  console.log('='.repeat(60));
  process.exit(result ? 0 : 1);
}).catch(error => {
  console.error('Test error:', error);
  process.exit(1);
});
