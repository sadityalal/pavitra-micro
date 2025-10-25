document.addEventListener('DOMContentLoaded', function() {
    initializeRegistrationForm();
});

function initializeRegistrationForm() {
    initializePhoneNumberInput();
    initializePasswordValidation();
    initializePasswordToggle();
    initializeFormSubmission();
    initializeCustomDatePicker();
}

function initializePhoneNumberInput() {
    const countryCodeBtn = document.getElementById('countryCodeBtn');
    const selectedCountryCode = document.getElementById('selectedCountryCode');
    const selectedCountryFlag = document.getElementById('selectedCountryFlag');
    const countryCodeInput = document.getElementById('country_code');
    const countryNameInput = document.getElementById('country_name');
    const phoneInput = document.getElementById('phone');
    const phoneFormatHint = document.getElementById('phone-format-hint');
    setCountry('+91', '🇮🇳', '10', 'India');
    document.querySelectorAll('.country-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const code = this.getAttribute('data-code');
            const flag = this.getAttribute('data-flag');
            const maxLength = this.getAttribute('data-maxlength');
            const country = this.getAttribute('data-country');
            setCountry(code, flag, maxLength, country);
            document.querySelectorAll('.country-option').forEach(opt => {
                opt.classList.remove('active');
            });
            this.classList.add('active');
            const dropdown = bootstrap.Dropdown.getInstance(countryCodeBtn);
            if (dropdown) {
                dropdown.hide();
            }
        });
    });
    function setCountry(code, flag, maxLength, country) {
        selectedCountryCode.textContent = code;
        selectedCountryFlag.textContent = flag;
        countryCodeInput.value = code;
        countryNameInput.value = country;
        phoneInput.setAttribute('maxlength', maxLength);
        phoneInput.setAttribute('pattern', `[0-9]{${maxLength}}`);
        phoneInput.setAttribute('data-current-maxlength', maxLength);
        phoneInput.placeholder = `Enter phone number (${maxLength} digits)`;
        updatePhoneFormatHint(code, maxLength, country);
        phoneInput.classList.remove('is-invalid', 'is-valid');
        if (phoneInput.value) {
            validatePhoneNumber(phoneInput);
        }
    }
    phoneInput.addEventListener('input', function() {
        let value = this.value.replace(/\D/g, '');
        const maxLength = parseInt(this.getAttribute('data-current-maxlength') || this.getAttribute('maxlength'));
        if (value.length > maxLength) {
            value = value.substring(0, maxLength);
        }
        this.value = value;
        validatePhoneNumber(this);
    });
    phoneInput.addEventListener('blur', function() {
        validatePhoneNumber(this);
    });
    updatePhoneFormatHint('+91', '10', 'India');
}

function updatePhoneFormatHint(countryCode, maxLength, countryName) {
    const phoneFormatHint = document.getElementById('phone-format-hint');
    let example = '';
    switch(countryCode) {
        case '+91':
            example = '9876543210';
            break;
        case '+1':
            example = '5551234567';
            break;
        case '+44':
            example = '7911123456';
            break;
        case '+61':
            example = '412345678';
            break;
        case '+65':
            example = '91234567';
            break;
        case '+971':
            example = '501234567';
            break;
        case '+86':
            example = '13123456789';
            break;
        case '+81':
            example = '9012345678';
            break;
        case '+49':
            example = '15123456789';
            break;
        case '+33':
            example = '612345678';
            break;
        case '+7':
            example = '9123456789';
            break;
        default:
            example = '1234567890';
    }
    phoneFormatHint.textContent = `${countryName} format: ${example} (${maxLength} digits)`;
    phoneFormatHint.className = 'form-text text-info small';
}

function validatePhoneNumber(input) {
    const value = input.value.replace(/\D/g, '');
    const maxLength = parseInt(input.getAttribute('data-current-maxlength') || input.getAttribute('maxlength'));
    if (value && value.length !== maxLength) {
        input.classList.add('is-invalid');
        input.classList.remove('is-valid');
        return false;
    } else if (value && value.length === maxLength) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    } else {
        input.classList.remove('is-invalid', 'is-valid');
        return null;
    }
}

function initializePasswordValidation() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordMatchFeedback = document.getElementById('password-match-feedback');
    function validatePasswordMatch() {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        if (!confirmPassword) {
            passwordMatchFeedback.textContent = '';
            confirmPasswordInput.classList.remove('is-invalid', 'is-valid');
            return;
        }
        if (password === confirmPassword && password.length >= 6) {
            passwordMatchFeedback.textContent = '✓ Passwords match';
            passwordMatchFeedback.className = 'form-text text-success';
            confirmPasswordInput.classList.remove('is-invalid');
            confirmPasswordInput.classList.add('is-valid');
        } else {
            passwordMatchFeedback.textContent = '✗ Passwords do not match';
            passwordMatchFeedback.className = 'form-text text-danger';
            confirmPasswordInput.classList.remove('is-valid');
            confirmPasswordInput.classList.add('is-invalid');
        }
    }
    passwordInput.addEventListener('input', validatePasswordMatch);
    confirmPasswordInput.addEventListener('input', validatePasswordMatch);
}

function initializePasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
}

function initializeFormSubmission() {
    const form = document.getElementById('registerForm');
    form.addEventListener('submit', function(e) {
        const phoneInput = document.getElementById('phone');
        const phoneValue = phoneInput.value.replace(/\D/g, '');
        const maxLength = parseInt(phoneInput.getAttribute('data-current-maxlength') || phoneInput.getAttribute('maxlength'));
        const existingAlerts = document.querySelectorAll('.alert.alert-danger');
        existingAlerts.forEach(alert => alert.remove());
        if (phoneValue && phoneValue.length !== maxLength) {
            e.preventDefault();
            phoneInput.classList.add('is-invalid');
            phoneInput.focus();
            const countryName = document.getElementById('country_name').value;
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
            errorDiv.innerHTML = `
                Please enter a valid ${maxLength}-digit phone number for ${countryName}.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            form.prepend(errorDiv);
            errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return false;
        }
        return true;
    });
}

function initializeCustomDatePicker() {
    const existingDate = document.getElementById('date_of_birth').value;
    if (existingDate) {
        const [year, month, day] = existingDate.split('-');
        document.getElementById('birth_year').value = year;
        document.getElementById('birth_month').value = month;
        document.getElementById('birth_day').value = day;
    }
}

function updateCustomDate() {
    const year = document.getElementById('birth_year').value;
    const month = document.getElementById('birth_month').value;
    const day = document.getElementById('birth_day').value;
    if (year && month && day) {
        const formattedDate = `${year}-${month}-${day}`;
        document.getElementById('date_of_birth').value = formattedDate;
    } else {
        document.getElementById('date_of_birth').value = '';
    }
}