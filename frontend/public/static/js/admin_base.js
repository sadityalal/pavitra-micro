class AdminPanel {
    constructor() {
        this.init();
    }
    init() {
        if (typeof AOS !== 'undefined') {
            AOS.init({
                duration: 800,
                easing: 'ease-in-out',
                once: true
            });
        }
        this.loadAdminStats();
        this.initEventListeners();
        console.log('Admin panel initialized');
    }
    initEventListeners() {
        this.autoDismissAlerts();
        this.initConfirmations();
        setInterval(() => {
            this.loadAdminStats();
        }, 30000);
    }
    autoDismissAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert && alert.parentNode) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        });
    }
    initConfirmations() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-confirm]') || e.target.closest('[data-confirm]')) {
                const element = e.target.matches('[data-confirm]') ? e.target : e.target.closest('[data-confirm]');
                const message = element.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
                if (!confirm(message)) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    return false;
                }
            }
        });
    }
    async loadAdminStats() {
        try {
            const response = await fetch('/admin/api/admin/stats');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.updateStatsDisplay(data);
        } catch (error) {
            console.log('Could not fetch admin stats:', error);
            this.updateStatsDisplay({
                pending_orders: 0,
                today_orders: 0,
                today_revenue: 0
            });
        }
    }
    updateStatsDisplay(data) {
        const pendingOrdersEl = document.getElementById('pending-orders-count');
        if (pendingOrdersEl && data.pending_orders !== undefined) {
            pendingOrdersEl.textContent = data.pending_orders;
            this.animateCounter(pendingOrdersEl, data.pending_orders);
        }
        const todayOrdersEl = document.getElementById('today-orders');
        if (todayOrdersEl && data.today_orders !== undefined) {
            todayOrdersEl.textContent = data.today_orders;
        }
        const todayRevenueEl = document.getElementById('today-revenue');
        if (todayRevenueEl && data.today_revenue !== undefined) {
            todayRevenueEl.textContent = '₹' + this.formatNumber(data.today_revenue);
        }
    }
    animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (currentValue === targetValue) return;
        const duration = 500;
        const steps = 20;
        const stepTime = duration / steps;
        const increment = (targetValue - currentValue) / steps;
        let currentStep = 0;
        const timer = setInterval(() => {
            currentStep++;
            const value = Math.round(currentValue + (increment * currentStep));
            element.textContent = value;
            if (currentStep >= steps) {
                element.textContent = targetValue;
                clearInterval(timer);
            }
        }, stepTime);
    }
    formatNumber(num) {
        return parseInt(num).toLocaleString('en-IN');
    }
    showLoading(element) {
        if (element) {
            element.disabled = true;
            const originalText = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            element.setAttribute('data-original-text', originalText);
        }
    }
    hideLoading(element) {
        if (element && element.hasAttribute('data-original-text')) {
            element.disabled = false;
            element.innerHTML = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }
    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
        toast.show();
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
    handleBulkAction(action, selectedIds) {
        if (!selectedIds || selectedIds.length === 0) {
            this.showToast('Please select items to perform this action', 'warning');
            return;
        }
        const confirmationMessage = {
            'delete': 'Are you sure you want to delete the selected items? This action cannot be undone.',
            'publish': 'Are you sure you want to publish the selected items?',
            'unpublish': 'Are you sure you want to unpublish the selected items?',
            'feature': 'Are you sure you want to feature the selected items?',
            'unfeature': 'Are you sure you want to remove featured status from selected items?'
        }[action] || 'Are you sure you want to perform this action?';
        if (confirm(confirmationMessage)) {
            console.log(`Performing ${action} on:`, selectedIds);
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.adminPanel = new AdminPanel();
});

const AdminUtils = {
    formatPrice(price) {
        return '₹' + parseFloat(price).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },
    formatDate(dateString) {
        const options = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('en-IN', options);
    },
    getStatusBadge(status) {
        const statusConfig = {
            'active': { class: 'success', text: 'Active' },
            'inactive': { class: 'secondary', text: 'Inactive' },
            'pending': { class: 'warning', text: 'Pending' },
            'completed': { class: 'success', text: 'Completed' },
            'cancelled': { class: 'danger', text: 'Cancelled' },
            'processing': { class: 'info', text: 'Processing' },
            'shipped': { class: 'primary', text: 'Shipped' },
            'delivered': { class: 'success', text: 'Delivered' },
            'published': { class: 'success', text: 'Published' },
            'draft': { class: 'secondary', text: 'Draft' }
        };
        const config = statusConfig[status] || { class: 'secondary', text: status };
        return `<span class="badge bg-${config.class}">${config.text}</span>`;
    },
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

window.AdminUtils = AdminUtils;