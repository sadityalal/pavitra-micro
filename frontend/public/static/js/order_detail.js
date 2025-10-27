document.addEventListener('DOMContentLoaded', function() {
    initializeOrderDetailPage();
});

function initializeOrderDetailPage() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 600,
            once: true,
            offset: 100
        });
    }
    console.log('Order detail page initialized');
}

function cancelOrder(orderNumber) {
    if (!confirm('Are you sure you want to cancel this order? This action cannot be undone.')) {
        return;
    }
    const csrfToken = ApiClient.getCSRFToken();
    fetch(`/account/order/${orderNumber}/cancel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            NotificationManager.showToast('Order cancelled successfully', 'success');
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.href = '/account?tab=orders';
                }
            }, 2000);
        } else {
            NotificationManager.showToast(data.message || 'Failed to cancel order', 'danger');
        }
    })
    .catch(error => {
        console.error('Error cancelling order:', error);
        NotificationManager.showToast('Error cancelling order. Please try again.', 'danger');
    });
}

function requestReturn(orderNumber) {
    if (!confirm('Would you like to request a return for this order?')) {
        return;
    }
    NotificationManager.showToast('Return request feature coming soon!', 'info');
}

function printOrder() {
    window.print();
}

document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        printOrder();
    }
    if (e.key === 'Escape') {
        window.history.back();
    }
});

window.cancelOrder = cancelOrder;
window.requestReturn = requestReturn;
window.printOrder = printOrder;