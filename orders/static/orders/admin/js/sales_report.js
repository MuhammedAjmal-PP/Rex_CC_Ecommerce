/**
 * Sales Report — Admin JS
 * Handles: custom date toggle, download link sync.
 */

document.addEventListener("DOMContentLoaded", function () {
  const customToggleBtn = document.getElementById("customToggleBtn");
  const customDateForm = document.getElementById("customDateForm");

  if (customToggleBtn && customDateForm) {
    customToggleBtn.addEventListener("click", function () {
      customDateForm.classList.toggle("visible");
      customToggleBtn.classList.toggle("active");
    });
  }
});
