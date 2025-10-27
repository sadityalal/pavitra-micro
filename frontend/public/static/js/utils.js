function getCSRFToken() {
    return ApiClient.getCSRFToken();
}

function showToast(message, type = 'success') {
    NotificationManager.showToast(message, type);
}

function formatPrice(price) {
    return DOMUtils.formatPrice(price);
}

function debounce(func, wait) {
    return DOMUtils.debounce(func, wait);
}