/**
 * Payment Logic
 * Currently just handles selection
 */
function selectPayment(method) {
    // UI Update
    CheckoutState.selectedPaymentMethod = method;
    // (Only COD active for now so logic is simple)
}
