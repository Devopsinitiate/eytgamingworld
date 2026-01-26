// Debug script to test console error handler loading
console.log('Starting debug...');

// Try to load the module
try {
    console.log('Loading module...');
    const moduleContent = require('./static/js/modules/console-error-handler.js');
    console.log('Module loaded, type:', typeof moduleContent);
    console.log('Module keys:', Object.keys(moduleContent));
    console.log('Module constructor:', moduleContent.constructor?.name);
    
    // Try to instantiate
    if (typeof moduleContent === 'function') {
        console.log('Trying to instantiate...');
        const instance = new moduleContent();
        console.log('Instance created:', typeof instance);
    } else {
        console.log('Module is not a function, cannot instantiate');
    }
} catch (error) {
    console.error('Error loading module:', error.message);
    console.error('Stack:', error.stack);
}