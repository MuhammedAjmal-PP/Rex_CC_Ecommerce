/**
 * Checkout Orchestrator
 * Handles Step Navigation, State Management, and Final Submission
 */

const CheckoutState = {
    step: 1,
    selectedAddressId: null,
    selectedPaymentMethod: 'cod',
    deliveryData: {} // To store address details for review
};

document.addEventListener('DOMContentLoaded', () => {
    initCheckout();
});

function initCheckout() {
    // Check if default address exists and auto-select
    const defaultAddr = document.querySelector('.checkout-address-card.default-selection');
    if (defaultAddr) {
        selectAddress(defaultAddr, defaultAddr.dataset.addressId);
    }
}

/**
 * Navigation Handler
 * @param {number} stepNum - 1: Address, 2: Payment, 3: Review
 */
function goToStep(stepNum) {
    if (!validateStep(CheckoutState.step, stepNum)) return;

    // Update UI Steps
    document.querySelectorAll('.chk-step').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.chk-step-item').forEach(el => el.classList.remove('active'));

    // Show Content
    if (stepNum === 1) document.getElementById('step-address').style.display = 'block';
    if (stepNum === 2) document.getElementById('step-payment').style.display = 'block';
    if (stepNum === 3) {
        document.getElementById('step-review').style.display = 'block';
        populateReview(); // specific function in review.js (or inline here if small)
    }

    // Update Stepper
    if (stepNum === 1) updateStepper(1);
    if (stepNum === 2) updateStepper(2);
    if (stepNum === 3) updateStepper(3);

    CheckoutState.step = stepNum;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateStepper(activeStep) {
    // Reset all
    const s1 = document.getElementById('stepper-address');
    const s2 = document.getElementById('stepper-payment');
    const s3 = document.getElementById('stepper-review');

    s1.className = 'chk-step-item'; 
    s2.className = 'chk-step-item';
    s3.className = 'chk-step-item';

    // Set logic
    if (activeStep >= 1) s1.classList.add('active'); // Address is always "active" or "completed" if passed
    if (activeStep > 1) {
        s1.classList.add('completed');
        s1.classList.remove('active');
        s2.classList.add('active');
    }
    if (activeStep > 2) {
        s2.classList.add('completed');
        s2.classList.remove('active');
        s3.classList.add('active');
    }
}

function validateStep(current, next) {
    // Moving backwards is always allowed
    if (next < current) return true;

    // 1 -> 2 (Address -> Payment)
    if (current === 1 && next === 2) {
        if (!CheckoutState.selectedAddressId) {
            alert("Please select a delivery address.");
            return false;
        }
    }

    return true;
}

// --- SHARED GLOBALS (Ideally modular imports, but using global scope for template simplicity) ---
window.CheckoutState = CheckoutState;
window.goToStep = goToStep;
