// Profile Edit JavaScript - Complete with Image Cropping and Password Management

let cropper = null;

// Password visibility toggle function (GLOBAL)
function togglePasswordVisibility(inputId, button) {
    const inputElement = document.getElementById(inputId);
    const icon = button.querySelector('.material-icons');

    if (inputElement.type === 'password') {
        inputElement.type = 'text';
        icon.textContent = 'visibility_off';
    } else {
        inputElement.type = 'password';
        icon.textContent = 'visibility';
    }
}

// Avatar Cropping Functionality
function initAvatarCropping() {
    const avatarInput = document.getElementById('id_avatar');
    const avatarPreview = document.getElementById('avatar-preview');
    const avatarWrapper = document.getElementById('avatarWrapper');
    const cropModal = document.getElementById('avatarCropModal');
    const cropImage = document.getElementById('cropImage');
    const cropBtn = document.getElementById('cropBtn');
    const cancelCropBtn = document.getElementById('cancelCropBtn');
    const removeAvatarBtn = document.getElementById('removeAvatarBtn');
    const removeAvatarInput = document.getElementById('remove_avatar');

    if (!avatarInput || !cropModal) return;

    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(cropModal);

    // Handle avatar input change
    avatarInput.addEventListener('change', function (e) {
        const file = e.target.files[0];

        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (JPG, PNG, GIF, or WebP)');
            avatarInput.value = '';
            return;
        }

        // Validate file size (5MB max)
        const maxSize = 5 * 1024 * 1024; // 5MB in bytes
        if (file.size > maxSize) {
            alert('File size must be less than 5MB');
            avatarInput.value = '';
            return;
        }

        // Load image into cropper
        const reader = new FileReader();
        reader.onload = function (event) {
            cropImage.src = event.target.result;
            modal.show();
        };
        reader.readAsDataURL(file);
    });

    // Initialize cropper when modal is shown
    cropModal.addEventListener('shown.bs.modal', function () {
        if (cropper) {
            cropper.destroy();
        }

        cropper = new Cropper(cropImage, {
            viewMode: 2,
            dragMode: 'crop',
            aspectRatio: NaN, // Free-form cropping
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

    // Cleanup cropper when modal is hidden
    cropModal.addEventListener('hidden.bs.modal', function () {
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        cropImage.src = '';
    });

    // Apply crop
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

        // Get original file info
        const originalFile = avatarInput.files[0];
        const originalName = originalFile.name;
        const originalType = originalFile.type;

        // Supported formats
        const supportedFormats = {
            'image/png': { mime: 'image/png', quality: undefined },
            'image/jpeg': { mime: 'image/jpeg', quality: 0.9 },
            'image/jpg': { mime: 'image/jpeg', quality: 0.9 },
            'image/webp': { mime: 'image/webp', quality: 0.9 },
            'image/gif': { mime: 'image/png', quality: undefined },
        };

        const formatSettings = supportedFormats[originalType] || { mime: 'image/png', quality: undefined };
        const mimeType = formatSettings.mime;
        const quality = formatSettings.quality;

        canvas.toBlob(function (blob) {
            if (!blob) {
                alert('Failed to create image blob');
                return;
            }

            // Create file from blob
            const croppedFile = new File([blob], originalName, {
                type: mimeType,
                lastModified: Date.now()
            });

            // Set the cropped file to the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(croppedFile);
            avatarInput.files = dataTransfer.files;

            // Update preview
            const previewUrl = URL.createObjectURL(blob);
            updateAvatarPreview(previewUrl);

            // Clear remove flag
            removeAvatarInput.value = '';

            // Close modal
            modal.hide();
        }, mimeType, quality);
    });

    // Cancel crop
    cancelCropBtn.addEventListener('click', function () {
        // Reset file input
        avatarInput.value = '';
        modal.hide();
    });

    // Remove avatar button
    if (removeAvatarBtn) {
        removeAvatarBtn.addEventListener('click', function (e) {
            e.preventDefault();

            if (confirm('Are you sure you want to remove your profile photo?')) {
                // Clear file input
                avatarInput.value = '';

                // Set remove flag
                removeAvatarInput.value = 'true';

                // Reset preview to placeholder
                resetAvatarPreview();
            }
        });
    }

    // Helper function to update avatar preview
    function updateAvatarPreview(imageUrl) {
        const wrapper = avatarWrapper || document.querySelector('.avatar-wrapper');
        const currentPreview = document.getElementById('avatar-preview'); // Re-query to avoid stale reference

        if (currentPreview) {
            if (currentPreview.tagName === 'IMG') {
                currentPreview.src = imageUrl;
            } else {
                // Replace placeholder with image
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = 'Profile Photo';
                img.id = 'avatar-preview';
                img.className = 'avatar-image';
                currentPreview.replaceWith(img);
            }
        }

        // Update state
        if (wrapper) {
            wrapper.setAttribute('data-has-image', 'true');
        }

        // Show remove button
        if (removeAvatarBtn) {
            removeAvatarBtn.style.display = 'flex';
        }
    }

    // Helper function to reset avatar preview
    function resetAvatarPreview() {
        const wrapper = avatarWrapper || document.querySelector('.avatar-wrapper');
        const currentPreview = document.getElementById('avatar-preview');

        if (currentPreview && currentPreview.tagName === 'IMG') {
            // Replace image with placeholder
            const placeholder = document.createElement('div');
            placeholder.className = 'avatar-placeholder';
            placeholder.id = 'avatar-preview';
            placeholder.innerHTML = '<span class="material-icons">person</span>';
            currentPreview.replaceWith(placeholder);
        }

        // Update state
        if (wrapper) {
            wrapper.setAttribute('data-has-image', 'false');
        }

        // Hide remove button
        if (removeAvatarBtn) {
            removeAvatarBtn.style.display = 'none';
        }
    }
}

// Password Change Toggle Button Text
function initPasswordToggle() {
    const toggleBtn = document.getElementById('passwordToggleBtn');
    const toggleText = document.getElementById('passwordToggleText');
    const securityCollapse = document.getElementById('securityCollapse');

    if (!toggleBtn || !toggleText || !securityCollapse) {
        console.log('Password toggle elements not found');
        return;
    }

    // Listen for collapse show/hide events
    securityCollapse.addEventListener('show.bs.collapse', function () {
        toggleText.textContent = 'Cancel';
    });

    securityCollapse.addEventListener('hide.bs.collapse', function () {
        toggleText.textContent = 'Change Password';
    });
}

// Password Change Functionality
function initPasswordChange() {
    const securityCollapse = document.getElementById('securityCollapse');
    const passwordForm = document.getElementById('changePasswordForm');

    if (!securityCollapse || !passwordForm) {
        console.log('Password form elements not found');
        return;
    }

    // Password change form submission
    passwordForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const form = e.target;
        const submitBtn = form.querySelector("button[type='submit']");
        const formData = new FormData(form);

        // Create or get alert container
        let alertBox = form.querySelector('.password-alert');
        if (!alertBox) {
            alertBox = document.createElement('div');
            alertBox.className = 'password-alert';
            form.insertBefore(alertBox, form.firstChild);
        }

        submitBtn.disabled = true;
        const originalHTML = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
        alertBox.innerHTML = ""; // Clear previous messages

        try {
            const response = await fetch(form.dataset.changePasswordUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            const data = await response.json();
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;

            if (data.success) {
                alertBox.innerHTML = `<div class="alert alert-success">${data.message || 'Password updated successfully!'}</div>`;
                form.reset();

                // Close collapse after delay
                setTimeout(() => {
                    bootstrap.Collapse.getInstance(securityCollapse)?.hide();
                    // Clear alert after closing
                    setTimeout(() => {
                        alertBox.innerHTML = "";
                    }, 300);
                }, 2000);

            } else {
                let errors = "";
                for (const field in data.errors) {
                    data.errors[field].forEach(msg => {
                        errors += `<p class="mb-0">${msg}</p>`;
                    });
                }
                alertBox.innerHTML = `<div class="alert alert-danger">${errors || 'Failed to update password'}</div>`;
            }
        } catch (error) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHTML;
            alertBox.innerHTML = `<div class="alert alert-danger">An error occurred. Please try again.</div>`;
            console.error('Password change error:', error);
        }
    });
}

// Main initialization
document.addEventListener('DOMContentLoaded', function () {
    // Initialize avatar cropping functionality
    initAvatarCropping();

    // Initialize password toggle button text
    initPasswordToggle();

    // Initialize password change functionality
    initPasswordChange();

    // Form validation feedback
    const forms = document.querySelectorAll('.profile-form, .add-email-form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalHTML = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalHTML;
                }, 5000);
            }
        });
    });

    // Email confirmation for making email primary
    const primaryEmailForms = document.querySelectorAll('button[name="action_make_primary"]');
    primaryEmailForms.forEach(button => {
        button.closest('form')?.addEventListener('submit', function (e) {
            const confirmed = confirm(
                'This will change your primary email. Continue?'
            );
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});