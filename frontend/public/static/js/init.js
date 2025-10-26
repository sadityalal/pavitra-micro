console.log('Initializing Pavitra Enterprises application...');

function initializeAllComponents() {
    console.log('Initializing all components...');
    initializeUserState();
    const announcementSwiper = new Swiper('.announcement-slider', {
        loop: true,
        speed: 600,
        autoplay: {
            delay: 5000,
        },
        slidesPerView: 1,
        direction: 'vertical',
        effect: 'slide'
    });
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            easing: 'ease-in-out',
            once: true,
            mirror: false
        });
    }
    if (typeof GLightbox !== 'undefined') {
        const lightbox = GLightbox({
            selector: '.glightbox'
        });
    }
    if (typeof PureCounter !== 'undefined') {
        new PureCounter();
    } else {
        console.log('PureCounter not found, skipping initialization');
    }
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    const navmenu = document.querySelector('#navmenu');
    if (mobileNavToggle && navmenu) {
        mobileNavToggle.addEventListener('click', function(e) {
            e.preventDefault();
            navmenu.classList.toggle('mobile-nav-active');
            this.classList.toggle('bi-list');
            this.classList.toggle('bi-x');
        });
    }
    const dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    const dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    CountManager.refreshCounts();
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    setupGlobalListeners();
    console.log('All components initialized successfully');
}

function initializeUserState() {
    const userElements = document.querySelectorAll('.user-account-menu, [data-user-authenticated="true"]');
    if (userElements.length > 0) {
        document.body.classList.add('user-authenticated');
        console.log('User is authenticated');
        if (typeof initializeSessionTimeout !== 'undefined') {
            initializeSessionTimeout();
        }
    } else {
        document.body.classList.remove('user-authenticated');
        console.log('User is not authenticated');
    }
}

function setupGlobalListeners() {
    document.addEventListener('click', function(e) {
        const productCard = e.target.closest('.product-card, .product-item');
        if (productCard && !e.target.closest('.product-actions') && !e.target.closest('button')) {
            const productLink = productCard.querySelector('a[href*="/product/"]');
            if (productLink) {
                e.preventDefault();
                window.location.href = productLink.href;
            }
        }
        const categoryCard = e.target.closest('.category-card, .category-featured');
        if (categoryCard) {
            const categoryLink = categoryCard.querySelector('a[href*="/category/"]');
            if (categoryLink) {
                e.preventDefault();
                window.location.href = categoryLink.href;
            }
        }
    });
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                NotificationManager.showToast('Please enter a search term', 'error');
            }
        });
    });
    const mobileSearchToggle = document.querySelector('.mobile-search-toggle');
    if (mobileSearchToggle) {
        mobileSearchToggle.addEventListener('click', function() {
            const mobileSearch = document.getElementById('mobileSearch');
            if (mobileSearch) {
                setTimeout(() => {
                    const searchInput = mobileSearch.querySelector('input[name="q"]');
                    if (searchInput) searchInput.focus();
                }, 300);
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeAllComponents();
});

window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.initializeAllComponents = initializeAllComponents;
window.initializeUserState = initializeUserState;
window.setupGlobalListeners = setupGlobalListeners;