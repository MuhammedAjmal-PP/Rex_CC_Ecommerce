/**
 * ADD TO CART LOGIC
 * Handles adding items to cart via AJAX from:
 * 1. Product Details Page (Form Submission)
 * 2. Wishlist Offcanvas (Button Click)
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================
    // 1. PDP FORM SUBMISSION
    // =========================================================
    const addToCartForm = document.getElementById('addToCartForm');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('pdp-add-to-cart-btn');

            // Construct FormData from Form
            const formData = new FormData(addToCartForm);
            const url = addToCartForm.action;

            await handleAddToCart(url, formData, btn);
        });
    }

    // =========================================================
    // 2. GLOBAL DELEGATED LISTENER (e.g. Wishlist Offcanvas)
    // =========================================================
    document.body.addEventListener('click', async (e) => {
        // Find closest .wishlist-add-cart-btn
        const btn = e.target.closest('.wishlist-add-cart-btn');
        if (!btn) return;

        e.preventDefault();

        const slug = btn.dataset.slug;
        const sku = btn.dataset.sku;

        if (!slug || !sku) {
            console.error('Missing slug or sku on add-to-cart button');
            return;
        }

        // URL Pattern: /api/mycart/<slug>/v/<sku>/add/
        const url = `/api/mycart/${slug}/v/${sku}/add/`;

        // Prepare FormData (Quantity 1)
        const formData = new FormData();
        formData.append('quantity', 1);

        await handleAddToCart(url, formData, btn);
    });


    // =========================================================
    // CORE HANDLER
    // =========================================================
    async function handleAddToCart(url, formData, btn) {
        const originalText = btn ? (btn.textContent || btn.innerHTML) : '';

        if (btn) {
            btn.disabled = true;
            // If it's an icon button, maybe show a spinner or opacity
            // For PDP text button:
            if (btn.tagName === 'BUTTON' && !btn.querySelector('span')) {
                btn.textContent = 'Adding...';
            } else {
                btn.style.opacity = '0.7';
            }
        }

        try {
            // Get CSRF Token
            const csrfToken = getCSRFToken();

            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            });

            if (response.redirected) {
                // If backend redirects (e.g. to login), follow it
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                // Try to parse error message from JSON response
                // If status is 401/403 (unauthorized) and NOT a redirect, standard API might return 403.
                // But @login_required usually 302s.
                // If it is an API error (json)
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || 'Network response was not ok');
            }

            const data = await response.json();

            if (data.success) {
                showToast(data.message || 'Added to Cart', 'success');

                // Dispatch Event
                const event = new CustomEvent('cart:updated', { detail: { added: true } });
                window.dispatchEvent(event);

                // If this action came from a Wishlist Button, we need to refresh the Wishlist
                // The backend automatically removes the item from Wishlist.
                // We need to tell the frontend to reflect that.
                if (btn && btn.closest('.wishlist-offcanvas')) {
                    // Extract variant ID from the button to notify other components (like product cards)
                    const variantId = btn.dataset.variantId || null;

                    const wishlistEvent = new CustomEvent('wishlist:changed', {
                        detail: {
                            added: false, // It was removed from wishlist
                            variantId: variantId
                        }
                    });
                    window.dispatchEvent(wishlistEvent);
                }

                // If currently on Cart Page, reload? 
                // Maybe not needed strictly, but good for UX if reusing this script there.

                // Update Header Badge (Implementation dependent)
                // updateGlobalCartBadge(); // Handled by event listener now

            } else {
                showToast(data.message || 'Could not add to cart', 'error');
            }

        } catch (error) {
            console.error(error);
            showToast(error.message || 'Something went wrong', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                if (btn.tagName === 'BUTTON' && !btn.querySelector('span')) {
                    btn.textContent = originalText;
                } else {
                    btn.style.opacity = '1';
                }
            }
        }
    }


    // =========================================================
    // HELPERS
    // =========================================================
    function getCSRFToken() {
        // Try Input first
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;

        // Try Cookie
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
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

    // Initial Load
    // Initial Load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateCartBadge);
    } else {
        updateCartBadge();
    }

    // Listen for Cart Updates
    window.addEventListener('cart:updated', () => {
        updateCartBadge();
    });

    async function updateCartBadge() {
        try {
            const response = await fetch('/api/mycart/count/');
            if (!response.ok) return;

            const data = await response.json();
            const badge = document.getElementById('cartBadge');

            if (badge) {
                const count = data.cart_count;
                badge.textContent = count;
                badge.style.display = count > 0 ? 'flex' : 'none';
            }
        } catch (error) {
            console.error('Error fetching cart count:', error);
        }
    }

});
