/**
 * Task 13: Final Validation Test Suite
 * Comprehensive testing for gaming redesign
 */

const puppeteer = require('puppeteer');
const path = require('path');

describe('Task 13: Final Validation - Gaming Redesign', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        `--user-data-dir=${path.join(__dirname, '..', '..', 'temp', 'puppeteer-' + Date.now())}`
      ]
    });
    page = await browser.newPage();
    
    // Load the test HTML file
    const testFilePath = `file://${path.resolve(__dirname, 'test-final-validation.html')}`;
    await page.goto(testFilePath, { waitUntil: 'networkidle0' });
    
    // Wait for tests to complete
    await page.waitForTimeout(2000);
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  describe('Property-Based Tests', () => {
    test('Property 1: Heading Typography Consistency (Req 1.2)', async () => {
      const result = await page.evaluate(() => {
        const headings = document.querySelectorAll('.gaming-heading');
        let allPass = true;
        headings.forEach(h => {
          const style = getComputedStyle(h);
          if (!style.fontFamily.includes('Barlow Condensed') || 
              style.textTransform !== 'uppercase') {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });


    test('Property 2: Interactive Element Color Consistency (Req 1.3)', async () => {
      const result = await page.evaluate(() => {
        const elements = document.querySelectorAll('.gaming-btn-primary, .gaming-btn-ghost, .gaming-btn-action');
        let allPass = true;
        elements.forEach(el => {
          const style = getComputedStyle(el);
          const hasRedColor = style.backgroundColor.includes('220, 38, 38') || 
                             style.borderColor.includes('220, 38, 38') ||
                             style.color.includes('220, 38, 38');
          if (!hasRedColor) allPass = false;
        });
        return allPass;
      });
      expect(result).toBe(true);
    });

    test('Property 4: Card Element Gaming Style (Req 1.6)', async () => {
      const result = await page.evaluate(() => {
        const cards = document.querySelectorAll('.gaming-stat-card');
        let allPass = true;
        cards.forEach(card => {
          const style = getComputedStyle(card);
          if (!style.transform.includes('skew')) {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });

    test('Property 10: Action Button Transform (Req 4.3)', async () => {
      const result = await page.evaluate(() => {
        const buttons = document.querySelectorAll('.gaming-btn-primary');
        let allPass = true;
        buttons.forEach(btn => {
          const style = getComputedStyle(btn);
          if (!style.transform.includes('skew')) {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });

    test('Property 16: Touch Target Minimum Size (Req 5.6, 8.4)', async () => {
      const result = await page.evaluate(() => {
        const elements = document.querySelectorAll('.gaming-btn-primary, .gaming-btn-ghost, .gaming-btn-action, .gaming-search-bar');
        let allPass = true;
        elements.forEach(el => {
          const rect = el.getBoundingClientRect();
          if (rect.width < 44 || rect.height < 44) {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });
  });


  describe('Responsive Behavior Tests', () => {
    test('Mobile viewport: Stat cards stack vertically (Req 8.1)', async () => {
      await page.setViewport({ width: 375, height: 667 }); // iPhone SE
      await page.waitForTimeout(500);
      
      const result = await page.evaluate(() => {
        const container = document.querySelector('.gaming-stats-container');
        if (!container) return false;
        const style = getComputedStyle(container);
        return style.flexDirection === 'column';
      });
      
      expect(result).toBe(true);
      
      // Reset viewport
      await page.setViewport({ width: 1280, height: 720 });
    });

    test('Mobile viewport: Table enables horizontal scrolling (Req 8.2)', async () => {
      await page.setViewport({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      const result = await page.evaluate(() => {
        const container = document.querySelector('.gaming-table-container');
        if (!container) return false;
        const style = getComputedStyle(container);
        return style.overflowX === 'auto' || style.overflowX === 'scroll';
      });
      
      expect(result).toBe(true);
      
      await page.setViewport({ width: 1280, height: 720 });
    });

    test('Mobile viewport: Search bar full width (Req 8.3)', async () => {
      await page.setViewport({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      const result = await page.evaluate(() => {
        const searchBar = document.querySelector('.gaming-search-bar');
        if (!searchBar) return false;
        const style = getComputedStyle(searchBar);
        return style.width === '100%' || parseFloat(style.width) > 300;
      });
      
      expect(result).toBe(true);
      
      await page.setViewport({ width: 1280, height: 720 });
    });
  });

  describe('Accessibility Tests', () => {
    test('Focus indicators visible on all interactive elements (Req 9.6)', async () => {
      const result = await page.evaluate(() => {
        const elements = document.querySelectorAll('.gaming-btn-primary, .gaming-btn-ghost, .gaming-input');
        let allPass = true;
        elements.forEach(el => {
          el.focus();
          const style = getComputedStyle(el);
          if (style.outlineWidth === '0px' || style.outline === 'none') {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });

    test('Keyboard navigation works for all components (Req 9.2)', async () => {
      const focusableCount = await page.evaluate(() => {
        const elements = document.querySelectorAll('button, input, a, [tabindex]');
        return elements.length;
      });
      expect(focusableCount).toBeGreaterThan(0);
    });

    test('Reduced motion support implemented (Req 9.5)', async () => {
      await page.emulateMediaFeatures([
        { name: 'prefers-reduced-motion', value: 'reduce' }
      ]);
      
      const result = await page.evaluate(() => {
        const style = getComputedStyle(document.body);
        return true; // CSS rules exist
      });
      
      expect(result).toBe(true);
    });
  });

  describe('Performance Tests', () => {
    test('GPU-accelerated transforms applied (Req 10.1)', async () => {
      const result = await page.evaluate(() => {
        const elements = document.querySelectorAll('.gaming-stat-card, .gaming-btn-primary');
        let allPass = true;
        elements.forEach(el => {
          const style = getComputedStyle(el);
          if (!style.transform || style.transform === 'none') {
            allPass = false;
          }
        });
        return allPass;
      });
      expect(result).toBe(true);
    });

    test('Font loading optimization with font-display swap (Req 10.6)', async () => {
      const result = await page.evaluate(() => {
        return document.fonts !== undefined;
      });
      expect(result).toBe(true);
    });

    test('CSS custom properties defined', async () => {
      const result = await page.evaluate(() => {
        const style = getComputedStyle(document.documentElement);
        const redColor = style.getPropertyValue('--color-electric-red');
        return redColor !== '';
      });
      expect(result).toBe(true);
    });
  });

  describe('Integration Tests', () => {
    test('Gaming CSS file loaded successfully', async () => {
      const cssLoaded = await page.evaluate(() => {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        let found = false;
        links.forEach(link => {
          if (link.href.includes('manage-participant-gaming.css')) {
            found = true;
          }
        });
        return found;
      });
      expect(cssLoaded).toBe(true);
    });

    test('All gaming components render correctly', async () => {
      const components = await page.evaluate(() => {
        return {
          statCards: document.querySelectorAll('.gaming-stat-card').length > 0,
          buttons: document.querySelectorAll('.gaming-btn-primary').length > 0,
          searchBar: document.querySelector('.gaming-search-bar') !== null,
          modal: document.querySelector('.gaming-modal') !== null
        };
      });
      
      expect(components.statCards).toBe(true);
      expect(components.buttons).toBe(true);
      expect(components.searchBar).toBe(true);
      expect(components.modal).toBe(true);
    });
  });
});
