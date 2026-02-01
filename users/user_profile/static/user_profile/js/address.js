// static/user_profile/js/address.js

function getCSRFToken() {
  const tokenInput = document.getElementById("csrf-token");
  return tokenInput ? tokenInput.dataset.csrf : "";
}

function deleteAddress(event, addressId) {
  if (!confirm("Delete this address?")) return;

  // Get URL from button's data-url attribute
  const url = event.currentTarget.getAttribute("data-url");

  if (!url) {
    alert("Invalid URL configuration. Please contact support.");
    return;
  }
  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const card = document.getElementById(`address-${addressId}`);
        if (card) {
          card.remove();
        }
      } else {
        alert("Failed to delete address.");
      }
    })
    .catch(() => {
      alert("Something went wrong. Please try again.");
    });
}

function setDefaultAddress(event, addressId) {
  // Get URL from button's data-url attribute
  const url = event.currentTarget.getAttribute("data-url");

  if (!url) {
    showMessage("Invalid URL configuration. Please contact support.", "error");
    return;
  }

  // Show loading state
  const button = event.currentTarget;
  const originalText = button.innerHTML;
  button.innerHTML = '<span class="material-icons">hourglass_empty</span><span>Setting...</span>';
  button.disabled = true;

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showMessage("Default address updated successfully!", "success");
        // Reload after showing message
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showMessage("Unable to update default address.", "error");
        button.innerHTML = originalText;
        button.disabled = false;
      }
    })
    .catch(() => {
      showMessage("Network error. Please try again.", "error");
      button.innerHTML = originalText;
      button.disabled = false;
    });
}

// Helper function to show messages (site-wide pattern)
function showMessage(message, type) {
  // Find or create toast container
  let container = document.querySelector(".toast-container");

  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    // Insert after breadcrumb or at top of addresses-page
    const addressesPage = document.querySelector(".addresses-page");
    const breadcrumb = addressesPage.querySelector(".breadcrumb-nav");
    if (breadcrumb) {
      breadcrumb.after(container);
    } else {
      addressesPage.prepend(container);
    }
  }

  // Create message element
  const toast = document.createElement("div");
  toast.className = "toast-msg";

  const iconName = type === "success" ? "check_circle" : type === "error" ? "error" : "info";
  const iconColor = type === "error" ? "#e74c3c" : "var(--color-gold)";

  toast.innerHTML = `
    <span class="material-icons" style="color:${iconColor}">${iconName}</span>
    ${message}
  `;

  // Add to container
  container.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => {
      toast.remove();
      // Remove container if empty
      if (container.children.length === 0) {
        container.remove();
      }
    }, 300);
  }, 4000);
}
