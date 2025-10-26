// brand.js - Brand page specific functionality
class BrandPage {
    constructor() {
        this.currentSort = 'name_asc';
        this.init();
    }

    init() {
        console.log('Brand page initialized');
        this.initializeEventListeners();
        this.initializeProductInteractions();
    }

    initializeEventListeners() {
        // Price filter inputs
        const minPriceInput = document.getElementById('minPrice');
        const maxPriceInput = document.getElementById('maxPrice');

        if (minPriceInput && maxPriceInput) {
            minPriceInput.addEventListener('input', this.debounce(() => this.filterProducts(), 300));
            maxPriceInput.addEventListener('input', this.debounce(() => this.filterProducts(), 300));

            // Price range validation
            minPriceInput.addEventListener('blur', () => this.validatePriceRange());
            maxPriceInput.addEventListener('blur', () => this.validatePriceRange());
        }

        // Stock filter checkboxes
        document.querySelectorAll('.stock-filter').forEach(filter => {
            filter.addEventListener('change', () => this.filterProducts());
        });
    }

    initializeProductInteractions() {
        // Add pulse animation to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('.add-to-cart-btn')) {
                const btn = e.target.closest('.add-to-cart-btn');
                btn.classList.add('pulse');
                setTimeout(() => btn.classList.remove('pulse'), 600);
            }
        });
    }

    validatePriceRange() {
        const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
        const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 100000;

        if (minPrice > maxPrice) {
            if (typeof NotificationManager !== 'undefined') {
                NotificationManager.showToast('Minimum price cannot be greater than maximum price', 'warning');
            }
            document.getElementById('minPrice').value = 0;
        }
    }

    filterProducts() {
        const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
        const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 100000;

        const selectedStock = Array.from(document.querySelectorAll('.stock-filter:checked'))
            .map(cb => cb.value);

        const products = document.querySelectorAll('.product-item');
        let visibleCount = 0;

        products.forEach(product => {
            const productPrice = parseFloat(product.getAttribute('data-price'));
            const productStock = product.getAttribute('data-stock');

            const priceMatch = productPrice >= minPrice && productPrice <= maxPrice;
            const stockMatch = selectedStock.length === 0 || selectedStock.includes(productStock);

            if (priceMatch && stockMatch) {
                product.style.display = 'block';
                visibleCount++;
            } else {
                product.style.display = 'none';
            }
        });

        this.updateDisplay(visibleCount);
    }

    sortProducts(sortBy) {
        this.currentSort = sortBy;
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

        this.updateShowingCount();

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    applyPriceFilter() {
        this.filterProducts();
    }

    clearAllFilters() {
        // Reset price inputs
        document.getElementById('minPrice').value = 0;
        document.getElementById('maxPrice').value = 100000;

        // Uncheck all stock filters
        document.querySelectorAll('.stock-filter').forEach(cb => {
            cb.checked = false;
        });

        // Reset sort
        const sortSelect = document.querySelector('.form-select');
        if (sortSelect) {
            sortSelect.value = 'name_asc';
        }
        this.currentSort = 'name_asc';

        this.filterProducts();
    }

    updateDisplay(visibleCount) {
        const emptyState = document.querySelector('.empty-state');
        const productsGrid = document.getElementById('productsGrid');

        if (visibleCount === 0) {
            if (emptyState) emptyState.style.display = 'block';
            if (productsGrid) productsGrid.style.display = 'none';
        } else {
            if (emptyState) emptyState.style.display = 'none';
            if (productsGrid) productsGrid.style.display = 'block';
        }

        this.updateShowingCount(visibleCount);

        if (typeof AOS !== 'undefined') {
            AOS.refresh();
        }
    }

    updateShowingCount(count = null) {
        const showingCount = document.getElementById('showingCount');
        if (!showingCount) return;

        if (count !== null) {
            showingCount.textContent = count;
        } else {
            const visibleProducts = document.querySelectorAll('.product-item[style="display: block"], .product-item:not([style])');
            showingCount.textContent = visibleProducts.length;
        }
    }

    debounce(func, wait) {
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.brandPage = new BrandPage();
});