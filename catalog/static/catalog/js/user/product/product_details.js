/**
 * REX CC Product Details Page - JavaScript
 * File: catalog/static/catalog/js/user/product/product_details.js
 * 
 * Features:
 * - Internal Image Zoom
 * - Thumbnail gallery navigation
 * - Quantity selector with stock limits
 * - Variant hover effects (if needed beyond CSS)
 */

document.addEventListener('DOMContentLoaded', function () {
    // ===========================================
    // INTERNAL IMAGE ZOOM FUNCTIONALITY
    // ===========================================
    const mainImageContainer = document.getElementById('mainImageContainer');
    const mainImage = document.getElementById('mainImage');

    if (mainImageContainer && mainImage) {

        mainImageContainer.addEventListener('mousemove', function (e) {
            const { left, top, width, height } = mainImageContainer.getBoundingClientRect();
            const x = e.clientX - left;
            const y = e.clientY - top;

            // Calculate percentage position
            const xPercent = (x / width) * 100;
            const yPercent = (y / height) * 100;

            // Set transform origin to the cursor position
            mainImage.style.transformOrigin = `${xPercent}% ${yPercent}%`;
            mainImage.style.transform = 'scale(2)'; // Zoom level
        });

        mainImageContainer.addEventListener('mouseleave', function () {
            // Reset zoom
            mainImage.style.transform = 'scale(1)';
            setTimeout(() => {
                mainImage.style.transformOrigin = 'center center';
            }, 300); // Reset origin after transition
        });
    }

    // ===========================================
    // THUMBNAIL GALLERY
    // ===========================================
    const thumbnailBtns = document.querySelectorAll('.thumbnail-btn');

    thumbnailBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const newImageUrl = this.getAttribute('data-image-url');

            // Update main image
            if (mainImage && newImageUrl) {
                // Fade out
                mainImage.style.opacity = '0';

                setTimeout(() => {
                    mainImage.src = newImageUrl;
                    // Fade in
                    mainImage.style.opacity = '1';
                }, 200);
            }

            // Update active state
            thumbnailBtns.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // ===========================================
    // QUANTITY SELECTOR
    // ===========================================
    const qtyInput = document.getElementById('qtyInput');
    const qtyMinus = document.getElementById('qtyMinus');
    const qtyPlus = document.getElementById('qtyPlus');

    if (qtyInput && qtyMinus && qtyPlus) {
        const maxQty = parseInt(qtyInput.getAttribute('max')) || 999;
        const minQty = parseInt(qtyInput.getAttribute('min')) || 1;

        qtyMinus.addEventListener('click', function () {
            let currentVal = parseInt(qtyInput.value) || 1;
            if (currentVal > minQty) {
                qtyInput.value = currentVal - 1;
            }
        });

        qtyPlus.addEventListener('click', function () {
            let currentVal = parseInt(qtyInput.value) || 1;
            if (currentVal < maxQty) {
                qtyInput.value = currentVal + 1;
            }
        });

        // Validate on manual input
        qtyInput.addEventListener('change', function () {
            let val = parseInt(this.value);
            if (isNaN(val) || val < minQty) {
                this.value = minQty;
            } else if (val > maxQty) {
                this.value = maxQty;
            }
        });
    }

    // ===========================================
    // WISHLIST BUTTON TOGGLE
    // ===========================================
    const wishlistBtn = document.getElementById('wishlistBtn');

    if (wishlistBtn) {
        wishlistBtn.addEventListener('click', function () {
            const icon = this.querySelector('.material-icons');
            if (icon.textContent === 'favorite_border') {
                icon.textContent = 'favorite';
                icon.style.color = '#D32F2F';
                this.style.borderColor = '#D32F2F';

                // Optional: Add a pulse animation
                this.style.transform = 'scale(1.1)';
                setTimeout(() => { this.style.transform = 'scale(1)'; }, 200);
            } else {
                icon.textContent = 'favorite_border';
                icon.style.color = '';
                this.style.borderColor = '';
            }
        });
    }

    // ===========================================
    // ADD TO CART BUTTON (Placeholder)
    // ===========================================
    const addToCartBtn = document.getElementById('addToCartBtn');

    if (addToCartBtn && !addToCartBtn.disabled) {
        addToCartBtn.addEventListener('click', function () {
            const originalText = this.innerHTML;
            const originalBg = this.style.background;

            this.innerHTML = '<span class="material-icons">check</span> Added to Cart';
            this.style.background = 'linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%)';
            this.disabled = true;

            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.background = originalBg;
                this.disabled = false;
            }, 2000);
        });
    }
});
