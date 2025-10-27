document.addEventListener('DOMContentLoaded', function() {
    initializeProductDetail();
});

function initializeProductDetail() {
    initializeImageGallery();
    initializeQuantitySelector();
    initializeTabs();
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

function initializeImageGallery() {
    ProductInteractions.initializeImageGallery('mainProductImage');
}

function initializeQuantitySelector() {
    const quantityInput = document.getElementById('productQuantity');
    if (quantityInput) {
        quantityInput.addEventListener('input', validateQuantity);
        quantityInput.addEventListener('change', validateQuantity);
    }
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function() {
            if (typeof AOS !== 'undefined') {
                AOS.refresh();
            }
        });
    });
}

function changeMainImage(src) {
    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        mainImage.src = src;
        mainImage.style.opacity = '0';
        setTimeout(() => {
            mainImage.style.opacity = '1';
            mainImage.style.transition = 'opacity 0.3s ease';
        }, 150);
    }
}

function increaseQuantity() {
    const quantityInput = document.getElementById('productQuantity');
    if (!quantityInput) return;
    const maxQuantity = parseInt(quantityInput.getAttribute('max')) || 10;
    let currentQuantity = parseInt(quantityInput.value) || 1;
    if (currentQuantity < maxQuantity) {
        quantityInput.value = currentQuantity + 1;
        validateQuantity();
    } else {
        NotificationManager.showToast(`Maximum quantity is ${maxQuantity}`, 'warning');
    }
}

function decreaseQuantity() {
    const quantityInput = document.getElementById('productQuantity');
    if (!quantityInput) return;
    let currentQuantity = parseInt(quantityInput.value) || 1;
    if (currentQuantity > 1) {
        quantityInput.value = currentQuantity - 1;
        validateQuantity();
    }
}

function validateQuantity() {
    const quantityInput = document.getElementById('productQuantity');
    if (!quantityInput) return;
    const maxQuantity = parseInt(quantityInput.getAttribute('max')) || 10;
    const minQuantity = parseInt(quantityInput.getAttribute('min')) || 1;
    let currentQuantity = parseInt(quantityInput.value) || 1;
    if (isNaN(currentQuantity) || currentQuantity < minQuantity) {
        quantityInput.value = minQuantity;
    } else if (currentQuantity > maxQuantity) {
        quantityInput.value = maxQuantity;
        NotificationManager.showToast(`Maximum quantity is ${maxQuantity}`, 'warning');
    }
}

function addToCartFromDetail(productId) {
    const quantityInput = document.getElementById('productQuantity');
    const quantity = quantityInput ? parseInt(quantityInput.value) : 1;
    const button = document.querySelector('.btn-dark.btn-lg');
    if (!button) return;
    ProductInteractions.addToCart(productId, button, quantity);
}

function addToWishlistFromDetail(productId, button) {
    ProductInteractions.addToWishlist(productId, button);
}

function shareProduct(platform) {
    const productUrl = window.location.href;
    const productTitle = document.querySelector('.product-title')?.textContent || 'Check out this product';
    const productImage = document.getElementById('mainProductImage')?.src || '';
    let shareUrl = '';
    switch(platform) {
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(productUrl)}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(productTitle)}&url=${encodeURIComponent(productUrl)}`;
            break;
        case 'pinterest':
            shareUrl = `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(productUrl)}&description=${encodeURIComponent(productTitle)}&media=${encodeURIComponent(productImage)}`;
            break;
        case 'whatsapp':
            shareUrl = `https://wa.me/?text=${encodeURIComponent(productTitle + ' ' + productUrl)}`;
            break;
    }
    if (shareUrl) {
        window.open(shareUrl, '_blank', 'width=600,height=400');
    }
}

function submitNotifyRequest() {
    const emailInput = document.getElementById('notifyEmail');
    const email = emailInput?.value;
    if (!email) {
        NotificationManager.showToast('Please enter your email address', 'error');
        return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        NotificationManager.showToast('Please enter a valid email address', 'error');
        return;
    }
    NotificationManager.showToast('We will notify you when this product is available!', 'success');
    const modal = bootstrap.Modal.getInstance(document.getElementById('notifyModal'));
    if (modal) {
        modal.hide();
    }
    if (emailInput) {
        emailInput.value = '';
    }
}

function getCSRFToken() {
    return ApiClient.getCSRFToken();
}

function updateCartCount(count) {
    CountManager.updateCartCount(count);
}

function updateWishlistCount(count) {
    CountManager.updateWishlistCount(count);
}

function showToast(message, type = 'info') {
    NotificationManager.showToast(message, type);
}

function showLoginAlert(event) {
    ProductInteractions.showLoginAlert(event);
}

document.addEventListener('keydown', function(event) {
    const quantityInput = document.getElementById('productQuantity');
    if (document.activeElement === quantityInput) {
        if (event.key === 'ArrowUp') {
            event.preventDefault();
            increaseQuantity();
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            decreaseQuantity();
        }
    }
});

const style = document.createElement('style');
style.textContent = `
    .pulse {
        animation: pulse 0.6s ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .btn.active {
        background-color: #ff6b6b !important;
        border-color: #ff6b6b !important;
        color: white !important;
    }
    .thumbnail-item.active .thumbnail-img {
        border-color: #0d6efd !important;
        box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.25);
    }
`;
document.head.appendChild(style);

console.log('Product detail page JavaScript initialized');