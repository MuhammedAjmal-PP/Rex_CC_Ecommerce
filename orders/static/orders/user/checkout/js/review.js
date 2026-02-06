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
    btn.innerHTML = '<span class="material-icons rotating">autorenew</span> Processing...';
    btn.disabled = true;

    // Simulate API Call or Form Submit
    setTimeout(() => {
        // Submit real form or API
        alert("Order Placement Logic here! (Address ID: " + CheckoutState.selectedAddressId + ")");
        btn.innerHTML = 'Confirm & Place Order';
        btn.disabled = false;
    }, 1500);
}
