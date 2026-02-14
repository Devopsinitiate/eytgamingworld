/**
 * EYTGaming Video Player Management
 * Handles hero video loading, error handling, and performance optimization
 */

(function() {
  'use strict';

  // ============================================================================
  // Hero Video Management
  // ============================================================================
  
  /**
   * Initialize hero video with error handling and fallback
   */
  function initHeroVideo() {
    const heroVideo = document.getElementById('hero-video');
    const heroSection = document.querySelector('.hero-section');
    
    if (!heroVideo || !heroSection) return;

    // Video error handling with fallback to animated gradient
    heroVideo.addEventListener('error', function(e) {
      console.warn('Hero video failed to load, using fallback background');
      
      // Add fallback class to show animated gradient
      heroSection.classList.add('video-fallback');
      
      // Hide the video element
      heroVideo.style.display = 'none';
      
      // Log error details for monitoring
      if (e.target.error) {
        console.error('Video error code:', e.target.error.code);
        console.error('Video error message:', e.target.error.message);
      }
    });

    // Ensure video is muted for autoplay to work
    heroVideo.muted = true;
    
    // Ensure video loops
    heroVideo.loop = true;
    
    // Attempt to play the video
    const playPromise = heroVideo.play();
    
    if (playPromise !== undefined) {
      playPromise
        .then(function() {
          // Video started playing successfully
          console.log('Hero video playing successfully');
        })
        .catch(function(error) {
          // Autoplay was prevented
          console.warn('Video autoplay prevented:', error);
          
          // Use fallback background
          heroSection.classList.add('video-fallback');
          heroVideo.style.display = 'none';
        });
    }

    // Optimize video loading - pause when not visible
    if ('IntersectionObserver' in window) {
      const videoObserver = new IntersectionObserver(
        function(entries) {
          entries.forEach(function(entry) {
            if (entry.isIntersecting) {
              // Video is visible, ensure it's playing
              if (heroVideo.paused && !heroSection.classList.contains('video-fallback')) {
                heroVideo.play().catch(function(error) {
                  console.warn('Could not resume video:', error);
                });
              }
            } else {
              // Video is not visible, pause to save resources
              if (!heroVideo.paused) {
                heroVideo.pause();
              }
            }
          });
        },
        {
          threshold: 0.25 // Trigger when 25% of video is visible
        }
      );

      videoObserver.observe(heroSection);
    }

    // Handle video loaded event
    heroVideo.addEventListener('loadeddata', function() {
      console.log('Hero video loaded successfully');
      
      // Remove fallback class if it was added
      heroSection.classList.remove('video-fallback');
    });

    // Handle video stalled event
    heroVideo.addEventListener('stalled', function() {
      console.warn('Hero video loading stalled');
    });

    // Preload video metadata only (not the entire video)
    heroVideo.preload = 'metadata';
  }

  // ============================================================================
  // Video Modal Player (for highlights section)
  // ============================================================================
  
  /**
   * Initialize video modal for highlight videos
   */
  function initVideoModal() {
    const videoCards = document.querySelectorAll('[data-video-url]');
    
    if (videoCards.length === 0) return;

    videoCards.forEach(function(card) {
      card.addEventListener('click', function(e) {
        e.preventDefault();
        
        const videoUrl = this.getAttribute('data-video-url');
        const videoTitle = this.getAttribute('data-video-title') || 'Video';
        
        if (videoUrl) {
          openVideoModal(videoUrl, videoTitle);
        }
      });
    });
  }

  /**
   * Open video modal with embedded player
   * @param {string} url - Video URL (YouTube, Twitch, or direct video file)
   * @param {string} title - Video title
   */
  function openVideoModal(url, title) {
    // Create modal backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4 animate-fade-in';
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');
    backdrop.setAttribute('aria-label', title);
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'relative w-full max-w-5xl bg-gray-900 rounded-lg overflow-hidden shadow-2xl';
    
    // Create close button
    const closeButton = document.createElement('button');
    closeButton.className = 'absolute top-4 right-4 z-10 text-white hover:text-red-600 transition-colors';
    closeButton.innerHTML = '<span class="material-symbols-outlined text-4xl">close</span>';
    closeButton.setAttribute('aria-label', 'Close video');
    
    // Create video container
    const videoContainer = document.createElement('div');
    videoContainer.className = 'relative aspect-video bg-black';
    
    // Determine video type and create appropriate embed
    let videoEmbed;
    
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      // YouTube video
      const videoId = extractYouTubeId(url);
      videoEmbed = document.createElement('iframe');
      videoEmbed.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
      videoEmbed.className = 'w-full h-full';
      videoEmbed.setAttribute('frameborder', '0');
      videoEmbed.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
      videoEmbed.setAttribute('allowfullscreen', '');
    } else if (url.includes('twitch.tv')) {
      // Twitch video
      const videoId = extractTwitchId(url);
      videoEmbed = document.createElement('iframe');
      videoEmbed.src = `https://player.twitch.tv/?video=${videoId}&parent=${window.location.hostname}&autoplay=true`;
      videoEmbed.className = 'w-full h-full';
      videoEmbed.setAttribute('frameborder', '0');
      videoEmbed.setAttribute('allowfullscreen', '');
    } else {
      // Direct video file
      videoEmbed = document.createElement('video');
      videoEmbed.src = url;
      videoEmbed.className = 'w-full h-full';
      videoEmbed.setAttribute('controls', '');
      videoEmbed.setAttribute('autoplay', '');
    }
    
    // Assemble modal
    videoContainer.appendChild(videoEmbed);
    modalContent.appendChild(closeButton);
    modalContent.appendChild(videoContainer);
    backdrop.appendChild(modalContent);
    
    // Add to page
    document.body.appendChild(backdrop);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Close modal function
    function closeModal() {
      backdrop.classList.add('opacity-0');
      setTimeout(function() {
        document.body.removeChild(backdrop);
        document.body.style.overflow = '';
      }, 300);
    }
    
    // Close button click
    closeButton.addEventListener('click', closeModal);
    
    // Click outside to close
    backdrop.addEventListener('click', function(e) {
      if (e.target === backdrop) {
        closeModal();
      }
    });
    
    // Escape key to close
    function handleEscape(e) {
      if (e.key === 'Escape') {
        closeModal();
        document.removeEventListener('keydown', handleEscape);
      }
    }
    document.addEventListener('keydown', handleEscape);
  }

  /**
   * Extract YouTube video ID from URL
   * @param {string} url - YouTube URL
   * @returns {string} Video ID
   */
  function extractYouTubeId(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : '';
  }

  /**
   * Extract Twitch video ID from URL
   * @param {string} url - Twitch URL
   * @returns {string} Video ID
   */
  function extractTwitchId(url) {
    const regExp = /videos\/(\d+)/;
    const match = url.match(regExp);
    return match ? match[1] : '';
  }

  // ============================================================================
  // Lazy Loading for Video Thumbnails
  // ============================================================================
  
  /**
   * Initialize lazy loading for video thumbnails
   */
  function initLazyVideoThumbnails() {
    if (!('IntersectionObserver' in window)) {
      // Fallback: load all images immediately
      return;
    }

    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    
    const imageObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          const img = entry.target;
          
          // Image will load automatically due to loading="lazy" attribute
          // But we can add a loaded class for styling
          img.addEventListener('load', function() {
            img.classList.add('loaded');
          });
          
          imageObserver.unobserve(img);
        }
      });
    });

    lazyImages.forEach(function(img) {
      imageObserver.observe(img);
    });
  }

  // ============================================================================
  // Initialization
  // ============================================================================
  
  /**
   * Initialize all video player features
   */
  function init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        initHeroVideo();
        initVideoModal();
        initLazyVideoThumbnails();
      });
    } else {
      // DOM is already ready
      initHeroVideo();
      initVideoModal();
      initLazyVideoThumbnails();
    }
  }

  // Start initialization
  init();

})();
