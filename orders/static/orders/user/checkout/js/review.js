/**
 * Review Logic
 */
function populateReview() {
    // Fill Address Info
    const data = CheckoutState.deliveryData;
    document.getElementById('review-addr-name').innerText = data.name || '-';
    document.getElementById('review-addr-details').innerText = data.address || '-';
    document.getElementById('review-addr-phone').innerText = data.phone || '-';
}

function placeOrder() {
    const btn = document.getElementById('btn-place-order');

    // Validate state
    if (!CheckoutState.selectedAddressId) {
        alert("Please select a delivery address.");
        return;
    }

    // Disable button and show loading
    btn.innerHTML = '<span class="material-icons rotating">autorenew</span> Processing...';
    btn.disabled = true;

    // Get CSRF token from the page
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Build and submit form
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/place-order/';

    const fields = {
        csrfmiddlewaretoken: csrfToken,
        address_id: CheckoutState.selectedAddressId,
        payment_method: CheckoutState.selectedPaymentMethod === 'cod' ? 'COD' : CheckoutState.selectedPaymentMethod,
    };

    for (const [key, value] of Object.entries(fields)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}
