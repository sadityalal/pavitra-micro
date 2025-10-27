// static/js/cart.js - Complete Working Version with Coupon Support & Guest User Fix
class CartManager {
    constructor() {
        this.isAuthenticated = document.body.classList.contains('user-authenticated');
        this.init();
    }

    init() {
        console.log('🛒 Cart Manager initialized - User:', this.isAuthenticated ? 'Authenticated' : 'Guest');
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Quantity buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quantity-btn')) {
                this.handleQuantityChange(e);
            }
        });

        // Remove buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.remove-item-btn')) {
                this.handleRemoveItem(e);
            }
        });

        // Clear cart button
        const clearCartBtn = document.getElementById('clearCartBtn');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => this.handleClearCart());
        }

        // Coupon events
        document.addEventListener('click', (e) => {
            if (e.target.closest('#applyCouponBtn')) {
                this.handleApplyCoupon();
            }
            if (e.target.closest('#removeCouponBtn')) {
                this.handleRemoveCoupon();
            }
        });

        // Enter key for coupon input
        const couponInput = document.getElementById('couponCode');
        if (couponInput) {
            couponInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleApplyCoupon();
                }
            });
        }
    }

    async handleQuantityChange(e) {
        e.preventDefault();
        const button = e.target.closest('.quantity-btn');
        const action = button.getAttribute('data-action');
        const quantityForm = button.closest('.quantity-form');
        const itemId = quantityForm.getAttribute('data-item-id');
        const quantityDisplay = quantityForm.querySelector('.quantity-display');
        const currentQuantity = parseInt(quantityDisplay.textContent);

        console.log(`🔄 Quantity change: itemId=${itemId}, action=${action}, currentQuantity=${currentQuantity}, User: ${this.isAuthenticated ? 'Auth' : 'Guest'}`);

        // Handle decrease to zero (remove item)
        if (action === 'decrease' && currentQuantity === 1) {
            if (confirm('Remove this item from cart?')) {
                await this.removeItem(itemId, quantityForm.closest('.cart-item'));
            }
            return;
        }

        try {
            const response = await fetch('/cart/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    item_id: parseInt(itemId),
                    action: action
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update quantity display
                const newQuantity = action === 'increase' ? currentQuantity + 1 : currentQuantity - 1;
                quantityDisplay.textContent = newQuantity;

                // Update item total
                this.updateItemTotal(quantityForm, newQuantity);

                // Update cart totals
                this.updateCartTotals();

                // Update cart count
                this.updateCartCount(data.cart_count);

                NotificationManager.show('Cart updated successfully', 'success');
            } else {
                NotificationManager.show(data.message || 'Failed to update cart', 'error');
            }
        } catch (error) {
            console.error('Error updating cart:', error);
            NotificationManager.show('Error updating cart. Please try again.', 'error');
        }
    }

    async handleRemoveItem(e) {
        e.preventDefault();
        const button = e.target.closest('.remove-item-btn');
        const itemId = button.getAttribute('data-item-id');
        const cartItem = button.closest('.cart-item');

        if (!confirm('Are you sure you want to remove this item from cart?')) {
            return;
        }

        await this.removeItem(itemId, cartItem);
    }

    async removeItem(itemId, cartItemElement) {
        try {
            console.log(`🗑️ Removing item: ${itemId}, User: ${this.isAuthenticated ? 'Auth' : 'Guest'}`);

            const response = await fetch(`/cart/remove/${itemId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                // Remove from DOM with animation
                cartItemElement.style.opacity = '0';
                cartItemElement.style.transform = 'translateX(-100px)';
                cartItemElement.style.transition = 'all 0.3s ease';

                setTimeout(() => {
                    cartItemElement.remove();

                    // CRITICAL FIX: Update remaining item IDs for guest users
                    if (!this.isAuthenticated) {
                        this.updateGuestItemIds();
                    }

                    this.updateCartDisplay();
                    this.updateCartCount(data.cart_count);
                    NotificationManager.show('Item removed from cart', 'success');
                }, 300);
            } else {
                NotificationManager.show(data.message || 'Failed to remove item', 'error');
            }
        } catch (error) {
            console.error('Error removing item:', error);
            NotificationManager.show('Error removing item. Please try again.', 'error');
        }
    }

    // CRITICAL FIX: Update guest user item IDs after removal
    updateGuestItemIds() {
        const cartItems = document.querySelectorAll('.cart-item');
        console.log(`🔄 Updating ${cartItems.length} guest item IDs...`);

        cartItems.forEach((item, newIndex) => {
            const newId = newIndex.toString();

            // Update cart item
            item.setAttribute('data-item-id', newId);

            // Update quantity form
            const quantityForm = item.querySelector('.quantity-form');
            if (quantityForm) {
                quantityForm.setAttribute('data-item-id', newId);
            }

            // Update remove button
            const removeBtn = item.querySelector('.remove-item-btn');
            if (removeBtn) {
                removeBtn.setAttribute('data-item-id', newId);
            }

            console.log(`Updated item ${newIndex} with ID: ${newId}`);
        });

        console.log('✅ Guest item IDs updated successfully');
    }

    async handleClearCart() {
        if (!confirm('Are you sure you want to clear your entire cart? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch('/cart/clear', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showEmptyCartState();
                this.updateCartCount(0);
                NotificationManager.show('Cart cleared successfully', 'success');
            } else {
                NotificationManager.show(data.message || 'Failed to clear cart', 'error');
            }
        } catch (error) {
            console.error('Error clearing cart:', error);
            NotificationManager.show('Error clearing cart. Please try again.', 'error');
        }
    }

    async handleApplyCoupon() {
    const couponInput = document.getElementById('couponCode');
    const couponMessage = document.getElementById('couponMessage');
    const applyBtn = document.getElementById('applyCouponBtn');

    if (!couponInput || !couponMessage) return;

    const couponCode = couponInput.value.trim().toUpperCase();

    if (!couponCode) {
        this.showCouponMessage('Please enter a coupon code', 'error');
        return;
    }

    // Show loading state
    applyBtn.disabled = true;
    applyBtn.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Applying...';

    try {
        // FIX: Change URL from '/apply-coupon' to '/cart/apply-coupon'
        const response = await fetch('/cart/apply-coupon', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ coupon_code: couponCode })
        });

        const data = await response.json();

        if (data.success) {
            this.showCouponMessage(data.message, 'success');
            // Reload page to show updated totals
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            this.showCouponMessage(data.message, 'error');
        }
    } catch (error) {
        console.error('Error applying coupon:', error);
        this.showCouponMessage('Error applying coupon', 'error');
    } finally {
        // Reset button state
        applyBtn.disabled = false;
        applyBtn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Apply';
    }
}

    async handleRemoveCoupon() {
    const removeBtn = document.getElementById('removeCouponBtn');

    if (!removeBtn) return;

    // Show loading state
    removeBtn.disabled = true;
    removeBtn.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Removing...';

    try {
        // FIX: Change URL from '/remove-coupon' to '/cart/remove-coupon'
        const response = await fetch('/cart/remove-coupon', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            NotificationManager.show(data.message, 'success');
            // Reload page to show updated totals
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            NotificationManager.show(data.message, 'error');
        }
    } catch (error) {
        console.error('Error removing coupon:', error);
        NotificationManager.show('Error removing coupon', 'error');
    }
}

    showCouponMessage(message, type) {
        const couponMessage = document.getElementById('couponMessage');
        if (!couponMessage) return;

        couponMessage.innerHTML = `
            <div class="alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    updateItemTotal(quantityForm, newQuantity) {
        const cartItem = quantityForm.closest('.cart-item');
        const priceElement = cartItem.querySelector('.current-price');
        const totalElement = cartItem.querySelector('.item-total .fw-bold');

        if (priceElement && totalElement) {
            const priceText = priceElement.textContent.replace(/[^\d.]/g, '');
            const price = parseFloat(priceText) || 0;
            const itemTotal = price * newQuantity;
            totalElement.textContent = `₹${itemTotal.toFixed(2)}`;
        }
    }

    updateCartTotals() {
        let subtotal = 0;
        let totalItems = 0;

        document.querySelectorAll('.cart-item').forEach(item => {
            const quantity = parseInt(item.querySelector('.quantity-display').textContent) || 0;
            const priceElement = item.querySelector('.current-price');
            const priceText = priceElement ? priceElement.textContent.replace(/[^\d.]/g, '') : '0';
            const price = parseFloat(priceText) || 0;
            const itemTotal = price * quantity;

            subtotal += itemTotal;
            totalItems += quantity;
        });

        // Update summary
        const subtotalElement = document.querySelector('.summary-item .summary-value');
        if (subtotalElement) {
            subtotalElement.textContent = `₹${subtotal.toFixed(2)}`;
        }

        const totalElement = document.querySelector('.summary-total .summary-value');
        if (totalElement) {
            const shippingCost = subtotal >= 999 ? 0 : 50;
            const taxAmount = subtotal * 0.18;
            const finalTotal = subtotal + taxAmount + shippingCost;
            totalElement.textContent = `₹${finalTotal.toFixed(2)}`;
        }
    }

    updateCartCount(count) {
        const cartCountElements = document.querySelectorAll('#cart-count, .cart-count');
        cartCountElements.forEach(element => {
            element.textContent = count;
        });
    }

    updateCartDisplay() {
        const cartItems = document.querySelectorAll('.cart-item');
        if (cartItems.length === 0) {
            this.showEmptyCartState();
        }
    }

    showEmptyCartState() {
        const cartContainer = document.querySelector('.cart-items');
        if (!cartContainer) return;

        cartContainer.innerHTML = `
            <div class="empty-cart text-center py-5">
                <div class="empty-icon mb-4">
                    <i class="bi bi-cart-x display-1 text-muted"></i>
                </div>
                <h3 class="mb-3">Your Cart is Empty</h3>
                <p class="text-muted mb-4">Looks like you haven't added any items to your cart yet.</p>
                <a href="/products" class="btn btn-primary btn-lg">
                    <i class="bi bi-bag me-2"></i>Start Shopping
                </a>
            </div>
        `;

        // Remove summary and actions
        const cartSummary = document.querySelector('.cart-summary');
        const cartActions = document.querySelector('.cart-actions');
        if (cartSummary) cartSummary.remove();
        if (cartActions) cartActions.remove();
    }

    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new CartManager();
});