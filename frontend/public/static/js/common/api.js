//api.js
class ApiClient {
    static async request(url, options = {}) {
        const csrfToken = this.getCSRFToken();

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'same-origin'
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);

            if (response.status === 403) {
                throw new Error('CSRF token missing or invalid');
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) return metaTag.getAttribute('content');

        const inputTag = document.querySelector('input[name="csrf_token"]');
        if (inputTag) return inputTag.value;

        console.error('CSRF token not found');
        return '';
    }

    static async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async get(url) {
        return this.request(url, { method: 'GET' });
    }
}

class CartAPI {
    static async addToCart(productId, quantity = 1) {
        return ApiClient.post('/add-to-cart', {
            product_id: parseInt(productId),
            quantity: quantity
        });
    }

    static async removeFromCart(itemId) {
        // FIXED: Use the correct URL pattern
        return ApiClient.post(`/cart/remove/${itemId}`);
    }

    static async updateCartQuantity(itemId, action) {
        // FIXED: Ensure proper parameter names
        return ApiClient.post('/cart/update', {
            item_id: parseInt(itemId),
            action: action
        });
    }

    static async clearCart() {
        return ApiClient.post('/cart/clear');
    }

    static async getCartCount() {
        return ApiClient.get('/api/cart-count');
    }
}

class WishlistAPI {
    static async addToWishlist(productId) {
        return ApiClient.post('/add-to-wishlist', {
            product_id: parseInt(productId)
        });
    }

    static async removeFromWishlist(itemId) {
        return ApiClient.post('/remove-from-wishlist', {
            item_id: parseInt(itemId)
        });
    }

    static async getWishlistCount() {
        return ApiClient.get('/api/wishlist-count');
    }
}

class ProductAPI {
    static async getProducts(filters = {}) {
        const params = new URLSearchParams(filters);
        return ApiClient.get(`/api/products?${params}`);
    }

    static async getProductDetails(productId) {
        return ApiClient.get(`/api/products/${productId}`);
    }
}

window.ApiClient = ApiClient;
window.CartAPI = CartAPI;
window.WishlistAPI = WishlistAPI;
window.ProductAPI = ProductAPI;