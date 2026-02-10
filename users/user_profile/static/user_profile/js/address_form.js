/**
 * Address Form Interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    const radioInputs = document.querySelectorAll('input[name="label_choice"]');
    const customLabelGroup = document.getElementById('customLabelGroup');
    const customLabelInput = document.getElementById('custom_label');
    const hiddenLabelInput = document.getElementById('label');

    function updateLabelState() {
        const selectedRadio = document.querySelector('input[name="label_choice"]:checked');
        if (!selectedRadio) return;

        const value = selectedRadio.value;

        if (value === 'Other') {
            customLabelGroup.style.display = 'block';
            hiddenLabelInput.value = customLabelInput.value || 'Other';
        } else {
            customLabelGroup.style.display = 'none';
            hiddenLabelInput.value = value;
        }
    }

    // Initial check
    updateLabelState();

    // Radio change listeners
    radioInputs.forEach(radio => {
        radio.addEventListener('change', updateLabelState);
    });

    // Custom label input listener
    if (customLabelInput) {
        customLabelInput.addEventListener('input', function() {
            hiddenLabelInput.value = this.value;
        });
    }

    // Address Validation Logic (India Post API)
    const postalCodeInput = document.getElementById('postal_code');
    const cityInput = document.getElementById('city'); 
    const stateInput = document.getElementById('state');
    const feedbackElement = document.createElement('div');
    feedbackElement.className = 'form-text text-muted';
    feedbackElement.style.fontSize = '0.85rem';
    feedbackElement.style.marginTop = '4px';
    
    if (postalCodeInput) {
        postalCodeInput.parentNode.appendChild(feedbackElement);

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
                            
                            // Success: Clear any error messages, but don't show "State detected" text clutter
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
                        
                        // Strict Mode: Keep State locked/empty if invalid? 
                        // Or allow fallback? User said "user must be enter valid postal_code".
                        // Use strict approach: Do NOT unlock state for manual entry if API fails.
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
                }
            }
        });
    }
});
