# Design Document: EYTGaming Landing Page Redesign

## Overview

This design document outlines the technical architecture and implementation approach for redesigning the EYTGaming landing page. The redesign transforms the current basic landing page (templates/home.html) into a premium, immersive esports experience that rivals AAA gaming organizations.

The design leverages the existing Django + Tailwind CSS stack while introducing advanced visual effects, animations, and interactive elements inspired by the Red template aesthetic. The implementation prioritizes performance, accessibility, and responsive design while delivering a dark, aggressive esports aesthetic with electric red accents and futuristic elements.

### Key Design Principles

1. **Performance First**: All animations and effects must maintain 60fps on modern devices
2. **Progressive Enhancement**: Core content accessible without JavaScript, enhanced with animations
3. **Mobile-First Responsive**: Design scales from mobile to desktop seamlessly
4. **Accessibility Compliance**: WCAG 2.1 AA standards throughout
5. **Component Modularity**: Reusable Django template partials for maintainability
6. **Brand Consistency**: Electric red (#DC2626), deep black (#0A0A0A), gunmetal gray (#1F2937), neon cyan (#06B6D4)

## Architecture

### High-Level Structure

```
templates/
├── home.html (main landing page)
├── base.html (extends from this)
└── partials/
    ├── hero_section.html
    ├── navigation.html
    ├── player_showcase.html
    ├── games_section.html
    ├── media_highlights.html
    ├── news_section.html
    ├── merch_teaser.html
    ├── community_cta.html
    └── footer.html

static/
├── css/
│   ├── landing-page.css (custom animations & effects)
│   └── tailwind.css (utility classes)
├── js/
│   ├── landing-animations.js (scroll effects, parallax)
│   ├── video-player.js (hero video management)
│   └── lazy-loading.js (performance optimization)
├── videos/
│   └── hero-background.mp4 (cinematic loop)
└── images/
    ├── players/ (player card images)
    ├── games/ (game key art)
    └── effects/ (particle overlays, glitch textures)
```

### Technology Stack

- **Backend**: Django 4.x with template system
- **Styling**: Tailwind CSS 3.x with custom configuration
- **Icons**: Material Symbols (already integrated)
- **Animations**: CSS animations + Intersection Observer API
- **Video**: HTML5 video with fallback to animated background
- **Fonts**: Google Fonts (Barlow Condensed, Inter)

### Django Integration

The landing page extends the existing base.html template and integrates with:
- User authentication system (personalized content for logged-in users)
- Django static files system
- Django template tags for dynamic content
- Existing URL routing structure

## Components and Interfaces

### 1. Hero Section Component

**Purpose**: Full-screen immersive entry point with brand messaging and primary CTAs

**Template**: `partials/hero_section.html`

**Structure**:
```html
<section class="hero-section relative h-screen overflow-hidden">
  <!-- Video Background -->
  <video autoplay muted loop playsinline class="hero-video">
    <source src="{% static 'videos/hero-background.mp4' %}" type="video/mp4">
  </video>
  
  <!-- Animated Overlay Effects -->
  <div class="hero-overlay">
    <div class="particle-embers"></div>
    <div class="glitch-lines"></div>
    <div class="light-flares"></div>
  </div>
  
  <!-- Content -->
  <div class="hero-content z-10 relative">
    <img src="{% static 'images/logo.svg' %}" alt="EYTGaming" class="hero-logo">
    <h1 class="hero-headline">GEAR UP. DOMINATE. EVOLVE.</h1>
    <p class="hero-subtext">Elite Competition. United Community. Future Esports.</p>
    <div class="hero-ctas">
      <a href="{% url 'register' %}" class="cta-primary">Join the Army</a>
      <a href="#highlights" class="cta-secondary">Watch Highlights</a>
    </div>
  </div>
</section>
```

**Styling Approach**:
- Full viewport height with `h-screen`
- Absolute positioned video background with dark overlay (opacity 0.6)
- CSS Grid for centered content alignment
- Gradient text effect on headline using `bg-clip-text`
- Animated particle system using CSS keyframes
- Glitch effect using pseudo-elements with transform skew

**Animations**:
- Fade-in on page load (0.8s ease-out)
- Particle embers floating upward (infinite loop, 4s duration)
- Glitch lines horizontal sweep (random intervals)
- Light flares pulsing (2s ease-in-out)
- CTA buttons glow on hover (0.3s transition)

**Responsive Behavior**:
- Mobile: Stack CTAs vertically, reduce headline size
- Tablet: Side-by-side CTAs, medium headline
- Desktop: Full effects, large headline with letter-spacing

### 2. Navigation Component

**Purpose**: Sticky navigation bar with smooth transitions and brand consistency

**Template**: `partials/navigation.html`

**Structure**:
```html
<nav class="navigation sticky top-0 z-50 transition-all duration-300">
  <div class="nav-container max-w-7xl mx-auto px-4">
    <div class="nav-content flex justify-between items-center h-16">
      <!-- Logo -->
      <a href="{% url 'home' %}" class="nav-logo">
        <img src="{% static 'images/logo-small.svg' %}" alt="EYT">
      </a>
      
      <!-- Menu Items -->
      <ul class="nav-menu hidden md:flex space-x-8">
        <li><a href="{% url 'home' %}" class="nav-link">Home</a></li>
        <li><a href="{% url 'teams' %}" class="nav-link">Teams</a></li>
        <li><a href="{% url 'games' %}" class="nav-link">Games</a></li>
        <li><a href="{% url 'tournaments' %}" class="nav-link">Tournaments</a></li>
        <li><a href="{% url 'store' %}" class="nav-link">Store</a></li>
        <li><a href="{% url 'community' %}" class="nav-link">Community</a></li>
      </ul>
      
      <!-- CTA Button -->
      <a href="{% url 'register' %}" class="nav-cta">Join EYTGaming</a>
      
      <!-- Mobile Menu Toggle -->
      <button class="mobile-menu-toggle md:hidden">
        <span class="material-symbols-outlined">menu</span>
      </button>
    </div>
  </div>
</nav>
```

**Styling Approach**:
- Initial state: Semi-transparent background (bg-black/40)
- Scrolled state: Solid background (bg-black) with backdrop blur
- Smooth transition between states (300ms)
- Nav links with neon glow on hover (red accent)
- CTA button with electric red background and glow effect

**JavaScript Behavior**:
```javascript
// Sticky navigation with scroll detection
const nav = document.querySelector('.navigation');
let lastScroll = 0;

window.addEventListener('scroll', () => {
  const currentScroll = window.pageYOffset;
  
  if (currentScroll > 100) {
    nav.classList.add('scrolled');
  } else {
    nav.classList.remove('scrolled');
  }
  
  lastScroll = currentScroll;
});
```

### 3. Player Showcase Component

**Purpose**: Display elite players with interactive cards and stat overlays

**Template**: `partials/player_showcase.html`

**Structure**:
```html
<section class="player-showcase py-20 bg-gradient-to-b from-black to-gray-900">
  <div class="container mx-auto px-4">
    <h2 class="section-title">ELITE ROSTER</h2>
    
    <div class="player-grid grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {% for player in players %}
      <div class="player-card group relative overflow-hidden">
        <!-- Player Image -->
        <img src="{{ player.image.url }}" alt="{{ player.gamer_tag }}" 
             class="player-image" loading="lazy">
        
        <!-- Card Content -->
        <div class="player-info">
          <h3 class="player-tag">{{ player.gamer_tag }}</h3>
          <p class="player-role">{{ player.role }} • {{ player.game }}</p>
          <span class="player-flag">{{ player.country_flag }}</span>
        </div>
        
        <!-- Hover Overlay with Stats -->
        <div class="player-stats-overlay">
          <div class="stat">
            <span class="stat-label">K/D</span>
            <span class="stat-value">{{ player.kd_ratio }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Rank</span>
            <span class="stat-value">{{ player.rank }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Wins</span>
            <span class="stat-value">{{ player.wins }}</span>
          </div>
        </div>
        
        <!-- Neon Border Effect -->
        <div class="neon-border"></div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

**Styling Approach**:
- Dark card background with metallic border
- Grayscale image by default, full color on hover
- Neon red glow border on hover (box-shadow with red)
- Scale transform on hover (scale: 1.05)
- Stats overlay slides up from bottom on hover
- Smooth transitions (0.3s ease-out)

**CSS Implementation**:
```css
.player-card {
  @apply relative rounded-lg overflow-hidden bg-gray-900 border border-gray-800;
  transition: transform 0.3s ease-out, box-shadow 0.3s ease-out;
}

.player-card:hover {
  transform: scale(1.05);
  box-shadow: 0 0 30px rgba(220, 38, 38, 0.6);
}

.player-image {
  @apply w-full h-64 object-cover;
  filter: grayscale(100%);
  transition: filter 0.3s ease-out;
}

.player-card:hover .player-image {
  filter: grayscale(0%);
}

.player-stats-overlay {
  @apply absolute inset-0 bg-black/90 flex flex-col justify-center items-center;
  @apply opacity-0 translate-y-full;
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}

.player-card:hover .player-stats-overlay {
  @apply opacity-100 translate-y-0;
}
```

### 4. Games Section Component

**Purpose**: Showcase supported games with animated cards and descriptions

**Template**: `partials/games_section.html`

**Structure**:
```html
<section class="games-section py-20 bg-black relative">
  <!-- Animated Grid Background -->
  <div class="grid-background"></div>
  
  <div class="container mx-auto px-4 relative z-10">
    <h2 class="section-title">BATTLEGROUNDS</h2>
    
    <div class="games-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {% for game in games %}
      <div class="game-card group">
        <!-- Game Icon/Art -->
        <div class="game-icon-wrapper">
          <img src="{{ game.key_art.url }}" alt="{{ game.name }}" 
               class="game-icon" loading="lazy">
        </div>
        
        <!-- Game Info -->
        <h3 class="game-title">{{ game.name }}</h3>
        <p class="game-category">{{ game.category }}</p>
        
        <!-- Hover Description -->
        <div class="game-description">
          <p>{{ game.description }}</p>
        </div>
        
        <!-- Animated Border -->
        <div class="animated-border"></div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

**Styling Approach**:
- Dark cards with animated neon borders
- Pulse animation on hover (scale + glow)
- Description fades in from bottom on hover
- Animated grid pattern in background (CSS gradient animation)
- Skewed border elements for aggressive look

**Animation Implementation**:
```css
.game-card {
  @apply relative p-6 rounded-lg bg-gray-900;
  border: 2px solid transparent;
  background-clip: padding-box;
  transition: transform 0.3s ease-out;
}

.animated-border {
  @apply absolute inset-0 rounded-lg;
  background: linear-gradient(45deg, #DC2626, #06B6D4, #DC2626);
  background-size: 300% 300%;
  animation: borderPulse 3s ease infinite;
  opacity: 0;
  transition: opacity 0.3s ease-out;
  z-index: -1;
}

.game-card:hover .animated-border {
  opacity: 1;
}

@keyframes borderPulse {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.game-card:hover {
  transform: scale(1.05);
}
```

### 5. Media Highlights Component

**Purpose**: Full-width video showcase with cinematic presentation

**Template**: `partials/media_highlights.html`

**Structure**:
```html
<section class="media-highlights py-20 bg-gradient-to-b from-gray-900 to-black">
  <div class="container mx-auto px-4">
    <h2 class="section-title text-center mb-12">BATTLE MOMENTS</h2>
    
    <!-- Featured Video -->
    <div class="featured-video mb-8">
      <div class="video-wrapper relative">
        <img src="{{ featured_video.thumbnail.url }}" alt="{{ featured_video.title }}"
             class="video-thumbnail" loading="lazy">
        <button class="play-button">
          <span class="material-symbols-outlined">play_circle</span>
        </button>
        <div class="video-overlay"></div>
      </div>
    </div>
    
    <!-- Video Grid -->
    <div class="video-grid grid grid-cols-1 md:grid-cols-3 gap-6">
      {% for video in highlight_videos %}
      <div class="video-card">
        <div class="video-thumbnail-wrapper">
          <img src="{{ video.thumbnail.url }}" alt="{{ video.title }}"
               class="video-thumbnail" loading="lazy">
          <div class="video-duration">{{ video.duration }}</div>
          <div class="video-overlay"></div>
        </div>
        <h3 class="video-title">{{ video.title }}</h3>
        <p class="video-meta">{{ video.views }} views • {{ video.date }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

**Styling Approach**:
- Cinematic 16:9 aspect ratio for videos
- Dark overlay on thumbnails (opacity 0.4)
- Overlay fades on hover to reveal full thumbnail
- Play button with pulsing animation
- Smooth fade transitions between video states

**JavaScript Behavior**:
```javascript
// Video player initialization
const videoCards = document.querySelectorAll('.video-card');

videoCards.forEach(card => {
  card.addEventListener('click', () => {
    const videoUrl = card.dataset.videoUrl;
    openVideoModal(videoUrl);
  });
});

function openVideoModal(url) {
  // Create modal with embedded video player
  // Implement smooth fade-in animation
}
```

### 6. News Section Component

**Purpose**: Display recent updates with esports-style cards

**Template**: `partials/news_section.html`

**Structure**:
```html
<section class="news-section py-20 bg-black">
  <div class="container mx-auto px-4">
    <h2 class="section-title">LATEST INTEL</h2>
    
    <div class="news-grid grid grid-cols-1 md:grid-cols-3 gap-6">
      {% for article in news_articles %}
      <article class="news-card group">
        <!-- Featured Image -->
        <div class="news-image-wrapper">
          <img src="{{ article.image.url }}" alt="{{ article.title }}"
               class="news-image" loading="lazy">
          <div class="news-category-badge">{{ article.category }}</div>
        </div>
        
        <!-- Content -->
        <div class="news-content">
          <time class="news-date">{{ article.published_date|date:"M d, Y" }}</time>
          <h3 class="news-title">{{ article.title }}</h3>
          <p class="news-excerpt">{{ article.excerpt|truncatewords:20 }}</p>
          <a href="{{ article.get_absolute_url }}" class="news-link">
            Read More <span class="material-symbols-outlined">arrow_forward</span>
          </a>
        </div>
        
        <!-- Glow Effect -->
        <div class="news-glow"></div>
      </article>
      {% endfor %}
    </div>
  </div>
</section>
```

**Styling Approach**:
- Sharp typography with uppercase headings
- Category badges with color coding (Tournament: red, Announcement: cyan, Update: gray)
- Card lift effect on hover (translateY: -8px)
- Glow outline appears on hover (box-shadow)
- Strong visual hierarchy with font sizes and weights

### 7. Merch Teaser Component

**Purpose**: Feature merchandise with spotlight effect

**Template**: `partials/merch_teaser.html`

**Structure**:
```html
<section class="merch-teaser py-20 bg-gradient-to-b from-black to-gray-900 relative overflow-hidden">
  <!-- Spotlight Effect -->
  <div class="spotlight-effect"></div>
  
  <div class="container mx-auto px-4 relative z-10">
    <h2 class="section-title text-center">GEAR UP</h2>
    
    <div class="merch-grid grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      {% for product in featured_products %}
      <div class="merch-card">
        <div class="merch-image-wrapper">
          <img src="{{ product.image.url }}" alt="{{ product.name }}"
               class="merch-image" loading="lazy">
        </div>
        <h3 class="merch-name">{{ product.name }}</h3>
        <p class="merch-price">${{ product.price }}</p>
      </div>
      {% endfor %}
    </div>
    
    <div class="text-center">
      <a href="{% url 'store' %}" class="cta-primary">Shop the Gear</a>
    </div>
  </div>
</section>
```

**Styling Approach**:
- Dark background with radial gradient spotlight
- Product images with subtle zoom on hover
- Clean product cards with minimal borders
- Spotlight follows cursor (JavaScript enhancement)

### 8. Community CTA Component

**Purpose**: High-energy call-to-action for community engagement

**Template**: `partials/community_cta.html`

**Structure**:
```html
<section class="community-cta py-20 relative overflow-hidden">
  <!-- Animated Gradient Background -->
  <div class="animated-gradient-bg"></div>
  
  <!-- Glitch Accent -->
  <div class="glitch-accent"></div>
  
  <div class="container mx-auto px-4 relative z-10 text-center">
    <h2 class="cta-headline">JOIN THE EYT GAMER ARMY</h2>
    <p class="cta-subtext">Connect. Compete. Conquer.</p>
    
    <div class="cta-buttons flex flex-wrap justify-center gap-4 mt-8">
      <a href="{{ discord_url }}" class="social-cta discord" target="_blank">
        <span class="material-symbols-outlined">forum</span>
        Join Discord
      </a>
      <a href="{% url 'register' %}" class="social-cta register">
        <span class="material-symbols-outlined">person_add</span>
        Register Now
      </a>
      <a href="{{ twitter_url }}" class="social-cta twitter" target="_blank">
        <span class="material-symbols-outlined">tag</span>
        Follow on X
      </a>
    </div>
  </div>
</section>
```

**Styling Approach**:
- High contrast animated gradient background
- Glitch effect accents (random intervals)
- Large, bold headline with gradient text
- Social buttons with platform-specific colors
- Ripple effect on button click

### 9. Footer Component

**Purpose**: Minimal footer with social links and legal information

**Template**: `partials/footer.html`

**Structure**:
```html
<footer class="footer py-12 bg-gradient-to-t from-black to-gray-900">
  <div class="container mx-auto px-4">
    <!-- Social Icons -->
    <div class="social-icons flex justify-center gap-6 mb-8">
      <a href="{{ discord_url }}" class="social-icon" target="_blank" aria-label="Discord">
        <span class="material-symbols-outlined">forum</span>
      </a>
      <a href="{{ twitter_url }}" class="social-icon" target="_blank" aria-label="X (Twitter)">
        <span class="material-symbols-outlined">tag</span>
      </a>
      <a href="{{ twitch_url }}" class="social-icon" target="_blank" aria-label="Twitch">
        <span class="material-symbols-outlined">live_tv</span>
      </a>
      <a href="{{ youtube_url }}" class="social-icon" target="_blank" aria-label="YouTube">
        <span class="material-symbols-outlined">play_circle</span>
      </a>
    </div>
    
    <!-- Divider -->
    <div class="footer-divider"></div>
    
    <!-- Legal & Copyright -->
    <div class="footer-legal text-center mt-8">
      <p class="text-gray-400 text-sm">
        © {{ current_year }} EYTGaming. All rights reserved.
      </p>
      <div class="legal-links mt-2">
        <a href="{% url 'privacy' %}" class="legal-link">Privacy Policy</a>
        <span class="separator">•</span>
        <a href="{% url 'terms' %}" class="legal-link">Terms of Service</a>
      </div>
    </div>
  </div>
</footer>
```

## Data Models

### Landing Page Context Data

The Django view for the landing page will provide the following context:

```python
# views.py
from django.views.generic import TemplateView
from .models import Player, Game, Video, NewsArticle, Product

class LandingPageView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured players (top 8)
        context['players'] = Player.objects.filter(
            is_featured=True
        ).select_related('team').order_by('-rank')[:8]
        
        # Supported games
        context['games'] = Game.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        # Highlight videos (featured + recent)
        context['featured_video'] = Video.objects.filter(
            is_featured=True
        ).first()
        context['highlight_videos'] = Video.objects.filter(
            is_published=True
        ).exclude(id=context['featured_video'].id)[:6]
        
        # Recent news
        context['news_articles'] = NewsArticle.objects.filter(
            is_published=True
        ).order_by('-published_date')[:6]
        
        # Featured products
        context['featured_products'] = Product.objects.filter(
            is_featured=True
        ).order_by('display_order')[:4]
        
        # Social media URLs
        context['discord_url'] = settings.DISCORD_URL
        context['twitter_url'] = settings.TWITTER_URL
        context['twitch_url'] = settings.TWITCH_URL
        context['youtube_url'] = settings.YOUTUBE_URL
        
        # Current year for copyright
        context['current_year'] = timezone.now().year
        
        return context
```

### Required Model Fields

**Player Model** (existing, may need additional fields):
- `gamer_tag`: CharField
- `role`: CharField
- `game`: ForeignKey to Game
- `country_flag`: CharField (emoji or icon code)
- `image`: ImageField
- `kd_ratio`: DecimalField
- `rank`: IntegerField
- `wins`: IntegerField
- `is_featured`: BooleanField

**Game Model** (existing, may need additional fields):
- `name`: CharField
- `category`: CharField (Fighting, FPS, Sports, Mobile)
- `key_art`: ImageField
- `description`: TextField
- `is_active`: BooleanField
- `display_order`: IntegerField

**Video Model** (may need to be created):
- `title`: CharField
- `thumbnail`: ImageField
- `video_url`: URLField
- `duration`: DurationField
- `views`: IntegerField
- `published_date`: DateTimeField
- `is_featured`: BooleanField
- `is_published`: BooleanField

**NewsArticle Model** (may need to be created):
- `title`: CharField
- `excerpt`: TextField
- `image`: ImageField
- `category`: CharField (Tournament, Announcement, Update)
- `published_date`: DateTimeField
- `is_published`: BooleanField

**Product Model** (existing, may need additional fields):
- `name`: CharField
- `image`: ImageField
- `price`: DecimalField
- `is_featured`: BooleanField
- `display_order`: IntegerField



## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property Reflection Analysis

After analyzing all acceptance criteria, I identified the following redundancies:
- Properties 11.6 and 14.6 are identical (prefers-reduced-motion support) - will consolidate into one property
- Multiple hover effect properties (3.3, 4.4, 6.4, 7.4, 8.4, 11.3) can be consolidated into a single comprehensive hover effects property
- Typography properties (10.1, 10.2, 10.3, 10.4) can be combined into a comprehensive typography system property
- Lazy loading properties (3.5, 5.5, 13.1, 13.2) can be consolidated into a single comprehensive lazy loading property
- Icon usage (15.4) is already covered by template integration examples

### Core Properties

**Property 1: Navigation Sticky Positioning**

*For any* scroll position on the landing page, when the user scrolls down, the navigation bar should remain visible at the top of the viewport.

**Validates: Requirements 2.2**

---

**Property 2: Player Card Information Completeness**

*For any* player card rendered on the page, the card should display the gamer tag, role/game title, and country flag or icon.

**Validates: Requirements 3.2**

---

**Property 3: Player Card Hover State**

*For any* player card, when a user hovers over it, the system should apply neon glow and scale-up effects, and reveal a stat overlay showing K/D ratio, rank, and achievements.

**Validates: Requirements 3.3, 3.4**

---

**Property 4: Game Card Styling Consistency**

*For any* game card rendered on the page, the card should have dark styling with animated border elements.

**Validates: Requirements 4.3**

---

**Property 5: Game Card Hover Effects**

*For any* game card, when a user hovers over it, the system should apply pulse effect animation and reveal the division description.

**Validates: Requirements 4.4, 4.5**

---

**Property 6: Video Thumbnail Styling**

*For any* video thumbnail in the media section, the thumbnail should have cinematic styling with dark overlay applied.

**Validates: Requirements 5.3**

---

**Property 7: News Card Information Display**

*For any* news card rendered on the page, the card should display both the publication date and category tag (Tournament, Announcement, or Update).

**Validates: Requirements 6.2**

---

**Property 8: News Card Hover Effects**

*For any* news card, when a user hovers over it, the system should apply card lift and glow outline animations.

**Validates: Requirements 6.4**

---

**Property 9: Interactive Element Hover Feedback**

*For any* interactive element (buttons, cards, links), when a user hovers over it, the system should apply visual feedback effects such as glow, ripple, scale, or color transitions.

**Validates: Requirements 2.7, 3.3, 4.4, 6.4, 7.4, 8.4, 11.3**

---

**Property 10: Social Button New Tab Behavior**

*For any* social media button or icon (Discord, X, Twitch, YouTube), when a user clicks it, the system should open the platform in a new browser tab.

**Validates: Requirements 8.5, 9.4**

---

**Property 11: Typography System Consistency**

*For any* text element on the page, the system should apply appropriate typography: heavy condensed fonts for headlines, modern sans-serif for body text, uppercase for section headings, and strong letter spacing throughout.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4**

---

**Property 12: Color Contrast Accessibility**

*For any* text element rendered on a dark background, the color contrast ratio should meet WCAG 2.1 AA standards (minimum 4.5:1 for normal text, 3:1 for large text).

**Validates: Requirements 10.5**

---

**Property 13: Reduced Motion Accessibility**

*For any* animation or transition on the page, when the user has enabled prefers-reduced-motion settings, the system should disable or significantly reduce the animation.

**Validates: Requirements 11.6, 14.6**

---

**Property 14: Touch Target Sizing**

*For any* interactive element on mobile viewports, the touch target should be at least 44x44 pixels to meet accessibility standards.

**Validates: Requirements 12.5**

---

**Property 15: Lazy Loading Implementation**

*For any* image or video element that is below the fold (not immediately visible), the system should implement lazy loading using the loading="lazy" attribute or Intersection Observer API.

**Validates: Requirements 3.5, 5.5, 13.1, 13.2**

---

**Property 16: GPU-Accelerated Animations**

*For any* CSS animation or transition, the system should use GPU-accelerated properties (transform, opacity) rather than layout-triggering properties (width, height, top, left).

**Validates: Requirements 13.3**

---

**Property 17: Asset Compression**

*For any* image or video asset loaded on the page, the file should be appropriately compressed (images under 200KB for standard resolution, videos with appropriate bitrate).

**Validates: Requirements 13.5**

---

**Property 18: Keyboard Navigation Support**

*For any* interactive element (buttons, links, form inputs), the element should be keyboard accessible with proper focus states and tab order.

**Validates: Requirements 14.2**

---

**Property 19: Image Alt Text Completeness**

*For any* image element on the page, the image should include descriptive alt text that conveys the image's purpose or content.

**Validates: Requirements 14.3**

---

**Property 20: Color Information Redundancy**

*For any* information conveyed using color (status indicators, categories, alerts), the system should provide additional non-color indicators such as icons, text labels, or patterns.

**Validates: Requirements 14.4**

---

**Property 21: Form Accessibility**

*For any* form element (input, select, textarea), the element should have an associated label and appropriate ARIA attributes for screen reader support.

**Validates: Requirements 14.5**

---

**Property 22: Icon Library Consistency**

*For any* icon displayed on the page, the icon should use the Material Symbols library with consistent sizing and styling.

**Validates: Requirements 15.4**

---

**Property 23: Gradient Text Effects**

*For any* emphasized or headline text, the system should apply gradient text effects using background-clip and gradient backgrounds.

**Validates: Requirements 16.2**

---

**Property 24: Brand Color Palette Adherence**

*For any* colored element on the page, the color should come from the defined brand palette: deep black (#0A0A0A), electric red (#DC2626), gunmetal gray (#1F2937), or neon cyan (#06B6D4).

**Validates: Requirements 16.5**

## Error Handling

### Video Loading Failures

**Scenario**: Hero background video fails to load due to network issues or unsupported format.

**Handling**:
```javascript
const heroVideo = document.querySelector('.hero-video');

heroVideo.addEventListener('error', () => {
  // Fallback to animated gradient background
  const heroSection = document.querySelector('.hero-section');
  heroSection.classList.add('video-fallback');
  
  // Log error for monitoring
  console.error('Hero video failed to load, using fallback background');
});
```

**CSS Fallback**:
```css
.hero-section.video-fallback {
  background: linear-gradient(135deg, #0A0A0A 0%, #1F2937 50%, #0A0A0A 100%);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}
```

### Image Loading Failures

**Scenario**: Player images, game art, or other images fail to load.

**Handling**:
```javascript
document.querySelectorAll('img[loading="lazy"]').forEach(img => {
  img.addEventListener('error', function() {
    // Replace with placeholder
    this.src = '/static/images/placeholder.svg';
    this.alt = 'Image unavailable';
  });
});
```

### JavaScript Disabled

**Scenario**: User has JavaScript disabled or it fails to load.

**Handling**:
- All core content must be accessible without JavaScript
- Navigation works with standard HTML links
- Videos have poster images as fallback
- Animations defined in CSS (no JS-dependent animations for core functionality)
- Progressive enhancement: JS adds interactivity, doesn't gate content

### Accessibility Errors

**Scenario**: Screen reader encounters improperly labeled elements.

**Handling**:
- All interactive elements have aria-label or aria-labelledby
- Skip navigation link for keyboard users
- Focus trap management for modals
- Announce dynamic content changes with aria-live regions

```html
<!-- Skip navigation for keyboard users -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Announce dynamic content -->
<div aria-live="polite" aria-atomic="true" class="sr-only" id="announcements"></div>
```

### Performance Degradation

**Scenario**: Page performance drops below acceptable thresholds.

**Handling**:
- Monitor Core Web Vitals (LCP, FID, CLS)
- Implement performance budgets
- Reduce animation complexity on low-end devices
- Use Intersection Observer to pause off-screen animations

```javascript
// Detect low-end devices and reduce animations
const isLowEndDevice = navigator.hardwareConcurrency <= 4 && 
                       navigator.deviceMemory <= 4;

if (isLowEndDevice) {
  document.body.classList.add('reduced-animations');
}
```

### Responsive Layout Breaks

**Scenario**: Layout breaks at uncommon viewport sizes.

**Handling**:
- Test at multiple breakpoints (320px, 375px, 768px, 1024px, 1440px, 1920px)
- Use fluid typography with clamp()
- Implement container queries for component-level responsiveness
- Graceful degradation for very small screens

```css
/* Fluid typography */
h1 {
  font-size: clamp(2rem, 5vw, 4rem);
}

/* Container queries for components */
@container (min-width: 400px) {
  .player-card {
    grid-template-columns: 1fr 1fr;
  }
}
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Verify specific UI elements are present (hero section, navigation, footer)
- Test specific user interactions (button clicks, navigation)
- Validate Django template rendering with specific context data
- Test responsive breakpoints at specific viewport widths
- Verify accessibility with automated tools (axe-core)

**Property Tests**: Verify universal properties across all inputs
- Test that ALL player cards have required information
- Test that ALL interactive elements have hover effects
- Test that ALL images have alt text
- Test that ALL colors meet contrast requirements
- Test that ALL animations respect reduced motion preferences

### Testing Framework Selection

**Frontend Testing**:
- **Framework**: Playwright for end-to-end testing
- **Accessibility**: axe-core for automated accessibility testing
- **Visual Regression**: Percy or Chromatic for visual testing
- **Performance**: Lighthouse CI for performance monitoring

**Property-Based Testing**:
- **Framework**: fast-check (JavaScript/TypeScript) for property-based tests
- **Configuration**: Minimum 100 iterations per property test
- **Tagging**: Each test tagged with feature name and property number

### Test Organization

```
tests/
├── unit/
│   ├── test_landing_page_view.py (Django view tests)
│   ├── test_template_rendering.py (Template integration tests)
│   └── test_context_data.py (Context data tests)
├── e2e/
│   ├── test_hero_section.spec.js (Hero section UI tests)
│   ├── test_navigation.spec.js (Navigation behavior tests)
│   ├── test_player_showcase.spec.js (Player cards tests)
│   ├── test_responsive.spec.js (Responsive design tests)
│   └── test_accessibility.spec.js (Accessibility tests)
└── properties/
    ├── test_hover_effects.spec.js (Property 9)
    ├── test_typography.spec.js (Property 11)
    ├── test_contrast.spec.js (Property 12)
    ├── test_lazy_loading.spec.js (Property 15)
    ├── test_keyboard_nav.spec.js (Property 18)
    ├── test_alt_text.spec.js (Property 19)
    └── test_color_palette.spec.js (Property 24)
```

### Property Test Examples

**Property 9: Interactive Element Hover Feedback**
```javascript
// Feature: eytgaming-landing-page-redesign, Property 9: Interactive element hover feedback
import fc from 'fast-check';
import { test, expect } from '@playwright/test';

test('all interactive elements provide hover feedback', async ({ page }) => {
  await page.goto('/');
  
  // Get all interactive elements
  const interactiveElements = await page.locator('button, a, .player-card, .game-card, .news-card').all();
  
  // Test each element
  for (const element of interactiveElements) {
    // Get initial styles
    const initialStyles = await element.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        transform: computed.transform,
        boxShadow: computed.boxShadow,
        opacity: computed.opacity
      };
    });
    
    // Hover over element
    await element.hover();
    
    // Get hover styles
    const hoverStyles = await element.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        transform: computed.transform,
        boxShadow: computed.boxShadow,
        opacity: computed.opacity
      };
    });
    
    // Verify styles changed (some visual feedback occurred)
    const stylesChanged = 
      initialStyles.transform !== hoverStyles.transform ||
      initialStyles.boxShadow !== hoverStyles.boxShadow ||
      initialStyles.opacity !== hoverStyles.opacity;
    
    expect(stylesChanged).toBeTruthy();
  }
});
```

**Property 12: Color Contrast Accessibility**
```javascript
// Feature: eytgaming-landing-page-redesign, Property 12: Color contrast accessibility
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test('all text meets WCAG AA contrast requirements', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);
  
  // Check contrast specifically
  await checkA11y(page, null, {
    rules: {
      'color-contrast': { enabled: true }
    }
  });
  
  // Additional manual check for dynamic content
  const textElements = await page.locator('h1, h2, h3, p, a, button').all();
  
  for (const element of textElements) {
    const contrast = await element.evaluate(el => {
      const computed = window.getComputedStyle(el);
      const color = computed.color;
      const backgroundColor = computed.backgroundColor;
      
      // Calculate contrast ratio (simplified)
      return calculateContrastRatio(color, backgroundColor);
    });
    
    const fontSize = await element.evaluate(el => {
      return parseFloat(window.getComputedStyle(el).fontSize);
    });
    
    // Large text (18pt+ or 14pt+ bold) needs 3:1, normal text needs 4.5:1
    const requiredRatio = fontSize >= 18 || (fontSize >= 14 && isBold) ? 3 : 4.5;
    
    expect(contrast).toBeGreaterThanOrEqual(requiredRatio);
  }
});
```

**Property 19: Image Alt Text Completeness**
```javascript
// Feature: eytgaming-landing-page-redesign, Property 19: Image alt text completeness
import { test, expect } from '@playwright/test';

test('all images have descriptive alt text', async ({ page }) => {
  await page.goto('/');
  
  // Get all images
  const images = await page.locator('img').all();
  
  for (const img of images) {
    const alt = await img.getAttribute('alt');
    
    // Alt text should exist
    expect(alt).not.toBeNull();
    
    // Alt text should not be empty (unless decorative)
    const role = await img.getAttribute('role');
    if (role !== 'presentation') {
      expect(alt.trim().length).toBeGreaterThan(0);
    }
    
    // Alt text should not be placeholder text
    const invalidAltText = ['image', 'picture', 'photo', 'img'];
    expect(invalidAltText.includes(alt.toLowerCase())).toBeFalsy();
  }
});
```

### Unit Test Examples

**Hero Section Rendering**
```python
# tests/unit/test_landing_page_view.py
from django.test import TestCase, Client
from django.urls import reverse

class LandingPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('home')
    
    def test_hero_section_renders(self):
        """Test that hero section is present in rendered page"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hero-section')
        self.assertContains(response, 'GEAR UP. DOMINATE. EVOLVE.')
    
    def test_cta_buttons_present(self):
        """Test that primary CTA buttons are rendered"""
        response = self.client.get(self.url)
        self.assertContains(response, 'Join the Army')
        self.assertContains(response, 'Watch Highlights')
```

**Responsive Breakpoints**
```javascript
// tests/e2e/test_responsive.spec.js
import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('mobile layout at 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Navigation should show mobile menu toggle
    const mobileToggle = page.locator('.mobile-menu-toggle');
    await expect(mobileToggle).toBeVisible();
    
    // Desktop menu should be hidden
    const desktopMenu = page.locator('.nav-menu');
    await expect(desktopMenu).toBeHidden();
  });
  
  test('desktop layout at 1920px', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    
    // Desktop menu should be visible
    const desktopMenu = page.locator('.nav-menu');
    await expect(desktopMenu).toBeVisible();
    
    // Mobile toggle should be hidden
    const mobileToggle = page.locator('.mobile-menu-toggle');
    await expect(mobileToggle).toBeHidden();
  });
});
```

### Performance Testing

**Lighthouse CI Configuration**
```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:8000/'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.85 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
      },
    },
  },
};
```

### Test Execution Strategy

1. **Development**: Run unit tests and property tests on every code change
2. **Pre-commit**: Run accessibility tests and linting
3. **CI Pipeline**: Run full test suite including visual regression
4. **Pre-deployment**: Run Lighthouse CI and performance tests
5. **Post-deployment**: Monitor real user metrics and Core Web Vitals

### Coverage Goals

- **Unit Test Coverage**: 80% of Django view and template logic
- **Property Test Coverage**: 100% of identified properties (24 properties)
- **Accessibility Coverage**: 100% WCAG 2.1 AA compliance
- **Visual Regression**: All major components and responsive breakpoints
- **Performance**: Lighthouse score > 85 on all metrics
