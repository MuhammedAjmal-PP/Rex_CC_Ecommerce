/**
 * Review Logic
 * Handles the review step + order placement (COD/Wallet/Razorpay)
 */
function populateReview() {
  const data = CheckoutState.deliveryData;
  document.getElementById("review-addr-name").innerText = data.name || "-";
  document.getElementById("review-addr-details").innerText =
    data.address || "-";
  document.getElementById("review-addr-phone").innerText = data.phone || "-";

  const payMethod = CheckoutState.selectedPaymentMethod;
  const payTextEl = document.getElementById("review-pay-method");
  const payIconEl = document.getElementById("review-pay-icon");

  if (payMethod === "cod") {
    payTextEl.innerText = "Cash on Delivery (COD)";
    payIconEl.innerText = "payments";
  } else if (payMethod === "wallet") {
    payTextEl.innerText = "Wallet";
    payIconEl.innerText = "account_balance_wallet";
  } else if (payMethod === "razorpay") {
    payTextEl.innerText = "Razorpay (Online Payment)";
    payIconEl.innerText = "credit_card";
  } else {
    payTextEl.innerText = payMethod.toUpperCase();
    payIconEl.innerText = "payments";
  }
}

function placeOrder() {
  const btn = document.getElementById("btn-place-order");

  if (!CheckoutState.selectedAddressId) {
    showToast("Please select a delivery address.", "error");
    return;
  }

  btn.innerHTML =
    '<span class="material-icons rotating">autorenew</span> Processing...';
  btn.disabled = true;

  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
  const method = CheckoutState.selectedPaymentMethod.toUpperCase();

  if (method === "RAZORPAY") {
    _placeOrderRazorpay(csrfToken, method, btn);
  } else {
    _placeOrderForm(csrfToken, method);
  }
}

/**
 * Standard form submit (COD / Wallet)
 */
function _placeOrderForm(csrfToken, method) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/place-order/";

  const fields = {
    csrfmiddlewaretoken: csrfToken,
    address_id: CheckoutState.selectedAddressId,
    payment_method: method,
  };

  for (const [key, value] of Object.entries(fields)) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = key;
    input.value = value;
    form.appendChild(input);
  }

  document.body.appendChild(form);
  form.submit();
}

/**
 * Razorpay AJAX flow:
 * 1. POST to /place-order/ → get Razorpay order data
 * 2. Open Razorpay checkout modal
 * 3. On success → POST to /razorpay/callback/
 * 4. On failure/dismiss → POST to /razorpay/failed/
 */
function _placeOrderRazorpay(csrfToken, method, btn) {
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("address_id", CheckoutState.selectedAddressId);
  formData.append("payment_method", method);

  fetch("/place-order/", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        showToast(data.error, "error");
        _resetPlaceOrderBtn(btn);
        return;
      }

      const options = {
        key: data.razorpay_key_id,
        amount: data.amount,
        currency: data.currency,
        name: data.name,
        description: data.description,
        order_id: data.razorpay_order_id,
        prefill: data.prefill || {},
        theme: { color: "#cd7f32" },
        handler: function (response) {
          // Payment successful — verify on server
          _verifyRazorpayPayment(csrfToken, response, data.order_number, btn);
        },
        modal: {
          ondismiss: function () {
            // User closed modal — mark as failed
            _markRazorpayFailed(
              csrfToken,
              data.order_number,
              "Payment cancelled by user",
              btn,
            );
          },
        },
      };

      const rzp = new Razorpay(options);

      rzp.on("payment.failed", function (response) {
        const reason = response.error.description || "Payment failed";
        _markRazorpayFailed(csrfToken, data.order_number, reason, btn);
      });

      rzp.open();
    })
    .catch((err) => {
      console.error("Razorpay order creation failed:", err);
      showToast("Something went wrong. Please try again.", "error");
      _resetPlaceOrderBtn(btn);
    });
}

/**
 * Verify Razorpay payment via callback
 */
function _verifyRazorpayPayment(csrfToken, response, orderNumber, btn) {
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("razorpay_payment_id", response.razorpay_payment_id);
  formData.append("razorpay_order_id", response.razorpay_order_id);
  formData.append("razorpay_signature", response.razorpay_signature);
  formData.append("order_number", orderNumber);

  fetch("/razorpay/callback/", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((res) => res.json())
    .then((data) => {
      window.location.href = data.redirect_url;
    })
    .catch((err) => {
      console.error("Razorpay callback failed:", err);
      window.location.href = "/order/" + orderNumber + "/failure/";
    });
}

/**
 * Mark Razorpay payment as failed on the backend
 */
function _markRazorpayFailed(csrfToken, orderNumber, reason, btn) {
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("order_number", orderNumber);
  formData.append("reason", reason);

  fetch("/razorpay/failed/", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.redirect_url) {
        window.location.href = data.redirect_url;
      } else {
        _resetPlaceOrderBtn(btn);
      }
    })
    .catch((err) => {
      console.error("Failed to mark payment as failed:", err);
      window.location.href = "/order/" + orderNumber + "/failure/";
    });
}

/**
 * Reset the place order button
 */
function _resetPlaceOrderBtn(btn) {
  btn.innerHTML = "Confirm & Place Order";
  btn.disabled = false;
}
