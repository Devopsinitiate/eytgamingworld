/**
 * Jest test setup file for tournament detail components
 * Sets up global mocks and utilities for testing
 */

// Mock gtag for analytics tracking
global.gtag = jest.fn();

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((callback) => {
    return setTimeout(callback, 16);
});

global.cancelAnimationFrame = jest.fn((id) => {
    clearTimeout(id);
});

// Mock performance API
global.performance = {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn()
};

// Mock CSS custom properties support
Object.defineProperty(document.documentElement.style, 'setProperty', {
    value: jest.fn(),
    writable: true
});

// Mock DOM methods properly for Jest
document.querySelector = jest.fn();
document.querySelectorAll = jest.fn();
document.getElementById = jest.fn();
document.createElement = jest.fn(() => ({
    className: '',
    innerHTML: '',
    textContent: '',
    style: {},
    dataset: {},
    setAttribute: jest.fn(),
    getAttribute: jest.fn(),
    appendChild: jest.fn(),
    remove: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    querySelector: jest.fn(),
    querySelectorAll: jest.fn()
}));
document.addEventListener = jest.fn();
document.removeEventListener = jest.fn();

// Mock document.body methods
document.body.appendChild = jest.fn();
document.body.removeChild = jest.fn();

// Mock window methods
window.addEventListener = jest.fn();
window.removeEventListener = jest.fn();
window.matchMedia = jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
}));

// Mock timer functions properly
global.setInterval = jest.fn();
global.clearInterval = jest.fn();
global.setTimeout = jest.fn();
global.clearTimeout = jest.fn();

// Mock fetch API
global.fetch = jest.fn();

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

// Mock focus method
Element.prototype.focus = jest.fn();

// Mock click method
Element.prototype.click = jest.fn();

// Mock remove method
Element.prototype.remove = jest.fn();

// Mock insertAdjacentHTML
Element.prototype.insertAdjacentHTML = jest.fn();

// Mock getBoundingClientRect
Element.prototype.getBoundingClientRect = jest.fn(() => ({
    top: 0,
    left: 0,
    bottom: 100,
    right: 100,
    width: 100,
    height: 100,
    x: 0,
    y: 0
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn()
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn()
}));

// Mock MutationObserver
global.MutationObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    disconnect: jest.fn()
}));

// Mock URL constructor
global.URL = jest.fn().mockImplementation((url) => ({
    href: url,
    pathname: url.split('?')[0],
    search: url.includes('?') ? '?' + url.split('?')[1] : '',
    hash: url.includes('#') ? '#' + url.split('#')[1] : ''
}));

// Suppress console.log in tests unless explicitly needed
global.console.log = jest.fn();

// Add custom matchers if needed
expect.extend({
    toBeVisible(received) {
        const pass = received.style.display !== 'none' && received.style.visibility !== 'hidden';
        return {
            message: () => `expected element to ${pass ? 'not ' : ''}be visible`,
            pass
        };
    }
});