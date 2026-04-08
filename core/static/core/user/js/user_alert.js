/**
 * REX CC User — UserAlert Modal System
 * File: core/static/core/user/js/user_alert.js
 *
 * Replaces native browser confirm() with a styled modal.
 * Matches the light hub-card style used across user pages.
 *
 * API:
 *   UserAlert.confirm(title, message, onConfirm, options?)
 */

(function () {
  'use strict';

  /* ── Build the DOM once ── */
  const backdrop = document.createElement('div');
  backdrop.className = 'ua-backdrop';
  backdrop.id = 'userAlertBackdrop';
  backdrop.innerHTML = `
    <div class="ua-modal" role="dialog" aria-modal="true" aria-labelledby="uaTitle">
      <h3 class="ua-title" id="uaTitle"></h3>
      <p class="ua-message" id="uaMessage"></p>
      <div class="ua-actions">
        <button class="ua-btn ua-btn-cancel" id="uaCancelBtn">Cancel</button>
        <button class="ua-btn ua-btn-confirm" id="uaConfirmBtn">Confirm</button>
      </div>
    </div>
  `;

  // Append once DOM is ready
  if (document.body) {
    document.body.appendChild(backdrop);
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      document.body.appendChild(backdrop);
    });
  }

  /* ── References ── */
  const titleEl = backdrop.querySelector('#uaTitle');
  const messageEl = backdrop.querySelector('#uaMessage');
  const cancelBtn = backdrop.querySelector('#uaCancelBtn');
  const confirmBtn = backdrop.querySelector('#uaConfirmBtn');

  let _onConfirm = null;

  /* ── Show / Hide ── */
  function show() {
    backdrop.classList.add('ua-visible');
    confirmBtn.focus();
    document.body.style.overflow = 'hidden';
  }

  function hide() {
    backdrop.classList.remove('ua-visible');
    document.body.style.overflow = '';
    _onConfirm = null;
  }

  /* ── Public: confirm() ── */
  function showConfirm(title, message, onConfirm, options) {
    options = options || {};

    titleEl.textContent = title;
    messageEl.textContent = message;

    confirmBtn.textContent = options.confirmText || 'Confirm';
    cancelBtn.textContent = options.cancelText || 'Cancel';

    // Button style
    confirmBtn.className = 'ua-btn ' + (options.danger ? 'ua-btn-danger' : 'ua-btn-confirm');

    _onConfirm = onConfirm;
    show();
  }

  /* ── Event Listeners ── */
  cancelBtn.addEventListener('click', hide);

  confirmBtn.addEventListener('click', function () {
    hide();
    if (typeof _onConfirm === 'function') {
      _onConfirm();
    }
  });

  // Close on backdrop click (outside modal)
  backdrop.addEventListener('click', function (e) {
    if (e.target === backdrop) {
      hide();
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && backdrop.classList.contains('ua-visible')) {
      hide();
    }
  });

  /* ── Expose globally ── */
  window.UserAlert = {
    confirm: showConfirm
  };
})();
