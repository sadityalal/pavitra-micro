class AdminUsersAPI {
    static async deactivateUser(userId) {
        return ApiClient.post(`/admin/users/${userId}/deactivate`);
    }

    static async reactivateUser(userId) {
        return ApiClient.post(`/admin/users/${userId}/reactivate`);
    }

    static async cancelUserDeletion(userId) {
        return ApiClient.post(`/admin/users/${userId}/cancel-deletion`);
    }
}

class AdminUsersManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('Admin Users Manager initialized');
        this.bindEventListeners();
    }

    bindEventListeners() {
        // Use event delegation for all admin user actions
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-admin-user-action]');
            if (!button) return;

            e.preventDefault();

            const action = button.dataset.adminUserAction;
            const userId = button.dataset.userId;
            const userEmail = button.dataset.userEmail;

            switch (action) {
                case 'deactivate':
                    this.handleDeactivateUser(userId, userEmail, button);
                    break;
                case 'reactivate':
                    this.handleReactivateUser(userId, userEmail, button);
                    break;
                case 'cancel-deletion':
                    this.handleCancelDeletion(userId, userEmail, button);
                    break;
                case 'view-details':
                    this.handleViewDetails(userId);
                    break;
            }
        });
    }

    async handleDeactivateUser(userId, userEmail, buttonElement) {
        if (!await this.confirmAction(`Deactivate user "${userEmail}"? They will not be able to login until reactivated.`)) {
            return;
        }

        DOMUtils.setLoadingState(buttonElement, true);

        try {
            const data = await AdminUsersAPI.deactivateUser(userId);

            if (data.success) {
                NotificationManager.show(data.message, 'warning');
                this.refreshPageAfterDelay();
            } else {
                NotificationManager.show(data.message, 'error');
                DOMUtils.setLoadingState(buttonElement, false);
            }
        } catch (error) {
            console.error('Error deactivating user:', error);
            NotificationManager.show('Error deactivating user', 'error');
            DOMUtils.setLoadingState(buttonElement, false);
        }
    }

    async handleReactivateUser(userId, userEmail, buttonElement) {
        if (!await this.confirmAction(`Reactivate user "${userEmail}"? They will be able to login again.`)) {
            return;
        }

        DOMUtils.setLoadingState(buttonElement, true);

        try {
            const data = await AdminUsersAPI.reactivateUser(userId);

            if (data.success) {
                NotificationManager.show(data.message, 'success');
                this.refreshPageAfterDelay();
            } else {
                NotificationManager.show(data.message, 'error');
                DOMUtils.setLoadingState(buttonElement, false);
            }
        } catch (error) {
            console.error('Error reactivating user:', error);
            NotificationManager.show('Error reactivating user', 'error');
            DOMUtils.setLoadingState(buttonElement, false);
        }
    }

    async handleCancelDeletion(userId, userEmail, buttonElement) {
        if (!await this.confirmAction(`Cancel scheduled deletion for user "${userEmail}"?`)) {
            return;
        }

        DOMUtils.setLoadingState(buttonElement, true);

        try {
            const data = await AdminUsersAPI.cancelUserDeletion(userId);

            if (data.success) {
                NotificationManager.show(data.message, 'success');
                this.refreshPageAfterDelay();
            } else {
                NotificationManager.show(data.message, 'error');
                DOMUtils.setLoadingState(buttonElement, false);
            }
        } catch (error) {
            console.error('Error cancelling deletion:', error);
            NotificationManager.show('Error cancelling deletion', 'error');
            DOMUtils.setLoadingState(buttonElement, false);
        }
    }

    handleViewDetails(userId) {
        // Navigation is handled by the link href, no JS needed
        console.log('Viewing details for user:', userId);
    }

    async confirmAction(message) {
        return new Promise((resolve) => {
            // You could use a custom confirm modal here
            resolve(confirm(message));
        });
    }

    refreshPageAfterDelay() {
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    }

    // Optional: Add search/filter functionality
    initSearch() {
        const searchInput = document.querySelector('#userSearch');
        if (searchInput) {
            const debouncedSearch = DOMUtils.debounce((value) => {
                this.performSearch(value);
            }, 300);

            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }
    }

    async performSearch(query) {
        // Implement search functionality if needed
        console.log('Searching users:', query);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminUsersManager = new AdminUsersManager();

    // Refresh AOS if available
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
});

// Keep global functions for backward compatibility (can be removed later)
window.cancelUserDeletion = (userId, userEmail) => {
    window.adminUsersManager?.handleCancelDeletion(userId, userEmail);
};

window.deactivateUser = (userId, userEmail) => {
    window.adminUsersManager?.handleDeactivateUser(userId, userEmail);
};

window.reactivateUser = (userId, userEmail) => {
    window.adminUsersManager?.handleReactivateUser(userId, userEmail);
};

window.AdminUsersManager = AdminUsersManager;
window.AdminUsersAPI = AdminUsersAPI;