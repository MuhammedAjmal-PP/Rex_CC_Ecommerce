/**
 * Wishlist Offcanvas JavaScript
 * Handles loading, displaying, and managing wishlist items
 * Supports guest + logged-in users
 * Updates header wishlist badge
 */

(function () {
  "use strict";

  // ===============================
  // DOM ELEMENTS
  // ===============================
  const wishlistOffcanvas = document.getElementById("offcanvasWishlist");
  const wishlistLoading = document.getElementById("wishlistLoading");
  const wishlistEmpty = document.getElementById("wishlistEmpty");
  const wishlistItems = document.getElementById("wishlistItems");
  const wishlistFooter = document.getElementById("wishlistFooter");
  const wishlistCount = document.getElementById("wishlistCount");
  const wishlistItemTemplate = document.getElementById("wishlistItemTemplate");
  const wishlistBadge = document.getElementById("wishlistBadge");

  // ===============================
  // API ENDPOINTS
  // ===============================
  const WISHLIST_API_URL = "/api/wishlist/";
  const REMOVE_WISHLIST_URL = (variantId) =>
    `/api/wishlist/${variantId}/remove/`;

  // ===============================
  // STATE
  // ===============================
  let isLoading = false;
  let wishlistData = [];
  let hasLoadedOnce = false;

  // ===============================
  // INIT
  // ===============================
  function init() {
    if (!wishlistOffcanvas) return;

    wishlistOffcanvas.addEventListener(
      "show.bs.offcanvas",
      handleOffcanvasOpen,
    );

    if (wishlistItems) {
      wishlistItems.addEventListener("click", handleItemAction);
    }

    // Initial badge sync (page load)
    syncWishlistBadge();
  }

  // ===============================
  // OFFCANVAS OPEN
  // ===============================
  function handleOffcanvasOpen() {
    if (!isLoading && !hasLoadedOnce) {
      loadWishlist();
    } else if (wishlistData.length) {
      renderWishlist();
    } else {
      showEmpty();
    }
  }

  // ===============================
  // LOAD WISHLIST
  // ===============================
  async function loadWishlist() {
    if (isLoading) return;
    isLoading = true;

    showLoading();

    try {
      const response = await fetch(WISHLIST_API_URL, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load wishlist");
      }

      const data = await response.json();

      wishlistData = data.products || [];

      hideLoading();

      if (wishlistData.length) {
        renderWishlist();
      } else {
        showEmpty();
      }

      hasLoadedOnce = true;
    } catch (error) {
      console.error("Wishlist load error:", error);
      hideLoading();
      showEmpty();
      hasLoadedOnce = true;
    } finally {
      isLoading = false;
    }
  }

  // ===============================
  // RENDER WISHLIST
  // ===============================
  function renderWishlist() {
    wishlistItems.innerHTML = "";

    updateCount(wishlistData.length);
    updateWishlistBadge(wishlistData.length);

    wishlistData.forEach((item) => {
      const el = createWishlistItem(item);
      wishlistItems.appendChild(el);
    });

    wishlistItems.style.display = "flex";
    wishlistFooter.style.display = "block";
    wishlistEmpty.style.display = "none";
  }

  // ===============================
  // CREATE ITEM
  // ===============================
  function createWishlistItem(item) {
    const template = wishlistItemTemplate.content.cloneNode(true);
    const itemElement = template.querySelector(".wishlist-item");

    itemElement.dataset.variantId = item.variant;

    // Image
    const img = itemElement.querySelector(".wishlist-product-img");
    img.src = item.image || "/static/images/placeholder.jpg";
    img.alt = item.product_name;

    // Links
    const productUrl = `/products/${item.variant}/`;
    itemElement.querySelectorAll(".wishlist-item-link").forEach((link) => {
      link.href = productUrl;
    });

    // Brand & name
    itemElement.querySelector(".wishlist-item-brand").textContent =
      item.brand || "";
    itemElement.querySelector(".wishlist-item-name a").textContent =
      item.product_name;

    // SKU
    const sku = itemElement.querySelector(".wishlist-item-sku");
    sku.textContent = item.sku ? `SKU: ${item.sku}` : "";

    // Price
    itemElement.querySelector(".wishlist-price-current").textContent =
      formatPrice(item.final_price);

    const original = itemElement.querySelector(".wishlist-price-original");
    if (parseFloat(item.final_price) < parseFloat(item.price)) {
      original.textContent = formatPrice(item.price);
      original.style.display = "inline";
    } else {
      original.style.display = "none";
    }

    // Stock badge
    const badge = itemElement.querySelector(".wishlist-stock-badge");
    if (item.is_in_stock) {
      badge.textContent = "In Stock";
      badge.classList.add("in-stock");
    } else {
      badge.textContent = "Out of Stock";
      badge.classList.add("out-of-stock");
    }

    return itemElement;
  }

  // ===============================
  // HANDLE ITEM ACTIONS
  // ===============================
  function handleItemAction(event) {
    const button = event.target.closest("button");
    if (!button) return;

    const itemElement = button.closest(".wishlist-item");
    if (!itemElement) return;

    const variantId = itemElement.dataset.variantId;

    if (button.classList.contains("wishlist-remove-btn")) {
      removeWishlistItem(variantId, itemElement);
    }
  }

  // ===============================
  // REMOVE ITEM
  // ===============================
  async function removeWishlistItem(variantId, itemElement) {
    const button = itemElement.querySelector(".wishlist-remove-btn");
    button.disabled = true;
    button.style.pointerEvents = "none";

    try {
      const response = await fetch(REMOVE_WISHLIST_URL(variantId), {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to remove wishlist item");
      }

      itemElement.classList.add("removing");

      setTimeout(() => {
        itemElement.remove();

        wishlistData = wishlistData.filter(
          (item) => String(item.variant) !== String(variantId),
        );

        updateCount(wishlistData.length);
        updateWishlistBadge(wishlistData.length);

        if (!wishlistData.length) {
          showEmpty();
          hasLoadedOnce = false;
        }
      }, 400);
    } catch (error) {
      console.error(error);
      button.disabled = false;
      button.style.pointerEvents = "";
      showToast("Failed to remove item", "error");
    }
  }

  // ===============================
  // BADGE HANDLING
  // ===============================
  function updateWishlistBadge(count) {
    if (!wishlistBadge) return;

    if (count > 0) {
      wishlistBadge.textContent = count > 99 ? "99+" : count;
      wishlistBadge.style.display = "inline-flex";

      // Trigger Pulse Animation
      wishlistBadge.classList.remove("pulse-active");
      void wishlistBadge.offsetWidth; // Trigger reflow
      wishlistBadge.classList.add("pulse-active");

      // Remove class after animation completes
      setTimeout(() => {
        wishlistBadge.classList.remove("pulse-active");
      }, 2500);
    } else {
      wishlistBadge.style.display = "none";
    }
  }

  function syncWishlistBadge() {
    fetch(WISHLIST_API_URL, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((res) => res.json())
      .then((data) => {
        updateWishlistBadge(data.count || 0);
      })
      .catch(() => { });
  }

  // ===============================
  // UI STATES
  // ===============================
  function showLoading() {
    wishlistLoading.style.display = "flex";
    wishlistItems.style.display = "none";
    wishlistFooter.style.display = "none";
    wishlistEmpty.style.display = "none";
  }

  function hideLoading() {
    wishlistLoading.style.display = "none";
  }

  function showEmpty() {
    wishlistItems.style.display = "none";
    wishlistFooter.style.display = "none";
    wishlistEmpty.style.display = "flex";
    updateCount(0);
    updateWishlistBadge(0);
  }

  function updateCount(count) {
    wishlistCount.textContent = `${count} item${count === 1 ? "" : "s"}`;
  }

  // ===============================
  // HELPERS
  // ===============================
  function formatPrice(price) {
    return `₹${parseFloat(price).toLocaleString("en-IN")}`;
  }

  function getCSRFToken() {
    const name = "csrftoken";
    let value = null;
    document.cookie.split(";").forEach((cookie) => {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        value = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
    return value;
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
      <span class="material-icons" style="color:${type === "error" ? "#e74c3c" : "var(--color-gold)"
      }">
        ${type === "error" ? "error" : "info"}
      </span>
      ${message}
    `;

    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
  }

  // ===============================
  // PUBLIC API
  // ===============================
  window.refreshWishlist = function () {
    hasLoadedOnce = false;
    loadWishlist();
  };

  // ===============================
  // INIT ON READY
  // ===============================
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
