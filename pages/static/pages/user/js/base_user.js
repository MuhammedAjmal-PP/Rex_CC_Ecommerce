// Debug: Check if script is loading
console.log("base_user.js loaded successfully");

// Header Scroll Logic - REVERSED for home page
let lastScroll = 0;
const header = document.getElementById("siteHeader");
const topBar = document.querySelector(".top-bar");
const isHomePage = document.body.classList.contains("home-page");

console.log("Is Home Page:", isHomePage);
console.log("Header element:", header);
console.log("Top bar element:", topBar);

// Hide header on page load if on home page
if (isHomePage) {
  header.classList.add("is-hidden");
  if (topBar) topBar.classList.add("is-hidden");
  console.log("Home page detected - header hidden on load");
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
  console.log("Opening search overlay");
  const overlay = document.getElementById("searchOverlay");
  if (overlay) {
    overlay.classList.add("is-open");
    const input = document.querySelector(".search-input-lg");
    if (input) {
      setTimeout(() => input.focus(), 100);
    }
  } else {
    console.error("Search overlay element not found");
  }
}

function closeSearch() {
  console.log("Closing search overlay");
  const overlay = document.getElementById("searchOverlay");
  if (overlay) {
    overlay.classList.remove("is-open");
  }
}

// Make functions globally available
window.openSearch = openSearch;
window.closeSearch = closeSearch;

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
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM Content Loaded - Initializing mega menu");

  const categoryLinks = document.querySelectorAll(".mega-category-link");
  const brandLinks = document.querySelectorAll(".mega-brand-link");
  const productImage = document.getElementById("megaProductImage");
  const productName = document.getElementById("megaProductName");
  const productLink = document.getElementById("megaProductLink");

  console.log("Category links found:", categoryLinks.length);
  console.log("Brand links found:", brandLinks.length);
  console.log("Product elements:", {
    image: !!productImage,
    name: !!productName,
    link: !!productLink,
  });

  let fetchTimeout;

  function updateProductPreview(slug, type) {
    console.log(`Updating preview for ${type}: ${slug}`);

    // Clear any pending requests
    if (fetchTimeout) clearTimeout(fetchTimeout);

    // Debounce the request
    fetchTimeout = setTimeout(() => {
      const url = `/api/latest-product/?${type}=${slug}`;
      console.log("Fetching from:", url);

      fetch(url)
        .then((response) => {
          console.log("Response status:", response.status);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          console.log("Data received:", data);

          if (data.success && data.variant) {
            const variant = data.variant;

            // Update image
            if (productImage) {
              if (variant.thumbnail) {
                productImage.src = variant.thumbnail;
                productImage.alt = variant.name;
              } else {
                productImage.src =
                  "https://via.placeholder.com/150x100?text=No+Image";
              }

              // Add fade-in animation
              productImage.style.opacity = "0";
              setTimeout(() => {
                productImage.style.transition = "opacity 0.3s ease";
                productImage.style.opacity = "1";
              }, 50);
            }

            // Update name with variant details
            if (productName) {
              let priceHtml = "";
              if (variant.discount_percentage > 0) {
                priceHtml = ` <br><span style="color:red; font-size:12px;">${variant.discount_percentage}% OFF</span>`;
              }
              productName.innerHTML = `New: ${variant.name}${priceHtml}`;
            }

            // Update link
            if (productLink && variant.slug) {
              productLink.href = `/product/${variant.slug}/`;
            }
          } else {
            console.warn("No variant data in response");
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
      if (categorySlug) {
        updateProductPreview(categorySlug, "category");
      }
    });
  });

  // Add hover listeners to brand links
  brandLinks.forEach((link) => {
    link.addEventListener("mouseenter", function () {
      const brandSlug = this.getAttribute("data-brand-slug");
      if (brandSlug) {
        updateProductPreview(brandSlug, "brand");
      }
    });
  });

  console.log("Mega menu initialization complete");
});
