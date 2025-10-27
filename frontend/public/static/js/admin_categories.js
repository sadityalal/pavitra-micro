// Category Health Management
class CategoryHealthManager {
    constructor() {
        this.emptyCategories = [];
        this.lowStockCategories = [];
        this.healthyCategories = [];
        this.init();
    }

    init() {
        this.calculateCategoryHealth();
        this.setupEventListeners();
        this.updateHealthCounts();
        console.log('Category Health Manager initialized');
    }

    calculateCategoryHealth() {
        const categoryRows = document.querySelectorAll('.category-row');

        this.emptyCategories = Array.from(categoryRows).filter(row => {
            return parseInt(row.getAttribute('data-product-count')) === 0;
        });

        this.lowStockCategories = Array.from(categoryRows).filter(row => {
            const count = parseInt(row.getAttribute('data-product-count'));
            return count > 0 && count <= 2;
        });

        this.healthyCategories = Array.from(categoryRows).filter(row => {
            const count = parseInt(row.getAttribute('data-product-count'));
            return count > 2;
        });
    }

    updateHealthCounts() {
        // Update card counts
        document.getElementById('empty-categories-count').textContent = this.emptyCategories.length;
        document.getElementById('low-stock-categories-count').textContent = this.lowStockCategories.length;
        document.getElementById('healthy-categories-count').textContent = this.healthyCategories.length;

        // Update badge counts
        const emptyBadge = document.getElementById('empty-categories-badge');
        const lowStockBadge = document.getElementById('low-stock-badge');

        if (emptyBadge) emptyBadge.textContent = this.emptyCategories.length;
        if (lowStockBadge) lowStockBadge.textContent = this.lowStockCategories.length;

        // Update overall health
        const totalCategories = this.emptyCategories.length + this.lowStockCategories.length + this.healthyCategories.length;
        const healthPercentage = totalCategories > 0 ?
            Math.round((this.healthyCategories.length / totalCategories) * 100) : 100;

        const healthScoreElement = document.getElementById('overall-health-score');
        if (healthScoreElement) {
            healthScoreElement.textContent = `${healthPercentage}%`;
            healthScoreElement.className = healthPercentage >= 80 ? 'text-success' :
                                          healthPercentage >= 60 ? 'text-warning' : 'text-danger';
        }
    }

    setupEventListeners() {
        // Clickable stats cards
        document.querySelectorAll('.clickable-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const action = card.getAttribute('data-action');
                this.handleCardAction(action);
            });
        });

        // Quick action cards
        document.querySelectorAll('.quick-action-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const action = card.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });

        // Search functionality
        const searchInput = document.getElementById('categorySearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.filterCategories(e.target.value);
            }, 300));
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshCategories');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshCategories();
            });
        }

        // Bulk actions
        const applyBulkBtn = document.getElementById('applyBulkAction');
        if (applyBulkBtn) {
            applyBulkBtn.addEventListener('click', () => {
                this.applyBulkAction();
            });
        }

        // Table row actions
        this.delegateEvents('.edit-category', 'click', this.handleEditCategory.bind(this));
        this.delegateEvents('.view-products', 'click', this.handleViewProducts.bind(this));
        this.delegateEvents('.add-products', 'click', this.handleAddProducts.bind(this));
        this.delegateEvents('.toggle-category', 'click', this.handleToggleStatus.bind(this));
        this.delegateEvents('.delete-category', 'click', this.handleDeleteCategory.bind(this));
    }

    delegateEvents(selector, event, handler) {
        document.addEventListener(event, (e) => {
            if (e.target.matches(selector) || e.target.closest(selector)) {
                handler(e);
            }
        });
    }

    handleCardAction(action) {
        switch(action) {
            case 'view-all':
                this.showAllCategories();
                break;
            case 'view-empty':
                this.showEmptyCategories();
                break;
            case 'view-low-stock':
                this.showLowStockCategories();
                break;
            case 'view-healthy':
                this.showHealthyCategories();
                break;
        }
    }

    handleQuickAction(action) {
        switch(action) {
            case 'fix-empty-categories':
                this.fixEmptyCategories();
                break;
            case 'restock-categories':
                this.showRestockSuggestions();
                break;
            case 'bulk-edit':
                this.startBulkEdit();
                break;
            case 'export-report':
                this.exportHealthReport();
                break;
        }
    }

    showAllCategories() {
        this.showCategories('all', 'All Categories');
    }

    showEmptyCategories() {
        this.showCategories('empty', 'Empty Categories');
    }

    showLowStockCategories() {
        this.showCategories('low-stock', 'Low Stock Categories');
    }

    showHealthyCategories() {
        this.showCategories('healthy', 'Healthy Categories');
    }

    showCategories(filter, title) {
        const rows = document.querySelectorAll('.category-row');
        let visibleCount = 0;

        rows.forEach(row => {
            const productCount = parseInt(row.getAttribute('data-product-count'));
            let show = false;

            switch(filter) {
                case 'empty':
                    show = productCount === 0;
                    break;
                case 'low-stock':
                    show = productCount > 0 && productCount <= 2;
                    break;
                case 'healthy':
                    show = productCount > 2;
                    break;
                default:
                    show = true;
            }

            row.style.display = show ? '' : 'none';
            if (show) visibleCount++;
        });

        this.showNotification(`Showing ${visibleCount} ${title.toLowerCase()}`, 'info');
        this.addActivity(`viewed ${title.toLowerCase()}`);
    }

    filterCategories(searchTerm) {
        const rows = document.querySelectorAll('.category-row');
        const term = searchTerm.toLowerCase();
        let visibleCount = 0;

        rows.forEach(row => {
            const categoryName = row.querySelector('h6').textContent.toLowerCase();
            const hindiName = row.querySelector('.text-info')?.textContent.toLowerCase() || '';

            if (categoryName.includes(term) || hindiName.includes(term)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (searchTerm) {
            this.showNotification(`Found ${visibleCount} categories matching "${searchTerm}"`, 'info');
            this.addActivity(`searched for "${searchTerm}"`);
        }
    }

    refreshCategories() {
        this.showNotification('Refreshing category data...', 'info');
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    applyBulkAction() {
        const bulkAction = document.getElementById('bulkAction');
        const selectedCategories = this.getSelectedCategories();

        if (!bulkAction.value) {
            this.showNotification('Please select a bulk action', 'warning');
            return;
        }

        if (selectedCategories.length === 0) {
            this.showNotification('Please select at least one category', 'warning');
            return;
        }

        this.performBulkAction(bulkAction.value, selectedCategories);
    }

    getSelectedCategories() {
        const selected = [];
        document.querySelectorAll('.category-checkbox:checked').forEach(checkbox => {
            selected.push(checkbox.value);
        });
        return selected;
    }

    async performBulkAction(action, categoryIds) {
        this.showNotification(`Performing bulk ${action} on ${categoryIds.length} categories...`, 'info');

        // Simulate API call
        await this.delay(1000);

        categoryIds.forEach((categoryId, index) => {
            setTimeout(() => {
                const row = document.querySelector(`[data-category-id="${categoryId}"]`);
                if (row) {
                    this.animateElement(row, 'pulse');

                    switch (action) {
                        case 'activate':
                            const activateBtn = row.querySelector('.toggle-category[data-action="activate"]');
                            if (activateBtn) activateBtn.click();
                            break;
                        case 'deactivate':
                            const deactivateBtn = row.querySelector('.toggle-category[data-action="deactivate"]');
                            if (deactivateBtn) deactivateBtn.click();
                            break;
                        case 'feature':
                            const starIcon = row.querySelector('.bi-star');
                            if (starIcon) {
                                starIcon.className = 'bi bi-star-fill text-warning';
                            }
                            break;
                        case 'unfeature':
                            const starFillIcon = row.querySelector('.bi-star-fill');
                            if (starFillIcon) {
                                starFillIcon.className = 'bi bi-star text-muted';
                            }
                            break;
                        case 'delete':
                            setTimeout(() => row.remove(), 300);
                            break;
                    }
                }
            }, index * 200);
        });

        setTimeout(() => {
            this.calculateCategoryHealth();
            this.updateHealthCounts();
            this.showNotification(`Bulk ${action} completed successfully!`, 'success');
        }, categoryIds.length * 200 + 500);
    }

    handleEditCategory(e) {
        const categoryId = e.currentTarget.getAttribute('data-category-id');
        const row = e.currentTarget.closest('.category-row');
        const categoryName = row.querySelector('h6').textContent;

        this.showNotification(`Editing: ${categoryName}`, 'info');
        // Implement your edit logic here
        console.log('Edit category:', categoryId);
    }

    handleViewProducts(e) {
        const categoryId = e.currentTarget.getAttribute('data-category-id');
        window.location.href = `/admin/products?category=${categoryId}`;
    }

    handleAddProducts(e) {
        const categoryId = e.currentTarget.getAttribute('data-category-id');
        window.location.href = `/admin/new-product?category=${categoryId}`;
    }

    handleToggleStatus(e) {
        const categoryId = e.currentTarget.getAttribute('data-category-id');
        const action = e.currentTarget.getAttribute('data-action');
        const row = e.currentTarget.closest('.category-row');
        const categoryName = row.querySelector('h6').textContent;

        this.showNotification(`${action === 'activate' ? 'Activating' : 'Deactivating'} ${categoryName}...`, 'info');

        // Simulate API call
        setTimeout(() => {
            const statusBadge = row.querySelector('.badge.bg-success, .badge.bg-secondary');
            const toggleButton = e.currentTarget;

            if (action === 'activate') {
                statusBadge.className = 'badge bg-success';
                statusBadge.textContent = 'Active';
                toggleButton.setAttribute('data-action', 'deactivate');
                toggleButton.className = 'btn btn-outline-warning toggle-category';
                toggleButton.innerHTML = '<i class="bi bi-pause"></i>';
                toggleButton.title = 'Deactivate';
            } else {
                statusBadge.className = 'badge bg-secondary';
                statusBadge.textContent = 'Inactive';
                toggleButton.setAttribute('data-action', 'activate');
                toggleButton.className = 'btn btn-outline-success toggle-category';
                toggleButton.innerHTML = '<i class="bi bi-play"></i>';
                toggleButton.title = 'Activate';
            }

            this.animateElement(row, 'pulse');
            this.showNotification(`Category ${action}d successfully!`, 'success');
        }, 800);
    }

    handleDeleteCategory(e) {
        const categoryId = e.currentTarget.getAttribute('data-category-id');
        const row = e.currentTarget.closest('.category-row');
        const categoryName = row.querySelector('h6').textContent;

        if (confirm(`Are you sure you want to delete "${categoryName}"? This action cannot be undone.`)) {
            this.deleteCategory(categoryId, row);
        }
    }

    async deleteCategory(categoryId, row) {
        try {
            this.showNotification(`Deleting ${row.querySelector('h6').textContent}...`, 'info');

            // Simulate API call
            await this.delay(800);

            this.animateElement(row, 'pulse');
            setTimeout(() => {
                row.remove();
                this.calculateCategoryHealth();
                this.updateHealthCounts();
                this.showNotification('Category deleted successfully!', 'success');
            }, 600);
        } catch (error) {
            console.error('Error deleting category:', error);
            this.showNotification('Error deleting category', 'error');
        }
    }

    async fixEmptyCategories() {
        if (this.emptyCategories.length === 0) {
            this.showNotification('No empty categories found!', 'success');
            return;
        }

        this.showNotification(`Analyzing ${this.emptyCategories.length} empty categories...`, 'info');

        await this.delay(1500);

        const emptyList = this.emptyCategories.map(row => {
            const categoryName = row.querySelector('h6').textContent;
            const categoryId = row.getAttribute('data-category-id');
            return `
                <div class="alert alert-warning d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${categoryName}</strong>
                        <small class="d-block text-muted">ID: ${categoryId}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/admin/new-product?category=${categoryId}'">
                        <i class="bi bi-plus-circle"></i> Add Products
                    </button>
                </div>
            `;
        }).join('');

        const content = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                <strong>${this.emptyCategories.length} empty categories found</strong>
                <p class="mb-0 mt-1">These categories don't have any products and may need attention.</p>
            </div>
            ${emptyList}
        `;

        document.getElementById('healthReportContent').innerHTML = content;
        new bootstrap.Modal(document.getElementById('healthReportModal')).show();
    }

    showRestockSuggestions() {
        if (this.lowStockCategories.length === 0) {
            this.showNotification('No low stock categories found!', 'success');
            return;
        }

        const lowStockList = this.lowStockCategories.map(row => {
            const categoryName = row.querySelector('h6').textContent;
            const productCount = row.getAttribute('data-product-count');
            const categoryId = row.getAttribute('data-category-id');

            return `
                <div class="alert alert-danger d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${categoryName}</strong>
                        <small class="d-block text-muted">Only ${productCount} products remaining</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="window.location.href='/admin/products?category=${categoryId}'">
                        <i class="bi bi-box-arrow-in-up"></i> Restock
                    </button>
                </div>
            `;
        }).join('');

        const content = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>${this.lowStockCategories.length} categories need restocking</strong>
                <p class="mb-0 mt-2">These categories have low product counts and may need attention.</p>
            </div>
            ${lowStockList}
        `;

        document.getElementById('healthReportContent').innerHTML = content;
        new bootstrap.Modal(document.getElementById('healthReportModal')).show();
    }

    startBulkEdit() {
        this.showNotification('Bulk edit mode activated. Select categories to edit.', 'info');
        // Implement bulk edit UI
    }

    exportHealthReport() {
        const reportData = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.emptyCategories.length + this.lowStockCategories.length + this.healthyCategories.length,
                empty: this.emptyCategories.length,
                lowStock: this.lowStockCategories.length,
                healthy: this.healthyCategories.length
            },
            categories: Array.from(document.querySelectorAll('.category-row')).map(row => ({
                name: row.querySelector('h6').textContent,
                products: row.getAttribute('data-product-count'),
                health: row.getAttribute('data-health-status')
            }))
        };

        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `category-health-report-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('Category health report exported successfully!', 'success');
    }

    // Utility methods
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

    animateElement(element, animationClass) {
        element.classList.add(animationClass);
        setTimeout(() => {
            element.classList.remove(animationClass);
        }, 600);
    }

    showNotification(message, type = 'info') {
        // Use your existing NotificationManager or create a simple one
        if (window.NotificationManager) {
            NotificationManager.show(message, type);
        } else {
            // Fallback notification
            const alertClass = {
                'success': 'alert-success',
                'error': 'alert-danger',
                'warning': 'alert-warning',
                'info': 'alert-info'
            }[type] || 'alert-info';

            const alert = document.createElement('div');
            alert.className = `alert ${alertClass} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            const container = document.querySelector('.admin-content');
            container.insertBefore(alert, container.firstChild);

            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }

    addActivity(description) {
        console.log('Activity:', description);
        // Integrate with your activity logging system
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.categoryHealthManager = new CategoryHealthManager();
});