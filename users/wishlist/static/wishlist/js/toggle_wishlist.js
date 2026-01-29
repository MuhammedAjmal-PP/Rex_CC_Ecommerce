/**
 * Toggle Wishlist JavaScript
 * Uses base_user toast container (no duplicate toast system)
 * Handles toggle functionality for Guest & Authenticated users
 * Implements Global Event Synchronization
 */

(function () {
  "use strict";

  // ===============================
  // INITIALIZE BUTTONS
  // ===============================
  function initWishlistButtons() {
    document.querySelectorAll(".add-to-wishlist").forEach((button) => {
      button.addEventListener("click", handleWishlistToggle);
    });

    // Listen for global wishlist changes
    window.addEventListener("wishlist:changed", handleGlobalWishlistChange);
  }

  // ===============================
  // HANDLE TOGGLE WISHLIST
  // ===============================
  async function handleWishlistToggle(event) {
    event.preventDefault();

    const button = event.currentTarget;
    const url = button.dataset.toggleUrl;
    const variantId = button.dataset.variantId;

    if (!url) {
      console.error("Wishlist toggle URL missing (data-toggle-url)");
      return;
    }

    // Prevent double-click
    if (button.dataset.loading === "true") return;
    button.dataset.loading = "true";

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();

      if (data.success) {
        showToast(data.message, "info");

        // Emit global event instead of updating just this button
        if (window.emitWishlistChange) {
          window.emitWishlistChange({
            variantId: variantId,
            added: data.added
          });
        } else {
          // Fallback if helper missing: manually update this button
          toggleWishlistIcon(button, data.added);

          // Should also manually dispatch event if helper missing?
          // Let's assume helper is there or dispatch manually
          const event = new CustomEvent("wishlist:changed", {
            detail: { variantId: variantId, added: data.added },
          });
          window.dispatchEvent(event);
        }

      } else {
        showToast(data.message || "Failed to update wishlist", "error");
      }

    } catch (error) {
      console.error("Wishlist toggle error:", error);
      showToast("Something went wrong. Please try again.", "error");
    } finally {
      button.dataset.loading = "false";
    }
  }

  // ===============================
  // GLOBAL EVENT LISTENER
  // ===============================
  function handleGlobalWishlistChange(event) {
    const { variantId, added } = event.detail;

    // Find all buttons for this variant
    // We select by data-variant-id
    const buttons = document.querySelectorAll(`.add-to-wishlist[data-variant-id="${variantId}"]`);

    buttons.forEach(button => {
      toggleWishlistIcon(button, added);
    });
  }

  // ===============================
  // UI HELPERS
  // ===============================
  function toggleWishlistIcon(button, added) {
    const icon = button.querySelector(".material-icons");
    if (!icon) return;

    // Switch between filled and border icon
    icon.textContent = added ? "favorite" : "favorite_border";
    button.classList.toggle("is-active", added);
  }

  // ===============================
  // CSRF TOKEN HELPER
  // ===============================
  function getCSRFToken() {
    const name = "csrftoken";
    let value = null;

    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          value = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return value;
  }

  // ===============================
  // TOAST NOTIFICATION (Reusing Base User)
  // ===============================
  function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");

    // Create container if it doesn't exist (fallback)
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = "toast-msg";

    const icon = type === "error" ? "error" : "info";
    const color = type === "error" ? "#e74c3c" : "var(--color-gold)";

    toast.innerHTML = `
      <span class="material-icons" style="color:${color}">
        ${icon}
      </span>
      ${message}
    `;

    container.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      toast.remove();
    }, 3000);
  }

  // ===============================
  // INIT ON DOM READY
  // ===============================
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWishlistButtons);
  } else {
    initWishlistButtons();
  }

})();
