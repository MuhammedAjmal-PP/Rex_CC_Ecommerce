/**
 * REX CC Authentication JS
 * accounts/static/account/js/user_auth.js
 */

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    messages.forEach(function (message) {
        setTimeout(function () {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            message.style.transition = 'all 0.3s ease';
            setTimeout(function () {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Add password toggle functionality
    addPasswordToggles();

    // Smooth button click feedback with ripple
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(function (button) {
        button.addEventListener('click', function (e) {
            const rect = button.getBoundingClientRect();
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                background: rgba(255,255,255,0.3);
                border-radius: 50%;
                width: 100px;
                height: 100px;
                transform: translate(-50%, -50%) scale(0);
                animation: ripple 0.6s ease-out;
                pointer-events: none;
            `;
            ripple.style.left = (e.clientX - rect.left) + 'px';
            ripple.style.top = (e.clientY - rect.top) + 'px';
            button.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add ripple animation
    if (!document.getElementById('ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: translate(-50%, -50%) scale(4);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
});

/**
 * Add password show/hide toggle to all password fields
 */
function addPasswordToggles() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');

    passwordInputs.forEach(function (input) {
        // Wrap input in a container if not already wrapped
        if (!input.parentElement.classList.contains('password-input-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'password-input-wrapper';
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);

            // Create toggle button
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'password-toggle';
            toggleBtn.setAttribute('aria-label', 'Toggle password visibility');
            toggleBtn.innerHTML = `
                <svg class="eye-icon eye-closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg class="eye-icon eye-open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display: none;">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>
            `;

            wrapper.appendChild(toggleBtn);

            // Add click handler
            toggleBtn.addEventListener('click', function () {
                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';

                const eyeClosed = toggleBtn.querySelector('.eye-closed');
                const eyeOpen = toggleBtn.querySelector('.eye-open');

                if (isPassword) {
                    eyeClosed.style.display = 'none';
                    eyeOpen.style.display = 'block';
                } else {
                    eyeClosed.style.display = 'block';
                    eyeOpen.style.display = 'none';
                }
            });
        }
    });
}
