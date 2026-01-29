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

// Dynamic Mega Menu Product Preview & Data Fetch
document.addEventListener("DOMContentLoaded", () => {
  const megaMenu = document.querySelector(".mega-menu");
  const card = document.getElementById("ProductCard");

  const image = document.getElementById("ProductImage");
  const name = document.getElementById("ProductName");
  const brand = document.getElementById("megaProductBrand");
  const category = document.getElementById("productCategory");
  const links = document.querySelectorAll(".ProductLink");

  let hoverTimeout = null;
  let activeController = null;

  // Hide featured column initially
  if (card) card.style.display = "none";

  // --- 1. Fetch Latest Variant for Preview ---
  async function fetchLatestVariant(query) {
    // Cancel previous request
    if (activeController) {
      activeController.abort();
    }

    activeController = new AbortController();

    try {
      const res = await fetch(`/api/latest-product/?${query}`, {
        signal: activeController.signal,
      });

      const data = await res.json();

      // ❌ No variant → remove featured column & collapse layout
      if (!data.success || !data.variant) {
        if (card) card.style.display = "none";
        if (megaMenu) megaMenu.classList.add("no-featured");
        return;
      }

      const v = data.variant;

      // ✅ Variant exists → populate data
      if (image) {
        image.src = v.image;
        image.alt = v.name;
      }

      if (name) name.textContent = v.name;
      if (brand) brand.textContent = v.brand;
      if (category) category.textContent = v.category;

      links.forEach((link) => {
        link.href = `/product/${v.slug}/v/${v.sku}/`;
      });

      // ✅ Show featured column & restore layout
      if (card) card.style.display = "flex";
      if (megaMenu) megaMenu.classList.remove("no-featured");
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Mega menu preview error:", err);
        if (card) card.style.display = "none";
        if (megaMenu) megaMenu.classList.add("no-featured");
      }
    }
  }

  function delayedFetch(query) {
    clearTimeout(hoverTimeout);
    hoverTimeout = setTimeout(() => {
      fetchLatestVariant(query);
    }, 140); // luxury hover delay
  }

  // --- 2. Fetch Mega Menu Categories & Brands (Global) ---
  async function fetchMegaMenuData() {
    try {
      const res = await fetch("/api/mega-menu/");
      const data = await res.json();

      if (!data.success) return;

      // Populate Categories
      const catContainer = document.querySelector(
        ".mega-menu .mega-column:nth-child(1)",
      );
      if (catContainer) {
        catContainer.innerHTML = "<h4>By Category</h4>"; // Reset

        if (data.categories.length > 0) {
          data.categories.forEach((cat) => {
            const a = document.createElement("a");
            a.href = `/products/?category=${cat.slug}`;
            a.className = "mega-category-link";
            a.dataset.categorySlug = cat.slug;
            a.textContent = cat.name;

            // Attach Event Listener Directly
            a.addEventListener("mouseenter", () => {
              delayedFetch(`category=${cat.slug}`);
            });

            catContainer.appendChild(a);
          });
        } else {
          catContainer.innerHTML += '<a href="#">No categories available</a>';
        }
      }

      // Populate Brands
      const brandListContainer = document.querySelector(".mega-brand-list");
      if (brandListContainer) {
        brandListContainer.innerHTML = ""; // Clear existing

        if (data.brands.length > 0) {
          data.brands.forEach((b) => {
            const span = document.createElement("span");
            const a = document.createElement("a");
            a.href = `/products/?brand=${b.slug}`;
            a.className = "mega-brand-link";
            a.dataset.brandSlug = b.slug;
            a.style.color = "inherit";
            a.style.textDecoration = "none";
            a.textContent = b.name;

            // Attach Event Listener Directly
            a.addEventListener("mouseenter", () => {
              delayedFetch(`brand=${b.slug}`);
            });

            span.appendChild(a);
            brandListContainer.appendChild(span);
          });
        } else {
          brandListContainer.innerHTML = "<span>No brands available</span>";
        }
      }
    } catch (err) {
      console.error("Failed to fetch mega menu data:", err);
    }
  }

  // Initialize
  if (megaMenu) {
    fetchMegaMenuData();
  }
});

// Dynamic Wishlist Badge Border
document.addEventListener("DOMContentLoaded", () => {
  const isHome = document.body.classList.contains("home-page");
  const badge = document.querySelector(".wishlist-badge");

  if (badge) {
    if (isHome) {
      badge.style.border = "none";
    } else {
      badge.style.border = "2px solid #fff";
    }
  }
});
