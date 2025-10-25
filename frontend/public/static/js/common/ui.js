//NotificationManager
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        this.removeExistingNotifications();

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification position-fixed`;
        notification.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        const icon = this.getIconForType(type);
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-${icon} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
            </div>
        `;

        document.body.appendChild(notification);

        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }

        return notification;
    }

    static getIconForType(type) {
        const icons = {
            success: 'check-circle-fill',
            error: 'exclamation-circle-fill',
            warning: 'exclamation-triangle-fill',
            info: 'info-circle-fill',
            danger: 'exclamation-circle-fill'
        };
        return icons[type] || 'info-circle-fill';
    }

    static removeExistingNotifications() {
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
    }

    static showToast(message, type = 'info') {
        return this.show(message, type, 3000);
    }
}

class DOMUtils {
    static addSafeEventListener(elementId, event, handler) {
        const element = document.getElementById(elementId);
        if (element) {
            element.addEventListener(event, handler);
        }
    }
    static debounce(func, wait) {
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

    static animateElement(element, animationClass, removeAfter = false) {
        element.classList.add(animationClass);
        setTimeout(() => {
            element.classList.remove(animationClass);
            if (removeAfter) {
                element.remove();
            }
        }, 600);
    }

    static formatPrice(price) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2
        }).format(price);
    }

    static formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static setLoadingState(button, isLoading) {
        if (isLoading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Loading...';
        } else {
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
                button.removeAttribute('data-original-text');
            }
        }
    }

    static updateCounter(element, count) {
        if (!element) return;
        element.textContent = count;
        this.animateElement(element, 'pulse');
    }
}

class CountManager {
    static updateCartCount(count) {
        const cartCountElements = document.querySelectorAll('#cart-count, .cart-count, [data-cart-count]');
        cartCountElements.forEach(element => {
            DOMUtils.updateCounter(element, count);
        });
        window.dispatchEvent(new CustomEvent('cartCountUpdated', { detail: { count } }));
    }

    static updateWishlistCount(count) {
        const wishlistCountElements = document.querySelectorAll('#wishlist-count, .wishlist-count, .user_wishlist_count');
        wishlistCountElements.forEach(element => {
            DOMUtils.updateCounter(element, count);
        });
    }

    static async refreshCounts() {
        try {
            const [cartData, wishlistData] = await Promise.all([
                CartAPI.getCartCount(),
                WishlistAPI.getWishlistCount()
            ]);

            this.updateCartCount(cartData.count);
            this.updateWishlistCount(wishlistData.count);
        } catch (error) {
            console.error('Error refreshing counts:', error);
        }
    }
}

// Initialize global styles
const globalStyles = document.createElement('style');
globalStyles.textContent = `
    .pulse {
        animation: pulse 0.6s ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    .spinner {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(globalStyles);

window.NotificationManager = NotificationManager;
window.DOMUtils = DOMUtils;
window.CountManager = CountManager;