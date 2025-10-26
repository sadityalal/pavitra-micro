//ProductInteractions
class ProductInteractions {
    static async addToCart(productId, buttonElement, quantity = 1) {
        if (!buttonElement) {
            NotificationManager.show('Error: Could not add to cart', 'error');
            return;
        }

        DOMUtils.setLoadingState(buttonElement, true);

        try {
            const data = await CartAPI.addToCart(productId, quantity);

            if (data.success) {
                CountManager.updateCartCount(data.cart_count);
                NotificationManager.show('Product added to cart!', 'success');

                // Visual feedback
                buttonElement.innerHTML = '<i class="bi bi-check"></i> Added!';
                buttonElement.classList.add('btn-success');

                setTimeout(() => {
                    if (buttonElement.parentNode) {
                        DOMUtils.setLoadingState(buttonElement, false);
                        buttonElement.classList.remove('btn-success');
                    }
                }, 2000);
            } else {
                NotificationManager.show(data.message || 'Failed to add to cart', 'error');
                DOMUtils.setLoadingState(buttonElement, false);
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            NotificationManager.show('Error adding to cart. Please try again.', 'error');
            DOMUtils.setLoadingState(buttonElement, false);
        }
    }

    static async addToWishlist(productId, buttonElement) {
        if (!buttonElement) {
            NotificationManager.show('Error: Could not add to wishlist', 'error');
            return;
        }

        const isActive = buttonElement.classList.contains('active');
        const originalHTML = buttonElement.innerHTML;

        if (!isActive) {
            buttonElement.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i>';
            buttonElement.disabled = true;
        }

        try {
            const data = await WishlistAPI.addToWishlist(productId);

            if (data.success) {
                CountManager.updateWishlistCount(data.wishlist_count);
                NotificationManager.show('Product added to wishlist!', 'success');

                buttonElement.innerHTML = '<i class="bi bi-heart-fill text-danger"></i>';
                buttonElement.classList.add('active');
                buttonElement.disabled = false;
            } else {
                buttonElement.innerHTML = originalHTML;
                buttonElement.classList.remove('active');
                buttonElement.disabled = false;
                NotificationManager.show(data.message || 'Failed to add to wishlist', 'error');
            }
        } catch (error) {
            console.error('Error adding to wishlist:', error);
            buttonElement.innerHTML = originalHTML;
            buttonElement.classList.remove('active');
            buttonElement.disabled = false;
            NotificationManager.show('Error adding to wishlist. Please try again.', 'error');
        }
    }

    static showLoginAlert(event = null) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        NotificationManager.show('Please login to add items to your wishlist', 'warning');
    }

    static initializeProductCardHover() {
        const productCards = document.querySelectorAll('.product-card, .product-item');
        productCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
                this.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '';
            });
        });
    }

    static initializeImageGallery(mainImageId = 'mainProductImage') {
        const thumbnails = document.querySelectorAll('.thumbnail-item');
        const mainImage = document.getElementById(mainImageId);

        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', function() {
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                if (mainImage) {
                    const newSrc = this.getAttribute('data-full-image') || this.src;
                    mainImage.style.opacity = '0';
                    setTimeout(() => {
                        mainImage.src = newSrc;
                        mainImage.style.opacity = '1';
                        mainImage.style.transition = 'opacity 0.3s ease';
                    }, 150);
                }
            });
        });

        if (mainImage) {
            mainImage.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.02)';
                this.style.transition = 'transform 0.3s ease';
            });

            mainImage.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        }
    }
}

window.ProductInteractions = ProductInteractions;