/**
 * Payment Logic
 * Handles selection between COD and Wallet
 */
function selectPayment(method) {
    CheckoutState.selectedPaymentMethod = method;

    // Remove selected class from all payment cards
    document.querySelectorAll('.payment-card:not(.disabled)').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selected class to the chosen card
    const cardId = method === 'cod' ? 'pay-cod' : 'pay-wallet';
    const selectedCard = document.getElementById(cardId);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
}
