/**
 * Wishlist Page JavaScript
 * Handles display and interaction on the dedicated wishlist page
 */

(function () {
    "use strict";

    // ELEMENTS
    const wishlistGrid = document.getElementById("wishlist-grid");
    const wishlistLoading = document.getElementById("wishlist-loading");
    const wishlistEmpty = document.getElementById("wishlist-empty");
    const itemTemplate = document.getElementById("wishlist-page-item-template");

    // API
    const WISHLIST_API_URL = "/api/wishlist/";
    const REMOVE_URL = (variantId) => `/api/wishlist/${variantId}/toggle/`;

    // STATE
    let wishlistItems = [];

    // INIT
    function init() {
        loadWishlist();

        // Listen for global changes (to sync if item removed from offcamvas or header)
        window.addEventListener("wishlist:changed", handleGlobalChange);
    }

    // GLOBAL CHANGE HANDLER
    function handleGlobalChange(event) {
        const { variantId, added } = event.detail;

        if (!added) {
            // Remove item from grid if it exists
            removeItemFromGrid(variantId);
        }
        // If added, we might want to reload or append, but typically 
        // user adds from other pages. If they are on wishlist page, 
        // they probably aren't adding items unless we have a "Quick Add" 
        // which we don't right now. 
        // Re-fetching is safest to maintain order.
        // However, usually you are removing items on this page.
    }

    // LOAD DATA
    async function loadWishlist() {
        showLoading();
        try {
            const response = await fetch(WISHLIST_API_URL, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const data = await response.json();

            if (data.success) {
                wishlistItems = data.products || [];
                renderWishlist();
            }
        } catch (error) {
            console.error("Failed to load wishlist", error);
        } finally {
            hideLoading();
        }
    }

    // RENDER
    function renderWishlist() {
        wishlistGrid.innerHTML = "";

        if (wishlistItems.length === 0) {
            showEmpty();
            return;
        }

        showGrid();

        wishlistItems.forEach((product) => {
            const el = createProductCard(product);
            wishlistGrid.appendChild(el);
        });
    }

    // CREATE CARD
    function createProductCard(product) {
        const template = itemTemplate.content.cloneNode(true);
        const card = template.querySelector(".wishlist-card");

        // Set ID for easy removal
        card.dataset.variantId = product.variant;

        // Image
        const img = card.querySelector(".wishlist-card-img");
        img.src = product.image || "https://via.placeholder.com/300";
        img.alt = product.product_name;

        // Link
        const link = card.querySelector(".wishlist-card-link");
        link.href = `/products/${product.variant}/`;

        // Remove Button
        const removeBtn = card.querySelector(".wishlist-remove-action");
        // We attach event listener manually instead of using global class
        // because we want specific behavior (remove card)
        removeBtn.addEventListener("click", () => handleRemove(product.variant));

        // Brand & Name
        card.querySelector(".wishlist-card-brand").textContent = product.brand;
        const nameLink = card.querySelector(".wishlist-card-name a");
        nameLink.textContent = product.product_name;
        nameLink.href = `/products/${product.variant}/`;

        // Price
        card.querySelector(".current-price").textContent = formatPrice(product.final_price);
        const originalPrice = card.querySelector(".original-price");

        if (parseFloat(product.final_price) < parseFloat(product.price)) {
            originalPrice.textContent = formatPrice(product.price);
        } else {
            originalPrice.style.display = 'none';
        }

        // View Button
        const viewBtn = card.querySelector(".btn-view-product");
        viewBtn.href = `/products/${product.variant}/`;

        // Stock
        const stockBadge = card.querySelector(".stock-badge");
        if (!product.is_in_stock) {
            stockBadge.textContent = "Out of Stock";
            stockBadge.classList.add("out-of-stock");
        } else {
            stockBadge.style.display = "none";
        }

        return card;
    }

    // REMOVE ACTION
    async function handleRemove(variantId) {
        try {
            const response = await fetch(REMOVE_URL(variantId), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            const data = await response.json();

            if (data.success) {
                // We emit the global event so header badge updates
                if (window.emitWishlistChange) {
                    window.emitWishlistChange({ variantId, added: false });
                } else {
                    // Fallback if helper missing
                    // Trigger local removal
                    removeItemFromGrid(variantId);
                }
            } else {
                alert(data.message || "Failed to remove item");
            }

        } catch (error) {
            console.error(error);
        }
    }

    // UI HELPERS
    function removeItemFromGrid(variantId) {
        const card = wishlistGrid.querySelector(`.wishlist-card[data-variant-id="${variantId}"]`);
        if (card) {
            // Animate out
            card.style.opacity = "0";
            card.style.transform = "scale(0.9)";

            setTimeout(() => {
                card.remove();

                // Check if empty
                if (wishlistGrid.children.length === 0) {
                    showEmpty();
                }
            }, 300);
        }
    }

    function showLoading() {
        wishlistLoading.style.display = "flex";
        wishlistGrid.style.display = "none";
        wishlistEmpty.style.display = "none";
    }

    function hideLoading() {
        wishlistLoading.style.display = "none";
    }

    function showEmpty() {
        wishlistEmpty.style.display = "flex";
        wishlistGrid.style.display = "none";
    }

    function showGrid() {
        wishlistEmpty.style.display = "none";
        wishlistGrid.style.display = "grid";
    }

    function formatPrice(price) {
        return "₹" + parseFloat(price).toLocaleString("en-IN");
    }

    function getCSRFToken() {
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

    // Run
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
