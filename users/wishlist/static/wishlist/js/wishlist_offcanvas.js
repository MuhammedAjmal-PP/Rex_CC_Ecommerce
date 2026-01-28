/**
 * Wishlist Offcanvas JavaScript
 * Handles loading, displaying, and managing wishlist items
 */

(function () {
  "use strict";

  // DOM Elements
  const wishlistOffcanvas = document.getElementById("offcanvasWishlist");
  const wishlistLoading = document.getElementById("wishlistLoading");
  const wishlistEmpty = document.getElementById("wishlistEmpty");
  const wishlistItems = document.getElementById("wishlistItems");
  const wishlistFooter = document.getElementById("wishlistFooter");
  const wishlistCount = document.getElementById("wishlistCount");
  const wishlistItemTemplate = document.getElementById("wishlistItemTemplate");

  // API endpoints
  const WISHLIST_API_URL = "api/wishlist/";
  const ADD_TO_CART_URL = ""; // TODO: Add your cart API URL here, e.g., '/cart/add/'
  const REMOVE_FROM_WISHLIST_URL = ""; // TODO: Add your remove from wishlist API URL here, e.g., `/wishlist/remove/${itemId}/`

  // State
  let isLoading = false;
  let wishlistData = [];
  let hasLoadedOnce = false;

  /**
   * Initialize the wishlist offcanvas
   */
  function init() {
    if (!wishlistOffcanvas) return;

    // Load wishlist only once when offcanvas is first shown
    wishlistOffcanvas.addEventListener(
      "show.bs.offcanvas",
      handleOffcanvasOpen,
    );

    // Delegate click events for item actions
    if (wishlistItems) {
      wishlistItems.addEventListener("click", handleItemAction);
    }
  }

  /**
   * Handle offcanvas open event
   */
  function handleOffcanvasOpen() {
    // Only load if not already loading or if data is stale
    if (!isLoading && !hasLoadedOnce) {
      loadWishlist();
    } else if (hasLoadedOnce && wishlistData.length > 0) {
      // If already loaded, just show the existing data
      renderWishlist();
    } else if (hasLoadedOnce && wishlistData.length === 0) {
      // If loaded but empty, show empty state
      showEmpty();
    }
  }

  /**
   * Load wishlist data from API
   */
  async function loadWishlist() {
    if (isLoading) return;
    isLoading = true;

    showLoading();

    try {
      const response = await fetch(WISHLIST_API_URL, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCSRFToken(),
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load wishlist");
      }

      const data = await response.json();

      hideLoading();

      if (data.success && data.count > 0) {
        wishlistData = data.products || [];
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

  /**
   * Render wishlist items
   */
  function renderWishlist() {
    if (!wishlistData.length) {
      showEmpty();
      return;
    }

    // Update count
    updateCount(wishlistData.length);

    // Clear existing items
    wishlistItems.innerHTML = "";

    // Render each item
    wishlistData.forEach((item) => {
      const itemElement = createWishlistItem(item);
      wishlistItems.appendChild(itemElement);
    });

    // Show items container and footer
    wishlistEmpty.style.display = "none";
    wishlistItems.style.display = "flex";
    wishlistFooter.style.display = "block";
  }

  /**
   * Create a wishlist item element from template
   */
  function createWishlistItem(item) {
    const template = wishlistItemTemplate.content.cloneNode(true);
    const itemElement = template.querySelector(".wishlist-item");

    // Set data attributes
    itemElement.dataset.itemId = item.item_id;
    itemElement.dataset.variantId = item.variant;

    // Set image
    const img = itemElement.querySelector(".wishlist-product-img");
    img.src = item.image || "/static/images/placeholder.jpg";
    img.alt = item.product_name;

    // Set product link
    const productUrl = `/products/${item.variant}/`;
    const productLinks = itemElement.querySelectorAll(".wishlist-item-link");
    productLinks.forEach((link) => {
      link.href = productUrl;
    });

    // Set stock badge
    const stockBadge = itemElement.querySelector(".wishlist-stock-badge");
    if (item.is_in_stock) {
      stockBadge.textContent = "In Stock";
      stockBadge.classList.add("in-stock");
    } else {
      stockBadge.textContent = "Out of Stock";
      stockBadge.classList.add("out-of-stock");
    }

    // Set brand
    const brand = itemElement.querySelector(".wishlist-item-brand");
    brand.textContent = item.brand || "";

    // Set product name
    const nameLink = itemElement.querySelector(".wishlist-item-name a");
    nameLink.textContent = item.product_name;
    nameLink.href = productUrl;

    // Set SKU
    const sku = itemElement.querySelector(".wishlist-item-sku");
    sku.textContent = item.sku || `SKU: ${item.sku}`;

    // Set prices
    const currentPrice = itemElement.querySelector(".wishlist-price-current");
    const originalPrice = itemElement.querySelector(".wishlist-price-original");

    currentPrice.textContent = formatPrice(item.final_price);

    if (parseFloat(item.final_price) < parseFloat(item.price)) {
      originalPrice.textContent = formatPrice(item.price);
      originalPrice.style.display = "inline";
    } else {
      originalPrice.textContent = "";
      originalPrice.style.display = "none";
    }

    // Disable add to cart if out of stock
    const addCartBtn = itemElement.querySelector(".wishlist-add-cart-btn");
    if (!item.is_in_stock) {
      addCartBtn.disabled = true;
      addCartBtn.title = "Out of Stock";
    } else {
      addCartBtn.disabled = false;
    }

    return itemElement;
  }

  /**
   * Handle item action clicks (add to cart, remove)
   */
  function handleItemAction(event) {
    const target = event.target.closest("button");
    if (!target) return;

    const itemElement = target.closest(".wishlist-item");
    if (!itemElement) return;

    const itemId = itemElement.dataset.itemId;
    const variantId = itemElement.dataset.variantId;

    if (target.classList.contains("wishlist-add-cart-btn")) {
      addToCart(variantId, itemElement);
    } else if (target.classList.contains("wishlist-remove-btn")) {
      removeFromWishlist(itemId, itemElement);
    }
  }

  /**
   * Add item to cart
   */
  async function addToCart(variantId, itemElement) {
    const button = itemElement.querySelector(".wishlist-add-cart-btn");
    const originalContent = button.innerHTML;

    // Show loading state
    button.disabled = true;
    button.innerHTML =
      '<span class="material-icons" style="animation: wishlistSpin 0.8s linear infinite;">sync</span>';

    try {
      if (!ADD_TO_CART_URL) {
        console.warn("ADD_TO_CART_URL is not configured");
        throw new Error("Cart API URL not configured");
      }

      const response = await fetch(ADD_TO_CART_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
          variant_id: variantId,
          quantity: 1,
        }),
      });

      if (response.ok) {
        // Show success feedback
        button.innerHTML = '<span class="material-icons">check</span>';
        button.style.background =
          "linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)";

        // Reset after delay
        setTimeout(() => {
          button.innerHTML = originalContent;
          button.style.background = "";
          button.disabled = false;
        }, 2000);
      } else {
        throw new Error("Failed to add to cart");
      }
    } catch (error) {
      console.error("Add to cart error:", error);
      button.innerHTML = originalContent;
      button.disabled = false;
      showToast("Failed to add item to cart", "error");
    }
  }

  /**
   * Remove item from wishlist
   */
  async function removeFromWishlist(itemId, itemElement) {
    const button = itemElement.querySelector(".wishlist-remove-btn");
    button.disabled = true;

    try {
      if (!REMOVE_FROM_WISHLIST_URL) {
        // UI-only removal if API URL not configured
        console.warn(
          "REMOVE_FROM_WISHLIST_URL is not configured - performing UI-only removal",
        );
        performUIRemoval(itemId, itemElement);
        return;
      }

      const response = await fetch(REMOVE_FROM_WISHLIST_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
          item_id: itemId,
        }),
      });

      if (response.ok) {
        performUIRemoval(itemId, itemElement);
      } else {
        throw new Error("Failed to remove from wishlist");
      }
    } catch (error) {
      console.error("Remove from wishlist error:", error);
      button.disabled = false;
      showToast("Failed to remove item", "error");
    }
  }

  /**
   * Perform UI removal animation and state update
   */
  function performUIRemoval(itemId, itemElement) {
    // Animate removal
    itemElement.classList.add("removing");

    // Remove from DOM after animation
    setTimeout(() => {
      itemElement.remove();

      // Update data
      wishlistData = wishlistData.filter((item) => item.item_id != itemId);

      // Update count
      updateCount(wishlistData.length);

      // Show empty state if no items left
      if (!wishlistData.length) {
        showEmpty();
        // Reset flag so it reloads fresh data next time
        hasLoadedOnce = false;
      }
    }, 400);
  }

  /**
   * Show loading state
   */
  function showLoading() {
    wishlistLoading.style.display = "flex";
    wishlistEmpty.style.display = "none";
    wishlistItems.style.display = "none";
    wishlistFooter.style.display = "none";
    wishlistItems.innerHTML = "";
  }

  /**
   * Hide loading state
   */
  function hideLoading() {
    wishlistLoading.style.display = "none";
  }

  /**
   * Show empty state
   */
  function showEmpty() {
    wishlistEmpty.style.display = "flex";
    wishlistItems.style.display = "none";
    wishlistFooter.style.display = "none";
    updateCount(0);
  }

  /**
   * Update wishlist count display
   */
  function updateCount(count) {
    if (wishlistCount) {
      wishlistCount.textContent = `${count} item${count === 1 ? "" : "s"}`;
    }
  }

  /**
   * Format price with currency symbol
   */
  function formatPrice(price) {
    const numPrice = parseFloat(price);
    return `₹${numPrice.toLocaleString("en-IN", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })}`;
  }

  /**
   * Get CSRF token from cookie
   */
  function getCSRFToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Show a toast notification
   */
  function showToast(message, type = "info") {
    // Check if toast container exists, if not create one
    let container = document.querySelector(".toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = "toast-msg";
    toast.innerHTML = `
      <span class="material-icons" style="color: ${type === "error" ? "#e74c3c" : "var(--color-gold)"}">
        ${type === "error" ? "error" : "info"}
      </span>
      ${message}
    `;

    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.animation = "slideDown 0.3s ease reverse";
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  /**
   * Public method to force refresh wishlist data
   * Can be called externally when items are added to wishlist
   */
  function refreshWishlist() {
    hasLoadedOnce = false;
    loadWishlist();
  }

  // Initialize on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Expose refresh method globally
  window.refreshWishlist = refreshWishlist;
})();
