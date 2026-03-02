/**
 * CART PAGE LOGIC
 * Fully AJAX — no page reloads for quantity changes or item removal.
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

    const maxAllowed = parseInt(qtyInput.dataset.max);

    updateButtonsState(qtyInput, decreaseBtn, increaseBtn, maxAllowed);

    // Decrease
    if (decreaseBtn) {
      decreaseBtn.addEventListener("click", () =>
        handleQuantityUpdate(
          item,
          slug,
          sku,
          qtyInput,
          -1,
          decreaseBtn,
          increaseBtn,
        ),
      );
    }

    // Increase
    if (increaseBtn) {
      increaseBtn.addEventListener("click", () =>
        handleQuantityUpdate(
          item,
          slug,
          sku,
          qtyInput,
          1,
          decreaseBtn,
          increaseBtn,
        ),
      );
    }

    // Remove
    if (removeBtn) {
      removeBtn.addEventListener("click", () => handleRemove(slug, sku, item));
    }
  });

  // =========================================================================
  // QUANTITY HANDLER (AJAX — no reload)
  // =========================================================================

  async function handleQuantityUpdate(
    cardEl,
    slug,
    sku,
    inputEl,
    change,
    decreaseBtn,
    increaseBtn,
  ) {
    const currentQty = parseInt(inputEl.value);
    const newQty = currentQty + change;
    const maxAllowed = parseInt(inputEl.dataset.max);

    if (newQty < 1) return;
    if (newQty > maxAllowed) {
      showToast(`Maximum allowed quantity is ${maxAllowed}.`, "error");
      return;
    }

    // Disable buttons while request is in flight
    setItemLoading(cardEl, true);

    try {
      const data = await updateCartItem(slug, sku, newQty);

      if (data.success && data.item) {
        // Update quantity input
        inputEl.value = data.item.quantity;
        inputEl.dataset.max = data.item.allowed_max;

        // Update item total
        const itemTotalEl = cardEl.querySelector(".lux-item-total");
        if (itemTotalEl) {
          itemTotalEl.textContent = `Total: ₹${formatNumber(data.item.total_amount)}`;
        }

        // Update price display
        const finalPriceEl = cardEl.querySelector(".final-price");
        if (finalPriceEl) {
          finalPriceEl.textContent = `₹${formatNumber(data.item.final_price)}`;
        }

        const originalPriceEl = cardEl.querySelector(".original-price");
        if (originalPriceEl) {
          if (data.item.price > data.item.final_price) {
            originalPriceEl.textContent = `₹${formatNumber(data.item.price)}`;
            originalPriceEl.style.display = "";
          } else {
            originalPriceEl.style.display = "none";
          }
        }

        // Update stock warning
        updateStockWarning(cardEl, data.item.stock, data.item.is_in_stock);

        // Update button states
        updateButtonsState(inputEl, decreaseBtn, increaseBtn, data.item.allowed_max);

        // Update order summary sidebar
        updateOrderSummary(data.order_summary);
      }
    } catch (error) {
      console.error(error);
      showToast(error.message || "Something went wrong.", "error");
    } finally {
      setItemLoading(cardEl, false);
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
  // REMOVE LOGIC (AJAX — no reload)
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
          performRemove(itemToRemove.slug, itemToRemove.sku, itemToRemove.cardEl);
        }
      });
    }
  }

  function handleRemove(slug, sku, cardEl) {
    itemToRemove = { slug, sku, cardEl };

    if (removeModal) {
      removeModal.show();
    } else {
      if (confirm("Remove this item?")) {
        performRemove(slug, sku, cardEl);
      }
    }
  }

  async function performRemove(slug, sku, cardEl) {
    if (removeModal) removeModal.hide();
    setItemLoading(cardEl, true);

    try {
      const formData = new FormData();
      formData.append("remove", "true");

      const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      const data = await response.json();

      if (data.success && data.removed) {
        // Animate card removal
        cardEl.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        cardEl.style.opacity = "0";
        cardEl.style.transform = "translateX(-20px)";

        setTimeout(() => {
          cardEl.remove();

          // Update order summary
          updateOrderSummary(data.order_summary);

          // If cart is now empty, show empty state
          const remainingItems = document.querySelectorAll(".cart-item");
          if (remainingItems.length === 0) {
            showEmptyCart();
          }
        }, 300);
      } else {
        throw new Error(data.message || "Remove failed");
      }
    } catch (error) {
      showToast(error.message || "Could not remove item.", "error");
      setItemLoading(cardEl, false);
    } finally {
      itemToRemove = null;
    }
  }

  // =========================================================================
  // BACKEND UPDATE (returns JSON)
  // =========================================================================

  async function updateCartItem(slug, sku, quantity) {
    const formData = new FormData();
    formData.append("quantity", quantity);

    const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Update failed");
    }

    return data;
  }

  // =========================================================================
  // DOM UPDATE HELPERS
  // =========================================================================

  function updateOrderSummary(summary) {
    if (!summary) return;

    const summaryEl = document.querySelector(".lux-cart-summary");
    if (!summaryEl) return;

    const rows = summaryEl.querySelectorAll(".summary-row");

    rows.forEach((row) => {
      const label = row.querySelector("span:first-child");
      if (!label) return;
      const text = label.textContent.trim();
      const valueSpan = row.querySelector("span:last-child");

      if (text.startsWith("Total") && text.includes("items")) {
        label.textContent = `Total (${summary.products_count} items)`;
        if (valueSpan && valueSpan !== label) {
          valueSpan.textContent = `₹${formatNumber(summary.total)}`;
        }
      } else if (text === "Discount") {
        if (valueSpan) {
          valueSpan.textContent = `−₹${formatNumber(summary.discount)}`;
        }
        // Toggle discount class
        if (summary.discount > 0) {
          row.classList.add("discount");
        } else {
          row.classList.remove("discount");
        }
      } else if (text === "Subtotal") {
        if (valueSpan) {
          valueSpan.textContent = `₹${formatNumber(summary.sub_total)}`;
        }
      } else if (text === "Shipping Fee") {
        if (valueSpan) {
          valueSpan.textContent =
            summary.shipping_fee === 0
              ? "Free"
              : `₹${formatNumber(summary.shipping_fee)}`;
        }
      } else if (text === "Total Payable") {
        if (valueSpan) {
          valueSpan.textContent = `₹${formatNumber(summary.total_amount_to_pay)}`;
        }
      }
    });
  }

  function updateStockWarning(cardEl, stock, isInStock) {
    const qtyWrapper = cardEl.querySelector(".lux-qty-wrapper");
    if (!qtyWrapper) return;

    // Remove existing warnings
    const existingWarning = qtyWrapper.querySelector(".stock-warning");
    const existingError = qtyWrapper.querySelector(".stock-error");
    if (existingWarning) existingWarning.remove();
    if (existingError) existingError.remove();

    // Add new warning if needed
    if (!isInStock) {
      const errorSpan = document.createElement("span");
      errorSpan.className = "stock-error";
      errorSpan.textContent = "Out of Stock";
      qtyWrapper.appendChild(errorSpan);
    } else if (stock <= 5 && stock > 0) {
      const warnSpan = document.createElement("span");
      warnSpan.className = "stock-warning";
      warnSpan.textContent = `Only ${stock} left`;
      qtyWrapper.appendChild(warnSpan);
    }
  }

  function showEmptyCart() {
    const layout = document.querySelector(".lux-cart-layout");
    if (layout) {
      layout.innerHTML = `
        <div class="lux-empty-state" style="margin-top: 60px; grid-column: 1 / -1;">
          <span class="material-icons empty-icon">shopping_bag</span>
          <h2>Your cart is empty</h2>
          <p>Explore our exclusive collection to find your next timepiece.</p>
          <div style="margin-top: 30px;">
            <a href="/shop/" class="btn-primary">Explore Collection</a>
          </div>
        </div>
      `;
    }
  }

  // =========================================================================
  // UI HELPERS
  // =========================================================================

  function setItemLoading(cardEl, loading) {
    const buttons = cardEl.querySelectorAll("button");
    buttons.forEach((btn) => (btn.disabled = loading));
    cardEl.style.opacity = loading ? "0.6" : "1";
  }

  function formatNumber(num) {
    return parseFloat(num)
      .toFixed(2)
      .replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
