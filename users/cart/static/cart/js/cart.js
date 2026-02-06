/**
 * CART PAGE LOGIC
 * Strict stock validation and safe updates.
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // DOM ELEMENTS
    // =========================================================================
    const cartItems = document.querySelectorAll('.cart-item');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // =========================================================================
    // EVENT LISTENERS
    // =========================================================================
    cartItems.forEach(item => {
        const slug = item.dataset.slug;
        const sku = item.dataset.sku;

        const decreaseBtn = item.querySelector('.qty-btn[data-action="decrease"]');
        const increaseBtn = item.querySelector('.qty-btn[data-action="increase"]');
        const removeBtn = item.querySelector('.remove-btn');
        const qtyInput = item.querySelector('.qty-input');

        // Decrease
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => handleQuantityUpdate(slug, sku, qtyInput, -1));
        }

        // Increase
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => handleQuantityUpdate(slug, sku, qtyInput, 1));
        }

        // Remove
        if (removeBtn) {
            removeBtn.addEventListener('click', () => handleRemove(slug, sku));
        }
    });


    // =========================================================================
    // HANDLERS
    // =========================================================================

    /**
     * Handles quantity changes:
     * 1. Check current val
     * 2. If increasing, FETCH STOCK first
     * 3. Validate
     * 4. Proceed to update
     */
    async function handleQuantityUpdate(slug, sku, inputEl, change) {
        const currentQty = parseInt(inputEl.value);
        const newQty = currentQty + change;

        // Frontend BLOCK: Min quantity
        if (newQty < 1) return;

        showLoadingCursor(true);

        try {
            // STEP 1: If increasing, we MUST validate stock with server
            if (change > 0) {
                const stockResponse = await fetch(`/api/${slug}/v/${sku}/stock/fetch/`);
                if (!stockResponse.ok) throw new Error('Failed to fetch stock');

                const stockData = await stockResponse.json();
                const stock = stockData.stock;

                if (newQty > stock) {
                    showToast(`Sorry, only ${stock} available.`, 'error');
                    // Disable btn potentially?
                    return; // BLOCK ACTION
                }
            }

            // STEP 2: Proceed to Update
            await updateCartItem(slug, sku, newQty);

        } catch (error) {
            console.error(error);
            showToast('Something went wrong. Please try again.', 'error');
        } finally {
            showLoadingCursor(false);
        }
    }

    /**
     * Handles removal of item
     */
    let itemToRemove = null; // Store {slug, sku}
    const removeModalEl = document.getElementById('removeConfirmModal');
    let removeModal = null;
    const confirmBtn = document.getElementById('confirmRemoveBtn');

    if (removeModalEl) {
        removeModal = new bootstrap.Modal(removeModalEl);
        
        // Bind Confirm Action once
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                if (itemToRemove) {
                    performRemove(itemToRemove.slug, itemToRemove.sku);
                }
            });
        }
    }

    function handleRemove(slug, sku) {
        itemToRemove = { slug, sku };
        if (removeModal) {
            removeModal.show();
        } else {
            // Fallback if modal missing
            if (confirm('Are you sure you want to remove this item?')) {
                performRemove(slug, sku);
            }
        }
    }

    async function performRemove(slug, sku) {
        if (removeModal) removeModal.hide();
        showLoadingCursor(true);
        try {
            const formData = new FormData();
            formData.append('remove', 'true');

            const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                body: formData
            });

            if (response.redirected || response.ok) {
                window.location.reload();
            } else {
                throw new Error('Remove failed');
            }

        } catch (error) {
            showToast('Could not remove item.', 'error');
        } finally {
            showLoadingCursor(false);
            itemToRemove = null;
        }
    }

    /**
     * Updates backend.
     * The backend returns a redirect on success, or JSON error on fail.
     * We follow the redirect/reload.
     */
    async function updateCartItem(slug, sku, quantity) {
        const formData = new FormData();
        formData.append('quantity', quantity);

        const response = await fetch(`/api/mycart/${slug}/v/${sku}/update/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            body: formData
        });

        // Backend returns redirect on success
        if (response.redirected) {
            window.location.href = response.url; // Follow redirect (reload)
            return;
        }

        // If backend returned JSON error (400)
        if (!response.ok) {
            const data = await response.json();
            if (data.error) {
                showToast(data.error, 'error');
            } else {
                throw new Error('Update failed');
            }
            return;
        }

        // Fallback reload
        window.location.reload();
    }


    // =========================================================================
    // UI HELPERS
    // =========================================================================

    function showLoadingCursor(show) {
        document.body.style.cursor = show ? 'wait' : 'default';
        const btns = document.querySelectorAll('button');
        btns.forEach(b => b.disabled = show);
    }

    function showToast(message, type = 'info') {
        // Reuse global toast container if exists, or create one
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
                ${type === 'error' ? 'error' : 'info'}
            </span>
            ${message}
        `;

        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
});
