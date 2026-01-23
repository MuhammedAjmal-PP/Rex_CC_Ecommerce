document.addEventListener("DOMContentLoaded", function () {
  const labelRadios = document.querySelectorAll('input[name="label_choice"]');
  const customLabelGroup = document.getElementById("customLabelGroup");
  const customLabelInput = document.getElementById("custom_label");
  const hiddenLabelInput = document.getElementById("label");

  // Function to update the hidden label field
  function updateLabel() {
    const selectedRadio = document.querySelector(
      'input[name="label_choice"]:checked',
    );

    if (selectedRadio.value === "Other") {
      customLabelGroup.style.display = "block";
      // If custom label has value, use it; otherwise use 'Other'
      hiddenLabelInput.value = customLabelInput.value.trim() || "Other";
    } else {
      customLabelGroup.style.display = "none";
      customLabelInput.value = "";
      hiddenLabelInput.value = selectedRadio.value;
    }
  }

  // Add event listeners to radio buttons
  labelRadios.forEach((radio) => {
    radio.addEventListener("change", updateLabel);
  });

  // Add event listener to custom label input
  customLabelInput.addEventListener("input", function () {
    const selectedRadio = document.querySelector(
      'input[name="label_choice"]:checked',
    );
    if (selectedRadio && selectedRadio.value === "Other") {
      // Update hidden field with custom value or 'Other' if empty
      hiddenLabelInput.value = this.value.trim() || "Other";
    }
  });

  // Initialize on page load
  updateLabel();

  // Form validation (optional)
  const form = document.querySelector(".address-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      const selectedRadio = document.querySelector(
        'input[name="label_choice"]:checked',
      );

      // Ensure hidden label field is updated before submission
      if (selectedRadio.value === "Other") {
        hiddenLabelInput.value = customLabelInput.value.trim() || "Other";
      }
    });
  }
});
