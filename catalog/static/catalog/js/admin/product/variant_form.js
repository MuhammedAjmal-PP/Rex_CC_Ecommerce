/* ============================================================
   REX CC ADMIN - VARIANT FORM JAVASCRIPT
   Handles formset image uploads with cropping, stock indicator
   Cropper.js v1.6.2 Compatible
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    initStockIndicator();
    initImageFormsetWithCropper();
    initPrimaryRadioLogic();
});

/* ========================================
   GLOBAL CROPPER VARIABLES
   ======================================== */

let cropper = null;
let currentFileInput = null;
let currentPreviewImg = null;
let currentPlaceholder = null;
let currentPreviewWrapper = null;
let currentUploadBox = null;

/* ========================================
   STOCK INDICATOR
   ======================================== */

function initStockIndicator() {
    const stockInput = document.querySelector('input[name="stock"]');
    const stockFill = document.getElementById('stockFill');
    const stockStatus = document.getElementById('stockStatus');

    if (!stockInput || !stockFill || !stockStatus) return;

    function updateStockIndicator(value) {
        const stock = parseInt(value) || 0;
        let percentage, statusText, colorClass;

        if (stock === 0) {
            percentage = 0;
            statusText = 'Out of Stock';
            colorClass = 'low';
        } else if (stock <= 10) {
            percentage = Math.min((stock / 50) * 100, 20);
            statusText = 'Low Stock - Only ' + stock + ' left';
            colorClass = 'low';
        } else if (stock <= 50) {
            percentage = Math.min((stock / 100) * 100, 50);
            statusText = 'Medium Stock - ' + stock + ' units';
            colorClass = 'medium';
        } else {
            percentage = Math.min((stock / 200) * 100, 100);
            statusText = 'Good Stock - ' + stock + ' units';
            colorClass = 'high';
        }

        stockFill.style.width = percentage + '%';
        stockFill.className = 'stock-fill ' + colorClass;
        stockStatus.textContent = statusText;
    }

    updateStockIndicator(stockInput.value);
    stockInput.addEventListener('input', function () {
        updateStockIndicator(this.value);
    });
}

/* ========================================
   IMAGE FORMSET WITH CROPPER
   ======================================== */

function initImageFormsetWithCropper() {
    const container = document.getElementById('imageFormsetContainer');
    const cropModalEl = document.getElementById('cropModal');
    const cropImage = document.getElementById('cropImage');
    const cropBtn = document.getElementById('cropBtn');

    if (!container || !cropModalEl) {
        console.log('Formset container or crop modal not found');
        return;
    }

    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded.');
        return;
    }

    const cropModal = new bootstrap.Modal(cropModalEl);
    const formItems = container.querySelectorAll('.image-form-item');

    formItems.forEach((item, index) => {
        const fileInput = item.querySelector('input[type="file"]');
        const uploadBox = item.querySelector('.image-upload-box');
        const placeholder = item.querySelector('.upload-placeholder-content');
        const previewWrapper = item.querySelector('.image-preview-wrapper');
        const previewImg = item.querySelector('.preview-image');
        const changeBtn = item.querySelector('.change-btn');
        const removeBtn = item.querySelector('.remove-btn');

        if (!fileInput) return;

        // Check for existing image (from data attribute)
        const existingUrl = item.dataset.existingUrl;
        if (existingUrl && existingUrl.trim() !== '') {
            // Mark as having image for styling
            if (uploadBox) uploadBox.classList.add('has-image');
            // Mark the item as having an existing image (for remove logic)
            item.dataset.hasExisting = 'true';
        }

        // Handle file selection - open cropper
        fileInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (!file) return;

            // Validate file type
            if (!file.type.startsWith('image/')) {
                alert('Please select an image file.');
                return;
            }

            // Validate file size (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                alert('Image is too large. Maximum size is 5MB.');
                return;
            }

            // Store references for cropper callback
            currentFileInput = fileInput;
            currentPreviewImg = previewImg;
            currentPlaceholder = placeholder;
            currentPreviewWrapper = previewWrapper;
            currentUploadBox = uploadBox;

            // Load image into cropper modal
            const reader = new FileReader();
            reader.onload = function (event) {
                cropImage.src = event.target.result;
                cropModal.show();
            };
            reader.readAsDataURL(file);
        });

        // Change button click - trigger file input
        if (changeBtn) {
            changeBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                fileInput.click();
            });
        }

        // Remove button click - clear the file input and preview
        if (removeBtn) {
            removeBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                // Clear file input
                fileInput.value = '';

                // Hide preview, show placeholder
                if (previewWrapper) previewWrapper.hidden = true;
                if (placeholder) placeholder.hidden = false;
                if (previewImg) previewImg.src = '';
                if (uploadBox) uploadBox.classList.remove('has-image');
            });
        }
    });

    /* ========= INIT CROPPER WHEN MODAL SHOWN ========= */
    cropModalEl.addEventListener('shown.bs.modal', function () {
        // Destroy existing cropper if any
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        // Initialize Cropper.js
        cropper = new Cropper(cropImage, {
            viewMode: 2,
            dragMode: 'crop',
            aspectRatio: NaN, // Free-form cropping - no aspect ratio restriction
            autoCropArea: 1, // Select full image by default
            autoCrop: true,
            restore: true,
            guides: true,
            center: true,
            highlight: true,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: true,
            responsive: true,
            background: true,
            minContainerWidth: 300,
            minContainerHeight: 300,
        });
    });

    /* ========= CLEANUP CROPPER WHEN MODAL HIDDEN ========= */
    cropModalEl.addEventListener('hidden.bs.modal', function () {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        cropImage.src = '';
    });

    /* ========= CROP CONFIRM ========= */
    cropBtn.addEventListener('click', function () {
        if (!cropper) {
            console.error('Cropper not initialized');
            return;
        }

        const canvas = cropper.getCroppedCanvas({
            imageSmoothingQuality: 'high'
        });

        if (!canvas) {
            alert('Failed to crop the image');
            return;
        }

        // Detect original file type to preserve format
        const originalFile = currentFileInput?.files[0];
        const originalName = originalFile?.name || 'variant_image.png';
        const originalType = originalFile?.type || 'image/png';

        // Supported formats by canvas.toBlob (browser support varies)
        // PNG, JPEG, WebP are widely supported
        // AVIF, GIF may need fallback
        const supportedFormats = {
            'image/png': { mime: 'image/png', quality: undefined },
            'image/jpeg': { mime: 'image/jpeg', quality: 0.9 },
            'image/jpg': { mime: 'image/jpeg', quality: 0.9 },
            'image/webp': { mime: 'image/webp', quality: 0.9 },
            'image/avif': { mime: 'image/avif', quality: 0.9 },
            'image/gif': { mime: 'image/png', quality: undefined }, // GIF -> PNG (canvas doesn't animate)
            'image/svg+xml': { mime: 'image/png', quality: undefined }, // SVG -> PNG (canvas rasterizes)
        };

        // Get format settings, default to PNG for unknown formats (preserves transparency)
        const formatSettings = supportedFormats[originalType] || { mime: 'image/png', quality: undefined };
        const mimeType = formatSettings.mime;
        const quality = formatSettings.quality;

        canvas.toBlob(function (blob) {
            if (!blob) {
                alert('Failed to create image blob');
                return;
            }

            // Create file from blob preserving original format
            const croppedFile = new File([blob], originalName, {
                type: mimeType,
                lastModified: Date.now()
            });

            // Set the cropped file to the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(croppedFile);
            currentFileInput.files = dataTransfer.files;

            // Show preview
            const previewUrl = URL.createObjectURL(blob);
            if (currentPreviewImg) currentPreviewImg.src = previewUrl;
            if (currentPlaceholder) currentPlaceholder.hidden = true;
            if (currentPreviewWrapper) currentPreviewWrapper.hidden = false;
            if (currentUploadBox) currentUploadBox.classList.add('has-image');

            // Close modal
            cropModal.hide();
        }, mimeType, quality);
    });
}

/* ========================================
   PRIMARY CHECKBOX LOGIC
   ======================================== */

function initPrimaryRadioLogic() {
    const container = document.getElementById('imageFormsetContainer');
    if (!container) return;

    const primaryCheckboxes = container.querySelectorAll('input[name$="-is_primary"]');

    // Make primary checkboxes act like radio buttons
    primaryCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                // Uncheck all other primary checkboxes
                primaryCheckboxes.forEach(other => {
                    if (other !== this) {
                        other.checked = false;
                    }
                });
            }
        });
    });
}

/* ========================================
   FORM VALIDATION
   ======================================== */

document.getElementById('variantForm')?.addEventListener('submit', function (e) {
    const sku = document.querySelector('input[name="sku"]');
    const price = document.querySelector('input[name="price"]');

    let isValid = true;

    // Clear previous dynamic errors
    document.querySelectorAll('.error-text.dynamic').forEach(el => el.remove());

    // Validate SKU
    if (sku && !sku.value.trim()) {
        showError(sku, 'SKU is required');
        isValid = false;
    }

    // Validate Price
    if (price && (!price.value || parseFloat(price.value) <= 0)) {
        showError(price, 'Price must be greater than 0');
        isValid = false;
    }

    // Images are optional - no validation required

    if (!isValid) {
        e.preventDefault();
        // Scroll to first error
        const firstError = document.querySelector('.error-text');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});

function showError(input, message) {
    const existingError = input.parentNode.querySelector('.error-text.dynamic');
    if (existingError) return;

    const errorSpan = document.createElement('span');
    errorSpan.className = 'error-text dynamic';
    errorSpan.textContent = message;
    input.parentNode.appendChild(errorSpan);
}

/* ========================================
   INPUT ANIMATIONS
   ======================================== */

document.querySelectorAll('.form-input').forEach(input => {
    input.addEventListener('focus', function () {
        this.parentElement.classList.add('focused');
    });

    input.addEventListener('blur', function () {
        this.parentElement.classList.remove('focused');
    });
});
