// Header Scroll Logic - REVERSED for home page
let lastScroll = 0;
const header = document.getElementById("siteHeader");
const topBar = document.querySelector(".top-bar");
const isHomePage = document.body.classList.contains("home-page");

// Hide header on page load if on home page
if (isHomePage) {
  header.classList.add("is-hidden");
  if (topBar) topBar.classList.add("is-hidden");
}

window.addEventListener("scroll", () => {
  const currentScroll = window.pageYOffset;

  if (isHomePage) {
    // REVERSED BEHAVIOR FOR HOME PAGE
    if (currentScroll > 50) {
      header.classList.add("is-visible");
      if (topBar) topBar.classList.add("top-bar-visible");

      // Show when scrolling DOWN, hide when scrolling UP
      if (currentScroll > lastScroll) {
        header.classList.remove("is-hidden");
        if (topBar) topBar.classList.remove("is-hidden");
      } else {
        header.classList.add("is-hidden");
        if (topBar) topBar.classList.add("is-hidden");
      }
    } else {
      // At top of page - hide header
      header.classList.add("is-hidden");
      header.classList.remove("is-visible");
      if (topBar) {
        topBar.classList.add("is-hidden");
        topBar.classList.remove("top-bar-visible");
      }
    }
  } else {
    // NORMAL BEHAVIOR FOR OTHER PAGES
    if (currentScroll > 50) {
      header.classList.add("is-visible");
      // Hide when scrolling down, show when up
      if (currentScroll > lastScroll) {
        header.classList.add("is-hidden");
      } else {
        header.classList.remove("is-hidden");
      }
    } else {
      // Transparent at top
      header.classList.remove("is-visible");
      header.classList.remove("is-hidden");
    }
  }

  lastScroll = currentScroll;
});

// Search Overlay Logic
function openSearch() {
  document.getElementById("searchOverlay").classList.add("is-open");
  document.querySelector(".search-input-lg").focus();
}

function closeSearch() {
  document.getElementById("searchOverlay").classList.remove("is-open");
}

// Keydown Escape
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeSearch();
});

// Auto-dismiss Toasts
setTimeout(() => {
  const toasts = document.querySelector(".toast-container");
  if (toasts) {
    toasts.style.transition = "opacity 0.5s ease";
    toasts.style.opacity = "0";
    setTimeout(() => toasts.remove(), 500);
  }
}, 4000);

// Dynamic Mega Menu Product Preview
const categoryLinks = document.querySelectorAll(".mega-category-link");
const brandLinks = document.querySelectorAll(".mega-brand-link");
const productImage = document.getElementById("megaProductImage");
const productName = document.getElementById("megaProductName");
const productLink = document.getElementById("megaProductLink");
let fetchTimeout;

function updateProductPreview(slug, type) {
  // Clear any pending requests
  if (fetchTimeout) clearTimeout(fetchTimeout);

  // Debounce the request
  fetchTimeout = setTimeout(() => {
    const url = `/api/latest-product/?${type}=${slug}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.variant) {
          const variant = data.variant;

          // Update image
          if (variant.thumbnail) {
            productImage.src = variant.thumbnail;
            productImage.alt = variant.name;
          } else {
            productImage.src =
              "https://via.placeholder.com/150x100?text=No+Image";
          }

          // Update name with variant details
          let variantDetails = "";

          // Format price display
          let priceHtml = "";
          if (variant.discount_percentage > 0) {
            priceHtml = ` <br><span style="color:red; font-size:12px;">${variant.discount_percentage}% OFF</span>`;
            // priceHtml += ` <span style="text-decoration:line-through; color:#999; font-size:12px;">₹${Math.round(variant.price)}</span>`;
            // priceHtml += ` <span style="color:#333; font-weight:600;">₹${Math.round(variant.final_price)}</span>`;
          }

          productName.innerHTML = `New: ${variant.name}${variantDetails}${priceHtml}`;

          // Update link
          if (productLink) {
            productLink.href = `/product/${variant.slug}/`;
          }

          // Add fade-in animation
          productImage.style.opacity = "0";
          setTimeout(() => {
            productImage.style.transition = "opacity 0.3s ease";
            productImage.style.opacity = "1";
          }, 50);
        }
      })
      .catch((error) => {
        console.error("Error fetching variant:", error);
      });
  }, 200); // 200ms debounce
}

// Add hover listeners to category links
categoryLinks.forEach((link) => {
  link.addEventListener("mouseenter", function () {
    const categorySlug = this.getAttribute("data-category-slug");
    updateProductPreview(categorySlug, "category");
  });
});

// Add hover listeners to brand links
brandLinks.forEach((link) => {
  link.addEventListener("mouseenter", function () {
    const brandSlug = this.getAttribute("data-brand-slug");
    updateProductPreview(brandSlug, "brand");
  });
});
