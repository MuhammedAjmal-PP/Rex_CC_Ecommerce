// static/user_profile/js/address.js

// static/user_profile/js/address.js

function getCSRFToken() {
  const globalToken = document.getElementById("global-csrf-token");
  if (globalToken) return globalToken.value;
  
  // Fallback (legacy)
  const tokenInput = document.getElementById("csrf-token");
  return tokenInput ? tokenInput.dataset.csrf : "";
}

function deleteAddress(event, addressId) {
  if (!confirm("Are you sure you want to delete this address?")) return;

  // Get URL from button's data-url attribute
  const url = event.currentTarget.getAttribute("data-url");

  if (!url) {
    showMessage("Invalid URL configuration.", "error");
    return;
  }
  
  const button = event.currentTarget;
  button.disabled = true;
  button.innerHTML = '<span class="material-icons">hourglass_empty</span> Removing...';

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
      "X-Requested-With": "XMLHttpRequest"
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showMessage("Address deleted successfully.", "success");
        setTimeout(() => {
             window.location.reload();
        }, 1000);
      } else {
        alert("Failed to delete address.");
        button.disabled = false;
        button.innerHTML = '<span class="material-icons">delete_outline</span> <span>Remove</span>';
      }
    })
    .catch(() => {
      showMessage("Something went wrong. Please try again.", "error");
      button.disabled = false;
      button.innerHTML = '<span class="material-icons">delete_outline</span> <span>Remove</span>';
    });
}

function setDefaultAddress(event, addressId) {
  // Get URL from button's data-url attribute
  const url = event.currentTarget.getAttribute("data-url");

  if (!url) {
    showMessage("Invalid URL configuration.", "error");
    return;
  }

  // Show loading state
  const button = event.currentTarget;
  // const originalText = button.innerHTML; // Can use but simpler to hardcode restore if needed
  button.innerHTML = '<span class="material-icons">hourglass_empty</span><span>Setting...</span>';
  button.disabled = true;

  fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFToken(),
      "X-Requested-With": "XMLHttpRequest"
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
        button.innerHTML = '<span class="material-icons">push_pin</span><span>Set as Default</span>';
        button.disabled = false;
      }
    })
    .catch(() => {
      showMessage("Network error. Please try again.", "error");
      button.innerHTML = '<span class="material-icons">push_pin</span><span>Set as Default</span>';
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
    
    // Updated selector to match address.html structure
    const addressesPage = document.querySelector(".profile-page-centered");
    
    if (addressesPage) {
        // Insert at the top of the content area
        addressesPage.prepend(container);
    } else {
        // Fallback to body
        document.body.appendChild(container);
    }
  }

  // Create message element
  const toast = document.createElement("div");
  toast.className = "toast-msg";

  const iconName = type === "success" ? "check_circle" : type === "error" ? "error" : "info";
  const iconColor = type === "error" ? "#e74c3c" : "var(--co-gold)"; // Fixed variable name if it was wrong, assuming co-gold works

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
