/**
 * Payment History Filtering and Pagination
 * Handles client-side filtering, URL parameters, and pagination
 */

document.addEventListener('DOMContentLoaded', function() {
    // Update ARIA live region for screen reader announcements
    const paginationStatus = document.getElementById('pagination-status');
    const urlParams = new URLSearchParams(window.location.search);
    
    // Announce page change to screen readers
    if (paginationStatus) {
        // Get current page from URL or default to 1
        const currentPage = urlParams.get('page') || '1';
        
        // Extract total pages from the pagination controls if they exist
        const paginationNav = document.querySelector('[role="navigation"][aria-label="Payment history pagination"]');
        if (paginationNav) {
            // Try to find the total pages from the page info text
            const pageInfo = paginationNav.querySelector('[aria-live="polite"]');
            if (pageInfo) {
                const text = pageInfo.textContent;
                const match = text.match(/of (\d+) payment/);
                if (match) {
                    const totalPayments = parseInt(match[1]);
                    const totalPages = Math.ceil(totalPayments / 25);
                    paginationStatus.textContent = `Page ${currentPage} of ${totalPages} loaded`;
                }
            } else {
                // Fallback: just announce the current page
                paginationStatus.textContent = `Page ${currentPage} loaded`;
            }
        }
    }
    
    // Mobile scroll to top on page change
    // Check if we're on mobile and if the page parameter exists in URL
    const isMobile = window.innerWidth < 768;
    const hasPageParam = urlParams.has('page');
    
    if (isMobile && hasPageParam) {
        // Scroll to the top of the payment list
        const paymentListTop = document.getElementById('payment-list-top');
        if (paymentListTop) {
            paymentListTop.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            // Fallback: scroll to top of page
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    
    // Add click handlers to pagination links for smooth scrolling on mobile
    const paginationLinks = document.querySelectorAll('[aria-label*="page"]');
    paginationLinks.forEach(link => {
        if (link.tagName === 'A') {
            link.addEventListener('click', function(e) {
                // On mobile, we want to scroll to top when navigating
                if (window.innerWidth < 768) {
                    // Let the link navigate normally, but the scroll will happen on next page load
                    // due to the code above
                }
            });
        }
    });
    
    // Configuration
    const ITEMS_PER_PAGE = 10;
    
    // Get DOM elements
    const statusFilter = document.getElementById('status-filter');
    const typeFilter = document.getElementById('type-filter');
    const dateFilter = document.getElementById('date-filter');
    const clearFiltersBtn = document.getElementById('clear-filters');
    const clearFiltersEmptyBtn = document.getElementById('clear-filters-empty');
    const paymentCount = document.getElementById('payment-count');
    const noResults = document.getElementById('no-results');
    const pagination = document.getElementById('pagination');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const currentPageSpan = document.getElementById('current-page');
    const totalPagesSpan = document.getElementById('total-pages');
    
    // Get all payment rows and cards
    const paymentRows = document.querySelectorAll('.payment-row');
    const paymentCards = document.querySelectorAll('.payment-card');
    const desktopTable = document.querySelector('.desktop-table');
    const mobileCards = document.querySelector('.mobile-cards');
    
    // State
    let currentPage = 1;
    let filteredPayments = [];
    
    /**
     * Initialize filters from URL parameters
     */
    function initializeFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        if (urlParams.has('status')) {
            statusFilter.value = urlParams.get('status');
        }
        if (urlParams.has('type')) {
            typeFilter.value = urlParams.get('type');
        }
        if (urlParams.has('date')) {
            dateFilter.value = urlParams.get('date');
        }
        if (urlParams.has('page')) {
            currentPage = parseInt(urlParams.get('page')) || 1;
        }
        
        applyFilters();
    }
    
    /**
     * Update URL with current filter parameters
     */
    function updateURL() {
        const params = new URLSearchParams();
        
        if (statusFilter.value) {
            params.set('status', statusFilter.value);
        }
        if (typeFilter.value) {
            params.set('type', typeFilter.value);
        }
        if (dateFilter.value) {
            params.set('date', dateFilter.value);
        }
        if (currentPage > 1) {
            params.set('page', currentPage);
        }
        
        const newURL = params.toString() 
            ? `${window.location.pathname}?${params.toString()}`
            : window.location.pathname;
        
        window.history.replaceState({}, '', newURL);
    }
    
    /**
     * Check if a date is within the selected range
     */
    function isDateInRange(dateString, daysBack) {
        if (!daysBack) return true;
        
        const paymentDate = new Date(dateString);
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - parseInt(daysBack));
        
        return paymentDate >= cutoffDate;
    }
    
    /**
     * Filter payments based on current filter values
     */
    function applyFilters() {
        const statusValue = statusFilter.value.toLowerCase();
        const typeValue = typeFilter.value.toLowerCase();
        const dateValue = dateFilter.value;
        
        filteredPayments = [];
        
        // Filter desktop table rows
        paymentRows.forEach(row => {
            const rowStatus = row.dataset.status.toLowerCase();
            const rowType = row.dataset.type.toLowerCase();
            const rowDate = row.dataset.date;
            
            const matchesStatus = !statusValue || rowStatus === statusValue;
            const matchesType = !typeValue || rowType === typeValue;
            const matchesDate = isDateInRange(rowDate, dateValue);
            
            if (matchesStatus && matchesType && matchesDate) {
                filteredPayments.push(row);
            }
        });
        
        // Filter mobile cards
        const filteredCards = [];
        paymentCards.forEach(card => {
            const cardStatus = card.dataset.status.toLowerCase();
            const cardType = card.dataset.type.toLowerCase();
            const cardDate = card.dataset.date;
            
            const matchesStatus = !statusValue || cardStatus === statusValue;
            const matchesType = !typeValue || cardType === typeValue;
            const matchesDate = isDateInRange(cardDate, dateValue);
            
            if (matchesStatus && matchesType && matchesDate) {
                filteredCards.push(card);
            }
        });
        
        // Update count
        paymentCount.textContent = filteredPayments.length;
        
        // Show/hide empty state
        if (filteredPayments.length === 0) {
            noResults.classList.remove('hidden');
            if (desktopTable) desktopTable.classList.add('hidden');
            if (mobileCards) mobileCards.classList.add('hidden');
            pagination.classList.add('hidden');
        } else {
            noResults.classList.add('hidden');
            if (desktopTable) desktopTable.classList.remove('hidden');
            if (mobileCards) mobileCards.classList.remove('hidden');
            pagination.classList.remove('hidden');
        }
        
        // Reset to page 1 when filters change
        currentPage = 1;
        
        // Apply pagination
        applyPagination(filteredPayments, filteredCards);
        
        // Update URL
        updateURL();
    }
    
    /**
     * Apply pagination to filtered results
     */
    function applyPagination(rows, cards) {
        const totalPages = Math.ceil(rows.length / ITEMS_PER_PAGE);
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
        const endIndex = startIndex + ITEMS_PER_PAGE;
        
        // Update pagination info
        currentPageSpan.textContent = currentPage;
        totalPagesSpan.textContent = totalPages || 1;
        
        // Enable/disable pagination buttons
        prevPageBtn.disabled = currentPage <= 1;
        nextPageBtn.disabled = currentPage >= totalPages;
        
        // Hide pagination if only one page
        if (totalPages <= 1) {
            pagination.classList.add('hidden');
        } else {
            pagination.classList.remove('hidden');
        }
        
        // Show/hide rows based on current page
        paymentRows.forEach((row, index) => {
            const isInFilteredSet = rows.includes(row);
            const isInCurrentPage = index >= startIndex && index < endIndex;
            
            if (isInFilteredSet && rows.indexOf(row) >= startIndex && rows.indexOf(row) < endIndex) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Show/hide cards based on current page
        paymentCards.forEach((card, index) => {
            const isInFilteredSet = cards.includes(card);
            
            if (isInFilteredSet && cards.indexOf(card) >= startIndex && cards.indexOf(card) < endIndex) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    /**
     * Clear all filters
     */
    function clearFilters() {
        // Navigate to payment history page without any query parameters
        // This ensures we go to page 1 with no filters
        window.location.href = window.location.pathname;
    }
    
    /**
     * Go to previous page
     */
    function goToPreviousPage() {
        if (currentPage > 1) {
            currentPage--;
            applyFilters();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    
    /**
     * Go to next page
     */
    function goToNextPage() {
        const totalPages = Math.ceil(filteredPayments.length / ITEMS_PER_PAGE);
        if (currentPage < totalPages) {
            currentPage++;
            applyFilters();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    
    // Event listeners
    statusFilter.addEventListener('change', applyFilters);
    typeFilter.addEventListener('change', applyFilters);
    dateFilter.addEventListener('change', applyFilters);
    clearFiltersBtn.addEventListener('click', clearFilters);
    
    if (clearFiltersEmptyBtn) {
        clearFiltersEmptyBtn.addEventListener('click', clearFilters);
    }
    
    prevPageBtn.addEventListener('click', goToPreviousPage);
    nextPageBtn.addEventListener('click', goToNextPage);
    
    // Initialize on page load
    initializeFromURL();
});
