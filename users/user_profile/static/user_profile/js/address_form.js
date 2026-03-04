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
});
