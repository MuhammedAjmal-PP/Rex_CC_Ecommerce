/**
 * Checkout Address Management
 * Handles: select, add, edit, set-default address within checkout flow.
 */

const ADDRESS_ENDPOINTS = {
    ADD:          '/myprofile/address/add/',
    EDIT:         '/myprofile/address/{id}/edit/',
    SET_DEFAULT:  '/myprofile/address/{id}/set-default/',
    REFRESH_LIST: '/api/addresses/get/'    // Returns partial address_section.html
};

// ────────────────── Selection ──────────────────

function selectAddress(cardEl, id) {
    if (!cardEl) return;

    document.querySelectorAll('.checkout-address-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');

    CheckoutState.selectedAddressId = id;

    CheckoutState.deliveryData = {
        name:    cardEl.querySelector('.addr-name')?.innerText   || '',
        address: cardEl.querySelector('.addr-details')?.innerText || '',
        phone:   cardEl.querySelector('.addr-phone')?.innerText   || ''
    };

    const btn = document.getElementById('btn-next-payment');
    if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor  = 'pointer';
        btn.onclick = () => goToStep(2);
    }
}

// ────────────────── Helpers ──────────────────

/** Wire the Cancel / Back button inside the form to just hide the container */
function _wireCancel(form) {
    // The address_form.html hides the cancel link when rendered on checkout
    // So we find or create one inside .lux-form-actions
    let cancelBtn = form.querySelector('.hub-btn-outline');
    const actionsDiv = form.querySelector('.lux-form-actions');

    if (!cancelBtn && actionsDiv) {
        // Create a cancel button
        cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'hub-btn-outline';
        cancelBtn.innerHTML = '<span class="material-icons" style="font-size:16px; margin-right:4px; vertical-align:middle;">close</span> Cancel';
        actionsDiv.insertBefore(cancelBtn, actionsDiv.firstChild);
    }

    if (cancelBtn) {
        cancelBtn.removeAttribute('href');
        cancelBtn.setAttribute('role', 'button');
        cancelBtn.style.cursor = 'pointer';
        cancelBtn.onclick = (e) => {
            e.preventDefault();
            document.getElementById('checkout-address-form-container').style.display = 'none';
        };
    }
}

/** Clear all previous error messages inside a form */
function _clearErrors(form) {
    form.querySelectorAll('.lux-form-error').forEach(el => el.remove());
}

/** Show field-level errors inside the form */
function _showErrors(form, errors) {
    _clearErrors(form);

    for (const field in errors) {
        const msg   = Array.isArray(errors[field]) ? errors[field][0] : errors[field];
        const input = form.querySelector(`[name="${field}"]`);

        const errorDiv = document.createElement('div');
        errorDiv.className = 'lux-form-error';
        errorDiv.textContent = msg;

        if (input) {
            const group = input.closest('.lux-form-group');
            (group || input.parentNode).appendChild(errorDiv);
        } else {
            // Non-field error → put at top of form
            form.prepend(errorDiv);
        }
    }
}

// ────────────────── Custom Label Logic ──────────────────

function _initLabelLogic(container) {
    if (!container) return;

    const radios      = container.querySelectorAll('input[name="label_choice"]');
    const customGroup = container.querySelector('#customLabelGroup');
    const customInput = container.querySelector('#custom_label');
    const hiddenInput = container.querySelector('#label');

    function sync() {
        const checked = container.querySelector('input[name="label_choice"]:checked');
        if (!checked) return;

        if (checked.value === 'Other') {
            if (customGroup)  customGroup.style.display = 'block';
            if (hiddenInput)  hiddenInput.value = customInput?.value || 'Other';
        } else {
            if (customGroup)  customGroup.style.display = 'none';
            if (customInput)  customInput.value = '';
            if (hiddenInput)  hiddenInput.value = checked.value;
        }
    }

    radios.forEach(r => r.addEventListener('change', sync));
    if (customInput && hiddenInput) {
        customInput.addEventListener('input', () => { hiddenInput.value = customInput.value; });
    }
    sync();
}

// ────────────────── Init helpers on a form inside a container ──────────────────

function _initFormPlugins(container) {
    _initLabelLogic(container);
}

// ────────────────── AJAX Form Submit ──────────────────

async function _submitAddressForm(e) {
    e.preventDefault();
    const form = e.target;
    const url  = form.getAttribute('data-action') || form.action;
    const fd   = new FormData(form);

    const submitBtn    = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.innerHTML || 'Save';
    if (submitBtn) { submitBtn.innerHTML = 'SAVING…'; submitBtn.disabled = true; }

    try {
        const resp = await fetch(url, {
            method:  'POST',
            body:    fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        if (resp.ok) {
            // Success → refresh the address list section
            _refreshAddressSection();
            return;
        }

        // Validation failed
        const ct = resp.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
            const data = await resp.json();
            if (data.errors) {
                _showErrors(form, data.errors);
            } else if (data.error) {
                alert(data.error);
            }
        } else {
            // Fallback: parse returned HTML and swap form contents
            const html   = await resp.text();
            const parser = new DOMParser();
            const doc    = parser.parseFromString(html, 'text/html');
            const newForm = doc.querySelector('.lux-address-form');
            if (newForm) {
                form.innerHTML = newForm.innerHTML;
                _wireCancel(form);
                _initFormPlugins(form.closest('#checkout-address-form-container') || form);
            } else {
                alert('Validation failed. Please check your inputs.');
            }
        }
    } catch (err) {
        console.error('Address save failed:', err);
        alert('Connection error. Please try again.');
    } finally {
        if (submitBtn) { submitBtn.innerHTML = originalText; submitBtn.disabled = false; }
    }
}

// ────────────────── Bind submit to a form element ──────────────────

function _bindSubmit(form, actionUrl) {
    // Store the target URL so it survives even if form.action gets weird
    form.setAttribute('data-action', actionUrl);

    // Remove any previous listener by cloning
    const freshForm = form.cloneNode(true);
    form.parentNode.replaceChild(freshForm, form);

    freshForm.addEventListener('submit', _submitAddressForm);
    _wireCancel(freshForm);

    return freshForm;
}

// ────────────────── Show "Add New" Address Form ──────────────────

function showAddAddressForm() {
    const container = document.getElementById('checkout-address-form-container');
    if (!container) return;

    // If already open with an Add form, toggle off
    if (container.style.display !== 'none' && container.getAttribute('data-mode') === 'add') {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';
    container.setAttribute('data-mode', 'add');

    // The form is already server-rendered inside this container
    let form = container.querySelector('.lux-address-form');
    if (form) {
        form.reset();
        _clearErrors(form);
        form = _bindSubmit(form, ADDRESS_ENDPOINTS.ADD);
        _initFormPlugins(container);

        // Update title
        const title = container.querySelector('.chk-section-title, .address-form-title');
        if (title) title.textContent = 'New Address';

        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
    }

    // Fallback: no pre-rendered form → fetch it
    _fetchAndInjectForm(container, ADDRESS_ENDPOINTS.ADD, false);
}

// ────────────────── Show "Edit" Address Form ──────────────────

function editAddress(e, id) {
    e.stopPropagation();
    const container = document.getElementById('checkout-address-form-container');
    if (!container) return;

    container.style.display = 'block';
    container.setAttribute('data-mode', 'edit');

    const url = ADDRESS_ENDPOINTS.EDIT.replace('{id}', id);
    _fetchAndInjectForm(container, url, true);
}

// ────────────────── Fetch form and inject into container ──────────────────

async function _fetchAndInjectForm(container, url, isEdit) {
    container.innerHTML = '<div style="padding:20px; text-align:center; font-family:Montserrat,sans-serif; color:#888;">Loading form…</div>';

    try {
        const resp = await fetch(url);
        if (!resp.ok) throw new Error('Failed to load form');

        const html   = await resp.text();
        const parser = new DOMParser();
        const doc    = parser.parseFromString(html, 'text/html');
        const srcForm = doc.querySelector('.lux-address-form');

        if (!srcForm) {
            container.innerHTML = '<div style="color:red; padding:10px;">Error loading form content.</div>';
            return;
        }

        // Build structure
        container.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = 'address-form-wrapper';

        const heading = document.createElement('h4');
        heading.className = 'chk-section-title';
        heading.style.fontSize = '1.1rem';
        heading.textContent = isEdit ? 'Edit Address' : 'New Address';

        wrapper.appendChild(heading);
        wrapper.appendChild(srcForm);
        container.appendChild(wrapper);

        // Bind
        const form = _bindSubmit(srcForm, url);
        form.style.padding = '0';
        form.style.border  = 'none';
        _initFormPlugins(container);

        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (err) {
        console.error('Error loading form:', err);
        container.innerHTML = '<div style="color:red; padding:10px;">Connection failed.</div>';
    }
}

// ────────────────── Refresh entire address section after add/edit ──────────────────

async function _refreshAddressSection() {
    const step = document.getElementById('step-address');
    if (!step) { window.location.reload(); return; }

    try {
        const resp = await fetch(ADDRESS_ENDPOINTS.REFRESH_LIST);
        if (!resp.ok) throw new Error();

        const html = await resp.text();
        step.innerHTML = html;

        // Re-initialise anything inside the newly injected section
        const formContainer = document.getElementById('checkout-address-form-container');
        if (formContainer) _initFormPlugins(formContainer);

        // Auto-select default address if any
        const defaultCard = step.querySelector('.checkout-address-card.default-selection');
        if (defaultCard) {
            selectAddress(defaultCard, defaultCard.getAttribute('data-address-id'));
        }
    } catch {
        window.location.reload();
    }
}

// ────────────────── Set as Default ──────────────────

async function setAsDefault(e, id) {
    e.stopPropagation();
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrf) return;

    try {
        const url  = ADDRESS_ENDPOINTS.SET_DEFAULT.replace('{id}', id);
        const resp = await fetch(url, {
            method:  'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrf }
        });
        if (resp.ok) _refreshAddressSection();
    } catch (err) {
        console.error('Toggle default failed:', err);
    }
}

// ────────────────── DOMContentLoaded ──────────────────

document.addEventListener('DOMContentLoaded', () => {
    const container   = document.getElementById('checkout-address-form-container');
    const cards       = document.querySelectorAll('.checkout-address-card');

    // Init plugins on the pre-rendered form
    if (container) {
        _initFormPlugins(container);

        // Pre-bind the existing Add form so it's ready on first click
        const form = container.querySelector('.lux-address-form');
        if (form) {
            _bindSubmit(form, ADDRESS_ENDPOINTS.ADD);
        }
    }

    // Auto-select default address
    const defaultCard = document.querySelector('.checkout-address-card.default-selection');
    if (defaultCard) {
        selectAddress(defaultCard, defaultCard.getAttribute('data-address-id'));
    }

    // If no addresses at all, auto-open the add form
    if (cards.length === 0) {
        setTimeout(showAddAddressForm, 100);
    }
});
