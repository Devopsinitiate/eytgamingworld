/**
 * Social Sharing Module for Tournament Detail Page
 * Provides social media sharing functionality with fallback support
 */

class SocialSharingManager {
    constructor() {
        this.shareData = {
            url: window.location.href,
            title: document.title,
            text: this.extractTournamentDescription()
        };
        
        this.init();
    }
    
    init() {
        this.setupShareButtons();
        this.setupCopyLinkFunctionality();
        this.log('Social Sharing Manager initialized');
    }
    
    extractTournamentDescription() {
        // Try to get tournament description from meta tags or page content
        const metaDescription = document.querySelector('meta[name="description"]');
        if (metaDescription) {
            return metaDescription.content;
        }
        
        const tournamentTitle = document.querySelector('.tournament-title, h1');
        if (tournamentTitle) {
            return `Check out this tournament: ${tournamentTitle.textContent.trim()}`;
        }
        
        return 'Check out this tournament on EYT Gaming!';
    }
    
    setupShareButtons() {
        const shareButtons = document.querySelectorAll('[data-share]');
        
        shareButtons.forEach(button => {
            const platform = button.dataset.share;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.shareToSocial(platform);
            });
        });
    }
    
    setupCopyLinkFunctionality() {
        const copyButtons = document.querySelectorAll('[data-copy-link], .copy-link-btn');
        
        copyButtons.forEach(button => {
            // Fix button text display (remove HTML class names)
            if (button.textContent.includes('class=') || button.textContent.includes('btn-')) {
                button.textContent = 'Copy Link';
            }
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.copyLinkToClipboard();
            });
        });
    }
    
    async shareToSocial(platform) {
        const { url, title, text } = this.shareData;
        
        // Try native Web Share API first (mobile browsers)
        if (navigator.share && platform === 'native') {
            try {
                await navigator.share({ url, title, text });
                this.showFeedback('Shared successfully!', 'success');
                return;
            } catch (error) {
                if (error.name !== 'AbortError') {
                    this.log('Web Share API failed:', error);
                }
            }
        }
        
        // Fallback to platform-specific sharing
        const shareUrls = {
            twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`,
            facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
            linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
            reddit: `https://reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}`,
            whatsapp: `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`,
            telegram: `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
        };
        
        const shareUrl = shareUrls[platform];
        if (shareUrl) {
            // Open in new window/tab
            const popup = window.open(shareUrl, '_blank', 'width=600,height=400,scrollbars=yes,resizable=yes');
            
            if (popup) {
                this.showFeedback(`Opening ${platform} share...`, 'info');
            } else {
                // Popup blocked, fallback to direct navigation
                window.location.href = shareUrl;
            }
        } else {
            this.showFeedback(`Sharing to ${platform} not supported`, 'error');
        }
    }
    
    async copyLinkToClipboard() {
        const url = this.shareData.url;
        
        try {
            // Modern Clipboard API (primary method)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(url);
                this.showFeedback('Link copied to clipboard!', 'success');
                return;
            }
            
            // Fallback method using execCommand
            if (document.execCommand) {
                const textArea = document.createElement('textarea');
                textArea.value = url;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (successful) {
                    this.showFeedback('Link copied to clipboard!', 'success');
                    return;
                } else {
                    throw new Error('execCommand copy failed');
                }
            }
            
            // Final fallback - show URL in modal for manual copying
            this.showCopyModal(url);
            
        } catch (error) {
            this.log('Copy to clipboard failed:', error);
            this.showCopyModal(url);
        }
    }
    
    showCopyModal(url) {
        // Create modal for manual copying
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-md mx-4">
                <h3 class="text-lg font-semibold mb-4">Copy Tournament Link</h3>
                <p class="text-gray-600 mb-4">Please copy the link below:</p>
                <div class="bg-gray-100 p-3 rounded border">
                    <input type="text" value="${url}" readonly class="w-full bg-transparent border-none outline-none" id="copy-url-input">
                </div>
                <div class="flex justify-end gap-2 mt-4">
                    <button class="px-4 py-2 text-gray-600 hover:text-gray-800" onclick="this.closest('.fixed').remove()">Cancel</button>
                    <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" onclick="document.getElementById('copy-url-input').select(); document.execCommand('copy'); this.textContent='Copied!'; setTimeout(() => this.closest('.fixed').remove(), 1000)">Copy</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Auto-select the URL
        setTimeout(() => {
            const input = modal.querySelector('#copy-url-input');
            input.focus();
            input.select();
        }, 100);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
    }
    
    showFeedback(message, type = 'info', duration = 3000) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300`;
        
        const typeClasses = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'info': 'bg-blue-500 text-white',
            'warning': 'bg-yellow-500 text-white'
        };
        
        toast.className += ` ${typeClasses[type] || typeClasses.info}`;
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <span>${message}</span>
                <button class="ml-2 text-white/80 hover:text-white" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, duration);
    }
    
    // Generate share buttons HTML
    generateShareButtons(options = {}) {
        const {
            platforms = ['twitter', 'facebook', 'copy'],
            showLabels = true,
            buttonClass = 'share-btn'
        } = options;
        
        const buttonConfigs = {
            twitter: { label: 'Twitter', icon: '🐦', color: 'bg-blue-400' },
            facebook: { label: 'Facebook', icon: '📘', color: 'bg-blue-600' },
            linkedin: { label: 'LinkedIn', icon: '💼', color: 'bg-blue-700' },
            reddit: { label: 'Reddit', icon: '🔴', color: 'bg-orange-500' },
            whatsapp: { label: 'WhatsApp', icon: '💬', color: 'bg-green-500' },
            telegram: { label: 'Telegram', icon: '✈️', color: 'bg-blue-500' },
            copy: { label: 'Copy Link', icon: '📋', color: 'bg-gray-600' }
        };
        
        const buttons = platforms.map(platform => {
            const config = buttonConfigs[platform];
            if (!config) return '';
            
            const action = platform === 'copy' ? 'data-copy-link' : `data-share="${platform}"`;
            const label = showLabels ? config.label : '';
            
            return `
                <button ${action} class="${buttonClass} ${config.color} text-white px-3 py-2 rounded-lg hover:opacity-80 transition-opacity flex items-center gap-2">
                    <span>${config.icon}</span>
                    ${label ? `<span>${label}</span>` : ''}
                </button>
            `;
        }).join('');
        
        return `<div class="share-buttons flex gap-2 flex-wrap">${buttons}</div>`;
    }
    
    log(...args) {
        console.log('[SocialSharing]', ...args);
    }
    
    destroy() {
        // Remove event listeners and clean up
        const shareButtons = document.querySelectorAll('[data-share], [data-copy-link]');
        shareButtons.forEach(button => {
            button.replaceWith(button.cloneNode(true));
        });
        
        // Remove any modals or toasts
        document.querySelectorAll('.fixed.inset-0, .fixed.top-4.right-4').forEach(el => {
            if (el.textContent.includes('Copy Tournament Link') || el.textContent.includes('copied')) {
                el.remove();
            }
        });
        
        this.log('Social Sharing Manager destroyed');
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.SocialSharingManager = new SocialSharingManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.SocialSharingManager) {
        window.SocialSharingManager.destroy();
    }
});

// Make available globally instead of using ES6 export
window.SocialSharingManager = SocialSharingManager;