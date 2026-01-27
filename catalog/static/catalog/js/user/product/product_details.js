document.addEventListener('DOMContentLoaded', () => {
  /* =========================================
     Quantity Selector
     ========================================= */
  const qtyInputs = document.querySelectorAll('.pdp-qty-input');

  qtyInputs.forEach(input => {
    const btnMinus = input.parentElement.querySelector('[data-action="decrease"]');
    const btnPlus = input.parentElement.querySelector('[data-action="increase"]');

    // Helper to update value
    const updateValue = (newVal) => {
      if (newVal < 1) newVal = 1;
      // You might add max stock check here if data attribute exists
      input.value = newVal;
    };

    btnMinus.addEventListener('click', () => {
      updateValue(parseInt(input.value) - 1);
    });

    btnPlus.addEventListener('click', () => {
      updateValue(parseInt(input.value) + 1);
    });

    // Prevent non-numeric input
    input.addEventListener('change', () => {
      const val = parseInt(input.value);
      if (isNaN(val) || val < 1) {
        input.value = 1;
      }
    });
  });

  /* =========================================
     Image Gallery
     ========================================= */
  const mainImage = document.querySelector('.pdp-main-image');
  const thumbBtns = document.querySelectorAll('.pdp-thumb-btn');

  if (mainImage && thumbBtns.length > 0) {
    thumbBtns.forEach(btn => {
      btn.addEventListener('click', function () {
        // Remove active class from all
        thumbBtns.forEach(b => b.classList.remove('active'));
        // Add to clicked
        this.classList.add('active');

        // Update main image
        const newSrc = this.querySelector('img').getAttribute('src');
        // Optional: Fade effect could be added here
        mainImage.style.opacity = '0.8';
        setTimeout(() => {
          mainImage.src = newSrc;
          mainImage.style.opacity = '1';
        }, 100);
      });
    });
  }

  /* =========================================
     Zoom Effect (Simple Lens/Pan)
     ========================================= */
  const imageContainer = document.querySelector('.pdp-main-image-container');

  if (imageContainer && mainImage) {
    imageContainer.addEventListener('mousemove', function (e) {
      const { left, top, width, height } = this.getBoundingClientRect();
      const x = e.clientX - left;
      const y = e.clientY - top;

      // Calculate percentage position
      const xPercent = (x / width) * 100;
      const yPercent = (y / height) * 100;

      // Apply transform to zoom and pan
      // Scale 1.5x (150%)
      mainImage.style.transformOrigin = `${xPercent}% ${yPercent}%`;
      mainImage.style.transform = 'scale(1.5)';
    });

    imageContainer.addEventListener('mouseleave', function () {
      // Reset
      mainImage.style.transform = 'scale(1)';
      setTimeout(() => {
        mainImage.style.transformOrigin = 'center center';
      }, 300);
    });
  }
});
