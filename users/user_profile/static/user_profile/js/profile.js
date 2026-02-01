// Safe Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initProfileLogic);
} else {
    initProfileLogic();
}

function initProfileLogic() {
    
    // -----------------------------------------------------------------------------
    // Profile Badge References
    // -----------------------------------------------------------------------------
    const profileWishlistBadge = document.getElementById('profileWishlistBadge');
    const profileCartBadge = document.getElementById('profileCartBadge');

    // -----------------------------------------------------------------------------
    // API Endpoints
    // -----------------------------------------------------------------------------
    const URLS = {
        cart: '/api/mycart/count/',
        wishlist: '/api/wishlist/'
    };

    // -----------------------------------------------------------------------------
    // Initial Load & Event Listeners
    // -----------------------------------------------------------------------------
    initProfileBadges();

    // Listen for global updates
    window.addEventListener('cart:updated', () => fetchProfileCartCount());
    window.addEventListener('wishlist:changed', () => fetchProfileWishlistCount());


    function initProfileBadges() {
        if (profileCartBadge) fetchProfileCartCount();
        if (profileWishlistBadge) fetchProfileWishlistCount();
    }

    // -----------------------------------------------------------------------------
    // Fetch Logic
    // -----------------------------------------------------------------------------
    async function fetchProfileCartCount() {
        if (!profileCartBadge) return;
        try {
            const response = await fetch(URLS.cart);
            if (response.ok) {
                const data = await response.json();
                updateBadge(profileCartBadge, data.cart_count);
            }
        } catch (error) {
            console.error('Profile: Error fetching cart count', error);
        }
    }

    async function fetchProfileWishlistCount() {
        if (!profileWishlistBadge) return;
        try {
            const response = await fetch(URLS.wishlist, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) {
                const data = await response.json();
                // Wishlist API returns { products: [], count: N } or similar
                // Based on wishlist_offcanvas.js: updateWishlistBadge(data.count || 0);
                updateBadge(profileWishlistBadge, data.count || 0);
            }
        } catch (error) {
            console.error('Profile: Error fetching wishlist count', error);
        }
    }

    // -----------------------------------------------------------------------------
    // Helper: Badge UI Updater
    // -----------------------------------------------------------------------------
    function updateBadge(badgeElement, count) {
        if (count > 0) {
            badgeElement.textContent = count;
            badgeElement.style.display = 'flex';
        } else {
            badgeElement.textContent = '0';
            badgeElement.style.display = 'none';
        }
    }
}
