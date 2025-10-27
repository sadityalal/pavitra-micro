/**
 * Reactivate Account Page JavaScript
 * Minimal implementation leveraging common modules
 */

class ReactivateManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('Reactivate Manager initialized');
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Password toggle - uses common UI utility if available
        const passwordToggle = document.querySelector('.password-toggle');
        if (passwordToggle) {
            passwordToggle.addEventListener('click', (e) => this.togglePasswordVisibility(e));
        }

        // Form submission
        const form = document.getElementById('reactivateForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }

        // Debug info
        console.log('Reactivate - Next page:', document.getElementById('nextField')?.value || 'Not set');
        console.log('Reactivate - Email:', document.getElementById('email_display')?.value || 'Not set');
    }

    togglePasswordVisibility(e) {
        e.preventDefault();
        const button = e.currentTarget;
        const targetId = button.getAttribute('data-target');
        const passwordInput = document.getElementById(targetId);
        const icon = button.querySelector('i');

        if (passwordInput && icon) {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);

            // Update icon
            icon.classList.toggle('bi-eye');
            icon.classList.toggle('bi-eye-slash');
        }
    }

    handleFormSubmission(e) {
        const submitBtn = document.getElementById('submitBtn');
        const originalText = submitBtn.innerHTML;

        // Show loading state using common utilities if available
        if (window.DOMUtils && window.DOMUtils.setLoadingState) {
            window.DOMUtils.setLoadingState(submitBtn, true, 'Reactivating...');
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-arrow-repeat spinner-border spinner-border-sm me-2"></i>Reactivating...';
        }

        // Form will submit normally, this just handles the loading state
        // The backend will handle the actual reactivation logic
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ReactivateManager();
    console.log('Reactivate page initialized');
});