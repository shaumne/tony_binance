// Binance Trading Bot - Dashboard JavaScript

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Real-time clock
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const dateString = now.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
    
    const clockEl = document.getElementById('live-clock');
    if (clockEl) {
        clockEl.textContent = `${dateString} ${timeString}`;
    }
}

setInterval(updateClock, 1000);
updateClock();

// Confirm close position
function confirmClose(symbol, side) {
    return confirm(`Are you sure you want to close the ${side} position for ${symbol}?`);
}

// Number formatting
function formatNumber(num, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    const container = document.querySelector('.flash-container') || createFlashContainer();
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
    return container;
}

// Loading state
function setLoading(button, loading = true) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Calculate PnL percentage
function calculatePnlPercentage(entry, current, side) {
    const diff = side.toLowerCase() === 'long' ? current - entry : entry - current;
    return (diff / entry) * 100;
}

// Websocket connection for real-time updates (optional enhancement)
function connectWebSocket() {
    // This would connect to a WebSocket endpoint for real-time price updates
    // Implementation would depend on your backend setup
    console.log('WebSocket connection ready for real-time updates');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Binance Trading Bot Dashboard Loaded');
    
    // Add smooth scroll
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + R to refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            // Allow default browser refresh
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
});

function closeAllModals() {
    // Close any open modals
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// Export functions for global use
window.confirmClose = confirmClose;
window.copyToClipboard = copyToClipboard;
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;

