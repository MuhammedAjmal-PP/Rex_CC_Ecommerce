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
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
}
