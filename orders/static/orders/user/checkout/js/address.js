/**
 * Address Configuration
 */
const ENDPOINTS = {
    ADD_ADDRESS: '/myprofile/address/add/', 
    EDIT_ADDRESS: '/myprofile/address/{id}/edit/',
    TOGGLE_DEFAULT: '/myprofile/address/{id}/set-default/'
};

// --- Selection Logic ---

function selectAddress(cardEl, id) {
    if (!cardEl) return;
    
    // UI Update
    document.querySelectorAll('.checkout-address-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');

    // State Update
    CheckoutState.selectedAddressId = id;
    
    // Store data for review
    const name = cardEl.querySelector('.addr-name').innerText;
    // Helper to get text without HTML tags if needed, but innerText is usually fine
    
    CheckoutState.deliveryData = {
        name: name,
        address: cardEl.querySelector('.addr-details').innerText,
        phone: cardEl.querySelector('.addr-phone').innerText
    };

    // Enable Next Button
    const btn = document.getElementById('btn-next-payment');
    if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
        btn.onclick = () => goToStep(2);
    }
}

// --- Management Logic ---

// Note: fetchAddresses is removed because we reload page on list update 
// to respect "no backend changes" constraint for checkout specific partials.

async function toggleAddressForm(isEdit = false, addressId = null) {
    const container = document.getElementById('checkout-address-form-container');
    const titleEl = container.querySelector('.address-form-title');
    
    // If closing (and not switching directly to another mode)
    // We check if it's currently visible and we are just toggling off
    if (container.style.display !== 'none' && !addressId && !isEdit) {
        container.style.display = 'none';
        return;
    }

    // Toggle On
    container.style.display = 'block';

    // If Add & Form already exists (and isn't the Edit form which would have a different action or no add action)
    // The server render puts the Add form there by default.
    // We need to check if we are in "Add Mode" and the form is already valid.
    
    if (!isEdit) {
        // Check if we need to reset/restore
        if (titleEl) titleEl.innerText = "New Address";
        
        // If content was overwritten by Edit previously, we might need to fetch Add.
        // Or if the initial render is there.
        const currentForm = container.querySelector('form');
        const isAddForm = currentForm && currentForm.action.includes('add/');
        
        if (currentForm && isAddForm) {
            // Already set up for add, just show it
            currentForm.reset(); // clear any previous input
            
            // Ensure Cancel button works (re-attach event if needed, but onclick is inline usually)
            setupCancelButton(currentForm);
            
            container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
    }

    // Determine URL
    let url = isEdit ? ENDPOINTS.EDIT_ADDRESS.replace('{id}', addressId) : ENDPOINTS.ADD_ADDRESS;
    
    // Show Loading ONLY if we are fetching
    // If we are here, it means we don't have the correct form inline.
    container.innerHTML = '<div style="padding:20px; text-align:center;">Loading form...</div>';

    try {
        const response = await fetch(url);
        if (response.ok) {
            const html = await response.text();
            
            // Parse HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const formWrapper = doc.querySelector('.form-wrapper') || doc.querySelector('form');
            
            if (formWrapper) {
                container.innerHTML = '';
                
                // Re-create wrapper structure if we blew it away
                const wrapperDiv = document.createElement('div');
                wrapperDiv.className = 'address-form-wrapper';
                
                const titleHeading = document.createElement('h4');
                titleHeading.className = 'address-form-title';
                titleHeading.innerText = isEdit ? 'Edit Address' : 'New Address';
                
                wrapperDiv.appendChild(titleHeading);
                
                // Append the fetched form 
                // (Note: partials/address_form.html usually has .form-wrapper, so we might nest wrappers or strip one)
                // The partial has <div class="form-wrapper" ...> so we might not need our own wrapper details.
                // But our CSS expects .address-form-title inside .address-form-wrapper potentially.
                
                // Let's just use the fetched content but inject the title.
                wrapperDiv.appendChild(formWrapper);
                container.appendChild(wrapperDiv);
                
                // Customize Form
                const form = container.querySelector('form');
                if (form) {
                    form.action = url;
                    form.onsubmit = handleAddressSubmit;
                    setupCancelButton(form);
                    
                    // Style overrides if necessary
                    form.style.padding = "0"; // Reset if partial has padding
                    form.style.border = "none";
                }
                
                // Initialize Custom Label Logic for the fetched form
                initCustomLabelLogic(container);
                
                container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                container.innerHTML = '<div style="color:red; padding:10px;">Error loading form content.</div>';
            }
        } else {
             const res = await response.json(); 
             if (res.error) alert(res.error);
             container.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading form:', error);
        container.innerHTML = '<div style="color:red; padding:10px;">Connection failed.</div>';
    }
}

function setupCancelButton(form) {
    const cancelBtn = form.querySelector('.btn-outline');
    if (cancelBtn) {
        cancelBtn.removeAttribute('href');
        cancelBtn.type = 'button';
        cancelBtn.onclick = () => {
             document.getElementById('checkout-address-form-container').style.display = 'none';
        };
        cancelBtn.innerHTML = '<span class="material-icons">close</span> Cancel';
    }
}

async function handleAddressSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const url = form.action;
    const formData = new FormData(form);
    
    // Add submit button loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerText : 'Save';
    if(submitBtn) {
        submitBtn.innerText = 'SAVING...';
        submitBtn.disabled = true;
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (response.ok) {
            // Success - Reload to refresh address list (since we don't have partial endpoint)
            window.location.reload();
        } else {
            const data = await response.json();
            if (data.errors) {
                 // Map errors to fields
                 // Clear previous errors
                 form.querySelectorAll('.form-error').forEach(e => e.remove());
                 
                 for (let field in data.errors) {
                     const errorMsg = data.errors[field][0];
                     const input = form.querySelector(`[name="${field}"]`);
                     if (input) {
                         // Insert error message
                         const errorDiv = document.createElement('div');
                         errorDiv.className = 'form-error';
                         errorDiv.style.color = '#dc3545';
                         errorDiv.style.fontSize = '0.8rem';
                         errorDiv.style.marginTop = '4px';
                         errorDiv.innerText = errorMsg;
                         input.parentNode.appendChild(errorDiv);
                     } else {
                         alert(`${field}: ${errorMsg}`);
                     }
                 }
            }
        }
    } catch (error) {
        console.error('Save failed:', error);
        alert('An error occurred. Please try again.');
    } finally {
        if (submitBtn) {
            submitBtn.innerText = originalText;
            submitBtn.disabled = false;
        }
    }
}

async function setAsDefault(e, id) {
    e.stopPropagation();
    try {
        const url = ENDPOINTS.TOGGLE_DEFAULT.replace('{id}', id);
        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrf
            }
        });
        
        if (response.ok) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Toggle default failed:', error);
    }
}

function editAddress(e, id) {
    e.stopPropagation();
    toggleAddressForm(true, id);
}

// Alias for add new (called by template button)
function showAddAddressForm() {
    toggleAddressForm(false);
}

// Custom Label Logic (Ported from address_form.js)
function initCustomLabelLogic(container) {
    if (!container) return;
    
    const radioInputs = container.querySelectorAll('input[name="label_choice"]');
    const customLabelGroup = container.querySelector('#customLabelGroup');
    const customLabelInput = container.querySelector('#custom_label');
    const hiddenLabelInput = container.querySelector('#label');

    function updateLabelState() {
        const selectedRadio = container.querySelector('input[name="label_choice"]:checked');
        if (!selectedRadio) return;

        const value = selectedRadio.value;

        if (value === 'Other') {
            if (customLabelGroup) customLabelGroup.style.display = 'block';
            if (hiddenLabelInput) hiddenLabelInput.value = (customLabelInput && customLabelInput.value) || 'Other';
        } else {
            if (customLabelGroup) customLabelGroup.style.display = 'none';
            if (customLabelInput) customLabelInput.value = ''; // Clear custom input logic if desired, or keep it. Original kept it. 
            // Original: hiddenLabelInput.value = value;
            if (hiddenLabelInput) hiddenLabelInput.value = value;
        }
    }

    if (radioInputs.length > 0) {
        // Initial check
        updateLabelState();

        // Radio change listeners
        radioInputs.forEach(radio => {
            radio.addEventListener('change', updateLabelState);
        });
    }

    // Custom label input listener
    if (customLabelInput && hiddenLabelInput) {
        customLabelInput.addEventListener('input', function() {
            hiddenLabelInput.value = this.value;
        });
    }
}

// Initialization Logic
document.addEventListener('DOMContentLoaded', () => {
    // Check if there are any addresses
    const addressCards = document.querySelectorAll('.checkout-address-card');
    const formContainer = document.getElementById('checkout-address-form-container');
    
    // Initialize label logic for the pre-rendered form if it exists
    if (formContainer) {
        initCustomLabelLogic(formContainer);
    }
    
    // If no addresses found, automatically open the Add Address form
    if (addressCards.length === 0) {
        // We use a slight timeout to ensure DOM is fully ready if script is deferred
        setTimeout(() => {
            showAddAddressForm();
        }, 100);
    }
});
