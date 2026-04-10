/**
 * Payment Logic
 * Handles selection between COD, Wallet, and Razorpay
 */
function selectPayment(method) {
    CheckoutState.selectedPaymentMethod = method;

    // Remove selected class from all payment cards
    document.querySelectorAll('.checkout-payment-card:not(.disabled)').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selected class to the chosen card
    const cardMap = {
        'cod': 'pay-cod',
        'wallet': 'pay-wallet',
        'razorpay': 'pay-razorpay',
    };
    const selectedCard = document.getElementById(cardMap[method]);
    if (selectedCard && !selectedCard.classList.contains('disabled')) {
        selectedCard.classList.add('selected');
    }
}

// Auto-select first available payment method on load
document.addEventListener('DOMContentLoaded', () => {
    const codCard = document.getElementById('pay-cod');
    if (codCard && codCard.classList.contains('disabled')) {
        // COD is disabled — select Razorpay as default instead
        const razorpayCard = document.getElementById('pay-razorpay');
        if (razorpayCard && !razorpayCard.classList.contains('disabled')) {
            selectPayment('razorpay');
        }
    }
});
