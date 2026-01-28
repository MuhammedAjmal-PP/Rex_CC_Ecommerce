/**
 * Add to Wishlist JavaScript
 * Uses base_user toast container (no duplicate toast system)
 */

(function () {
  "use strict";

  // ===============================
  // INITIALIZE BUTTONS
  // ===============================
  function initWishlistButtons() {
    document.querySelectorAll(".add-to-wishlist").forEach((button) => {
      button.addEventListener("click", handleAddWishlist);
    });
  }

  // ===============================
  // HANDLE ADD TO WISHLIST
  // ===============================
  async function handleAddWishlist(event) {
    event.preventDefault();

    const button = event.currentTarget;
    const url = button.dataset.addUrl;

    if (!url) {
      console.error("add_wishlist URL missing");
      return;
    }

    // Prevent double click
    if (button.dataset.loading === "true") return;
    button.dataset.loading = "true";

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      /**
       * CASE: User not logged in
       * @login_required triggers redirect (302)
       */
      if (response.redirected) {
        showToast("Please login to use wishlist", "info");

        setTimeout(() => {
          window.location.href = response.url;
        }, 1200);

        return;
      }

      const data = await response.json();

      if (data.success) {
        showToast(data.message, "info");

        // Update icon state (optional visual feedback)
        toggleWishlistIcon(button, true);

        // Refresh wishlist offcanvas if available
        if (window.refreshWishlist) {
          window.refreshWishlist();
        }
      } else {
        showToast(data.message || "Something went wrong", "error");
      }
    } catch (error) {
      console.error("Add wishlist error:", error);
      showToast("Server error. Please try again.", "error");
    } finally {
      button.dataset.loading = "false";
    }
  }

  // ===============================
  // UI HELPERS
  // ===============================
  function toggleWishlistIcon(button, added) {
    const icon = button.querySelector(".material-icons");
    if (!icon) return;

    icon.textContent = added ? "favorite" : "favorite_border";
    button.classList.toggle("is-active", added);
  }

  // ===============================
  // CSRF TOKEN
  // ===============================
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

  // ===============================
  // BASE USER TOAST (REUSED)
  // ===============================
  function showToast(message, type = "info") {
    // Reuse existing container from base_user.html
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
        type === "error" ? "#e74c3c" : "var(--color-gold)"
      }">
        ${type === "error" ? "error" : "info"}
      </span>
      ${message}
    `;

    container.appendChild(toast);

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
