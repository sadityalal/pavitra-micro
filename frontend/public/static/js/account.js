class AccountManager {
    constructor() {
        this.currentFilter = 'all';
        this.init();
    }
    init() {
        this.initializeEventListeners();
        this.handleOrderDetailsView();
        console.log('Account Manager initialized');
    }
    initializeEventListeners() {
        const orderSearch = document.getElementById('orderSearch');
        if (orderSearch) {
            orderSearch.addEventListener('input', (e) => {
                this.searchOrders(e.target.value);
            });
        }
        const addAllToCart = document.getElementById('addAllToCart');
        if (addAllToCart) {
            addAllToCart.addEventListener('click', () => {
                this.addAllWishlistToCart();
            });
        }
        document.querySelectorAll('.remove-wishlist').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const itemId = e.currentTarget.getAttribute('data-item-id');
                this.removeFromWishlist(itemId, e.currentTarget);
            });
        });
        document.querySelectorAll('.add-to-cart-wishlist').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = e.currentTarget.getAttribute('data-product-id');
                ProductInteractions.addToCart(productId, e.currentTarget);
            });
        });
        this.initializeAddressForm();
        this.initializeFormValidation();
        this.initializeQuickStats();
    }
    initializeQuickStats() {
        document.querySelectorAll('.clickable-stat').forEach(stat => {
            stat.addEventListener('click', (e) => {
                const filter = e.currentTarget.getAttribute('data-filter');
                this.filterOrders(filter);
            });
        });
    }
    filterOrders(filter) {
        this.currentFilter = filter;
        const orderCards = document.querySelectorAll('.order-card');
        const ordersTitle = document.getElementById('orders-title');
        document.querySelectorAll('.clickable-stat').forEach(stat => {
            stat.classList.remove('active');
        });
        const activeStat = document.querySelector(`.clickable-stat[data-filter="${filter}"]`);
        if (activeStat) {
            activeStat.classList.add('active');
        }
        let visibleCount = 0;
        let title = 'All Orders';
        orderCards.forEach(card => {
            const status = card.getAttribute('data-order-status');
            let shouldShow = false;
            switch (filter) {
                case 'all':
                    shouldShow = true;
                    title = 'All Orders';
                    break;
                case 'delivered':
                    shouldShow = status === 'delivered';
                    title = 'Delivered Orders';
                    break;
                case 'active':
                    shouldShow = ['pending', 'confirmed', 'processing', 'shipped'].includes(status);
                    title = 'Orders In Progress';
                    break;
                case 'cancelled':
                    shouldShow = status === 'cancelled';
                    title = 'Cancelled Orders';
                    break;
                default:
                    shouldShow = true;
            }
            if (shouldShow) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        if (ordersTitle) {
            ordersTitle.textContent = title;
        }
        this.toggleEmptyState(visibleCount);
    }
    toggleEmptyState(visibleCount) {
        const emptyState = document.querySelector('#orders-content .empty-state');
        const ordersGrid = document.getElementById('ordersGrid');
        if (emptyState && ordersGrid) {
            if (visibleCount === 0) {
                emptyState.style.display = 'block';
                ordersGrid.style.display = 'none';
                const emptyTitle = emptyState.querySelector('h3');
                const emptyText = emptyState.querySelector('p');
                if (emptyTitle && emptyText) {
                    switch (this.currentFilter) {
                        case 'delivered':
                            emptyTitle.textContent = 'No Delivered Orders';
                            emptyText.textContent = 'You don\'t have any delivered orders yet.';
                            break;
                        case 'active':
                            emptyTitle.textContent = 'No Active Orders';
                            emptyText.textContent = 'You don\'t have any orders in progress.';
                            break;
                        case 'cancelled':
                            emptyTitle.textContent = 'No Cancelled Orders';
                            emptyText.textContent = 'You haven\'t cancelled any orders.';
                            break;
                        default:
                            emptyTitle.textContent = 'No Orders Yet';
                            emptyText.textContent = 'You haven\'t placed any orders yet. Start shopping to see your orders here.';
                    }
                }
            } else {
                emptyState.style.display = 'none';
                ordersGrid.style.display = 'block';
            }
        }
    }
    handleOrderDetailsView() {
        const urlParams = new URLSearchParams(window.location.search);
        const orderNumber = urlParams.get('order_number');
        if (orderNumber && urlParams.get('tab') === 'orders') {
            setTimeout(() => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 100);
        }
    }
    searchOrders(query) {
        const orderCards = document.querySelectorAll('.order-card');
        let visibleCount = 0;
        orderCards.forEach(card => {
            const orderText = card.textContent.toLowerCase();
            const status = card.getAttribute('data-order-status');
            const matchesSearch = orderText.includes(query.toLowerCase());
            const matchesFilter = this.matchesCurrentFilter(status);
            if (matchesSearch && matchesFilter) {
                card.style.display = 'block';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        this.toggleEmptyState(visibleCount);
    }
    matchesCurrentFilter(status) {
        switch (this.currentFilter) {
            case 'all': return true;
            case 'delivered': return status === 'delivered';
            case 'active': return ['pending', 'confirmed', 'processing', 'shipped'].includes(status);
            case 'cancelled': return status === 'cancelled';
            default: return true;
        }
    }
    async removeFromWishlist(itemId, button) {
        if (!button) return;
        try {
            const data = await WishlistAPI.removeFromWishlist(itemId);
            if (data.success) {
                const wishlistCard = button.closest('.wishlist-card');
                if (wishlistCard) {
                    wishlistCard.style.opacity = '0';
                    wishlistCard.style.transform = 'scale(0.8)';
                    wishlistCard.style.transition = 'all 0.3s ease';
                    setTimeout(() => {
                        wishlistCard.remove();
                        CountManager.updateWishlistCount(data.wishlist_count || 0);
                        NotificationManager.show('Item removed from wishlist', 'success');
                        const remainingItems = document.querySelectorAll('.wishlist-card');
                        if (remainingItems.length === 0) {
                            setTimeout(() => {
                                window.location.reload();
                            }, 1000);
                        }
                    }, 300);
                }
            } else {
                NotificationManager.show(data.message || 'Failed to remove from wishlist', 'error');
            }
        } catch (error) {
            console.error('Error removing from wishlist:', error);
            NotificationManager.show('Error removing from wishlist', 'error');
        }
    }
    async addAllWishlistToCart() {
        const addButtons = document.querySelectorAll('.add-to-cart-wishlist:not(:disabled)');
        if (addButtons.length === 0) {
            NotificationManager.show('No items available to add to cart', 'warning');
            return;
        }
        const addAllBtn = document.getElementById('addAllToCart');
        DOMUtils.setLoadingState(addAllBtn, true);
        let successCount = 0;
        let errorCount = 0;
        for (let i = 0; i < addButtons.length; i++) {
            const button = addButtons[i];
            const productId = button.getAttribute('data-product-id');
            try {
                const data = await CartAPI.addToCart(productId, 1);
                if (data.success) {
                    successCount++;
                    CountManager.updateCartCount(data.cart_count || 0);
                } else {
                    errorCount++;
                }
            } catch (error) {
                console.error('Error adding product to cart:', error);
                errorCount++;
            }
        }
        DOMUtils.setLoadingState(addAllBtn, false);
        if (successCount > 0) {
            NotificationManager.show(`Successfully added ${successCount} item(s) to cart`, 'success');
        }
        if (errorCount > 0) {
            NotificationManager.show(`Failed to add ${errorCount} item(s) to cart`, 'error');
        }
    }
    initializeAddressForm() {
        const showAddressFormBtn = document.getElementById('showAddressForm');
        const showAddressFormEmptyBtn = document.getElementById('showAddressFormEmpty');
        const hideAddressFormBtn = document.getElementById('hideAddressForm');
        const addressForm = document.getElementById('addAddressForm');
        if (showAddressFormBtn && addressForm) {
            showAddressFormBtn.addEventListener('click', () => {
                addressForm.style.display = 'block';
                addressForm.scrollIntoView({ behavior: 'smooth' });
            });
        }
        if (showAddressFormEmptyBtn && addressForm) {
            showAddressFormEmptyBtn.addEventListener('click', () => {
                addressForm.style.display = 'block';
                addressForm.scrollIntoView({ behavior: 'smooth' });
            });
        }
        if (hideAddressFormBtn && addressForm) {
            hideAddressFormBtn.addEventListener('click', () => {
                addressForm.style.display = 'none';
            });
        }
    }
    initializeFormValidation() {
        const profileForm = document.getElementById('profileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', (e) => {
                const phone = document.getElementById('phone')?.value;
                if (phone && !/^\d{10}$/.test(phone)) {
                    e.preventDefault();
                    NotificationManager.show('Please enter a valid 10-digit phone number', 'error');
                    return false;
                }
            });
        }
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => {
                const newPassword = document.getElementById('new_password')?.value;
                const confirmPassword = document.getElementById('confirm_password')?.value;
                if (newPassword !== confirmPassword) {
                    e.preventDefault();
                    NotificationManager.show('New password and confirm password do not match', 'error');
                    return false;
                }
                if (newPassword.length < 6) {
                    e.preventDefault();
                    NotificationManager.show('Password must be at least 6 characters long', 'error');
                    return false;
                }
            });
        }
    }
    updateWishlistCount(count) {
        CountManager.updateWishlistCount(count);
    }
    updateCartCount(count) {
        CountManager.updateCartCount(count);
    }
    getCSRFToken() {
        return ApiClient.getCSRFToken();
    }
    showAlert(message, type) {
        NotificationManager.show(message, type);
    }
}

class ModernCalendar {
    constructor(container) {
        this.container = container;
        this.input = container.querySelector('.date-picker-input');
        this.dropdown = container.querySelector('.calendar-dropdown');
        this.calendarDays = container.querySelector('#calendarDays');
        this.monthSelect = container.querySelector('.month-select');
        this.yearSelect = container.querySelector('.year-select');
        this.todayBtn = container.querySelector('.today-btn');
        this.applyBtn = container.querySelector('.apply-btn');
        this.clearBtn = container.querySelector('.clear-date');
        this.toggleBtn = container.querySelector('.calendar-toggle');
        this.ageDisplay = document.querySelector('#ageDisplay');
        this.dobSet = this.input.getAttribute('data-dob-set') === 'true';
        this.currentDate = new Date();
        this.selectedDate = null;
        this.isOpen = false;
        this.init();
    }
    init() {
        if (this.dobSet) {
            this.disableCalendar();
        } else {
            this.initializeEventListeners();
            this.populateYearSelect();
            this.setInitialDate();
            this.renderCalendar();
        }
    }
    initializeEventListeners() {
        this.toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleCalendar();
        });
        this.input.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.openCalendar();
        });
        this.input.addEventListener('focus', (e) => {
            e.preventDefault();
            this.openCalendar();
        });
        const calendarIcon = this.container.querySelector('.input-group-text');
        if (calendarIcon) {
            calendarIcon.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleCalendar();
            });
        }
        this.container.querySelector('.prev-year').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.navigateYear(-1);
        });
        this.container.querySelector('.prev-month').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.navigateMonth(-1);
        });
        this.container.querySelector('.next-month').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.navigateMonth(1);
        });
        this.container.querySelector('.next-year').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.navigateYear(1);
        });
        this.monthSelect.addEventListener('change', (e) => {
            e.stopPropagation();
            this.onMonthYearChange();
        });
        this.yearSelect.addEventListener('change', (e) => {
            e.stopPropagation();
            this.onMonthYearChange();
        });
        this.todayBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.selectToday();
        });
        this.applyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.applySelection();
        });
        this.clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.clearSelection();
        });
        document.addEventListener('click', (e) => this.handleClickOutside(e));
        this.input.addEventListener('keydown', (e) => this.handleKeyboard(e));
        this.dropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    disableCalendar() {
        this.input.disabled = true;
        this.input.placeholder = "Date of birth is permanently set";
        this.input.classList.add('bg-light', 'text-muted');
        const toggleBtn = this.container.querySelector('.calendar-toggle');
        const clearBtn = this.container.querySelector('.clear-date');
        if (toggleBtn) toggleBtn.disabled = true;
        if (clearBtn) clearBtn.disabled = true;
        this.dropdown.style.display = 'none';
        this.container.classList.add('dob-locked');
    }
    populateYearSelect() {
        const currentYear = this.currentDate.getFullYear();
        const startYear = currentYear - 100;
        const endYear = currentYear;
        this.yearSelect.innerHTML = '';
        for (let year = endYear; year >= startYear; year--) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            this.yearSelect.appendChild(option);
        }
    }
    setInitialDate() {
        if (this.input.value) {
            const dateParts = this.input.value.split('-');
            this.selectedDate = new Date(dateParts[0], dateParts[1] - 1, dateParts[2]);
            this.currentDate = new Date(this.selectedDate);
        } else {
            this.selectedDate = null;
        }
        this.updateSelects();
    }
    updateSelects() {
        this.monthSelect.value = this.currentDate.getMonth();
        this.yearSelect.value = this.currentDate.getFullYear();
    }
    renderCalendar() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const today = new Date();
        this.calendarDays.innerHTML = '';
        for (let i = 0; i < firstDay; i++) {
            this.addDayCell('', 'other-month');
        }
        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(year, month, day);
            const cell = this.addDayCell(day, '');
            if (this.isSameDay(date, today)) {
                cell.classList.add('today');
            }
            if (this.selectedDate && this.isSameDay(date, this.selectedDate)) {
                cell.classList.add('selected');
            }
            if (date > today) {
                cell.classList.add('disabled');
            } else {
                cell.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectDate(date);
                });
            }
        }
        this.updateAgeDisplay();
    }
    addDayCell(content, className) {
        const cell = document.createElement('button');
        cell.type = 'button';
        cell.className = `calendar-day ${className}`;
        cell.textContent = content;
        cell.setAttribute('aria-label', content ? `Select date ${content}` : 'Empty day');
        cell.style.cursor = className.includes('disabled') ? 'not-allowed' : 'pointer';
        cell.style.width = '100%';
        cell.style.height = '100%';
        cell.style.border = 'none';
        cell.style.background = 'transparent';
        this.calendarDays.appendChild(cell);
        return cell;
    }
    isSameDay(date1, date2) {
        return date1.getDate() === date2.getDate() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getFullYear() === date2.getFullYear();
    }
    selectDate(date) {
        this.selectedDate = date;
        this.renderCalendar();
        const formattedDate = this.formatDate(date);
        this.input.value = formattedDate;
        this.input.classList.add('temp-selection');
        this.updateAgeDisplay();
        setTimeout(() => {
            this.applySelection();
        }, 500);
    }
    applySelection() {
        if (this.selectedDate) {
            const formattedDate = this.formatDate(this.selectedDate);
            this.input.value = formattedDate;
            this.input.classList.remove('temp-selection');
            this.closeCalendar();
            this.showPermanentWarning();
        }
    }
    showPermanentWarning() {
        const formattedDate = this.formatDisplayDate(this.selectedDate);
        const age = this.calculateAge(this.selectedDate);
        NotificationManager.show(
            `Date of birth will be set to ${formattedDate} (Age: ${age} years). ` +
            `This is permanent and cannot be changed after saving your profile.`,
            'warning'
        );
    }
    formatDisplayDate(date) {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    clearSelection() {
        this.selectedDate = null;
        this.input.value = '';
        this.input.classList.remove('temp-selection');
        this.renderCalendar();
        this.updateAgeDisplay();
        NotificationManager.show('Date cleared', 'info');
        this.closeCalendar();
    }
    selectToday() {
        const today = new Date();
        if (today <= new Date()) {
            this.selectDate(today);
        } else {
            NotificationManager.show('Cannot select future date', 'error');
        }
    }
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    navigateMonth(direction) {
        this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        this.updateSelects();
        this.renderCalendar();
    }
    navigateYear(direction) {
        this.currentDate.setFullYear(this.currentDate.getFullYear() + direction);
        this.updateSelects();
        this.renderCalendar();
    }
    onMonthYearChange() {
        this.currentDate.setMonth(parseInt(this.monthSelect.value));
        this.currentDate.setFullYear(parseInt(this.yearSelect.value));
        this.renderCalendar();
    }
    toggleCalendar() {
        this.isOpen ? this.closeCalendar() : this.openCalendar();
    }
    openCalendar() {
        this.closeAllOtherCalendars();
        this.dropdown.classList.add('show');
        this.isOpen = true;
        this.toggleBtn.innerHTML = '<i class="bi bi-chevron-up"></i>';
        this.toggleBtn.classList.add('active');
        if (!this.selectedDate) {
            this.currentDate = new Date();
            this.updateSelects();
            this.renderCalendar();
        }
    }
    closeCalendar() {
        this.dropdown.classList.remove('show');
        this.isOpen = false;
        this.toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i>';
        this.toggleBtn.classList.remove('active');
    }
    closeAllOtherCalendars() {
        document.querySelectorAll('.calendar-dropdown.show').forEach(dropdown => {
            if (dropdown !== this.dropdown) {
                dropdown.classList.remove('show');
                const toggleBtn = dropdown.closest('.date-picker-container').querySelector('.calendar-toggle');
                if (toggleBtn) {
                    toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i>';
                    toggleBtn.classList.remove('active');
                }
            }
        });
    }
    handleClickOutside(event) {
        if (!this.container.contains(event.target) && this.isOpen) {
            this.closeCalendar();
            if (this.input.classList.contains('temp-selection')) {
                this.input.value = this.selectedDate ? this.formatDate(this.selectedDate) : '';
                this.input.classList.remove('temp-selection');
            }
        }
    }
    handleKeyboard(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            this.toggleCalendar();
        } else if (event.key === 'Escape' && this.isOpen) {
            this.closeCalendar();
        }
    }
    updateAgeDisplay() {
        if (!this.ageDisplay) return;
        if (this.selectedDate) {
            const age = this.calculateAge(this.selectedDate);
            this.ageDisplay.innerHTML = `
                <span class="badge bg-info">
                    <i class="bi bi-person me-1"></i>
                    Age: ${age} years
                </span>
            `;
        } else {
            this.ageDisplay.innerHTML = '';
        }
    }
    calculateAge(birthDate) {
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        return age;
    }
}

function injectEnhancedCSS() {
    if (!document.querySelector('#enhanced-calendar-css')) {
        const style = document.createElement('style');
        style.id = 'enhanced-calendar-css';
        style.textContent = `
            .date-picker-container .input-group-text {
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .date-picker-container .input-group-text:hover {
                background-color: #0b5ed7 !important;
            }
            .calendar-toggle {
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .calendar-toggle:hover {
                background-color: #0d6efd;
                color: white;
            }
            .calendar-toggle.active {
                background-color: #0d6efd;
                color: white;
            }
            .date-picker-input {
                cursor: pointer !important;
            }
            .calendar-day {
                min-height: 45px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                z-index: 1;
            }
            .calendar-header button,
            .calendar-footer button {
                cursor: pointer;
                transition: all 0.2s ease;
            }
            .calendar-header button:hover,
            .calendar-footer button:hover {
                transform: translateY(-1px);
            }
            .date-picker-input:focus {
                z-index: 3;
            }
            .calendar-day:focus {
                outline: 2px solid #0d6efd;
                outline-offset: 2px;
            }
            .dob-locked .form-control:disabled {
                background-color: #f8f9fa !important;
                color: #6c757d !important;
            }
        `;
        document.head.appendChild(style);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    injectEnhancedCSS();
    const accountManager = new AccountManager();
    const datePickerContainer = document.querySelector('.date-picker-container');
    if (datePickerContainer) {
        new ModernCalendar(datePickerContainer);
    }
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
    const interactiveCards = document.querySelectorAll('.order-card, .wishlist-card, .address-card');
    interactiveCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
            this.style.transition = 'all 0.2s ease';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
    const quickStats = document.querySelectorAll('.clickable-stat');
    quickStats.forEach(stat => {
        stat.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
            this.style.transition = 'all 0.2s ease';
            this.style.cursor = 'pointer';
        });
        stat.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
    const tabLinks = document.querySelectorAll('a[data-tab]');
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const tab = this.getAttribute('data-tab');
            if (tab) {
                const contentArea = document.querySelector('.content-area');
                if (contentArea) {
                    contentArea.style.opacity = '0.7';
                    contentArea.style.transition = 'opacity 0.2s ease';
                    setTimeout(() => {
                        contentArea.style.opacity = '1';
                    }, 300);
                }
            }
        });
    });
});

window.AccountManager = AccountManager;
window.ModernCalendar = ModernCalendar;
window.showAccountAlert = NotificationManager.show;
window.updateCartCountGlobal = CountManager.updateCartCount;
window.updateWishlistCountGlobal = CountManager.updateWishlistCount;

document.addEventListener('DOMContentLoaded', function() {
    const confirmDeactivate = document.getElementById('confirmDeactivate');
    const deactivateSubmit = document.getElementById('deactivateSubmit');
    if (confirmDeactivate && deactivateSubmit) {
        confirmDeactivate.addEventListener('change', function() {
            deactivateSubmit.disabled = !this.checked;
        });
    }
    const confirmDelete1 = document.getElementById('confirmDelete1');
    const confirmDelete2 = document.getElementById('confirmDelete2');
    const confirmDelete3 = document.getElementById('confirmDelete3');
    const deleteSubmit = document.getElementById('deleteSubmit');
    if (confirmDelete1 && confirmDelete2 && confirmDelete3 && deleteSubmit) {
        function validateDeletion() {
            deleteSubmit.disabled = !(confirmDelete1.checked && confirmDelete2.checked && confirmDelete3.checked);
        }
        confirmDelete1.addEventListener('change', validateDeletion);
        confirmDelete2.addEventListener('change', validateDeletion);
        confirmDelete3.addEventListener('change', validateDeletion);
    }
    const deactivateModal = document.getElementById('deactivateModal');
    const deleteModal = document.getElementById('deleteModal');
    if (deactivateModal) {
        deactivateModal.addEventListener('hidden.bs.modal', function() {
            confirmDeactivate.checked = false;
            deactivateSubmit.disabled = true;
        });
    }
    if (deleteModal) {
        deleteModal.addEventListener('hidden.bs.modal', function() {
            confirmDelete1.checked = false;
            confirmDelete2.checked = false;
            confirmDelete3.checked = false;
            deleteSubmit.disabled = true;
        });
    }
});