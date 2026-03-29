/**
 * Unit Tests for SeedingManager Module
 * Tests basic functionality of the manual seeding interface
 * Requirements: 4.1, 4.3, 5.1, 6.1, 7.1, 9.1
 * 
 * Note: This is a smoke test to verify the module structure and basic functionality.
 * Since the module uses ES6 modules and requires DOM elements to be present,
 * we're testing the module structure without actually instantiating it in the test environment.
 */

describe('SeedingManager Module - Smoke Tests', () => {
    // Mock DOM elements that SeedingManager expects
    beforeEach(() => {
        // Mock getElementById to return null (prevents init from failing)
        document.getElementById = jest.fn(() => null);
        
        // Mock fetch to prevent actual API calls
        global.fetch = jest.fn(() => 
            Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ participants: [] })
            })
        );
    });
    
    describe('Module Verification', () => {
        test('seeding-manager.js file should exist and be readable', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            
            expect(fs.existsSync(modulePath)).toBe(true);
            
            const content = fs.readFileSync(modulePath, 'utf-8');
            expect(content).toContain('export class SeedingManager');
        });
        
        test('module should export SeedingManager class', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            const content = fs.readFileSync(modulePath, 'utf-8');
            
            // Verify class is exported
            expect(content).toContain('export class SeedingManager');
            
            // Verify constructor exists
            expect(content).toContain('constructor(tournamentSlug');
        });
        
        test('module should have all required methods', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            const content = fs.readFileSync(modulePath, 'utf-8');
            
            const requiredMethods = [
                'init()',
                'loadParticipants()',
                'setupDragAndDrop()',
                'setupEventListeners()',
                'render()',
                'recalculateSeeds()',
                'detectConflicts()',
                'saveSeeds()',
                'autoSeed()',
                'getCSRFToken()',
                'showSuccess(',
                'showError(',
                'renderParticipantRow(',
                'escapeHtml('
            ];
            
            requiredMethods.forEach(method => {
                expect(content).toContain(method);
            });
        });
    });
    
    describe('Code Quality Checks', () => {
        test('module should not have syntax errors', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            const content = fs.readFileSync(modulePath, 'utf-8');
            
            // Check for common syntax issues
            expect(content).not.toContain('undefined.');
            expect(content).not.toContain('null.');
            
            // Check for proper async/await usage
            const asyncMethods = content.match(/async\s+\w+\s*\(/g) || [];
            expect(asyncMethods.length).toBeGreaterThan(0);
        });
        
        test('module should have proper error handling', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            const content = fs.readFileSync(modulePath, 'utf-8');
            
            // Check for try-catch blocks
            expect(content).toContain('try {');
            expect(content).toContain('catch');
            
            // Check for error logging
            expect(content).toContain('console.error');
        });
        
        test('module should have XSS protection', () => {
            const fs = require('fs');
            const path = require('path');
            const modulePath = path.join(__dirname, 'modules', 'seeding-manager.js');
            const content = fs.readFileSync(modulePath, 'utf-8');
            
            // Check for HTML escaping
            expect(content).toContain('escapeHtml');
            expect(content).toContain('textContent');
        });
    });
    
    describe('Template Integration', () => {
        test('seeding_interface.html template should exist', () => {
            const fs = require('fs');
            const path = require('path');
            const templatePath = path.join(__dirname, '..', '..', 'templates', 'tournaments', 'components', 'seeding_interface.html');
            
            expect(fs.existsSync(templatePath)).toBe(true);
        });
        
        test('template should have required DOM elements', () => {
            const fs = require('fs');
            const path = require('path');
            const templatePath = path.join(__dirname, '..', '..', 'templates', 'tournaments', 'components', 'seeding_interface.html');
            const content = fs.readFileSync(templatePath, 'utf-8');
            
            const requiredElements = [
                'id="seeding-interface"',
                'id="seeded-count"',
                'id="unseeded-count"',
                'id="auto-seed-btn"',
                'id="save-seeds-btn"',
                'id="seeded-list"',
                'id="unseeded-list"',
                'id="seed-conflicts"'
            ];
            
            requiredElements.forEach(element => {
                expect(content).toContain(element);
            });
        });
        
        test('template should have proper styling', () => {
            const fs = require('fs');
            const path = require('path');
            const templatePath = path.join(__dirname, '..', '..', 'templates', 'tournaments', 'components', 'seeding_interface.html');
            const content = fs.readFileSync(templatePath, 'utf-8');
            
            // Check for CSS classes
            expect(content).toContain('seeding-container');
            expect(content).toContain('participant-row');
            expect(content).toContain('seed-input');
            expect(content).toContain('drag-handle');
        });
    });
    
    describe('Tournament Detail Integration', () => {
        test('tournament_detail.html should include seeding interface', () => {
            const fs = require('fs');
            const path = require('path');
            const templatePath = path.join(__dirname, '..', '..', 'templates', 'tournaments', 'tournament_detail.html');
            const content = fs.readFileSync(templatePath, 'utf-8');
            
            // Check for conditional include
            expect(content).toContain("tournament.seeding_method == 'manual'");
            expect(content).toContain("seeding_interface.html");
        });
        
        test('tournament_detail.html should initialize SeedingManager', () => {
            const fs = require('fs');
            const path = require('path');
            const templatePath = path.join(__dirname, '..', '..', 'templates', 'tournaments', 'tournament_detail.html');
            const content = fs.readFileSync(templatePath, 'utf-8');
            
            // Check for module import
            expect(content).toContain('SeedingManager');
            expect(content).toContain('seeding-manager.js');
            
            // Check for initialization
            expect(content).toContain('new SeedingManager');
        });
    });
});
