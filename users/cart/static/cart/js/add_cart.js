/* ===============================
   PRODUCT DETAIL - ADD TO CART
================================ */

document.addEventListener("DOMContentLoaded", function () {
  initializeAddToCartForm();
  initializeCartCount();
});

/* ===============================
   CSRF TOKEN
================================ */
function getCSRFToken() {
  return document.querySelector("[name=csrfmiddlewaretoken]")?.value;
}

/* ===============================
   HANDLE FORM SUBMIT (AJAX)
================================ */
function initializeAddToCartForm() {
  const form = document.getElementById("addToCartForm");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const submitBtn = document.getElementById("pdp-add-to-cart-btn");
    const quantityInput = form.querySelector("input[name='quantity']");
    const quantity = quantityInput ? quantityInput.value : 1;

    submitBtn.disabled = true;
    submitBtn.classList.add("loading");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCSRFToken(),
        },
        body: new URLSearchParams({
          quantity: quantity,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        showToast(data.message || "Something went wrong", "error");
      } else {
        showToast(data.message || "Added to cart", "success");
        updateCartCount();
      }
    } catch (error) {
      console.error("Add to cart error:", error);
      showToast("Network error. Please try again.", "error");
    }

    submitBtn.disabled = false;
    submitBtn.classList.remove("loading");
  });
}

/* ===============================
   CART COUNT
================================ */
async function updateCartCount() {
  try {
    const response = await fetch("/api/mycart/count/");
    const data = await response.json();

    const badge = document.querySelector(".cart-count");
    if (badge) {
      badge.innerText = data.cart_count || 0;
    }
  } catch (error) {
    console.error("Cart count error:", error);
  }
}

function initializeCartCount() {
  updateCartCount();
}

/* ===============================
   QTY INCREASE / DECREASE
================================ */
document.addEventListener("click", function (e) {
  if (e.target.matches(".pdp-qty-btn")) {
    const action = e.target.dataset.action;
    const input = e.target
      .closest(".pdp-qty-wrapper")
      .querySelector(".pdp-qty-input");

    let current = parseInt(input.value);
    const max = parseInt(input.getAttribute("max")) || 99;

    if (action === "increase" && current < max) {
      input.value = current + 1;
    }

    if (action === "decrease" && current > 1) {
      input.value = current - 1;
    }
  }
});

/* ===============================
   TOAST SYSTEM
================================ */
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `custom-toast ${type}`;
  toast.innerText = message;

  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add("show"), 50);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
