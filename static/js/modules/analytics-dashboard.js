/**
 * Analytics Dashboard Component
 * Displays performance monitoring and analytics data for tournament organizers
 */

class AnalyticsDashboard {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Analytics dashboard container '${containerId}' not found`);
        }
        
        this.options = {
            refreshInterval: 30000, // 30 seconds
            tournamentSlug: null,
            apiEndpoint: '/tournaments/analytics/dashboard/',
            ...options
        };
        
        this.data = null;
        this.charts = {};
        this.refreshTimer = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        console.log('Analytics Dashboard initialized');
        this.render();
        this.loadData();
        this.setupAutoRefresh();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="analytics-dashboard">
                <div class="dashboard-header">
                    <h2>Analytics Dashboard</h2>
                    <div class="dashboard-controls">
                        <select id="time-period" class="form-select">
                            <option value="1">Last 24 Hours</option>
                            <option value="7" selected>Last 7 Days</option>
                            <option value="30">Last 30 Days</option>
                        </select>
                        <button id="refresh-btn" class="btn btn-outline-primary">
                            <i class="material-symbols-outlined">refresh</i>
                            Refresh
                        </button>
                    </div>
                </div>
                
                <div class="dashboard-loading" id="dashboard-loading">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p>Loading analytics data...</p>
                </div>
                
                <div class="dashboard-content" id="dashboard-content" style="display: none;">
                    <!-- Overview Cards -->
                    <div class="row mb-4">
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="metric-icon">
                                    <i class="material-symbols-outlined">visibility</i>
                                </div>
                                <div class="metric-content">
                                    <div class="metric-value" id="total-views">-</div>
                                    <div class="metric-label">Total Views</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="metric-icon">
                                    <i class="material-symbols-outlined">people</i>
                                </div>
                                <div class="metric-content">
                                    <div class="metric-value" id="unique-visitors">-</div>
                                    <div class="metric-label">Unique Visitors</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="metric-icon">
                                    <i class="material-symbols-outlined">trending_up</i>
                                </div>
                                <div class="metric-content">
                                    <div class="metric-value" id="conversion-rate">-</div>
                                    <div class="metric-label">Conversion Rate</div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="metric-icon">
                                    <i class="material-symbols-outlined">speed</i>
                                </div>
                                <div class="metric-content">
                                    <div class="metric-value" id="avg-load-time">-</div>
                                    <div class="metric-label">Avg Load Time</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Charts Row -->
                    <div class="row mb-4">
                        <div class="col-md-8">
                            <div class="chart-card">
                                <h3>Daily Views & Conversions</h3>
                                <canvas id="daily-chart" width="400" height="200"></canvas>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="chart-card">
                                <h3>Device Breakdown</h3>
                                <canvas id="device-chart" width="200" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Performance Metrics -->
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="performance-card">
                                <h3>Performance Metrics</h3>
                                <div class="performance-metrics">
                                    <div class="performance-metric">
                                        <span class="metric-name">First Paint</span>
                                        <span class="metric-value" id="first-paint">-</span>
                                    </div>
                                    <div class="performance-metric">
                                        <span class="metric-name">Largest Contentful Paint</span>
                                        <span class="metric-value" id="lcp">-</span>
                                    </div>
                                    <div class="performance-metric">
                                        <span class="metric-name">Average Time on Page</span>
                                        <span class="metric-value" id="time-on-page">-</span>
                                    </div>
                                    <div class="performance-metric">
                                        <span class="metric-name">Bounce Rate</span>
                                        <span class="metric-value" id="bounce-rate">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="engagement-card">
                                <h3>Engagement Metrics</h3>
                                <div class="engagement-metrics">
                                    <div class="engagement-metric">
                                        <span class="metric-name">Total Clicks</span>
                                        <span class="metric-value" id="total-clicks">-</span>
                                    </div>
                                    <div class="engagement-metric">
                                        <span class="metric-name">Average Scroll Depth</span>
                                        <span class="metric-value" id="scroll-depth">-</span>
                                    </div>
                                    <div class="engagement-metric">
                                        <span class="metric-name">Error Rate</span>
                                        <span class="metric-value" id="error-rate">-</span>
                                    </div>
                                    <div class="engagement-metric">
                                        <span class="metric-name">Mobile Usage</span>
                                        <span class="metric-value" id="mobile-percentage">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recent Errors -->
                    <div class="row">
                        <div class="col-12">
                            <div class="errors-card">
                                <h3>Recent Errors</h3>
                                <div class="errors-list" id="errors-list">
                                    <p class="text-muted">No recent errors</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-error" id="dashboard-error" style="display: none;">
                    <div class="alert alert-danger">
                        <h4>Error Loading Analytics</h4>
                        <p id="error-message">Failed to load analytics data. Please try again.</p>
                        <button class="btn btn-danger" onclick="this.parentElement.parentElement.style.display='none'; window.analyticsDashboard.loadData();">
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Time period selector
        const timePeriodSelect = document.getElementById('time-period');
        timePeriodSelect.addEventListener('change', () => {
            this.loadData();
        });
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        refreshBtn.addEventListener('click', () => {
            this.loadData();
        });
    }
    
    async loadData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const days = document.getElementById('time-period').value;
            const url = this.buildApiUrl(days);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
            }
            
            this.data = result.data;
            this.updateDisplay();
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading analytics data:', error);
            this.showError(error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    buildApiUrl(days) {
        let url = this.options.apiEndpoint;
        if (this.options.tournamentSlug) {
            url = `/tournaments/${this.options.tournamentSlug}/analytics/dashboard/`;
        }
        return `${url}?days=${days}`;
    }
    
    updateDisplay() {
        if (!this.data) return;
        
        // Update overview metrics
        this.updateElement('total-views', this.formatNumber(this.data.overview.total_views));
        this.updateElement('unique-visitors', this.formatNumber(this.data.overview.unique_visitors));
        this.updateElement('conversion-rate', `${this.data.overview.conversion_rate}%`);
        this.updateElement('avg-load-time', `${this.data.performance.avg_load_time}ms`);
        
        // Update performance metrics
        this.updateElement('first-paint', `${this.data.performance.avg_first_paint}ms`);
        this.updateElement('lcp', `${this.data.performance.avg_largest_contentful_paint}ms`);
        this.updateElement('time-on-page', `${this.data.engagement.avg_time_on_page}s`);
        this.updateElement('bounce-rate', `${this.data.engagement.bounce_rate}%`);
        
        // Update engagement metrics
        this.updateElement('total-clicks', this.formatNumber(this.data.engagement.total_clicks));
        this.updateElement('scroll-depth', `${this.data.engagement.avg_scroll_depth}%`);
        this.updateElement('error-rate', `${this.data.overview.error_rate}%`);
        this.updateElement('mobile-percentage', `${this.data.overview.mobile_percentage}%`);
        
        // Update charts
        this.updateDailyChart();
        this.updateDeviceChart();
    }
    
    updateDailyChart() {
        const ctx = document.getElementById('daily-chart').getContext('2d');
        
        if (this.charts.daily) {
            this.charts.daily.destroy();
        }
        
        const labels = this.data.daily_data.map(d => new Date(d.date).toLocaleDateString());
        const viewsData = this.data.daily_data.map(d => d.views);
        const conversionsData = this.data.daily_data.map(d => d.conversions);
        
        this.charts.daily = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Views',
                    data: viewsData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Conversions',
                    data: conversionsData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    }
    
    updateDeviceChart() {
        const ctx = document.getElementById('device-chart').getContext('2d');
        
        if (this.charts.device) {
            this.charts.device.destroy();
        }
        
        const mobilePercentage = this.data.overview.mobile_percentage;
        const desktopPercentage = 100 - mobilePercentage;
        
        this.charts.device = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Desktop', 'Mobile'],
                datasets: [{
                    data: [desktopPercentage, mobilePercentage],
                    backgroundColor: ['#3b82f6', '#10b981'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    showLoading() {
        document.getElementById('dashboard-loading').style.display = 'block';
        document.getElementById('dashboard-content').style.display = 'none';
        document.getElementById('dashboard-error').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('dashboard-loading').style.display = 'none';
        document.getElementById('dashboard-content').style.display = 'block';
        document.getElementById('dashboard-error').style.display = 'none';
    }
    
    showError(message) {
        document.getElementById('error-message').textContent = message;
        document.getElementById('dashboard-loading').style.display = 'none';
        document.getElementById('dashboard-content').style.display = 'none';
        document.getElementById('dashboard-error').style.display = 'block';
    }
    
    setupAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadData();
        }, this.options.refreshInterval);
    }
    
    destroy() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        console.log('Analytics Dashboard destroyed');
    }
}

// Auto-initialize if container exists
document.addEventListener('DOMContentLoaded', () => {
    const dashboardContainer = document.getElementById('analytics-dashboard');
    if (dashboardContainer) {
        const tournamentSlug = dashboardContainer.dataset.tournamentSlug;
        window.analyticsDashboard = new AnalyticsDashboard('analytics-dashboard', {
            tournamentSlug: tournamentSlug
        });
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsDashboard;
}