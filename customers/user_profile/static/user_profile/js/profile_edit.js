// Profile Edit JavaScript - Avatar Preview and Form Enhancements

document.addEventListener('DOMContentLoaded', function () {
    // Avatar preview functionality
    const avatarInput = document.getElementById('id_avatar');
    const avatarPreview = document.getElementById('avatar-preview');

    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', function (e) {
            const file = e.target.files[0];

            if (file) {
                // Validate file type
                const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (!validTypes.includes(file.type)) {
                    alert('Please select a valid image file (JPG, PNG, or GIF)');
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

                // Preview the image
                const reader = new FileReader();
                reader.onload = function (e) {
                    // If preview is an img tag
                    if (avatarPreview.tagName === 'IMG') {
                        avatarPreview.src = e.target.result;
                    } else {
                        // If preview is a placeholder div, convert it to img
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.alt = 'Avatar Preview';
                        img.id = 'avatar-preview';
                        avatarPreview.parentNode.replaceChild(img, avatarPreview);
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

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
