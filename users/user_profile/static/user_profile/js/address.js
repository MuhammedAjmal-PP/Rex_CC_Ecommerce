// static/user_profile/js/address.js

function getCSRFToken() {
  const tokenInput = document.getElementById("csrf-token");
  return tokenInput ? tokenInput.value : "";
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
        // safest sync after atomic DB update
        window.location.reload();
      } else {
        alert("Unable to update default address.");
      }
    })
    .catch(() => {
      alert("Network error. Try again.");
    });
}
