// static/user_profile/js/address.js

// static/user_profile/js/address.js

function getCSRFToken() {
  const csrfInput = document.querySelector('#csrf-form input[name="csrfmiddlewaretoken"]');
  if (csrfInput) return csrfInput.value;
  
  // Fallback to cookie
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, 10) === ('csrftoken=')) {
              cookieValue = decodeURIComponent(cookie.substring(10));
              break;
          }
      }
  }
  return cookieValue;
}

function deleteAddress(button) {
  if (!confirm("Are you sure you want to delete this address?")) return;

  // Get URL from button's data-url attribute
  const url = button.getAttribute("data-url");

  if (!url) {
    showMessage("Invalid URL configuration.", "error");
    return;
  }
  
  button.disabled = true;
  button.innerHTML = 'Removing...';

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
        button.innerHTML = 'Remove';
      }
    })
    .catch(() => {
      showMessage("Something went wrong. Please try again.", "error");
      button.disabled = false;
      button.innerHTML = 'Remove';
    });
}

function setDefaultAddress(button) {
  // Get URL from button's data-url attribute
  const url = button.getAttribute("data-url");

  if (!url) {
    showMessage("Invalid URL configuration.", "error");
    return;
  }

  // Show loading state
  button.innerHTML = 'Setting...';
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
        button.innerHTML = 'Set Default';
        button.disabled = false;
      }
    })
    .catch(() => {
      showMessage("Network error. Please try again.", "error");
      button.innerHTML = 'Set Default';
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
    const addressesPage = document.querySelector(".lux-hub-wrapper");
    
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
  const iconColor = type === "error" ? "#e74c3c" : "#bfa15f";

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
