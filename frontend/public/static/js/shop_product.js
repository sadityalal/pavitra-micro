document.addEventListener('DOMContentLoaded', function() {
    initializeProductsPage();
});

function initializeProductsPage() {
    initializeFilters();
    initializeSorting();
    initializeProductCards();
    updateShowingCount();
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

function initializeFilters() {
    const minPriceInput = document.getElementById('minPrice');
    const maxPriceInput = document.getElementById('maxPrice');
    if (minPriceInput && maxPriceInput) {
        minPriceInput.addEventListener('input', DOMUtils.debounce(filterProducts, 300));
        maxPriceInput.addEventListener('input', DOMUtils.debounce(filterProducts, 300));
    }
    document.querySelectorAll('.brand-filter').forEach(filter => {
        filter.addEventListener('change', filterProducts);
    });
    document.querySelectorAll('.stock-filter').forEach(filter => {
        filter.addEventListener('change', filterProducts);
    });
}

function initializeSorting() {
    document.querySelectorAll('.sort-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const sortBy = this.getAttribute('data-sort');
            sortProducts(sortBy);
        });
    });
}

function initializeProductCards() {
    ProductInteractions.initializeProductCardHover();
}

function filterProducts() {
    const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
    const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 1000000;
    const selectedBrands = Array.from(document.querySelectorAll('.brand-filter:checked'))
        .map(cb => cb.value);
    const selectedStock = Array.from(document.querySelectorAll('.stock-filter:checked'))
        .map(cb => cb.value);
    const products = document.querySelectorAll('.product-item');
    let visibleCount = 0;
    products.forEach(product => {
        const productPrice = parseFloat(product.getAttribute('data-price'));
        const productBrand = product.getAttribute('data-brand');
        const productStock = product.getAttribute('data-stock');
        const priceMatch = productPrice >= minPrice && productPrice <= maxPrice;
        const brandMatch = selectedBrands.length === 0 || selectedBrands.includes(productBrand);
        const stockMatch = selectedStock.length === 0 || selectedStock.includes(productStock);
        if (priceMatch && brandMatch && stockMatch) {
            product.style.display = 'block';
            visibleCount++;
        } else {
            product.style.display = 'none';
        }
    });
    updateShowingCount(visibleCount);
    const existingEmptyState = document.querySelector('.empty-state');
    if (visibleCount === 0 && products.length > 0) {
        if (!existingEmptyState) {
            showEmptyState();
        }
    } else if (existingEmptyState) {
        existingEmptyState.remove();
    }
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

function sortProducts(sortBy) {
    const productsGrid = document.getElementById('productsGrid');
    const products = Array.from(document.querySelectorAll('.product-item'));
    products.sort((a, b) => {
        switch(sortBy) {
            case 'name_asc':
                return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
            case 'name_desc':
                return b.getAttribute('data-name').localeCompare(a.getAttribute('data-name'));
            case 'price_asc':
                return parseFloat(a.getAttribute('data-price')) - parseFloat(b.getAttribute('data-price'));
            case 'price_desc':
                return parseFloat(b.getAttribute('data-price')) - parseFloat(a.getAttribute('data-price'));
            case 'newest':
                return parseFloat(b.getAttribute('data-created')) - parseFloat(a.getAttribute('data-created'));
            default:
                return 0;
        }
    });
    productsGrid.innerHTML = '';
    products.forEach(product => {
        productsGrid.appendChild(product);
    });
    updateShowingCount();
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

function applyPriceFilter() {
    filterProducts();
}

function clearAllFilters() {
    document.getElementById('minPrice').value = 0;
    document.getElementById('maxPrice').value = 100000;
    document.querySelectorAll('.brand-filter').forEach(cb => cb.checked = false);
    document.querySelectorAll('.stock-filter').forEach(cb => cb.checked = false);
    filterProducts();
}

function updateShowingCount(count = null) {
    const showingCount = document.getElementById('showingCount');
    if (!showingCount) return;
    if (count !== null) {
        showingCount.textContent = count;
    } else {
        const visibleProducts = document.querySelectorAll('.product-item[style="display: block"], .product-item:not([style])');
        showingCount.textContent = visibleProducts.length;
    }
}

function addToCart(productId, button) {
    ProductInteractions.addToCart(productId, button);
}

function addToWishlist(productId, button) {
    ProductInteractions.addToWishlist(productId, button);
}

function showLoginAlert(event) {
    ProductInteractions.showLoginAlert(event);
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

function showEmptyState() {
    const productsGrid = document.getElementById('productsGrid');
    const emptyState = document.createElement('div');
    emptyState.className = 'col-12 empty-state';
    emptyState.innerHTML = `
        <div class="text-center py-4" data-aos="fade-up">
            <div class="mb-3">
                <i class="bi bi-search display-1 text-muted"></i>
            </div>
            <h3 class="text-muted">No Products Match Your Filters</h3>
            <p class="text-muted mb-3">Try adjusting your filters or search criteria.</p>
            <button class="btn btn-dark" onclick="clearAllFilters()">Clear All Filters</button>
        </div>
    `;
    productsGrid.appendChild(emptyState);
}

function debounce(func, wait) {
    return DOMUtils.debounce(func, wait);
}

function quickView(productId) {
    NotificationManager.showToast('Quick view feature coming soon!', 'info');
}

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
    .wishlist-btn.active {
        background-color: #ff6b6b !important;
    }
`;
document.head.appendChild(style);

console.log('Products page JavaScript initialized');