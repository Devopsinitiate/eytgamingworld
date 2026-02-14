/**
 * EYTGaming Landing Page Animations
 * Handles navigation behavior, scroll effects, and interactive animations
 */

(function() {
  'use strict';

  // ============================================================================
  // Navigation Sticky Behavior
  // ============================================================================
  
  /**
   * Initialize sticky navigation with scroll detection
   */
  function initStickyNavigation() {
    const nav = document.getElementById('main-navigation');
    if (!nav) return;

    let lastScroll = 0;
    const scrollThreshold = 100;

    function handleScroll() {
      const currentScroll = window.pageYOffset;

      // Add scrolled class when past threshold
      if (currentScroll > scrollThreshold) {
        nav.classList.add('scrolled');
        nav.classList.remove('bg-black/40');
        nav.classList.add('bg-black/90');
      } else {
        nav.classList.remove('scrolled');
        nav.classList.remove('bg-black/90');
        nav.classList.add('bg-black/40');
      }

      lastScroll = currentScroll;
    }

    // Throttle scroll events for performance
    let ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    });

    // Initial check
    handleScroll();
  }

  // ============================================================================
  // Mobile Menu Toggle
  // ============================================================================
  
  /**
   * Initialize mobile menu toggle functionality
   */
  function initMobileMenu() {
    const toggleButton = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (!toggleButton || !mobileMenu) return;

    toggleButton.addEventListener('click', function() {
      const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';
      
      // Toggle menu visibility
      if (isExpanded) {
        mobileMenu.classList.add('hidden');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.querySelector('.material-symbols-outlined').textContent = 'menu';
      } else {
        mobileMenu.classList.remove('hidden');
        toggleButton.setAttribute('aria-expanded', 'true');
        toggleButton.querySelector('.material-symbols-outlined').textContent = 'close';
      }
    });

    // Close mobile menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
      link.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.querySelector('.material-symbols-outlined').textContent = 'menu';
      });
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
      const isClickInsideMenu = mobileMenu.contains(event.target);
      const isClickOnToggle = toggleButton.contains(event.target);
      const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';

      if (!isClickInsideMenu && !isClickOnToggle && isExpanded) {
        mobileMenu.classList.add('hidden');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.querySelector('.material-symbols-outlined').textContent = 'menu';
      }
    });
  }

  // ============================================================================
  // Smooth Scrolling
  // ============================================================================
  
  /**
   * Initialize smooth scrolling for anchor links
   */
  function initSmoothScrolling() {
    // Select all links with hashes
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
      link.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        
        // Skip if it's just "#"
        if (href === '#') return;
        
        const target = document.querySelector(href);
        
        if (target) {
          e.preventDefault();
          
          // Calculate offset for fixed navigation
          const nav = document.getElementById('main-navigation');
          const navHeight = nav ? nav.offsetHeight : 0;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
          
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // ============================================================================
  // Navigation Link Active State
  // ============================================================================
  
  /**
   * Update active navigation link based on scroll position
   */
  function initActiveNavLinks() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    if (sections.length === 0 || navLinks.length === 0) return;

    function updateActiveLink() {
      let current = '';
      const scrollPosition = window.pageYOffset;

      sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        
        if (scrollPosition >= sectionTop - 200) {
          current = section.getAttribute('id');
        }
      });

      navLinks.forEach(link => {
        link.classList.remove('text-red-600');
        const href = link.getAttribute('href');
        
        if (href && href.includes('#' + current)) {
          link.classList.add('text-red-600');
        }
      });
    }

    // Throttle scroll events
    let ticking = false;
    window.addEventListener('scroll', function() {
      if (!ticking) {
        window.requestAnimationFrame(function() {
          updateActiveLink();
          ticking = false;
        });
        ticking = true;
      }
    });

    // Initial check
    updateActiveLink();
  }

  // ============================================================================
  // Initialization
  // ============================================================================
  
  /**
   * Initialize all navigation and animation features
   */
  function init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        initStickyNavigation();
        initMobileMenu();
        initSmoothScrolling();
        initActiveNavLinks();
      });
    } else {
      // DOM is already ready
      initStickyNavigation();
      initMobileMenu();
      initSmoothScrolling();
      initActiveNavLinks();
    }
  }

  // Start initialization
  init();

})();
