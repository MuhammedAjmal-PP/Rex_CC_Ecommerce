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

// --- DOM & Helper Logic ---

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
            if (customLabelInput) customLabelInput.value = ''; 
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

// Address Validation Logic (India Post API)
function initAddressValidation(container) {
    if (!container) return;

    const postalCodeInput = container.querySelector('#postal_code');
    const cityInput = container.querySelector('#city');
    const stateInput = container.querySelector('#state');
    
    // Remove existing feedback if re-initializing
    let feedbackElement = container.querySelector('.api-feedback');
    if (!feedbackElement) {
        feedbackElement = document.createElement('div');
        feedbackElement.className = 'form-text text-muted api-feedback';
        feedbackElement.style.fontSize = '0.85rem';
        feedbackElement.style.marginTop = '4px';
        if (postalCodeInput) {
            postalCodeInput.parentNode.appendChild(feedbackElement);
        }
    }

    if (postalCodeInput) {
        postalCodeInput.addEventListener('change', function() {
            const pin = this.value.trim();
            if (pin.length === 6 && /^\d+$/.test(pin)) {
                
                // Show loading state
                feedbackElement.textContent = 'Fetching details from India Post...';
                feedbackElement.style.color = '#666';
                postalCodeInput.classList.remove('is-invalid');
                
                // Fetch from Public API
                fetch(`https://api.postalpincode.in/pincode/${pin}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data && data[0].Status === "Success") {
                            const postOfficeData = data[0].PostOffice[0];
                            const state = postOfficeData.State;
                            
                            // 1. Auto-fill State & Lock it
                            if (stateInput) {
                                stateInput.value = state;
                                stateInput.setAttribute('readonly', true);
                                stateInput.classList.add('locked-input');
                            }
                            
                            // 2. City Logic: Leave it UNLOCKED and UNTOUCHED
                            if (cityInput) {
                                 cityInput.removeAttribute('readonly');
                            }
                            
                            // Success: Clear any error messages
                            feedbackElement.textContent = '';
                            postalCodeInput.classList.remove('is-invalid');
                            postalCodeInput.classList.add('is-valid');
                        } else {
                            throw new Error('Invalid Pincode');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        feedbackElement.textContent = 'Invalid Postal Code. Please enter a valid code.';
                        feedbackElement.style.color = '#d9534f'; 
                        postalCodeInput.classList.add('is-invalid');
                        
                        // Strict Mode: Keep State locked/empty if invalid
                        if (stateInput) {
                            stateInput.value = ''; // Clear invalid state
                            stateInput.setAttribute('readonly', true); // Keep it locked
                        }
                    });
            } else if (pin.length > 0) {
                 feedbackElement.textContent = 'Postal code must be 6 digits.';
                 feedbackElement.style.color = '#d9534f';
                 postalCodeInput.classList.add('is-invalid');
            } else {
                feedbackElement.textContent = '';
                postalCodeInput.classList.remove('is-invalid', 'is-valid');
                if (stateInput && !stateInput.value) {
                     stateInput.removeAttribute('readonly'); 
                     stateInput.setAttribute('readonly', true); // Strict consistency
                }
            }
        });
    }
}

// --- Form Management Logic ---

async function toggleAddressForm(isEdit = false, addressId = null) {
    const container = document.getElementById('checkout-address-form-container');
    const titleEl = container.querySelector('.address-form-title');
    
    // Toggle Off if already visible and matching mode
    if (container.style.display !== 'none' && !addressId && !isEdit) {
        container.style.display = 'none';
        return;
    }

    // Toggle On
    container.style.display = 'block';

    // Handle "Add New" Mode reuse
    if (!isEdit) {
        if (titleEl) titleEl.innerText = "New Address";
        
        const currentForm = container.querySelector('form');
        const isAddForm = currentForm && currentForm.action.includes('add/');
        
        if (currentForm && isAddForm) {
            currentForm.reset(); 
            setupCancelButton(currentForm);
            container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }
    }

    // Determine URL
    let url = isEdit ? ENDPOINTS.EDIT_ADDRESS.replace('{id}', addressId) : ENDPOINTS.ADD_ADDRESS;
    
    // Show Loading
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
                
                // Re-create wrapper structure
                const wrapperDiv = document.createElement('div');
                wrapperDiv.className = 'address-form-wrapper';
                
                const titleHeading = document.createElement('h4');
                titleHeading.className = 'address-form-title';
                titleHeading.innerText = isEdit ? 'Edit Address' : 'New Address';
                
                wrapperDiv.appendChild(titleHeading);
                wrapperDiv.appendChild(formWrapper);
                container.appendChild(wrapperDiv);
                
                // Customize Form
                const form = container.querySelector('form');
                if (form) {
                    form.action = url;
                    form.onsubmit = handleAddressSubmit;
                    setupCancelButton(form);
                    form.style.padding = "0"; 
                    form.style.border = "none";
                }
                
                // Initialize Custom Logic
                initCustomLabelLogic(container);
                initAddressValidation(container);
                
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

async function handleAddressSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const url = form.action;
    const formData = new FormData(form);
    
    // Loading State
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
            // Success - Reload to refresh list
            window.location.reload();
        } else {
            const data = await response.json();
            if (data.errors) {
                 // Clear previous errors
                 form.querySelectorAll('.form-error').forEach(e => e.remove());
                 
                 for (let field in data.errors) {
                     const errorMsg = data.errors[field][0];
                     const input = form.querySelector(`[name="${field}"]`);
                     if (input) {
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

function showAddAddressForm() {
    toggleAddressForm(false);
}

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    // Check if there are any addresses
    const addressCards = document.querySelectorAll('.checkout-address-card');
    const formContainer = document.getElementById('checkout-address-form-container');
    
    // Initialize label & validation logic for the pre-rendered form if it exists
    if (formContainer) {
        initCustomLabelLogic(formContainer);
        initAddressValidation(formContainer);
    }
    
    // If no addresses found, automatically open the Add Address form
    if (addressCards.length === 0) {
        setTimeout(() => {
            showAddAddressForm();
        }, 100);
    }
});
