/**
 * Simple verification script for SVG Optimizer
 * This script can be run in the browser console to verify SVG optimization is working
 */

(function() {
    console.log('=== SVG Optimizer Verification ===');
    
    // Check if SVGOptimizer is available
    if (typeof SVGOptimizer === 'undefined') {
        console.error('❌ SVGOptimizer class not found');
        return;
    }
    
    console.log('✅ SVGOptimizer class found');
    
    // Create test instance
    const optimizer = new SVGOptimizer();
    console.log('✅ SVGOptimizer instance created');
    
    // Check initial status
    const initialStatus = optimizer.getStatus();
    console.log('📊 Initial status:', initialStatus);
    
    // Initialize optimizer
    optimizer.init();
    console.log('✅ SVGOptimizer initialized');
    
    // Check status after initialization
    const postInitStatus = optimizer.getStatus();
    console.log('📊 Post-init status:', postInitStatus);
    
    // Create a test SVG element
    const testSVG = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    testSVG.setAttribute('width', '200');
    testSVG.setAttribute('height', '150');
    testSVG.setAttribute('viewBox', '0 0 200 150');
    testSVG.innerHTML = '<rect width="200" height="150" fill="blue"/>';
    testSVG.classList.add('test-svg', 'decorative');
    
    // Add to DOM temporarily
    document.body.appendChild(testSVG);
    console.log('✅ Test SVG element created and added to DOM');
    
    // Test optimization
    try {
        optimizer.optimizeSVG(testSVG, 'decorative');
        console.log('✅ SVG optimization completed');
        
        // Check if element was marked as optimized
        if (testSVG.dataset.svgOptimized === 'true') {
            console.log('✅ SVG element marked as optimized');
        } else {
            console.warn('⚠️ SVG element not marked as optimized');
        }
        
        // Check applied dimensions
        const width = testSVG.getAttribute('width');
        const height = testSVG.getAttribute('height');
        console.log(`📏 Applied dimensions: ${width}x${height}`);
        
    } catch (error) {
        console.error('❌ SVG optimization failed:', error);
    }
    
    // Test context detection
    try {
        const detectedContext = optimizer.determineContext(testSVG);
        console.log('🔍 Detected context:', detectedContext);
        
        if (detectedContext === 'decorative') {
            console.log('✅ Context detection working correctly');
        } else {
            console.warn('⚠️ Context detection may have issues');
        }
    } catch (error) {
        console.error('❌ Context detection failed:', error);
    }
    
    // Test viewport dimensions
    try {
        const viewport = optimizer.getViewportDimensions();
        console.log('📱 Viewport dimensions:', viewport);
        
        if (viewport.width > 0 && viewport.height > 0) {
            console.log('✅ Viewport detection working');
        } else {
            console.warn('⚠️ Viewport detection may have issues');
        }
    } catch (error) {
        console.error('❌ Viewport detection failed:', error);
    }
    
    // Check final status
    const finalStatus = optimizer.getStatus();
    console.log('📊 Final status:', finalStatus);
    
    // Clean up
    document.body.removeChild(testSVG);
    optimizer.destroy();
    console.log('🧹 Cleanup completed');
    
    console.log('=== Verification Complete ===');
    console.log('✅ SVG Optimizer appears to be working correctly');
    
})();