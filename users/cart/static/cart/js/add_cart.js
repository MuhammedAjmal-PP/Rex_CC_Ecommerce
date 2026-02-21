/**
 * ADD TO CART LOGIC
 * Handles adding items to cart via AJAX from:
 * 1. Product Details Page (Form Submission)
 * 2. Wishlist Offcanvas / any button with .wishlist-add-cart-btn
 */

document.addEventListener("DOMContentLoaded", function () {
  initializeAddToCartForm();
  initializeWishlistCartButtons();
  initializeCartBadge();
});

/* ===============================
   CSRF TOKEN (input fallback → cookie)
================================ */
function getCSRFToken() {
  const input = document.querySelector("[name=csrfmiddlewaretoken]");
  if (input) return input.value;

  // Fallback: read from cookie
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, 10) === "csrftoken=") {
        cookieValue = decodeURIComponent(cookie.substring(10));
        break;
      }
    }
  }
  return cookieValue;
}

/* ===============================
   1. PDP FORM SUBMISSION
================================ */
function initializeAddToCartForm() {
  const form = document.getElementById("addToCartForm");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const submitBtn = document.getElementById("pdp-add-to-cart-btn");
    const quantityInput = form.querySelector("input[name='quantity']");
    const quantity = quantityInput ? quantityInput.value : 1;

    const formData = new FormData();
    formData.append("quantity", quantity);

    await handleAddToCart(form.action, formData, submitBtn);
  });
}

/* ===============================
   2. WISHLIST / GENERIC BUTTON CLICK
================================ */
function initializeWishlistCartButtons() {
  document.body.addEventListener("click", async function (e) {
    const btn = e.target.closest(".wishlist-add-cart-btn");
    if (!btn) return;

    e.preventDefault();

    const slug = btn.dataset.slug;
    const sku = btn.dataset.sku;

    if (!slug || !sku) {
      console.error("Missing slug or sku on add-to-cart button");
      return;
    }

    const url = `/api/mycart/${slug}/v/${sku}/add/`;
    const formData = new FormData();
    formData.append("quantity", 1);

    await handleAddToCart(url, formData, btn);
  });
}

/* ===============================
   CORE ADD-TO-CART HANDLER
================================ */
async function handleAddToCart(url, formData, btn) {
  const originalText = btn ? btn.textContent || btn.innerHTML : "";

  // Disable button & show loading state
  if (btn) {
    btn.disabled = true;
    if (btn.tagName === "BUTTON" && !btn.querySelector("span")) {
      btn.textContent = "Adding...";
    } else {
      btn.style.opacity = "0.7";
    }
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCSRFToken(),
      },
    });

    // If backend redirects (e.g. to login), follow it
    if (response.redirected) {
      window.location.href = response.url;
      return;
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || "Network response was not ok");
    }

    const data = await response.json();

    if (data.success) {
      showToast(data.message || "Added to Cart", "success");

      // Dispatch cart update event (other scripts listen for this)
      window.dispatchEvent(
        new CustomEvent("cart:updated", { detail: { added: true } })
      );

      // Update cart badge immediately
      updateCartBadge();

      // If this came from the wishlist offcanvas, notify wishlist to refresh
      if (btn && btn.closest(".wishlist-offcanvas")) {
        const variantId = btn.dataset.variantId || null;

        window.dispatchEvent(
          new CustomEvent("wishlist:changed", {
            detail: { added: false, variantId: variantId },
          })
        );
      }
    } else {
      showToast(data.message || "Could not add to cart", "error");
    }
  } catch (error) {
    console.error("Add to cart error:", error);
    showToast(error.message || "Something went wrong", "error");
  } finally {
    // Restore button state
    if (btn) {
      btn.disabled = false;
      if (btn.tagName === "BUTTON" && !btn.querySelector("span")) {
        btn.textContent = originalText;
      } else {
        btn.style.opacity = "1";
      }
    }
  }
}

/* ===============================
   CART BADGE
================================ */
function initializeCartBadge() {
  updateCartBadge();

  // Also update when other scripts dispatch cart:updated
  window.addEventListener("cart:updated", () => updateCartBadge());
}

async function updateCartBadge() {
  try {
    const response = await fetch("/api/mycart/count/");
    if (!response.ok) return;

    const data = await response.json();
    const count = data.cart_count || 0;

    // Support both id and class selectors for cart badge
    const badgeById = document.getElementById("cartBadge");
    if (badgeById) {
      badgeById.textContent = count;
      badgeById.style.display = count > 0 ? "flex" : "none";
    }

    const badgeByClass = document.querySelector(".cart-count");
    if (badgeByClass) {
      badgeByClass.textContent = count;
    }
  } catch (error) {
    console.error("Cart badge update error:", error);
  }
}

/* ===============================
   QTY INCREASE / DECREASE (PDP)
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
   TOAST NOTIFICATION
   (Uses same .toast-container / .toast-msg
    pattern as wishlist & address JS)
================================ */
function showToast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast-msg";
  toast.innerHTML = `
    <span class="material-icons" style="color:${type === "error" ? "#d32f2f" : "#cd7f32"}">
      ${type === "error" ? "error" : "check_circle"}
    </span>
    ${message}
  `;

  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
