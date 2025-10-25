class CheckoutManager {
    constructor() {
        this.init();
    }
    init() {
        this.initializeEventListeners();
        this.initializeFormValidation();
        console.log('Checkout Manager initialized');
    }
    initializeEventListeners() {
        const billingSameCheckbox = document.getElementById('billing-same');
        const billingAddressSection = document.querySelector('.billing-address-section');
        if (billingSameCheckbox && billingAddressSection) {
            billingSameCheckbox.addEventListener('change', () => {
                this.toggleBillingAddress(billingSameCheckbox.checked);
            });
        }
        const paymentMethods = document.querySelectorAll('input[name="payment_method"]');
        paymentMethods.forEach(method => {
            method.addEventListener('change', () => {
                this.togglePaymentDetails(method.value);
            });
        });
        const checkoutForm = document.getElementById('checkoutForm');
        if (checkoutForm) {
            checkoutForm.addEventListener('submit', (e) => this.handleFormSubmission(e));
        }
        this.togglePaymentDetails('cash_on_delivery');
    }
    initializeFormValidation() {
        const checkoutForm = document.getElementById('checkoutForm');
        if (checkoutForm) {
            checkoutForm.addEventListener('input', () => {
                this.validateForm();
            });
        }
    }
    toggleBillingAddress(isSame) {
        const billingAddressSection = document.querySelector('.billing-address-section');
        const billingAddressInputs = document.querySelectorAll('input[name="billing_address_id"]');
        if (isSame) {
            billingAddressSection.classList.add('d-none');
            billingAddressInputs.forEach(radio => {
                radio.checked = false;
                radio.required = false;
            });
        } else {
            billingAddressSection.classList.remove('d-none');
            billingAddressInputs.forEach(radio => {
                radio.required = true;
                if (!document.querySelector('input[name="billing_address_id"]:checked')) {
                    const firstBilling = document.querySelector('input[name="billing_address_id"]');
                    if (firstBilling) firstBilling.checked = true;
                }
            });
        }
    }
    togglePaymentDetails(paymentMethod) {
        document.querySelectorAll('.payment-details').forEach(detail => {
            detail.classList.add('d-none');
        });
        const detailsElement = document.getElementById(paymentMethod + '-details');
        if (detailsElement) {
            detailsElement.classList.remove('d-none');
        }
        this.handlePaymentMethodRequirements(paymentMethod);
    }
    handlePaymentMethodRequirements(paymentMethod) {
        const paymentFields = document.querySelectorAll('.payment-details input, .payment-details select');
        paymentFields.forEach(field => {
            field.required = false;
        });
        switch (paymentMethod) {
            case 'upi':
                const upiField = document.getElementById('upi_id');
                if (upiField) upiField.required = true;
                break;
            case 'credit_card':
                const cardFields = ['card-number', 'expiry', 'cvv', 'card-name'];
                cardFields.forEach(fieldId => {
                    const field = document.getElementById(fieldId);
                    if (field) field.required = true;
                });
                break;
            case 'netbanking':
                const bankField = document.getElementById('bank');
                if (bankField) bankField.required = true;
                break;
        }
    }
    validateForm() {
        const placeOrderBtn = document.getElementById('placeOrderBtn');
        const termsCheckbox = document.getElementById('terms');
        const shippingAddress = document.querySelector('input[name="shipping_address_id"]:checked');
        let isValid = true;
        if (!shippingAddress) {
            isValid = false;
        }
        if (!termsCheckbox || !termsCheckbox.checked) {
            isValid = false;
        }
        if (placeOrderBtn) {
            placeOrderBtn.disabled = !isValid;
        }
        return isValid;
    }
    async handleFormSubmission(e) {
    e.preventDefault();
    if (!this.validateForm()) {
        NotificationManager.show('Please fill in all required fields', 'warning');
        return;
    }
    const form = e.target;
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    const originalText = placeOrderBtn.innerHTML;
    try {
        placeOrderBtn.disabled = true;
        placeOrderBtn.innerHTML = '<i class="bi bi-arrow-repeat spinner"></i> Processing Order...';
        const formData = new FormData(form);
        const formAction = form.getAttribute('action') || form.action;
        console.log('Form action:', formAction);
        if (!formAction || formAction === 'undefined') {
            throw new Error('Form action is undefined. Form HTML might be malformed.');
        }
        const response = await fetch(formAction, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': this.getCSRFToken()
            }
        });
        const result = await response.json();
        if (result.success) {
            NotificationManager.show('Order placed successfully! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = result.data.redirect_url || result.redirect_url;
            }, 1500);
        } else {
            NotificationManager.show(result.message || 'Error placing order. Please try again.', 'danger');
            placeOrderBtn.disabled = false;
            placeOrderBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Checkout error:', error);
        NotificationManager.show('An error occurred during checkout. Please try again.', 'danger');
        placeOrderBtn.disabled = false;
        placeOrderBtn.innerHTML = originalText;
        this.logJSError('Checkout Form Submission', error.message, window.location.href);
    }
}
    getCSRFToken() {
        return ApiClient.getCSRFToken();
    }
    logJSError(type, message, url) {
        console.error('JS Error:', { type, message, url });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    new CheckoutManager();
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
    const cardNumberInput = document.getElementById('card-number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            let matches = value.match(/\d{4,16}/g);
            let match = matches && matches[0] || '';
            let parts = [];
            for (let i = 0, len = match.length; i < len; i += 4) {
                parts.push(match.substring(i, i + 4));
            }
            if (parts.length) {
                e.target.value = parts.join(' ');
            } else {
                e.target.value = value;
            }
        });
    }
    const expiryInput = document.getElementById('expiry');
    if (expiryInput) {
        expiryInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                e.target.value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
        });
    }
});

window.CheckoutManager = CheckoutManager;