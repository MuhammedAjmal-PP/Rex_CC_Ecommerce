// REX CC Admin Auth JavaScript
// Auto-dismiss messages and smooth interactions

document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss messages after 5 seconds
    const messages = document.querySelectorAll('.message');

    messages.forEach(function (message) {
        setTimeout(function () {
            message.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            message.style.opacity = '0';
            message.style.transform = 'translateY(-20px)';

            setTimeout(function () {
                message.remove();
            }, 500);
        }, 5000);
    });

    // Password toggle functionality
    const passwordToggles = document.querySelectorAll('.password-toggle');

    passwordToggles.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
            const wrapper = this.closest('.password-input-wrapper');
            const input = wrapper.querySelector('input');
            const svg = this.querySelector('.eye-icon');

            if (input.type === 'password') {
                // Show password
                input.type = 'text';
                svg.style.opacity = '0.5';

                // Add slash line to eye icon
                const slash = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                slash.setAttribute('x1', '1');
                slash.setAttribute('y1', '1');
                slash.setAttribute('x2', '23');
                slash.setAttribute('y2', '23');
                slash.setAttribute('stroke', 'currentColor');
                slash.setAttribute('stroke-width', '2');
                slash.setAttribute('class', 'eye-slash');
                svg.appendChild(slash);
            } else {
                // Hide password
                input.type = 'password';
                svg.style.opacity = '1';

                // Remove slash line from eye icon
                const slash = svg.querySelector('.eye-slash');
                if (slash) {
                    slash.remove();
                }
            }
        });
    });

    // Add smooth button click animation
    const buttons = document.querySelectorAll('.btn-primary');

    buttons.forEach(function (button) {
        button.addEventListener('click', function (e) {
            // Create ripple effect
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            this.appendChild(ripple);

            setTimeout(function () {
                ripple.remove();
            }, 600);
        });
    });

    // Form validation feedback
    const inputs = document.querySelectorAll('input[type="email"], input[type="password"], input[type="text"]');

    inputs.forEach(function (input) {
        input.addEventListener('blur', function () {
            if (this.value.trim() === '' && this.hasAttribute('required')) {
                this.style.borderColor = '#DC3545';
            } else {
                this.style.borderColor = '';
            }
        });

        input.addEventListener('focus', function () {
            this.style.borderColor = '';
        });
    });
});
