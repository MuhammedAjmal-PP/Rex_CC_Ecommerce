/* ============================================================
   REX CC ADMIN - VARIANT FORM JAVASCRIPT
   Handles formset image uploads, dynamic slots, cropping, validation
   Cropper.js v1.6.2 Compatible
   ============================================================ */

document.addEventListener('DOMContentLoaded', function () {
    initStockIndicator();
    initImageFormsetWithCropper(); // Initializes existing forms
    initPrimaryRadioLogic();
    initDynamicFormset(); // New: Handles adding slots
    initFormValidation(); // New: Strict validation
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
   DYNAMIC FORMSET HANDLING
   ======================================== */

function initDynamicFormset() {
    const addBtn = document.getElementById('addFormBtn');
    const container = document.getElementById('imageFormsetContainer');
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
    const badge = document.querySelector('.card-header-badge');

    if (!addBtn || !container || !totalFormsInput) return;

    addBtn.addEventListener('click', function(e) {
        e.preventDefault();

        const formCount = parseInt(totalFormsInput.value);
        const forms = container.querySelectorAll('.image-form-item');
        
        if (forms.length === 0) {
            console.error("No form template found to clone!");
            return;
        }

        // Clone the last form
        const templateForm = forms[forms.length - 1];
        const newForm = templateForm.cloneNode(true);
        
        // Update regex to find the old index
        const oldIndex = templateForm.dataset.formIndex;
        const newIndex = formCount;
        const regex = new RegExp(`-${oldIndex}-`, 'g');
        const regexId = new RegExp(`_${oldIndex}_`, 'g'); // Django IDs often use underscores

        newForm.dataset.formIndex = newIndex;
        newForm.dataset.existingUrl = '';
        newForm.dataset.hasExisting = 'false';
        
        // Update all inputs/labels/ids inside the new form
        newForm.innerHTML = newForm.innerHTML.replace(regex, `-${newIndex}-`); 
        // Note: HTML replace might not catch all attribute mutations if done this way on complex nodes,
        // but for standard Django formsets it usually works. 
        // Better approach: iterate elements.
        
        // Let's iterate to be safe and clean properties
        resetFormElements(newForm, newIndex, oldIndex);

        // Update visual elements
        const uploadLabel = newForm.querySelector('.upload-label');
        if (uploadLabel) uploadLabel.textContent = `Image ${newIndex + 1}`;
        
        const uploadBox = newForm.querySelector('.image-upload-box');
        if (uploadBox) uploadBox.classList.remove('has-image');
        
        const previewWrapper = newForm.querySelector('.image-preview-wrapper');
        const placeholder = newForm.querySelector('.upload-placeholder-content');
        const previewImg = newForm.querySelector('.preview-image');
        
        if (previewWrapper) previewWrapper.hidden = true;
        if (placeholder) placeholder.hidden = false;
        if (previewImg) previewImg.src = '';

        // Remove any error messages
        newForm.querySelectorAll('.error-text').forEach(el => el.remove());
        newForm.querySelectorAll('.form-errors').forEach(el => el.remove());

        // Remove DELETE input if it was copied
        const deleteInput = newForm.querySelector(`input[name$="-DELETE"]`);
        if (deleteInput) deleteInput.remove();

        // Append to container
        container.appendChild(newForm);

        // Update Management Form
        totalFormsInput.value = formCount + 1;
        if (badge) badge.textContent = `${formCount + 1} slots`;

        // Re-initialize listeners for the new form
        initSingleImageForm(newForm);
        
        // Re-init primary logic to include new radio
        initPrimaryRadioLogic();
    });
}

function resetFormElements(form, newIndex, oldIndex) {
    // Inputs, Selects, Textareas
    const inputs = form.querySelectorAll('input, select, textarea, label');
    const regexName = new RegExp(`-${oldIndex}-`, 'g');
    const regexId = new RegExp(`id_form-${oldIndex}-`, 'g'); // Standard Django ID prefix
    const regexFor = new RegExp(`id_form-${oldIndex}-`, 'g');

    inputs.forEach(input => {
        if (input.name) {
            input.name = input.name.replace(regexName, `-${newIndex}-`);
        }
        if (input.id) {
            input.id = input.id.replace(regexId, `id_form-${newIndex}-`);
            // Custom ID replacements if needed (e.g. previewImg0 -> previewImg1)
            // Our current HTML uses specific IDs like uploadBox0.
        }
        if (input.tagName === 'LABEL' && input.htmlFor) {
            input.htmlFor = input.htmlFor.replace(regexFor, `id_form-${newIndex}-`);
        }
        
        // Clear values
        if (input.type !== 'hidden' && input.type !== 'checkbox' && input.type !== 'radio') {
            input.value = '';
        }
        if (input.type === 'checkbox' || input.type === 'radio') {
            input.checked = false;
        }
        if (input.type === 'file') {
            input.value = '';
        }
    });

    // Fix custom IDs in our template (uploadBox0, placeholder0, etc.)
    // Note: The innerHTML replace in initDynamicFormset handles text content and other attributes,
    // but we should manually update IDs that don't match standard Django patterns if they exist.
    // Our template uses: uploadBox{{index}}, placeholder{{index}}, preview{{index}}, previewImg{{index}}
    
    const elementsWithId = form.querySelectorAll('[id]');
    elementsWithId.forEach(el => {
        if (el.id.includes(oldIndex)) {
            // Replace the LAST occurrence of the index to avoid breaking if index is part of name
            // But here our IDs are suffixed with index: uploadBox0
            const idBase = el.id.substring(0, el.id.length - String(oldIndex).length);
            if (el.id === idBase + oldIndex) {
               el.id = idBase + newIndex;
            }
        }
    });
}


/* ========================================
   IMAGE FORMSET WITH CROPPER
   ======================================== */

function initImageFormsetWithCropper() {
    const container = document.getElementById('imageFormsetContainer');
    if (!container) return;
    
    const formItems = container.querySelectorAll('.image-form-item');
    formItems.forEach(item => {
        initSingleImageForm(item);
    });

    // Init the modal only once
    const cropModalEl = document.getElementById('cropModal');
    if (cropModalEl) {
        initCropperModal(cropModalEl);
    }
}

function initSingleImageForm(item) {
    const fileInput = item.querySelector('input[type="file"]');
    // Re-query elements scoped to this item to ensure we get the right ones
    // especially after cloning/ID updates
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
        if (uploadBox) uploadBox.classList.add('has-image');
        item.dataset.hasExisting = 'true';
    }

    // Handle file selection - open cropper
    // Remove existing listener if any (cloning copies listeners? No, usually not.)
    // But to be safe, just add.
    
    fileInput.onchange = function (e) {
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
        // Need to update global references to match THIS item's elements
        currentPreviewImg = previewImg; 
        currentPlaceholder = placeholder; 
        currentPreviewWrapper = previewWrapper;
        currentUploadBox = uploadBox;

        const cropModalEl = document.getElementById('cropModal');
        const cropImage = document.getElementById('cropImage');
        const cropModal = bootstrap.Modal.getOrCreateInstance(cropModalEl);

        const reader = new FileReader();
        reader.onload = function (event) {
            cropImage.src = event.target.result;
            cropModal.show();
        };
        reader.readAsDataURL(file);
    };

    if (changeBtn) {
        changeBtn.onclick = function (e) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        };
    }

    if (removeBtn) {
        removeBtn.onclick = function (e) {
            e.preventDefault();
            e.stopPropagation();

            fileInput.value = '';

            if (previewWrapper) previewWrapper.hidden = true;
            if (placeholder) placeholder.hidden = false;
            if (previewImg) previewImg.src = '';
            if (uploadBox) uploadBox.classList.remove('has-image');

            const hasExisting = item.dataset.hasExisting === 'true';
            if (hasExisting) {
                // Find existing DELETE input in this item scope
                let deleteInput = item.querySelector(`input[name$="-DELETE"]`);
                
                if (!deleteInput) {
                    const index = item.dataset.formIndex;
                    deleteInput = document.createElement('input');
                    deleteInput.type = 'hidden';
                    deleteInput.name = `form-${index}-DELETE`;
                    deleteInput.id = `id_form-${index}-DELETE`;
                    deleteInput.value = 'on';
                    item.appendChild(deleteInput);
                } else {
                    deleteInput.value = 'on';
                }

                item.dataset.existingUrl = '';
                item.dataset.hasExisting = 'false';
            }
        };
    }
}

function initCropperModal(cropModalEl) {
    const cropImage = document.getElementById('cropImage');
    const cropBtn = document.getElementById('cropBtn');
    
    // Remove existing listeners to avoid duplicates
    const newCropModal = cropModalEl.cloneNode(true);
    cropModalEl.parentNode.replaceChild(newCropModal, cropModalEl);
    
    // Re-query after replace
    const modalEl = document.getElementById('cropModal');
    const imgEl = document.getElementById('cropImage');
    const btnEl = document.getElementById('cropBtn');
    
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    modalEl.addEventListener('shown.bs.modal', function () {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }

        cropper = new Cropper(imgEl, {
            viewMode: 2,
            dragMode: 'crop',
            aspectRatio: NaN,
            autoCropArea: 1,
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

    modalEl.addEventListener('hidden.bs.modal', function () {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        imgEl.src = '';
    });

    btnEl.addEventListener('click', function () {
        if (!cropper) return;

        const canvas = cropper.getCroppedCanvas({ imageSmoothingQuality: 'high' });
        if (!canvas) {
            alert('Failed to crop');
            return;
        }

        const originalFile = currentFileInput?.files[0];
        const originalName = originalFile?.name || 'variant_image.png';
        const originalType = originalFile?.type || 'image/png';
        
        const supportedFormats = {
             'image/png': { mime: 'image/png' },
             'image/jpeg': { mime: 'image/jpeg', quality: 0.9 },
             'image/jpg': { mime: 'image/jpeg', quality: 0.9 },
             'image/webp': { mime: 'image/webp', quality: 0.9 },
        };

        const formatSettings = supportedFormats[originalType] || { mime: 'image/png' };
        
        canvas.toBlob(function (blob) {
            if (!blob) return;

            const croppedFile = new File([blob], originalName, {
                type: formatSettings.mime,
                lastModified: Date.now()
            });

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(croppedFile);
            if (currentFileInput) currentFileInput.files = dataTransfer.files;

            const previewUrl = URL.createObjectURL(blob);
            if (currentPreviewImg) currentPreviewImg.src = previewUrl;
            if (currentPlaceholder) currentPlaceholder.hidden = true;
            if (currentPreviewWrapper) currentPreviewWrapper.hidden = false;
            if (currentUploadBox) currentUploadBox.classList.add('has-image');

            modal.hide();
        }, formatSettings.mime, formatSettings.quality);
    });
}


/* ========================================
   PRIMARY CHECKBOX LOGIC
   ======================================== */

function initPrimaryRadioLogic() {
    // Re-query because elements might be added
    const container = document.getElementById('imageFormsetContainer');
    if (!container) return;

    // Use event delegation? Or just re-attach. 
    // Re-attaching is safer given current structure.
    const primaryCheckboxes = container.querySelectorAll('input[name$="-is_primary"]');

    primaryCheckboxes.forEach(checkbox => {
        // Remove old listener to avoid duplicates if re-init
        checkbox.onchange = function () {
            if (this.checked) {
                primaryCheckboxes.forEach(other => {
                    if (other !== this) {
                        other.checked = false;
                    }
                });
            }
        };
    });
}

/* ========================================
   STRICT FORM VALIDATION
   ======================================== */

function initFormValidation() {
    const form = document.getElementById('variantForm');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        let isValid = true;
        document.querySelectorAll('.error-text.dynamic').forEach(el => el.remove());

        // 1. Basic Fields
        const sku = form.querySelector('input[name="sku"]');
        const price = form.querySelector('input[name="price"]');
        
        if (sku && !sku.value.trim()) {
            showError(sku, 'SKU is required');
            isValid = false;
        }
        if (price && (!price.value || parseFloat(price.value) <= 0)) {
            showError(price, 'Price must be greater than 0');
            isValid = false;
        }

        // 2. Image Count Validation
        const imageItems = form.querySelectorAll('.image-form-item');
        let validImageCount = 0;
        let primarySelected = false;

        imageItems.forEach(item => {
            const hasExisting = item.dataset.hasExisting === 'true';
            const fileInput = item.querySelector('input[type="file"]');
            const hasNewFile = fileInput && fileInput.files.length > 0;
            const isMarkedForDelete = item.querySelector('input[name$="-DELETE"]')?.value === 'on';

            // It counts if:
            // (Existing AND NOT Deleted) OR (New File Selected)
            if ((hasExisting && !isMarkedForDelete) || hasNewFile) {
                validImageCount++;
                
                // Check if this valid image is primary
                const primaryCb = item.querySelector('input[name$="-is_primary"]');
                if (primaryCb && primaryCb.checked) {
                    primarySelected = true;
                }
            }
        });

        const imageContainer = document.querySelector('.form-card .card-header'); // Anchor for error

        if (validImageCount < 3) {
            showError(imageContainer, `Minimum 3 images required. You have ${validImageCount}.`);
            isValid = false;
        }

        if (!primarySelected && validImageCount > 0) {
            // Only show if we have images but none are primary
            showError(imageContainer, 'You must select one primary image.');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
            const firstError = document.querySelector('.error-text.dynamic');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
}

function showError(input, message) {
    // If input is not a direct input element (like the card header), handle gracefully
    let parent = input.parentNode;
    if (input.classList.contains('card-header')) {
        parent = input; // append inside header
    }

    const errorSpan = document.createElement('span');
    errorSpan.className = 'error-text dynamic';
    errorSpan.style.display = 'block'; // Ensure block display
    errorSpan.style.color = '#dc3545';
    errorSpan.style.fontSize = '0.875rem';
    errorSpan.style.marginTop = '0.25rem';
    errorSpan.textContent = message;
    
    parent.appendChild(errorSpan);
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
