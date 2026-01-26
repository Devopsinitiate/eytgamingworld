/**
 * Copy Link Handler Module
 * Provides robust clipboard functionality with multi-tier fallback system
 * Addresses Requirements 4.1, 4.2, 4.3, 4.4, 4.5
 */

class CopyLinkHandler {
    constructor(element = null) {
        this.element = element;
        this.url = window.location.href;
        this.fallbackMethods = ['clipboard', 'execCommand', 'modal'];
        this.currentMethodIndex = 0;
        
        this.init();
    }
    
    init() {
        this.setupCopyButtons();
        this.fixButtonTextDisplay();
        this.log('Copy Link Handler initialized');
    }
    
    setupCopyButtons() {
        // Find all copy link buttons
        const copyButtons = document.querySelectorAll(
            '.copy-button, .copy-link, [data-copy-link], [data-action="copy-link"]'
        );
        
        copyButtons.forEach(button => {
            // Remove existing event listeners by cloning
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add new event listener
            newButton.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const urlToCopy = newButton.dataset.copyText || 
                                newButton.dataset.url || 
                                this.url;
                
                await this.copyToClipboard(urlToCopy);
            });
        });
    }
    
    fixButtonTextDisplay() {
        // Fix button text display (remove HTML class names)
        const copyButtons = document.querySelectorAll(
            '.copy-button, .copy-link, [data-copy-link], [data-action="copy-link"]'
        );
        
        copyButtons.forEach(button => {
            const text = button.textContent || button.innerText;
            
            // Check if button text contains HTML class names or unwanted content
            if (text.includes('class=') || 
                text.includes('btn-') || 
                text.includes('copy-') ||
                text.trim() === '' ||
                text.includes('<') ||
                text.includes('>')) {
                
                // Set proper button text
                button.textContent = 'Copy Link';
                
                // Also update aria-label for accessibility
                if (!button.getAttribute('aria-label')) {
                    button.setAttribute('aria-label', 'Copy tournament link to clipboard');
                }
            }
        });
    }
    
    async copyToClipboard(url = this.url) {
        this.currentMethodIndex = 0;
        return await this.attemptCopy(url);
    }
    
    async attemptCopy(url) {
        const method = this.fallbackMethods[this.currentMethodIndex];
        
        try {
            switch (method) {
                case 'clipboard':
                    return await this.copyWithClipboardAPI(url);
                case 'execCommand':
                    return await this.copyWithExecCommand(url);
                case 'modal':
                    return await this.copyWithModal(url);
                default:
                    throw new Error('No more fallback methods available');
            }
        } catch (error) {
            this.log(`Copy method '${method}' failed:`, error);
            
            // Try next fallback method
            this.currentMethodIndex++;
            if (this.currentMethodIndex < this.fallbackMethods.length) {
                return await this.attemptCopy(url);
            } else {
                // All methods failed
                this.showFeedback('Failed to copy link. Please copy manually from address bar.', 'error');
                throw new Error('All copy methods failed');
            }
        }
    }
    
    async copyWithClipboardAPI(url) {
        // Modern Clipboard API (primary method)
        if (!navigator.clipboard || !navigator.clipboard.writeText) {
            throw new Error('Clipboard API not available');
        }
        
        // Check for secure context (HTTPS or localhost)
        if (!window.isSecureContext) {
            throw new Error('Clipboard API requires secure context');
        }
        
        await navigator.clipboard.writeText(url);
        this.showFeedback('Link copied to clipboard!', 'success');
        return true;
    }
    
    async copyWithExecCommand(url) {
        // Legacy browser support using execCommand
        if (!document.execCommand) {
            throw new Error('execCommand not available');
        }
        
        const textArea = document.createElement('textarea');
        textArea.value = url;
        
        // Style to make it invisible but still functional
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.width = '1px';
        textArea.style.height = '1px';
        textArea.style.opacity = '0';
        textArea.style.pointerEvents = 'none';
        textArea.setAttribute('readonly', '');
        textArea.setAttribute('tabindex', '-1');
        
        document.body.appendChild(textArea);
        
        try {
            // Focus and select the text
            textArea.focus();
            textArea.select();
            textArea.setSelectionRange(0, textArea.value.length);
            
            // Attempt to copy
            const successful = document.execCommand('copy');
            
            if (!successful) {
                throw new Error('execCommand copy returned false');
            }
            
            this.showFeedback('Link copied to clipboard!', 'success');
            return true;
            
        } finally {
            // Always clean up
            document.body.removeChild(textArea);
        }
    }
    
    async copyWithModal(url) {
        // Manual fallback - display URL in modal for manual copying
        return new Promise((resolve) => {
            const modal = this.createCopyModal(url);
            document.body.appendChild(modal);
            
            // Auto-select the URL
            setTimeout(() => {
                const input = modal.querySelector('.copy-url-input');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 100);
            
            // Resolve when modal is closed
            const closeHandler = () => {
                resolve(true);
            };
            
            modal.addEventListener('modal-closed', closeHandler);
            
            this.showFeedback('Please copy the link manually', 'info');
        });
    }
    
    createCopyModal(url) {
        const modal = document.createElement('div');
        modal.className = 'copy-link-modal fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'copy-modal-title');
        
        modal.innerHTML = `
            <div class="bg-gray-800 rounded-lg p-6 max-w-md mx-4 border border-white/10">
                <h3 id="copy-modal-title" class="text-lg font-semibold mb-4 text-white">Copy Tournament Link</h3>
                <p class="text-gray-300 mb-4">Please copy the link below:</p>
                <div class="bg-gray-700 p-3 rounded border border-white/10">
                    <input type="text" 
                           value="${url}" 
                           readonly 
                           class="copy-url-input w-full bg-transparent border-none outline-none text-white" 
                           aria-label="Tournament URL to copy">
                </div>
                <div class="flex justify-end gap-2 mt-4">
                    <button class="cancel-btn px-4 py-2 text-gray-400 hover:text-white transition-colors" 
                            aria-label="Cancel and close modal">
                        Cancel
                    </button>
                    <button class="copy-manual-btn px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors" 
                            aria-label="Select and copy URL">
                        Select & Copy
                    </button>
                </div>
            </div>
        `;
        
        // Event handlers
        const closeModal = () => {
            modal.dispatchEvent(new CustomEvent('modal-closed'));
            modal.remove();
        };
        
        // Cancel button
        modal.querySelector('.cancel-btn').addEventListener('click', closeModal);
        
        // Manual copy button
        modal.querySelector('.copy-manual-btn').addEventListener('click', () => {
            const input = modal.querySelector('.copy-url-input');
            input.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    modal.querySelector('.copy-manual-btn').textContent = 'Copied!';
                    setTimeout(closeModal, 1000);
                } else {
                    this.showFeedback('Please select the text and copy manually (Ctrl+C)', 'warning');
                }
            } catch (err) {
                this.showFeedback('Please select the text and copy manually (Ctrl+C)', 'warning');
            }
        });
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
        
        return modal;
    }
    
    showFeedback(message, type = 'info', duration = 3000) {
        // Create toast notification with accessibility support
        const toast = document.createElement('div');
        toast.className = `copy-link-toast fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transform translate-x-full transition-transform duration-300`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        
        const typeClasses = {
            'success': 'bg-green-600 text-white border border-green-500',
            'error': 'bg-red-600 text-white border border-red-500',
            'info': 'bg-blue-600 text-white border border-blue-500',
            'warning': 'bg-yellow-600 text-white border border-yellow-500'
        };
        
        toast.className += ` ${typeClasses[type] || typeClasses.info}`;
        
        const icons = {
            'success': '✓',
            'error': '✗',
            'info': 'ℹ',
            'warning': '⚠'
        };
        
        toast.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="text-lg" aria-hidden="true">${icons[type] || icons.info}</span>
                <span>${message}</span>
                <button class="ml-2 text-white/80 hover:text-white transition-colors" 
                        aria-label="Close notification"
                        onclick="this.parentElement.parentElement.remove()">
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
        
        // Announce to screen readers
        this.announceToScreenReader(message);
    }
    
    announceToScreenReader(message) {
        // Create or use existing ARIA live region
        let liveRegion = document.getElementById('copy-link-live-region');
        
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'copy-link-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            liveRegion.style.position = 'absolute';
            liveRegion.style.left = '-10000px';
            liveRegion.style.width = '1px';
            liveRegion.style.height = '1px';
            liveRegion.style.overflow = 'hidden';
            document.body.appendChild(liveRegion);
        }
        
        liveRegion.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 1000);
    }
    
    // Cross-browser compatibility check
    checkBrowserSupport() {
        const support = {
            clipboardAPI: !!(navigator.clipboard && navigator.clipboard.writeText),
            execCommand: !!document.execCommand,
            secureContext: window.isSecureContext,
            userAgent: navigator.userAgent
        };
        
        this.log('Browser support:', support);
        return support;
    }
    
    // Mobile-specific handling
    handleMobileClipboard(url) {
        // Mobile browsers may have different clipboard behavior
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile) {
            // On mobile, try to use the native share API if available
            if (navigator.share) {
                return navigator.share({
                    title: document.title,
                    url: url
                }).then(() => {
                    this.showFeedback('Shared successfully!', 'success');
                    return true;
                }).catch((error) => {
                    if (error.name !== 'AbortError') {
                        this.log('Mobile share failed:', error);
                        // Fall back to regular copy methods
                        return this.copyToClipboard(url);
                    }
                    return false;
                });
            }
        }
        
        // Use regular copy methods for non-mobile or when share API is not available
        return this.copyToClipboard(url);
    }
    
    log(...args) {
        console.log('[CopyLinkHandler]', ...args);
    }
    
    destroy() {
        // Clean up event listeners
        const copyButtons = document.querySelectorAll(
            '.copy-button, .copy-link, [data-copy-link], [data-action="copy-link"]'
        );
        
        copyButtons.forEach(button => {
            // Remove event listeners by cloning
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
        });
        
        // Remove any modals or toasts
        document.querySelectorAll('.copy-link-modal, .copy-link-toast').forEach(el => {
            el.remove();
        });
        
        // Remove live region
        const liveRegion = document.getElementById('copy-link-live-region');
        if (liveRegion) {
            liveRegion.remove();
        }
        
        this.log('Copy Link Handler destroyed');
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (!window.CopyLinkHandler) {
        window.CopyLinkHandler = new CopyLinkHandler();
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.CopyLinkHandler && window.CopyLinkHandler.destroy) {
        window.CopyLinkHandler.destroy();
    }
});

export default CopyLinkHandler;