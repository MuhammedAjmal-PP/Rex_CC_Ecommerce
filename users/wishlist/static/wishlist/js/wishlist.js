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
    const wishlistCountDisplay = document.getElementById("wishlist-count-display");
    const wishlistCountBadge = document.getElementById("wishlist-count-badge");

    // API
    const WISHLIST_API_URL = "/api/wishlist/";
    const REMOVE_URL = (slug, sku) => `/api/wishlist/${slug}/v/${sku}/toggle/`;

    // STATE
    let wishlistItems = [];

    // INIT
    function init() {
        if (!wishlistGrid) return; // Guard
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
        } else {
            // If added externally, reload to keep sync
            loadWishlist();
        }
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
                updatecount(wishlistItems.length);
                renderWishlist();
            }
        } catch (error) {
            console.error("Failed to load wishlist", error);
        } finally {
            hideLoading();
        }
    }

    function updatecount(count) {
        if (wishlistCountDisplay) wishlistCountDisplay.textContent = count;
        if (wishlistCountBadge) {
            if (count === 0) wishlistCountBadge.style.display = 'none';
            else wishlistCountBadge.style.display = 'inline-block';
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
        // The root is a document fragment, we need the column div
        const colWrapper = template.querySelector("div");
        const card = colWrapper.querySelector(".product-card-simple");

        // Set ID for easy removal on the wrapper/col
        colWrapper.dataset.variantId = product.variant;

        // Image
        const img = card.querySelector(".card-img-top");
        img.src = product.image || "https://via.placeholder.com/300";
        img.alt = product.product_name;

        // Link
        const link = card.querySelector(".card-link-wrapper");
        link.href = `/product/${product.slug}/v/${product.sku}/`;

        // Remove Button
        const removeBtn = card.querySelector(".btn-remove-icon");
        removeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleRemove(product.variant, product.slug, product.sku);
        });

        // Brand & Name
        card.querySelector(".brand-name").textContent = product.brand;
        const titleLink = card.querySelector(".title-link");
        titleLink.href = `/product/${product.slug}/v/${product.sku}/`;
        card.querySelector(".product-title").textContent = product.product_name;

        // Variant Details
        const variantContainer = card.querySelector(".variant-details-container");
        if (product.variant_details && product.variant_details.length > 0) {
            variantContainer.innerHTML = "";
            product.variant_details.forEach(detail => {
                const detailSpan = document.createElement("span");
                detailSpan.className = "variant-detail";
                detailSpan.textContent = detail;
                variantContainer.appendChild(detailSpan);
            });
        } else {
            variantContainer.remove();
        }

        // Price
        card.querySelector(".current-price").textContent = formatPrice(product.final_price);
        const originalPrice = card.querySelector(".original-price");

        if (parseFloat(product.final_price) < parseFloat(product.price)) {
            originalPrice.textContent = formatPrice(product.price);
        } else {
            originalPrice.style.display = "none";
        }

        // Stock
        const stockBadge = card.querySelector(".stock-badge");
        if (!product.is_in_stock) {
            stockBadge.textContent = "Out of Stock";
            stockBadge.classList.add("out-of-stock");
        }

        return colWrapper;
    }

    // REMOVE ACTION
    async function handleRemove(variantId, slug, sku) {
        try {
            const response = await fetch(REMOVE_URL(slug, sku), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            const data = await response.json();

            if (data.success) {
                // Remove from local list
                wishlistItems = wishlistItems.filter(item => item.variant != variantId);
                updatecount(wishlistItems.length);

                // We emit the global event so header badge updates
                if (window.emitWishlistChange) {
                    window.emitWishlistChange({ variantId, added: false });
                } else {
                    removeItemFromGrid(variantId);
                }
            }
        } catch (error) {
            console.error(error);
        }
    }

    // UI HELPERS
    function removeItemFromGrid(variantId) {
        // Find the column wrapper
        const col = wishlistGrid.querySelector(`div[data-variant-id="${variantId}"]`);

        if (col) {
            // Animate out
            col.style.transition = "all 0.3s ease";
            col.style.opacity = "0";
            col.style.transform = "scale(0.9)";

            setTimeout(() => {
                col.remove();
                if (wishlistGrid.children.length === 0) {
                    showEmpty();
                }
            }, 300);
        }
    }

    function showLoading() {
        if (wishlistLoading) wishlistLoading.style.display = "block";
        if (wishlistGrid) wishlistGrid.style.display = "none";
        if (wishlistEmpty) wishlistEmpty.style.display = "none";
    }

    function hideLoading() {
        if (wishlistLoading) wishlistLoading.style.display = "none";
    }

    function showEmpty() {
        if (wishlistEmpty) wishlistEmpty.style.display = "block";
        if (wishlistGrid) wishlistGrid.style.display = "none";
    }

    function showGrid() {
        if (wishlistEmpty) wishlistEmpty.style.display = "none";
        if (wishlistGrid) wishlistGrid.style.display = "flex"; // Row is flex
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
