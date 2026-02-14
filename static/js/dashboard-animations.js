/**
 * Dashboard Gaming Animations
 * Particle effects, background gradients, and visual enhancements
 */

class DashboardAnimations {
    constructor() {
        this.particles = [];
        this.canvas = null;
        this.ctx = null;
        this.animationFrameId = null;
        this.gradientAnimationId = null;
    }

    /**
     * Initialize particle background effect
     */
    initParticles(containerId = 'dashboard-particles') {
        // Create canvas for particles
        const container = document.getElementById(containerId) || document.body;
        
        // Check if canvas already exists
        if (document.getElementById('particle-canvas')) {
            return;
        }

        this.canvas = document.createElement('canvas');
        this.canvas.id = 'particle-canvas';
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        this.canvas.style.opacity = '0.3';

        container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        // Set canvas size
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Create particles
        this.createParticles();

        // Start animation
        this.animateParticles();
    }

    resizeCanvas() {
        if (!this.canvas) return;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const particleCount = Math.min(50, Math.floor(window.innerWidth / 20));
        this.particles = [];

        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: Math.random() * 2 + 1,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                color: Math.random() > 0.5 ? 'rgba(220, 38, 38, 0.5)' : 'rgba(6, 182, 212, 0.5)'
            });
        }
    }

    animateParticles() {
        if (!this.ctx) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update and draw particles
        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;

            // Bounce off edges
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;

            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = particle.color;
            this.ctx.fill();

            // Draw glow
            const gradient = this.ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, particle.radius * 3
            );
            gradient.addColorStop(0, particle.color);
            gradient.addColorStop(1, 'transparent');
            this.ctx.fillStyle = gradient;
            this.ctx.fill();
        });

        // Draw connections between nearby particles
        this.particles.forEach((p1, i) => {
            this.particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(p1.x, p1.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.strokeStyle = `rgba(220, 38, 38, ${0.1 * (1 - distance / 100)})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.stroke();
                }
            });
        });

        this.animationFrameId = requestAnimationFrame(() => this.animateParticles());
    }

    stopParticles() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
        }
    }

    /**
     * Animated background gradient
     */
    initBackgroundGradient(elementId = 'main-content') {
        const element = document.getElementById(elementId);
        if (!element) return;

        let hue = 0;

        const animateGradient = () => {
            hue = (hue + 0.5) % 360;
            
            const gradient = `
                radial-gradient(
                    circle at 20% 50%,
                    hsla(${hue}, 70%, 15%, 0.15) 0%,
                    transparent 50%
                ),
                radial-gradient(
                    circle at 80% 80%,
                    hsla(${(hue + 180) % 360}, 70%, 15%, 0.15) 0%,
                    transparent 50%
                ),
                radial-gradient(
                    circle at 40% 20%,
                    hsla(${(hue + 90) % 360}, 70%, 15%, 0.1) 0%,
                    transparent 50%
                )
            `;

            element.style.background = gradient;
            this.gradientAnimationId = requestAnimationFrame(animateGradient);
        };

        animateGradient();
    }

    stopBackgroundGradient() {
        if (this.gradientAnimationId) {
            cancelAnimationFrame(this.gradientAnimationId);
            this.gradientAnimationId = null;
        }
    }

    /**
     * Scroll-triggered animations
     */
    initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe all cards and sections
        document.querySelectorAll('.card-gaming, .stat-card-gaming, .mobile-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            observer.observe(el);
        });
    }

    /**
     * Number counter animation
     */
    animateCounter(element, target, duration = 1000) {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;

        const updateCounter = () => {
            current += increment;
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.textContent = Math.round(target);
                return;
            }
            element.textContent = Math.round(current);
            requestAnimationFrame(updateCounter);
        };

        updateCounter();
    }

    /**
     * Init all stat counters on page
     */
    initStatCounters() {
        document.querySelectorAll('.stat-value, .mobile-stat-value, .gaming-stat').forEach(el => {
            const target = parseInt(el.textContent);
            if (!isNaN(target)) {
                el.textContent = '0';
                
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.animateCounter(el, target, 1500);
                            observer.unobserve(el);
                        }
                    });
                }, { threshold: 0.5 });

                observer.observe(el);
            }
        });
    }

    /**
     * Glow pulse effect on hover
     */
    initHoverGlow() {
        document.querySelectorAll('.btn-gaming-primary, .btn-gaming-secondary, .stat-card-gaming').forEach(el => {
            el.addEventListener('mouseenter', () => {
                el.style.transition = 'box-shadow 0.3s ease';
                el.style.boxShadow = '0 0 40px rgba(220, 38, 38, 0.8), 0 0 60px rgba(220, 38, 38, 0.5)';
            });

            el.addEventListener('mouseleave', () => {
                el.style.boxShadow = '';
            });
        });
    }

    /**
     * Initialize all animations
     */
    init(options = {}) {
        const defaults = {
            particles: true,
            gradient: false, // Disabled by default for performance
            scrollAnimations: true,
            counters: true,
            hoverGlow: true
        };

        const config = { ...defaults, ...options };

        if (config.particles) {
            this.initParticles();
        }

        if (config.gradient) {
            this.initBackgroundGradient();
        }

        if (config.scrollAnimations) {
            this.initScrollAnimations();
        }

        if (config.counters) {
            this.initStatCounters();
        }

        if (config.hoverGlow) {
            this.initHoverGlow();
        }
    }

    /**
     * Destroy all animations
     */
    destroy() {
        this.stopParticles();
        this.stopBackgroundGradient();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardAnimations;
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.dashboard-mobile-container, #main-content')) {
        window.dashboardAnimations = new DashboardAnimations();
        window.dashboardAnimations.init({
            particles: true,
            gradient: false,
            scrollAnimations: true,
            counters: true,
            hoverGlow: true
        });
    }
});
