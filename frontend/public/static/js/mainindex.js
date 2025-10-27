document.addEventListener('DOMContentLoaded', function() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            mirror: false
        });
    }
    function toggleSearch() {
        const mobileSearch = document.getElementById('mobileSearch');
        if (mobileSearch && window.innerWidth < 1200) {
            const bsCollapse = new bootstrap.Collapse(mobileSearch, {
                toggle: true
            });
        } else {
            const desktopSearch = document.querySelector('.desktop-search-form input');
            if (desktopSearch) {
                desktopSearch.focus();
            } else {
                window.location.href = "/search";
            }
        }
    }
    const floatingIcons = document.querySelectorAll('.floating-icon');
    floatingIcons.forEach(icon => {
        icon.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
            this.style.transition = 'transform 0.3s ease';
        });
        icon.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
        icon.addEventListener('click', function() {
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
    const productCards = document.querySelectorAll('.product-item, .product-card');
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
    window.addToCart = function(productId, button) {
        if (!button) return;
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Adding...';
        button.disabled = true;
        fetch('/add-to-cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': ApiClient.getCSRFToken()
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: 1
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const cartCount = document.getElementById('cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_count;
                }
                showNotification('Product added to cart!', 'success');
                button.innerHTML = '<i class="bi bi-check"></i> Added!';
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            } else {
                showNotification(data.message || 'Failed to add product to cart', 'error');
                button.innerHTML = originalText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showNotification('Error adding product to cart', 'error');
            button.innerHTML = originalText;
            button.disabled = false;
        });
    };
    window.addToWishlist = function(productId, button) {
        if (!button) return;
        button.classList.toggle('active');
        fetch('/add-to-wishlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': ApiClient.getCSRFToken()
            },
            body: JSON.stringify({
                product_id: productId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const wishlistCount = document.getElementById('wishlist-count');
                if (wishlistCount) {
                    wishlistCount.textContent = data.wishlist_count;
                }
                showNotification('Product added to wishlist!', 'success');
            } else {
                button.classList.toggle('active');
                showNotification(data.message || 'Failed to add product to wishlist', 'error');
            }
        })
        .catch(error => {
            console.error('Error adding to wishlist:', error);
            button.classList.toggle('active');
            showNotification('Error adding product to wishlist', 'error');
        });
    };
    function showNotification(message, type = 'info') {
        NotificationManager.showToast(message, type);
    }
    const categoryCards = document.querySelectorAll('.category-card, .category-featured');
    categoryCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            const img = this.querySelector('img');
            if (img) {
                img.style.transform = 'scale(1.05)';
                img.style.transition = 'transform 0.5s ease';
            }
        });
        card.addEventListener('mouseleave', function() {
            const img = this.querySelector('img');
            if (img) {
                img.style.transform = 'scale(1)';
            }
        });
    });
    function initializeCountdown() {
        const countdownElement = document.querySelector('.countdown-timer');
        if (!countdownElement) return;
        const endTime = new Date();
        endTime.setHours(endTime.getHours() + 48);
        function updateCountdown() {
            const now = new Date();
            const difference = endTime - now;
            if (difference <= 0) {
                countdownElement.innerHTML = 'Sale Ended!';
                return;
            }
            const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((difference % (1000 * 60)) / 1000);
            countdownElement.innerHTML = `${hours}h ${minutes}m ${seconds}s`;
        }
        setInterval(updateCountdown, 1000);
        updateCountdown();
    }
    initializeCountdown();
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    window.toggleSearch = toggleSearch;
    console.log('Homepage JavaScript initialized successfully');
});

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

window.addEventListener('resize', function() {
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
});