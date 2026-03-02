/**
 * Retry Payment — Razorpay
 *
 * Standalone script for retrying a failed Razorpay payment.
 * Used on both the order failure page and the order detail page.
 *
 * Required data attributes on the trigger button:
 *   data-order-number="ORD-XXXXXX"
 *
 * Required global:
 *   window.RAZORPAY_KEY_ID (set via template)
 */


/* ── Toast helper (matches site .toast-container / .toast-msg styles) ── */

function _showRetryToast(message, type) {
    type = type || 'error';

    // Re-use an existing container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Pick icon & accent colour
    const icons = { error: 'error', warning: 'warning', success: 'check_circle', info: 'info' };
    const colors = { error: '#dc3545', warning: '#f0ad4e', success: '#28a745', info: '#17a2b8' };
    const icon = icons[type] || icons.info;
    const color = colors[type] || colors.info;

    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    // toast.style.borderLeft = '4px solid ' + color;
    toast.innerHTML =
        '<span class="material-icons" style="color:' + color + ';font-size:20px;">' + icon + '</span> ' +
        '<span>' + message + '</span>';

    container.appendChild(toast);

    // Auto-dismiss after 5 seconds
    setTimeout(function () {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(function () { toast.remove(); }, 400);
    }, 5000);
}


/* ── Main retry flow ── */

function retryRazorpayPayment(btn) {
    const orderNumber = btn.dataset.orderNumber;
    if (!orderNumber) return;

    // Disable button and show loading
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="material-icons rotating">autorenew</span> Processing...';
    btn.disabled = true;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.querySelector('meta[name="csrf-token"]')?.content || '';

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('order_number', orderNumber);

    fetch('/razorpay/retry/', {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            _showRetryToast(data.error, 'error');
            _resetRetryBtn(btn, originalHTML);
            return;
        }

        // Open Razorpay checkout modal
        const options = {
            key: data.razorpay_key_id,
            amount: data.amount,
            currency: data.currency,
            name: data.name,
            description: data.description,
            order_id: data.razorpay_order_id,
            prefill: data.prefill || {},
            theme: { color: '#cd7f32' },
            handler: function (response) {
                // Payment successful — verify on server
                _retryVerifyPayment(csrfToken, response, data.order_number, btn, originalHTML);
            },
            modal: {
                ondismiss: function () {
                    // User closed modal — mark as failed
                    _retryMarkFailed(csrfToken, data.order_number, 'Payment cancelled by user', btn, originalHTML);
                },
            },
        };

        const rzp = new Razorpay(options);

        rzp.on('payment.failed', function (response) {
            const reason = response.error.description || 'Payment failed';
            _retryMarkFailed(csrfToken, data.order_number, reason, btn, originalHTML);
        });

        rzp.open();
    })
    .catch(err => {
        console.error('Retry payment failed:', err);
        _showRetryToast('Something went wrong. Please try again.', 'error');
        _resetRetryBtn(btn, originalHTML);
    });
}


function _retryVerifyPayment(csrfToken, response, orderNumber, btn, originalHTML) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('razorpay_payment_id', response.razorpay_payment_id);
    formData.append('razorpay_order_id', response.razorpay_order_id);
    formData.append('razorpay_signature', response.razorpay_signature);
    formData.append('order_number', orderNumber);

    fetch('/razorpay/callback/', {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(res => res.json())
    .then(data => {
        window.location.href = data.redirect_url;
    })
    .catch(err => {
        console.error('Retry callback failed:', err);
        window.location.href = '/order/' + orderNumber + '/failure/';
    });
}


function _retryMarkFailed(csrfToken, orderNumber, reason, btn, originalHTML) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('order_number', orderNumber);
    formData.append('reason', reason);

    fetch('/razorpay/failed/', {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(res => res.json())
    .then(data => {
        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            _resetRetryBtn(btn, originalHTML);
        }
    })
    .catch(err => {
        console.error('Failed to mark retry as failed:', err);
        window.location.href = '/order/' + orderNumber + '/failure/';
    });
}


function _resetRetryBtn(btn, originalHTML) {
    btn.innerHTML = originalHTML;
    btn.disabled = false;
}
