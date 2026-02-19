/**
 * CART PAGE LOGIC
 * Strict stock + max purchase validation
 */

document.addEventListener("DOMContentLoaded", () => {
  // =========================================================================
  // DOM ELEMENTS
  // =========================================================================
  const cartItems = document.querySelectorAll(".cart-item");
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  // =========================================================================
  // INIT PER ITEM
  // =========================================================================
  cartItems.forEach((item) => {
    const slug = item.dataset.slug;
    const sku = item.dataset.sku;

    const decreaseBtn = item.querySelector('.qty-btn[data-action="decrease"]');
    const increaseBtn = item.querySelector('.qty-btn[data-action="increase"]');
    const removeBtn = item.querySelector(".remove-btn");
    const qtyInput = item.querySelector(".qty-input");

    const maxAllowed = parseInt(qtyInput.dataset.max); // ← IMPORTANT

    updateButtonsState(qtyInput, decreaseBtn, increaseBtn, maxAllowed);

    // Decrease
    if (decreaseBtn) {
      decreaseBtn.addEventListener("click", () =>
        handleQuantityUpdate(
          slug,
          sku,
          qtyInput,
          -1,
          maxAllowed,
          decreaseBtn,
          increaseBtn,
        ),
      );
    }

    // Increase
    if (increaseBtn) {
      increaseBtn.addEventListener("click", () =>
        handleQuantityUpdate(
          slug,
          sku,
          qtyInput,
          1,
          maxAllowed,
          decreaseBtn,
          increaseBtn,
        ),
      );
    }

    // Remove
    if (removeBtn) {
      removeBtn.addEventListener("click", () => handleRemove(slug, sku));
    }
  });

  // =========================================================================
  // QUANTITY HANDLER
  // =========================================================================

  async function handleQuantityUpdate(
    slug,
    sku,
    inputEl,
    change,
    maxAllowed,
    decreaseBtn,
    increaseBtn,
  ) {
    const currentQty = parseInt(inputEl.value);
    const newQty = currentQty + change;

    if (newQty < 1) return;
    if (newQty > maxAllowed) {
      showToast(`Maximum allowed quantity is ${maxAllowed}.`, "error");
      return;
    }

    showLoadingCursor(true);

    try {
      await updateCartItem(slug, sku, newQty);
      inputEl.value = newQty;
      updateButtonsState(inputEl, decreaseBtn, increaseBtn, maxAllowed);
    } catch (error) {
      console.error(error);
      showToast("Something went wrong.", "error");
    } finally {
      showLoadingCursor(false);
    }
  }

  function updateButtonsState(inputEl, decreaseBtn, increaseBtn, maxAllowed) {
    const currentQty = parseInt(inputEl.value);

    if (decreaseBtn) {
      decreaseBtn.disabled = currentQty <= 1;
    }

    if (increaseBtn) {
      increaseBtn.disabled = currentQty >= maxAllowed;
    }
  }

  // =========================================================================
  // REMOVE LOGIC
  // =========================================================================

  let itemToRemove = null;
  const removeModalEl = document.getElementById("removeConfirmModal");
  let removeModal = null;
  const confirmBtn = document.getElementById("confirmRemoveBtn");

  if (removeModalEl) {
    removeModal = new bootstrap.Modal(removeModalEl);

    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => {
        if (itemToRemove) {
          performRemove(itemToRemove.slug, itemToRemove.sku);
        }
      });
    }
  }

  function handleRemove(slug, sku) {
    itemToRemove = { slug, sku };

    if (removeModal) {
      removeModal.show();
    } else {
      if (confirm("Remove this item?")) {
        performRemove(slug, sku);
      }
    }
  }

  async function performRemove(slug, sku) {
    if (removeModal) removeModal.hide();
    showLoadingCursor(true);

    try {
      const formData = new FormData();
      formData.append("remove", "true");

      const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      if (response.redirected || response.ok) {
        window.location.reload();
      } else {
        throw new Error("Remove failed");
      }
    } catch {
      showToast("Could not remove item.", "error");
    } finally {
      showLoadingCursor(false);
      itemToRemove = null;
    }
  }

  // =========================================================================
  // BACKEND UPDATE
  // =========================================================================

  async function updateCartItem(slug, sku, quantity) {
    const formData = new FormData();
    formData.append("quantity", quantity);

    const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });

    if (response.redirected) {
      window.location.href = response.url;
      return;
    }

    if (!response.ok) {
      const data = await response.json();
      if (data.error) {
        showToast(data.error, "error");
      } else {
        throw new Error("Update failed");
      }
    }
  }

  // =========================================================================
  // UI HELPERS
  // =========================================================================

  function showLoadingCursor(show) {
    document.body.style.cursor = show ? "wait" : "default";
    document.querySelectorAll("button").forEach((btn) => {
      btn.disabled = show;
    });
  }

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
      <span class="material-icons" style="color:${
        type === "error" ? "#d32f2f" : "#cd7f32"
      }">
        ${type === "error" ? "error" : "info"}
      </span>
      ${message}
    `;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }
});
