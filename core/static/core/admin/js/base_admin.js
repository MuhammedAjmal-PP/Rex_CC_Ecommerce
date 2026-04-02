/**
 * REX CC Admin — Base JavaScript
 * File: core/static/core/admin/js/base_admin.js
 *
 * 1. Message auto-dismiss (moved from inline script in base_admin.html)
 * 2. AdminAlert — reusable modal alert system (replaces native alert/confirm)
 */

(function () {
    'use strict';

    /* ========================================
       MESSAGE AUTO-DISMISS
       ======================================== */

    document.addEventListener('DOMContentLoaded', function () {
        const messages = document.querySelectorAll('.alert-message');

        messages.forEach(function (message) {
            // Auto-dismiss after 3 seconds
            setTimeout(function () {
                dismissMessage(message);
            }, 3000);

            // Manual close button
            const closeBtn = message.querySelector('.alert-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', function () {
                    dismissMessage(message);
                });
            }
        });

        function dismissMessage(message) {
            message.classList.add('fade-out');
            setTimeout(function () {
                message.remove();

                // Remove container if no messages left
                var container = document.querySelector('.messages-container');
                if (container && container.children.length === 0) {
                    container.remove();
                }
            }, 300); // Match animation duration
        }

        /* ========================================
           SIDEBAR ACTIVE PAGE DETECTION
           Uses data-section attributes on nav items
           to match URL path segments.
           ======================================== */

        var currentPath = window.location.pathname;
        var pathSegments = currentPath.split('/').filter(Boolean);
        var navItems = document.querySelectorAll('.sidebar-nav .nav-item[data-section]');
        var matched = false;

        navItems.forEach(function (item) {
            var section = item.getAttribute('data-section');
            if (!section || section === 'dashboard') return;

            // Check if any URL path segment starts with the section keyword
            var isMatch = pathSegments.some(function (seg) {
                return seg.startsWith(section);
            });

            if (isMatch) {
                item.classList.add('active');
                matched = true;
            }
        });

        // Fallback: if nothing matched, highlight Dashboard
        if (!matched) {
            var dashItem = document.querySelector('.sidebar-nav .nav-item[data-section="dashboard"]');
            if (dashItem) dashItem.classList.add('active');
        }
    });

    /* ========================================
       ADMIN ALERT — MODAL ALERT SYSTEM
       ======================================== */

    const ICON_MAP = {
        success: 'check_circle',
        error: 'cancel',
        warning: 'warning',
        info: 'info',
        confirm: 'help_outline'
    };

    const COLOR_MAP = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6',
        confirm: '#000000'
    };

    /**
     * Show a modal alert dialog.
     * @param {string} type - 'success' | 'error' | 'warning' | 'info'
     * @param {string} title - Modal title
     * @param {string} message - Modal body message
     */
    function showAlert(type, title, message) {
        var modalEl = document.getElementById('adminAlertModal');
        if (!modalEl) {
            // Fallback if modal not in DOM
            window.alert(message);
            return;
        }

        var icon = modalEl.querySelector('.admin-alert-icon');
        var titleEl = modalEl.querySelector('.admin-alert-title');
        var messageEl = modalEl.querySelector('.admin-alert-message');
        var confirmBtn = modalEl.querySelector('.admin-alert-confirm-btn');
        var okBtn = modalEl.querySelector('.admin-alert-ok-btn');

        // Set content
        icon.textContent = ICON_MAP[type] || ICON_MAP.info;
        icon.style.color = COLOR_MAP[type] || COLOR_MAP.info;
        titleEl.textContent = title;
        messageEl.textContent = message;

        // Show OK button, hide Confirm button
        if (okBtn) okBtn.style.display = '';
        if (confirmBtn) confirmBtn.style.display = 'none';

        // Remove any old confirm handler
        if (confirmBtn) {
            confirmBtn.replaceWith(confirmBtn.cloneNode(true));
        }

        var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    /**
     * Show a confirmation dialog with a callback.
     * @param {string} title - Modal title
     * @param {string} message - Modal body message
     * @param {function} onConfirm - Callback if user clicks "Confirm"
     */
    function showConfirm(title, message, onConfirm) {
        var modalEl = document.getElementById('adminAlertModal');
        if (!modalEl) {
            if (window.confirm(message)) {
                onConfirm();
            }
            return;
        }

        var icon = modalEl.querySelector('.admin-alert-icon');
        var titleEl = modalEl.querySelector('.admin-alert-title');
        var messageEl = modalEl.querySelector('.admin-alert-message');
        var confirmBtn = modalEl.querySelector('.admin-alert-confirm-btn');
        var okBtn = modalEl.querySelector('.admin-alert-ok-btn');

        // Set content
        icon.textContent = ICON_MAP.confirm;
        icon.style.color = COLOR_MAP.confirm;
        titleEl.textContent = title;
        messageEl.textContent = message;

        // Show Confirm button, hide OK button
        if (okBtn) okBtn.style.display = 'none';
        if (confirmBtn) {
            confirmBtn.style.display = '';
            // Fresh listener (avoid stacking)
            var freshBtn = confirmBtn.cloneNode(true);
            confirmBtn.replaceWith(freshBtn);
            freshBtn.addEventListener('click', function () {
                var modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
                if (typeof onConfirm === 'function') onConfirm();
            });
        }

        var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    // Expose globally
    window.AdminAlert = {
        show: showAlert,
        confirm: showConfirm
    };
})();
