// Profile Edit JavaScript - Complete with Image Cropping and Password Management

let cropper = null;

// Password visibility toggle
function togglePassword(inputElement, button) {
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
    const avatarInput = document.getElementById('avatar-input');
    const avatarPreview = document.getElementById('avatar-preview');
    const cropModal = document.getElementById('avatarCropModal');
    const cropImage = document.getElementById('cropImage');
    const cropBtn = document.getElementById('cropBtn');
    const cancelCropBtn = document.getElementById('cancelCropBtn');

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
            aspectRatio: NaN, // Free-form cropping - no aspect ratio restriction
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

        // Reset file input if crop was cancelled
        if (!avatarInput.dataset.croppedFile) {
            avatarInput.value = '';
        }
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
            avatarInput.dataset.croppedFile = 'true';

            // Update preview
            const previewUrl = URL.createObjectURL(blob);
            if (avatarPreview.tagName === 'IMG') {
                avatarPreview.src = previewUrl;
            } else {
                // If preview is a placeholder div, convert it to img
                const img = document.createElement('img');
                img.src = previewUrl;
                img.alt = 'Avatar Preview';
                img.id = 'avatar-preview';
                avatarPreview.parentNode.replaceChild(img, avatarPreview);
            }

            // Close modal
            modal.hide();
        }, mimeType, quality);
    });

    // Cancel crop
    cancelCropBtn.addEventListener('click', function () {
        avatarInput.value = '';
        delete avatarInput.dataset.croppedFile;
        modal.hide();
    });
}

// Password Change Functionality
function initPasswordChange() {
    const collapseElement = document.getElementById('changePasswordCollapse');
    const toggleBtn = document.getElementById('togglePasswordBtn');
    const toggleBtnText = document.getElementById('toggleBtnText');
    const passwordForm = document.getElementById('changePasswordForm');
    const alertBox = document.getElementById('passwordAlert');

    // Check if elements exist
    if (!collapseElement || !toggleBtn || !toggleBtnText) {
        console.error('Required password change elements not found');
        return;
    }

    // Toggle button text when collapse shows/hides
    collapseElement.addEventListener('shown.bs.collapse', function () {
        toggleBtnText.textContent = 'Cancel';
    });

    collapseElement.addEventListener('hidden.bs.collapse', function () {
        toggleBtnText.textContent = 'Change Password';
    });

    // Password change form submission
    if (passwordForm && alertBox) {
        passwordForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const form = e.target;
            const submitBtn = form.querySelector("button[type='submit']");
            const formData = new FormData(form);

            submitBtn.disabled = true;
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

                if (data.success) {
                    alertBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    form.reset();

                    // Close collapse after a short delay
                    setTimeout(() => {
                        bootstrap.Collapse.getOrCreateInstance(collapseElement).hide();
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
                    alertBox.innerHTML = `<div class="alert alert-danger">${errors}</div>`;
                }
            } catch (error) {
                submitBtn.disabled = false;
                alertBox.innerHTML = `<div class="alert alert-danger">An error occurred. Please try again.</div>`;
                console.error('Password change error:', error);
            }
        });
    }
}

// Main initialization
document.addEventListener('DOMContentLoaded', function () {
    // Initialize avatar cropping functionality
    initAvatarCropping();

    // Initialize password change functionality
    initPasswordChange();

    // Form validation feedback
    const forms = document.querySelectorAll('.profile-form, .add-email-form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
            }
        });
    });

    // Email confirmation for making email primary
    const primaryEmailForms = document.querySelectorAll('form[action*="make-primary"]');
    primaryEmailForms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const confirmed = confirm(
                'This will change your primary email and block the old email from being reused. Continue?'
            );
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});