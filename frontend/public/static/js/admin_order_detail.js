class AdminOrderDetail {
    constructor() {
        this.orderId = window.location.pathname.split('/').pop();
        this.init();
    }
    init() {
        this.initializeEventListeners();
        this.loadOrderHistory();
        console.log('Admin Order Detail initialized for order:', this.orderId);
    }
    initializeEventListeners() {
        const statusForm = document.getElementById('statusUpdateForm');
        if (statusForm) {
            statusForm.addEventListener('submit', (e) => this.updateOrderStatus(e));
        }
        const noteForm = document.getElementById('adminNoteForm');
        if (noteForm) {
            noteForm.addEventListener('submit', (e) => this.saveAdminNote(e));
        }
        const cancelForm = document.getElementById('cancelOrderForm');
        if (cancelForm) {
            cancelForm.addEventListener('submit', (e) => this.cancelOrder(e));
        }
        const markAsPaidBtn = document.getElementById('markAsPaid');
        if (markAsPaidBtn) {
            markAsPaidBtn.addEventListener('click', () => this.markAsPaid());
        }
        const sendTrackingBtn = document.getElementById('sendTrackingEmail');
        if (sendTrackingBtn) {
            sendTrackingBtn.addEventListener('click', () => this.sendTrackingEmail());
        }
        this.setupRealTimeUpdates();
    }
    async updateOrderStatus(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const newStatus = formData.get('status');
        try {
            const response = await fetch(`/admin/orders/${this.orderId}/update-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `status=${encodeURIComponent(newStatus)}`
            });
            if (response.ok) {
                this.showAlert('Order status updated successfully!', 'success');
                this.refreshOrderData();
            } else {
                throw new Error('Failed to update status');
            }
        } catch (error) {
            console.error('Error updating order status:', error);
            this.showAlert('Error updating order status. Please try again.', 'danger');
        }
    }
    async saveAdminNote(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const adminNote = formData.get('admin_note');
        try {
            const response = await fetch(`/admin/orders/${this.orderId}/admin-note`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ admin_note: adminNote })
            });
            if (response.ok) {
                this.showAlert('Admin note saved successfully!', 'success');
            } else {
                throw new Error('Failed to save note');
            }
        } catch (error) {
            console.error('Error saving admin note:', error);
            this.showAlert('Error saving admin note. Please try again.', 'danger');
        }
    }
    async cancelOrder(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const reason = formData.get('reason');
        try {
            const response = await fetch(`/admin/orders/${this.orderId}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ reason: reason })
            });
            if (response.ok) {
                this.showAlert('Order cancelled successfully!', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('cancelOrderModal'));
                modal.hide();
                this.refreshOrderData();
            } else {
                throw new Error('Failed to cancel order');
            }
        } catch (error) {
            console.error('Error cancelling order:', error);
            this.showAlert('Error cancelling order. Please try again.', 'danger');
        }
    }
    async markAsPaid() {
        if (!confirm('Mark this order as paid?')) return;
        try {
            const response = await fetch(`/admin/orders/${this.orderId}/mark-paid`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            if (response.ok) {
                this.showAlert('Order marked as paid successfully!', 'success');
                this.refreshOrderData();
            } else {
                throw new Error('Failed to mark as paid');
            }
        } catch (error) {
            console.error('Error marking order as paid:', error);
            this.showAlert('Error marking order as paid. Please try again.', 'danger');
        }
    }
    async sendTrackingEmail() {
        try {
            const response = await fetch(`/admin/orders/${this.orderId}/send-tracking`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            if (response.ok) {
                this.showAlert('Tracking email sent successfully!', 'success');
            } else {
                throw new Error('Failed to send tracking email');
            }
        } catch (error) {
            console.error('Error sending tracking email:', error);
            this.showAlert('Error sending tracking email. Please try again.', 'danger');
        }
    }
    async loadOrderHistory() {
        try {
            const response = await fetch(`/admin/api/orders/${this.orderId}/history`);
            if (response.ok) {
                const history = await response.json();
                this.updateOrderHistoryDisplay(history);
            }
        } catch (error) {
            console.error('Error loading order history:', error);
        }
    }
    updateOrderHistoryDisplay(history) {
        console.log('Order history loaded:', history);
    }
    refreshOrderData() {
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    }
    setupRealTimeUpdates() {
        setInterval(() => {
            this.checkOrderUpdates();
        }, 30000);
    }
    async checkOrderUpdates() {
        try {
            const response = await fetch(`/admin/api/orders/${this.orderId}/status`);
            if (response.ok) {
                const data = await response.json();
                this.updateStatusIndicators(data);
            }
        } catch (error) {
            console.error('Error checking order updates:', error);
        }
    }
    updateStatusIndicators(data) {
        const statusBadge = document.querySelector('.badge.bg-warning, .badge.bg-info, .badge.bg-primary, .badge.bg-secondary, .badge.bg-success, .badge.bg-danger');
        const paymentBadge = document.querySelectorAll('.badge.bg-warning, .badge.bg-info, .badge.bg-primary, .badge.bg-secondary, .badge.bg-success, .badge.bg-danger')[1];
        if (statusBadge) {
            statusBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            statusBadge.className = `badge ${this.getStatusBadgeClass(data.status)} fs-6`;
        }
        if (paymentBadge) {
            paymentBadge.textContent = data.payment_status.charAt(0).toUpperCase() + data.payment_status.slice(1);
            paymentBadge.className = `badge ${this.getPaymentStatusBadgeClass(data.payment_status)} fs-6`;
        }
    }
    getStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning',
            'confirmed': 'bg-info',
            'processing': 'bg-primary',
            'shipped': 'bg-secondary',
            'delivered': 'bg-success',
            'cancelled': 'bg-danger'
        };
        return classes[status] || 'bg-secondary';
    }
    getPaymentStatusBadgeClass(status) {
        const classes = {
            'pending': 'bg-warning',
            'paid': 'bg-success',
            'failed': 'bg-danger',
            'refunded': 'bg-info'
        };
        return classes[status] || 'bg-secondary';
    }
    showAlert(message, type) {
        const existingAlerts = document.querySelectorAll('.alert-dismissible');
        existingAlerts.forEach(alert => alert.remove());
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}-fill me-2"></i>
                <div>${message}</div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        const contentArea = document.querySelector('.admin-content');
        if (contentArea) {
            contentArea.insertBefore(alert, contentArea.firstChild);
        }
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    new AdminOrderDetail();
});

window.AdminOrderUtils = {
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    },
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    getStatusColor: function(status) {
        const colors = {
            'pending': '#ffc107',
            'confirmed': '#0dcaf0',
            'processing': '#0d6efd',
            'shipped': '#6c757d',
            'delivered': '#198754',
            'cancelled': '#dc3545'
        };
        return colors[status] || '#6c757d';
    }
};