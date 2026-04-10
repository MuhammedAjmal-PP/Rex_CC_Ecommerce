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

    setItemLoading(cardEl, true);

    try {
      const formData = new FormData();
      formData.append("quantity", newQty);

      const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Update failed");
      }

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

        // Update order summary sidebar
        updateOrderSummary(data.order_summary);
      }
    } catch (error) {
      console.error(error);
      showToast(error.message || "Something went wrong.", "error");
    } finally {
      // Re-enable card first, then set correct button disabled states
      setItemLoading(cardEl, false);
      updateButtonsState(inputEl, decreaseBtn, increaseBtn, parseInt(inputEl.dataset.max));
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

  function handleRemove(slug, sku, cardEl) {
    UserAlert.confirm(
      'Remove Item',
      'Are you sure you want to remove this timepiece from your collection?',
      function () { performRemove(slug, sku, cardEl); },
      { danger: true, confirmText: 'Remove' }
    );
  }

  async function performRemove(slug, sku, cardEl) {
    setItemLoading(cardEl, true);

    try {
      const response = await fetch(`/api/mycart/${slug}/v/${sku}/remove/`, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
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

          // Update cart badge in navbar
          updateNavCartBadge(data.cart_count);

          // Dispatch global event so add_cart.js badge also updates
          window.dispatchEvent(new CustomEvent("cart:updated"));

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
    }
  }

  // =========================================================================
  // DOM UPDATE HELPERS
  // =========================================================================

  function updateNavCartBadge(count) {
    const badge = document.getElementById("cartBadge");
    if (!badge) return;

    if (count > 0) {
      badge.textContent = count;
      badge.style.display = "";
    } else {
      badge.textContent = "0";
      badge.style.display = "none";
    }
  }

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

    const existingWarning = qtyWrapper.querySelector(".stock-warning");
    const existingError = qtyWrapper.querySelector(".stock-error");
    if (existingWarning) existingWarning.remove();
    if (existingError) existingError.remove();

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
