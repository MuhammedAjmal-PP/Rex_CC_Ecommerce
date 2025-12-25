/* ============================================================
   REX CC ADMIN - PRODUCT FORM JAVASCRIPT
   File: catalog/static/catalog/js/admin/product/product_form.js
   Cropper.js v1.6.2 Compatible
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    initFileUpload();
});

/* ========================================
   FILE UPLOAD + CROPPER
   ======================================== */

let cropper = null;
let selectedFile = null;

function initFileUpload() {
    const uploadWrapper = document.getElementById('uploadWrapper');
    const fileInput = uploadWrapper?.querySelector('input[type="file"]');
    const uploadInfo = document.getElementById('uploadInfo');
    const uploadPreview = document.getElementById('uploadPreview');
    const previewImg = document.getElementById('previewImg');
    const cropImage = document.getElementById('cropImage');
    const cropModalEl = document.getElementById('cropModal');
    const cropBtn = document.getElementById('cropBtn');

    if (!uploadWrapper || !fileInput || !cropModalEl) {
        console.log('Missing elements for cropper');
        return;
    }

    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded.');
        return;
    }

    const cropModal = new bootstrap.Modal(cropModalEl);

    /* ========= FILE SELECT ========= */
    fileInput.addEventListener('change', function () {
        if (this.files && this.files.length > 0) {
            selectedFile = this.files[0];
            handleImageSelect(selectedFile);
        }
    });

    /* ========= DRAG & DROP ========= */
    uploadWrapper.addEventListener('dragover', function (e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
    });

    uploadWrapper.addEventListener('dragleave', function (e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
    });

    uploadWrapper.addEventListener('drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            selectedFile = files[0];
            handleImageSelect(selectedFile);
        }
    });

    /* ========= CHANGE IMAGE BUTTON ========= */
    const changeImageBtn = document.getElementById('changeImageBtn');
    if (changeImageBtn) {
        changeImageBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
    }

    /* ========= REMOVE IMAGE BUTTON ========= */
    const removeImageBtn = document.getElementById('removeImageBtn');
    const removeThumbnailInput = document.getElementById('removeThumbnail');
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            // Clear the file input
            fileInput.value = '';

            // Set the hidden input to indicate removal
            if (removeThumbnailInput) {
                removeThumbnailInput.value = 'true';
            }

            // Hide preview and show upload placeholder
            hidePreview();
        });
    }

    /* ========= HANDLE IMAGE ========= */
    function handleImageSelect(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            cropImage.src = e.target.result;
            cropModal.show();
        };
        reader.readAsDataURL(file);
    }

    /* ========= INIT CROPPER WHEN MODAL SHOWN ========= */
    cropModalEl.addEventListener('shown.bs.modal', function () {
        // Destroy existing cropper if any
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        // Initialize Cropper.js v1
        cropper = new Cropper(cropImage, {
            viewMode: 2,
            dragMode: 'crop',
            aspectRatio: 1, // Square ratio for product thumbnails
            autoCropArea: 0.8,
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
        // Reset the crop image src to prevent memory issues
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

        canvas.toBlob(function (blob) {
            if (!blob) {
                alert('Failed to create image blob');
                return;
            }

            // Create file from blob
            const originalName = selectedFile?.name || 'product_thumbnail.jpg';
            const croppedFile = new File([blob], originalName, {
                type: 'image/jpeg',
                lastModified: Date.now()
            });

            // Set the cropped file to the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(croppedFile);
            fileInput.files = dataTransfer.files;

            // Show preview in upload area
            const previewUrl = URL.createObjectURL(blob);
            showPreview(previewUrl);

            // Close modal
            cropModal.hide();
        }, 'image/jpeg', 0.9);
    });

    /* ========= SHOW/HIDE PREVIEW ========= */
    function showPreview(src) {
        if (uploadInfo && uploadPreview && previewImg) {
            previewImg.src = src;
            uploadInfo.hidden = true;
            uploadPreview.hidden = false;
            uploadWrapper.classList.add('has-preview');
        }
    }

    function hidePreview() {
        if (uploadInfo && uploadPreview && previewImg) {
            previewImg.src = '';
            uploadInfo.hidden = false;
            uploadPreview.hidden = true;
            uploadWrapper.classList.remove('has-preview');
        }
    }
}
