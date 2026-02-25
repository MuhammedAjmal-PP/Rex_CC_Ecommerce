/**
 * Coupon apply / remove  –  checkout sidebar AJAX
 */

function getCSRF() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

function formatCurrency(val) {
    return parseFloat(val).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

/* ── Apply ────────────────────────────────────── */

async function applyCoupon() {
    const input = document.getElementById('coupon-code-input');
    const errorDiv = document.getElementById('coupon-error');
    const code = (input?.value || '').trim();

    errorDiv.style.display = 'none';
    errorDiv.textContent = '';

    if (!code) {
        errorDiv.textContent = 'Please enter a coupon code.';
        errorDiv.style.display = 'block';
        return;
    }

    const btn = document.getElementById('apply-coupon-btn');
    const origText = btn.textContent;
    btn.textContent = 'Applying…';
    btn.disabled = true;

    try {
        const resp = await fetch('/coupon/apply/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ code }),
        });

        const data = await resp.json();

        if (data.success) {
            // Show applied state
            document.getElementById('coupon-applied').style.display = 'block';
            document.getElementById('coupon-applied-code').textContent = data.coupon_code;
            document.getElementById('coupon-discount-amount').textContent = '-₹' + formatCurrency(data.discount_amount);

            // Hide input & available list
            document.getElementById('coupon-input-group').style.display = 'none';
            const availDiv = document.getElementById('available-coupons');
            if (availDiv) availDiv.style.display = 'none';

            // Update grand total
            document.getElementById('grand-total-display').textContent = '₹' + formatCurrency(data.new_grand_total);

            // Update ReviewState if exists (for review step)
            if (window.CheckoutState) {
                CheckoutState.couponCode = data.coupon_code;
                CheckoutState.couponDiscount = data.discount_amount;
            }
        } else {
            errorDiv.textContent = data.message || 'Failed to apply coupon.';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        console.error('Apply coupon error:', err);
        errorDiv.textContent = 'Connection error. Please try again.';
        errorDiv.style.display = 'block';
    } finally {
        btn.textContent = origText;
        btn.disabled = false;
    }
}

/* ── Remove ───────────────────────────────────── */

async function removeCoupon() {
    try {
        const resp = await fetch('/coupon/remove/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRF(),
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: '{}',
        });

        const data = await resp.json();

        if (data.success) {
            // Hide applied state
            document.getElementById('coupon-applied').style.display = 'none';
            document.getElementById('coupon-applied-code').textContent = '';
            document.getElementById('coupon-discount-amount').textContent = '';

            // Show input
            document.getElementById('coupon-input-group').style.display = 'block';
            document.getElementById('coupon-code-input').value = '';

            const availDiv = document.getElementById('available-coupons');
            if (availDiv) availDiv.style.display = 'block';

            // Update grand total
            document.getElementById('grand-total-display').textContent = '₹' + formatCurrency(data.grand_total);

            if (window.CheckoutState) {
                CheckoutState.couponCode = null;
                CheckoutState.couponDiscount = null;
            }
        }
    } catch (err) {
        console.error('Remove coupon error:', err);
    }
}

/* ── Quick-fill from available coupons list ───── */

function useCouponCode(code) {
    const input = document.getElementById('coupon-code-input');
    if (input) {
        input.value = code;
        applyCoupon();
    }
}
