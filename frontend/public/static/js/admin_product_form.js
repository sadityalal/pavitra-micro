document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Product Form initialized');
    const categorySelect = document.getElementById('category_id');
    const gstRateInput = document.getElementById('gst_rate');
    const hsnCodeInput = document.getElementById('hsn_code');
    const basePriceInput = document.getElementById('base_price');
    const isGstInclusiveSelect = document.getElementById('is_gst_inclusive');
    const gstInfoText = document.getElementById('gst-info-text');
    const gstCalculationPreview = document.getElementById('gst-calculation-preview');
    const gstInclusiveStatus = document.getElementById('gst-inclusive-status');
    initGSTFunctionality();
    function initGSTFunctionality() {
        if (categorySelect) {
            categorySelect.addEventListener('change', handleCategoryChange);
            if (categorySelect.value) {
                handleCategoryChange();
            }
        }
        if (gstRateInput && basePriceInput) {
            gstRateInput.addEventListener('input', updateGSTCalculation);
            basePriceInput.addEventListener('input', updateGSTCalculation);
        }
        if (isGstInclusiveSelect) {
            isGstInclusiveSelect.addEventListener('change', updateGSTInclusiveStatus);
            updateGSTInclusiveStatus();
        }
        setupSlugGeneration();
        setupHSNValidation();
    }
    function handleCategoryChange() {
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const gstRate = selectedOption.getAttribute('data-gst-rate');
        const hsnCode = selectedOption.getAttribute('data-hsn-code');
        if (gstRate && gstRateInput) {
            gstRateInput.value = gstRate;
            gstRateInput.classList.add('gst-calculation-animate');
            setTimeout(() => {
                gstRateInput.classList.remove('gst-calculation-animate');
            }, 300);
        }
        if (hsnCode && hsnCodeInput) {
            hsnCodeInput.value = hsnCode;
        }
        updateCategoryGSTInfo(selectedOption);
        updateGSTCalculation();
    }
    function updateCategoryGSTInfo(selectedOption) {
        const categoryName = selectedOption.text.split(' (GST:')[0];
        const gstRate = selectedOption.getAttribute('data-gst-rate') || '18.00';
        const hsnCode = selectedOption.getAttribute('data-hsn-code') || 'Not specified';
        let infoHTML = '';
        if (selectedOption.value) {
            infoHTML = `
                <strong>${categoryName}</strong><br>
                <small>
                    Default GST Rate: <span class="badge bg-primary">${gstRate}%</span> |
                    HSN Code: <code>${hsnCode}</code>
                </small>
            `;
        } else {
            infoHTML = 'Select a category to see GST information';
        }
        gstInfoText.innerHTML = infoHTML;
    }
    function updateGSTCalculation() {
        const basePrice = parseFloat(basePriceInput.value) || 0;
        const gstRate = parseFloat(gstRateInput.value) || 0;
        const isGstInclusive = isGstInclusiveSelect.value === '1';
        let calculationHTML = '';
        if (basePrice > 0 && gstRate > 0) {
            if (isGstInclusive) {
                const gstAmount = (basePrice * gstRate) / (100 + gstRate);
                const baseAmount = basePrice - gstAmount;
                calculationHTML = `
                    <div class="row small">
                        <div class="col-6">Base Price:</div>
                        <div class="col-6 text-end">₹${baseAmount.toFixed(2)}</div>
                        <div class="col-6">GST (${gstRate}%):</div>
                        <div class="col-6 text-end">₹${gstAmount.toFixed(2)}</div>
                        <div class="col-6 border-top"><strong>Total Price:</strong></div>
                        <div class="col-6 border-top text-end"><strong>₹${basePrice.toFixed(2)}</strong></div>
                    </div>
                `;
            } else {
                const gstAmount = (basePrice * gstRate) / 100;
                const totalAmount = basePrice + gstAmount;
                calculationHTML = `
                    <div class="row small">
                        <div class="col-6">Base Price:</div>
                        <div class="col-6 text-end">₹${basePrice.toFixed(2)}</div>
                        <div class="col-6">+ GST (${gstRate}%):</div>
                        <div class="col-6 text-end">₹${gstAmount.toFixed(2)}</div>
                        <div class="col-6 border-top"><strong>Total Price:</strong></div>
                        <div class="col-6 border-top text-end"><strong>₹${totalAmount.toFixed(2)}</strong></div>
                    </div>
                `;
            }
        } else {
            calculationHTML = 'Enter price and GST rate to see calculation';
        }
        gstCalculationPreview.innerHTML = calculationHTML;
    }
    function updateGSTInclusiveStatus() {
        const isGstInclusive = isGstInclusiveSelect.value === '1';
        if (isGstInclusive) {
            gstInclusiveStatus.innerHTML = '✅ Price includes GST (recommended)';
            gstInclusiveStatus.className = 'text-muted text-success';
        } else {
            gstInclusiveStatus.innerHTML = '⚠️ GST will be calculated separately';
            gstInclusiveStatus.className = 'text-muted text-warning';
        }
        updateGSTCalculation();
    }
    function setupSlugGeneration() {
        const nameInput = document.getElementById('name');
        const slugInput = document.getElementById('slug');
        if (nameInput && slugInput) {
            nameInput.addEventListener('blur', function() {
                if (!slugInput.value) {
                    const slug = generateSlug(nameInput.value);
                    slugInput.value = slug;
                }
            });
        }
    }
    function generateSlug(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
    function setupHSNValidation() {
        if (hsnCodeInput) {
            hsnCodeInput.addEventListener('blur', function() {
                const hsnCode = hsnCodeInput.value.trim();
                if (hsnCode && !isValidHSNCode(hsnCode)) {
                    showHSNWarning(hsnCode);
                }
            });
        }
    }
    function isValidHSNCode(code) {
        const hsnPattern = /^\d{4,8}$/;
        return hsnPattern.test(code);
    }
    function showHSNWarning(code) {
        const existingWarning = hsnCodeInput.parentNode.querySelector('.hsn-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
        const warningDiv = document.createElement('div');
        warningDiv.className = 'form-text text-warning hsn-warning';
        warningDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle"></i>
            HSN code "${code}" may not be valid. Please verify.
        `;
        hsnCodeInput.parentNode.appendChild(warningDiv);
    }
    const productForm = document.getElementById('product-form');
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            if (!validateGSTFields()) {
                e.preventDefault();
                showValidationError();
            }
        });
    }
    function validateGSTFields() {
        const gstRate = parseFloat(gstRateInput.value);
        const hsnCode = hsnCodeInput.value.trim();
        if (!gstRate || gstRate <= 0) {
            return false;
        }
        if (!hsnCode) {
            return false;
        }
        return true;
    }
    function showValidationError() {
        alert('Please fill all GST fields correctly. GST Rate and HSN Code are required.');
    }
    window.adminProductForm = {
        updateGSTCalculation,
        handleCategoryChange,
        validateGSTFields
    };
});

function calculateGSTAmount(price, gstRate, isInclusive = true) {
    if (isInclusive) {
        return (price * gstRate) / (100 + gstRate);
    } else {
        return (price * gstRate) / 100;
    }
}

function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}