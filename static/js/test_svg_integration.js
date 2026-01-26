/**
 * Integration test for SVG Optimization System
 * Tests the integration of SVGOptimizer with the tournament detail page
 */

describe('SVG Optimization Integration', () => {
    let mockDocument, mockWindow, mockSVGOptimizer;
    
    beforeEach(() => {
        // Mock DOM
        mockDocument = {
            createElement: jest.fn(() => ({
                src: '',
                onload: null,
                onerror: null,
                setAttribute: jest.fn(),
                getAttribute: jest.fn()
            })),
            head: {
                appendChild: jest.fn()
            },
            querySelectorAll: jest.fn(() => []),
            addEventListener: jest.fn()
        };
        
        mockWindow = {
            SVGOptimizer: jest.fn().mockImplementation(() => ({
                init: jest.fn(),
                destroy: jest.fn(),
                optimizeSVG: jest.fn(),
                getStatus: jest.fn(() => ({
                    initialized: true,
                    optimizedCount: 0
                }))
            })),
            innerWidth: 1920,
            innerHeight: 1080,
            addEventListener: jest.fn(),
            location: {
                pathname: '/tournaments/test-tournament/',
                href: 'http://localhost/tournaments/test-tournament/'
            },
            matchMedia: jest.fn(() => ({ matches: false }))
        };
        
        global.document = mockDocument;
        global.window = mockWindow;
        global.console = {
            log: jest.fn(),
            warn: jest.fn(),
            error: jest.fn()
        };
    });
    
    test('should initialize SVG optimizer when SVGOptimizer is available', () => {
        // Mock TournamentDetailPage class
        class TournamentDetailPage {
            constructor() {
                this.initCoreFeatures();
            }
            
            initCoreFeatures() {
                this.initSVGOptimization();
            }
            
            initSVGOptimization() {
                if (window.SVGOptimizer) {
                    this.svgOptimizer = new window.SVGOptimizer();
                    this.svgOptimizer.init();
                    console.log('SVG optimization initialized');
                }
            }
        }
        
        const page = new TournamentDetailPage();
        
        expect(window.SVGOptimizer).toHaveBeenCalled();
        expect(page.svgOptimizer.init).toHaveBeenCalled();
        expect(console.log).toHaveBeenCalledWith('SVG optimization initialized');
    });
    
    test('should load SVG optimizer module when not available', () => {
        // Remove SVGOptimizer from window
        delete window.SVGOptimizer;
        
        class TournamentDetailPage {
            constructor() {
                this.initCoreFeatures();
            }
            
            initCoreFeatures() {
                this.initSVGOptimization();
            }
            
            initSVGOptimization() {
                if (window.SVGOptimizer) {
                    this.svgOptimizer = new window.SVGOptimizer();
                    this.svgOptimizer.init();
                    console.log('SVG optimization initialized');
                } else {
                    const script = document.createElement('script');
                    script.src = '/static/js/modules/svg-optimizer.js';
                    script.onload = () => {
                        if (window.SVGOptimizer) {
                            this.svgOptimizer = new window.SVGOptimizer();
                            this.svgOptimizer.init();
                            console.log('SVG optimization initialized after module load');
                        }
                    };
                    script.onerror = () => {
                        console.warn('Failed to load SVG optimizer module');
                    };
                    document.head.appendChild(script);
                }
            }
        }
        
        const page = new TournamentDetailPage();
        
        expect(document.createElement).toHaveBeenCalledWith('script');
        expect(document.head.appendChild).toHaveBeenCalled();
        
        const scriptElement = document.createElement.mock.results[0].value;
        expect(scriptElement.src).toBe('/static/js/modules/svg-optimizer.js');
    });
    
    test('should handle SVG optimizer module load success', () => {
        delete window.SVGOptimizer;
        
        class TournamentDetailPage {
            constructor() {
                this.initSVGOptimization();
            }
            
            initSVGOptimization() {
                if (window.SVGOptimizer) {
                    this.svgOptimizer = new window.SVGOptimizer();
                    this.svgOptimizer.init();
                } else {
                    const script = document.createElement('script');
                    script.src = '/static/js/modules/svg-optimizer.js';
                    script.onload = () => {
                        if (window.SVGOptimizer) {
                            this.svgOptimizer = new window.SVGOptimizer();
                            this.svgOptimizer.init();
                            console.log('SVG optimization initialized after module load');
                        }
                    };
                    document.head.appendChild(script);
                }
            }
        }
        
        const page = new TournamentDetailPage();
        const scriptElement = document.createElement.mock.results[0].value;
        
        // Simulate successful module load
        window.SVGOptimizer = jest.fn().mockImplementation(() => ({
            init: jest.fn(),
            destroy: jest.fn()
        }));
        
        scriptElement.onload();
        
        expect(window.SVGOptimizer).toHaveBeenCalled();
        expect(console.log).toHaveBeenCalledWith('SVG optimization initialized after module load');
    });
    
    test('should handle SVG optimizer module load failure', () => {
        delete window.SVGOptimizer;
        
        class TournamentDetailPage {
            constructor() {
                this.initSVGOptimization();
            }
            
            initSVGOptimization() {
                if (window.SVGOptimizer) {
                    this.svgOptimizer = new window.SVGOptimizer();
                    this.svgOptimizer.init();
                } else {
                    const script = document.createElement('script');
                    script.src = '/static/js/modules/svg-optimizer.js';
                    script.onload = () => {
                        if (window.SVGOptimizer) {
                            this.svgOptimizer = new window.SVGOptimizer();
                            this.svgOptimizer.init();
                        }
                    };
                    script.onerror = () => {
                        console.warn('Failed to load SVG optimizer module');
                    };
                    document.head.appendChild(script);
                }
            }
        }
        
        const page = new TournamentDetailPage();
        const scriptElement = document.createElement.mock.results[0].value;
        
        // Simulate module load failure
        scriptElement.onerror();
        
        expect(console.warn).toHaveBeenCalledWith('Failed to load SVG optimizer module');
    });
    
    test('should clean up SVG optimizer on destroy', () => {
        class TournamentDetailPage {
            constructor() {
                this.svgOptimizer = new window.SVGOptimizer();
                this.modules = new Map();
            }
            
            destroy() {
                if (this.svgOptimizer) {
                    this.svgOptimizer.destroy();
                }
                
                this.modules.forEach(module => {
                    if (module.destroy && typeof module.destroy === 'function') {
                        module.destroy();
                    }
                });
            }
        }
        
        const page = new TournamentDetailPage();
        page.destroy();
        
        expect(page.svgOptimizer.destroy).toHaveBeenCalled();
    });
    
    test('should handle missing SVG optimizer gracefully on destroy', () => {
        class TournamentDetailPage {
            constructor() {
                this.svgOptimizer = null;
                this.modules = new Map();
            }
            
            destroy() {
                if (this.svgOptimizer) {
                    this.svgOptimizer.destroy();
                }
                
                this.modules.forEach(module => {
                    if (module.destroy && typeof module.destroy === 'function') {
                        module.destroy();
                    }
                });
            }
        }
        
        const page = new TournamentDetailPage();
        
        // Should not throw error
        expect(() => {
            page.destroy();
        }).not.toThrow();
    });
});