document.addEventListener("DOMContentLoaded", () => {
  /* =========================================
     Quantity Selector
     ========================================= */
  const qtyInputs = document.querySelectorAll(".pdp-qty-input");

  qtyInputs.forEach((input) => {
    const btnMinus = input.parentElement.querySelector(
      '[data-action="decrease"]',
    );
    const btnPlus = input.parentElement.querySelector(
      '[data-action="increase"]',
    );

    // Helper to update value
    const updateValue = (newVal) => {
      if (newVal < 1) newVal = 1;

      // Check max limit (stock)
      const maxStock = parseInt(input.getAttribute("max"));
      if (!isNaN(maxStock) && newVal > maxStock) {
        newVal = maxStock;
      }

      input.value = newVal;
    };

    btnMinus.addEventListener("click", () => {
      updateValue(parseInt(input.value) - 1);
    });

    btnPlus.addEventListener("click", () => {
      updateValue(parseInt(input.value) + 1);
    });

    // Prevent non-numeric input and respect limits
    input.addEventListener("change", () => {
      let val = parseInt(input.value);
      const maxStock = parseInt(input.getAttribute("max"));

      if (isNaN(val) || val < 1) {
        val = 1;
      } else if (!isNaN(maxStock) && val > maxStock) {
        val = maxStock;
      }

      input.value = val;
    });
  });

  /* =========================================
     Image Gallery
     ========================================= */
  const mainImage = document.querySelector(".pdp-main-image");
  const thumbBtns = document.querySelectorAll(".pdp-thumb-btn");

  if (mainImage && thumbBtns.length > 0) {
    thumbBtns.forEach((btn) => {
      btn.addEventListener("click", function () {
        // Remove active class from all
        thumbBtns.forEach((b) => b.classList.remove("active"));
        // Add to clicked
        this.classList.add("active");

        // Update main image
        const newSrc = this.querySelector("img").getAttribute("src");
        // Optional: Fade effect could be added here
        mainImage.style.opacity = "0.8";
        setTimeout(() => {
          mainImage.src = newSrc;
          mainImage.style.opacity = "1";
        }, 100);
      });
    });
  }

  /* =========================================
     Zoom Effect (Simple Lens/Pan)
     ========================================= */
  const imageContainer = document.querySelector(".pdp-main-image-container");

  if (imageContainer && mainImage) {
    imageContainer.addEventListener("mousemove", function (e) {
      const { left, top, width, height } = this.getBoundingClientRect();
      const x = e.clientX - left;
      const y = e.clientY - top;

      // Calculate percentage position
      const xPercent = (x / width) * 100;
      const yPercent = (y / height) * 100;

      // Apply transform to zoom and pan
      // Scale 1.5x (150%)
      mainImage.style.transformOrigin = `${xPercent}% ${yPercent}%`;
      mainImage.style.transform = "scale(1.5)";
    });

    imageContainer.addEventListener("mouseleave", function () {
      // Reset
      mainImage.style.transform = "scale(1)";
      setTimeout(() => {
        mainImage.style.transformOrigin = "center center";
      }, 300);
    });
  }
  /* =========================================
     Real-Time Stock Check
     ========================================= */
  const stockContainer = document.getElementById("pdp-stock-container");
  const addBtn = document.getElementById("pdp-add-to-cart-btn");

  if (stockContainer && stockContainer.dataset.stockUrl) {
    const fetchStock = async () => {
      try {
        const response = await fetch(stockContainer.dataset.stockUrl, {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        if (!response.ok) throw new Error("Stock fetch failed");

        const data = await response.json();
        const stock = data.stock;

        updateStockUI(stock);
      } catch (error) {
        console.error("Error fetching stock:", error);
      }
    };

    const updateStockUI = (stock) => {
      // 1. Update Stock Message & Class
      stockContainer.className = "pdp-stock-status width-fit"; // Reset classes
      let icon = "";
      let message = "";

      if (stock > 10) {
        stockContainer.classList.add("in_stock");
        icon =
          '<span class="material-icons" style="font-size: 1.2em;">check_circle</span>';
        message = "In Stock";
        enableAddToCart(true);
      } else if (stock > 0) {
        stockContainer.classList.add("low_stock");
        icon =
          '<span class="material-icons" style="font-size: 1.2em;">warning</span>';
        message = `Only ${stock} left!`;
        enableAddToCart(true);
      } else {
        stockContainer.classList.add("out_of_stock");
        icon =
          '<span class="material-icons" style="font-size: 1.2em;">highlight_off</span>';
        message = "Out of Stock";
        enableAddToCart(false);
      }

      stockContainer.innerHTML = `${icon} ${message}`;

      // 2. Update Quantity Inputs
      qtyInputs.forEach((input) => {
        // input.setAttribute("max", stock);

        if (input.getAttribute("max") > stock) {
          input.setAttribute("max", stock);
          // console.log(input.getAttribute("max"));
        }
        // Clamp existing valueinput.getAttribute("max")
        if (parseInt(input.value) > stock) {
          input.value = Math.max(0, stock);
        }
        if (stock === 0) {
          input.value = 1; // Or 0? Usually keep 1 but disable add button
        }
      });
    };

    const enableAddToCart = (enable) => {
      if (addBtn) {
        addBtn.disabled = !enable;
        if (!enable) {
          addBtn.textContent = "Out of Stock";
        } else {
          addBtn.textContent = "Add to Cart";
        }
      }
    };

    // Fetch on load
    fetchStock();
  }
});
