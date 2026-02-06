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
        const card = colWrapper.querySelector(".product-card");

        // Set ID for easy removal on the wrapper/col
        colWrapper.dataset.variantId = product.variant;

        // Image
        const img = card.querySelector(".product-card__image");
        img.src = product.image || "https://static.vecteezy.com/system/resources/previews/005/337/799/original/icon-image-not-found-free-vector.jpg";
        img.alt = product.product_name;

        // Link
        const link = card.querySelector(".card-link-wrapper");
        link.href = `/product/${product.slug}/v/${product.sku}/`;

        // Remove Button
        const removeBtn = card.querySelector(".wishlist-remove-btn");
        removeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleRemove(product.variant, product.slug, product.sku);
        });

        // Add to Cart Link
        const addToCartLink = card.querySelector(".btn-add-to-cart-wishlist");
        // URL: /cart/api/mycart/<slug>/v/<sku>/add/
        const addUrl = `/cart/api/mycart/${product.slug}/v/${product.sku}/add/`;
        
        addToCartLink.href = addUrl;
        
        addToCartLink.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleAddToCart(product.variant, product.slug, product.sku, addToCartLink);
        });
        
        // If out of stock, disable Add to Cart styling/action
        if (!product.is_in_stock) {
            addToCartLink.style.pointerEvents = "none";
            addToCartLink.style.opacity = "0.5";
            addToCartLink.textContent = "Out of Stock";
        }

        // Brand & Name
        card.querySelector(".product-card__brand").textContent = product.brand;
        card.querySelector(".product-card__name").textContent = product.product_name;

        // Variant Details
        const variantContainer = card.querySelector(".product-card__variant-info");
        if (product.variant_details && product.variant_details.length > 0) {
            variantContainer.innerHTML = "";
            product.variant_details.forEach(detail => {
                const detailSpan = document.createElement("span");
                detailSpan.className = "variant-attr";
                detailSpan.textContent = detail;
                variantContainer.appendChild(detailSpan); // CSS handles the separator
            });
        } else {
            variantContainer.innerHTML = "";
        }

        // Stock Badge (Primary Status)
        const stockBadge = card.querySelector(".product-card__stock-badge");
        const discountBadge = card.querySelector(".product-card__discount-badge");
        
        let isOutOfStock = false;
        if (!product.is_in_stock) {
            isOutOfStock = true;
            stockBadge.style.display = "block";
            // Disable Add to Cart styling/action
            addToCartLink.style.pointerEvents = "none";
            addToCartLink.style.opacity = "0.5";
            addToCartLink.textContent = "Out of Stock";
        } else {
             stockBadge.style.display = "none";
        }

        // Price & Discount Badge
        card.querySelector(".product-card__price").textContent = formatPrice(product.final_price);
        const originalPrice = card.querySelector(".product-card__original-price");

        if (parseFloat(product.final_price) < parseFloat(product.price)) {
            originalPrice.textContent = formatPrice(product.price);
            originalPrice.style.display = "inline";
            
            // Show Discount Badge ONLY if In Stock (prevent overlap)
            if (!isOutOfStock && product.price > 0) {
                const discount = Math.round(((product.price - product.final_price) / product.price) * 100);
                if (discount > 0) {
                    discountBadge.textContent = `-${discount}%`;
                    discountBadge.style.display = "block";
                } else {
                    discountBadge.style.display = "none";
                }
            } else {
                discountBadge.style.display = "none";
            }
        } else {
            originalPrice.style.display = "none";
            discountBadge.style.display = "none";
        }

        return colWrapper;
    }

    // ADD TO CART ACTION
    async function handleAddToCart(variantId, slug, sku, btn) {
        // Prevent double clicks
        if (btn.dataset.loading === "true") return;
        btn.dataset.loading = "true";
        
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="material-icons rotating" style="font-size:16px;">autorenew</span> Adding...';
        
        try {
            // URL: /api/mycart/<slug>/v/<sku>/add/
            const url = `/api/mycart/${slug}/v/${sku}/add/`;
            
            const formData = new FormData();
            formData.append('quantity', 1);
            
            const response = await fetch(url, {
                 method: 'POST',
                 headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                 },
                 body: formData
            });
            
            // Handle redirects (e.g. login)
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                 showToast(data.message || 'Added to Cart', 'success');
                 
                 // 1. Update Global Cart Badge
                 const event = new CustomEvent('cart:updated', { detail: { added: true } });
                 window.dispatchEvent(event);
                 
                 // 2. Remove from Wishlist Grid
                 removeItemFromGrid(variantId);
                 
                 // 3. Update Wishlist Item Count locally
                 wishlistItems = wishlistItems.filter(item => item.variant != variantId);
                 updatecount(wishlistItems.length);
                 
                 // 4. Update Header Wishlist Badge
                 if (window.emitWishlistChange) {
                    window.emitWishlistChange({ variantId, added: false });
                 }

            } else {
                 showToast(data.message || 'Failed to add to cart', 'error');
            }
        } catch (e) {
             console.error(e);
             showToast('Something went wrong', 'error');
        } finally {
            // Restore button state if it wasn't removed
            if (document.body.contains(btn)) {
                btn.dataset.loading = "false";
                btn.innerHTML = originalText;
            }
        }
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

    function showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = 'toast-msg';
        toast.innerHTML = `
            <span class="material-icons" style="color:${type === 'error' ? '#d32f2f' : '#cd7f32'}">
                ${type === 'error' ? 'error' : 'check_circle'}
            </span>
            ${message}
        `;

        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
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
