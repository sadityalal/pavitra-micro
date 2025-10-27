document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 10) {
                this.value = this.value.substring(0, 10);
            }
        });
    }
    const pinInput = document.getElementById('postal_code');
    if (pinInput) {
        pinInput.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
            if (this.value.length > 6) {
                this.value = this.value.substring(0, 6);
            }
        });
    }
    const addAddressForm = document.querySelector('#addAddressModal form');
    if (addAddressForm) {
        addAddressForm.addEventListener('submit', function() {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addAddressModal'));
            setTimeout(() => {
                modal.hide();
            }, 1000);
        });
    }
});