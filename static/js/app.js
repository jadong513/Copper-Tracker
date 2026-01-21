// Copper Price Tracker - Frontend JavaScript

let priceChart = null;
let refreshInterval = null;
let currentPeriod = '1mo';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initChart();
    fetchCurrentPrice();
    fetchPriceHistory(currentPeriod);
    fetchAlerts();
    setupEventListeners();
    startAutoRefresh();
    checkTriggeredAlerts();
});

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Raw Copper ($/lb)',
                    data: [],
                    borderColor: '#6c757d',
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    tension: 0.1,
                    fill: false
                },
                {
                    label: '16oz Sheet ($/lb)',
                    data: [],
                    borderColor: '#b87333',
                    backgroundColor: 'rgba(184, 115, 51, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Coil ($/lb)',
                    data: [],
                    borderColor: '#17a2b8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    tension: 0.1,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(4);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

// Show/hide error banner
function showError(message) {
    const banner = document.getElementById('error-banner');
    const errorMsg = document.getElementById('error-message');
    errorMsg.textContent = message;
    banner.classList.remove('d-none');
}

function hideError() {
    const banner = document.getElementById('error-banner');
    banner.classList.add('d-none');
}

// Fetch current price
async function fetchCurrentPrice() {
    try {
        const response = await fetch('/api/price/current');
        const data = await response.json();

        if (data.error) {
            console.error('Error fetching price:', data.error);
            showError('Unable to fetch price data from Yahoo Finance. Markets may be closed or there may be a connection issue.');
            document.getElementById('last-updated').textContent = 'Error loading data';
            return;
        }

        // Hide error banner on success
        hideError();

        // Update price displays
        document.getElementById('raw-price').textContent = '$' + data.raw_price.toFixed(4);
        document.getElementById('sheet-price').textContent = '$' + data.sheet_price.toFixed(4);
        document.getElementById('coil-price').textContent = '$' + data.coil_price.toFixed(4);

        // Update change info
        if (data.change) {
            const changeEl = document.getElementById('price-change');
            const changePercentEl = document.getElementById('price-change-percent');
            const prevEl = document.getElementById('previous-close');

            const isUp = data.change.change >= 0;
            const sign = isUp ? '+' : '';

            changeEl.textContent = sign + '$' + data.change.change.toFixed(4);
            changeEl.className = 'ms-2 fs-5 ' + (isUp ? 'price-up' : 'price-down');

            changePercentEl.textContent = '(' + sign + data.change.change_percent.toFixed(2) + '%)';
            changePercentEl.className = 'ms-1 badge ' + (isUp ? 'badge-up' : 'badge-down');

            prevEl.textContent = '$' + data.change.previous.toFixed(4);
        }

        // Update timestamp
        document.getElementById('last-updated').textContent =
            'Updated: ' + new Date().toLocaleTimeString();

    } catch (error) {
        console.error('Error fetching current price:', error);
        showError('Network error. Please check your connection and try again.');
        document.getElementById('last-updated').textContent = 'Connection error';
    }
}

// Fetch price history
async function fetchPriceHistory(period) {
    try {
        const response = await fetch(`/api/price/history?period=${period}`);
        const data = await response.json();

        if (!data.records || data.records.length === 0) {
            console.warn('No historical data available');
            return;
        }

        // Update chart
        const labels = data.records.map(r => {
            const date = new Date(r.timestamp);
            if (period === '1d') {
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        });

        priceChart.data.labels = labels;
        priceChart.data.datasets[0].data = data.records.map(r => r.raw_price);
        priceChart.data.datasets[1].data = data.records.map(r => r.sheet_price);
        priceChart.data.datasets[2].data = data.records.map(r => r.coil_price);
        priceChart.update();

    } catch (error) {
        console.error('Error fetching price history:', error);
    }
}

// Fetch alerts
async function fetchAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const alerts = await response.json();
        renderAlerts(alerts);
    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}

// Render alerts list
function renderAlerts(alerts) {
    const list = document.getElementById('alerts-list');

    if (alerts.length === 0) {
        list.innerHTML = '<li class="list-group-item text-muted">No alerts configured</li>';
        return;
    }

    list.innerHTML = alerts.map(alert => `
        <li class="list-group-item alert-item ${alert.is_active ? '' : 'inactive'}">
            <div class="alert-info">
                <strong>${formatPriceType(alert.price_type)}</strong>
                ${alert.condition} $${alert.threshold.toFixed(2)}
                ${alert.triggered_at ? '<span class="badge bg-warning ms-2">Triggered</span>' : ''}
            </div>
            <div class="alert-actions">
                <button class="btn btn-sm btn-outline-secondary" onclick="toggleAlert(${alert.id})">
                    ${alert.is_active ? 'Disable' : 'Enable'}
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteAlert(${alert.id})">
                    Delete
                </button>
            </div>
        </li>
    `).join('');
}

// Format price type for display
function formatPriceType(type) {
    const types = {
        'raw': 'Raw Copper',
        'sheet': '16oz Sheet',
        'coil': 'Coil'
    };
    return types[type] || type;
}

// Create alert
async function createAlert(priceType, condition, threshold) {
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                price_type: priceType,
                condition: condition,
                threshold: threshold
            })
        });

        if (response.ok) {
            fetchAlerts();
        }
    } catch (error) {
        console.error('Error creating alert:', error);
    }
}

// Toggle alert
async function toggleAlert(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/toggle`, { method: 'POST' });
        if (response.ok) {
            fetchAlerts();
        }
    } catch (error) {
        console.error('Error toggling alert:', error);
    }
}

// Delete alert
async function deleteAlert(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
        if (response.ok) {
            fetchAlerts();
        }
    } catch (error) {
        console.error('Error deleting alert:', error);
    }
}

// Check for triggered alerts
async function checkTriggeredAlerts() {
    try {
        const response = await fetch('/api/alerts/triggered');
        const alerts = await response.json();

        if (alerts.length > 0) {
            const banner = document.getElementById('alert-banner');
            const message = document.getElementById('alert-message');
            message.textContent = alerts.map(a => a.message).join(' | ');
            banner.classList.remove('d-none');
            fetchAlerts();
        }
    } catch (error) {
        console.error('Error checking triggered alerts:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Period buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.dataset.period;
            fetchPriceHistory(currentPeriod);
        });
    });

    // Alert form
    document.getElementById('alert-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const priceType = document.getElementById('alert-type').value;
        const condition = document.getElementById('alert-condition').value;
        const threshold = parseFloat(document.getElementById('alert-threshold').value);

        createAlert(priceType, condition, threshold);
        this.reset();
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', function() {
        fetchCurrentPrice();
        fetchPriceHistory(currentPeriod);
    });

    // Refresh interval
    document.getElementById('refresh-interval').addEventListener('change', function() {
        startAutoRefresh();
    });
}

// Start auto-refresh
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    const interval = parseInt(document.getElementById('refresh-interval').value);

    if (interval > 0) {
        refreshInterval = setInterval(() => {
            fetchCurrentPrice();
            checkTriggeredAlerts();
        }, interval);
    }
}
