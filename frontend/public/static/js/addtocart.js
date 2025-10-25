console.log('addtocart.js loaded');

function addToCart(productId, buttonElement) {
    console.log('Adding product to cart:', productId);
    ProductInteractions.addToCart(productId, buttonElement);
}

function updateCartCountWithData(count) {
    console.log('Updating cart count to:', count);
    CountManager.updateCartCount(count);
}

function updateCartCount() {
    CartAPI.getCartCount()
        .then(data => {
            console.log('Cart count API response:', data);
            updateCartCountWithData(data.count);
        })
        .catch(error => console.error('Error updating cart count:', error));
}

function addToWishlist(productId, buttonElement) {
    console.log('Adding product to wishlist:', productId);
    ProductInteractions.addToWishlist(productId, buttonElement);
}

function updateWishlistCountWithData(count) {
    console.log('Updating wishlist count to:', count);
    CountManager.updateWishlistCount(count);
}

function updateWishlistCount() {
    WishlistAPI.getWishlistCount()
        .then(data => {
            updateWishlistCountWithData(data.count);
        })
        .catch(error => console.error('Error updating wishlist count:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing cart and wishlist counts...');
    updateCartCount();
    updateWishlistCount();
});