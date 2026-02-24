(function () {
    /* ── Offer-type target toggle ─────────────── */
    const typeSelect = document.getElementById("id_offer_type");
    const groups = {
        PRODUCT:  document.getElementById("target-product"),
        CATEGORY: document.getElementById("target-category"),
        BRAND:    document.getElementById("target-brand"),
    };
    const placeholder = document.getElementById("target-placeholder");

    function showTarget(val) {
        Object.keys(groups).forEach(k => {
            groups[k].style.display = "none";
        });
        if (val && groups[val]) {
            groups[val].style.display = "block";
            placeholder.style.display = "none";
        } else {
            placeholder.style.display = "block";
        }
    }

    showTarget(typeSelect ? typeSelect.value : "");

    if (typeSelect) {
        typeSelect.addEventListener("change", function () {
            showTarget(this.value);
        });
    }

    /* ── Date validation ──────────────────────── */
    const startInput = document.getElementById("id_start_date");
    const endInput   = document.getElementById("id_end_date");
    const form       = document.getElementById("offerForm");
    const isEdit     = form.dataset.edit === "true";

    // Store original values for edit mode (so we skip validation on unchanged dates)
    const originalStart = isEdit ? startInput.value : null;
    const originalEnd   = isEdit ? endInput.value : null;

    // Format Date to datetime-local string (YYYY-MM-DDTHH:MM)
    function toLocalISO(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, "0");
        const d = String(date.getDate()).padStart(2, "0");
        const h = String(date.getHours()).padStart(2, "0");
        const min = String(date.getMinutes()).padStart(2, "0");
        return `${y}-${m}-${d}T${h}:${min}`;
    }

    // Set min on start_date to now (only for new offers)
    function setStartMin() {
        if (!isEdit) {
            startInput.min = toLocalISO(new Date());
        }
    }

    // Set min on end_date to whichever is later: now or start_date
    function setEndMin() {
        const now = new Date();
        const startVal = startInput.value ? new Date(startInput.value) : null;
        const minDate = startVal && startVal > now ? startVal : now;
        // Add 1 minute to ensure end > start
        minDate.setMinutes(minDate.getMinutes() + 1);
        endInput.min = toLocalISO(minDate);
    }

    // Helper: show/clear inline error
    function showError(input, msg) {
        clearError(input);
        const span = document.createElement("span");
        span.className = "error-text";
        span.textContent = msg;
        span.dataset.jsError = "true";
        input.parentElement.appendChild(span);
    }

    function clearError(input) {
        const existing = input.parentElement.querySelector('[data-js-error="true"]');
        if (existing) existing.remove();
    }

    // Init min attributes
    setStartMin();
    setEndMin();

    // Update end_date min whenever start_date changes
    startInput.addEventListener("change", function () {
        setEndMin();
        clearError(startInput);
    });

    endInput.addEventListener("change", function () {
        clearError(endInput);
    });

    // On submit: validate dates
    form.addEventListener("submit", function (e) {
        let valid = true;
        const now = new Date();
        const startVal = startInput.value ? new Date(startInput.value) : null;
        const endVal   = endInput.value ? new Date(endInput.value) : null;

        clearError(startInput);
        clearError(endInput);

        // Start date: must not be in the past (skip if unchanged on edit)
        if (startVal && (!isEdit || startInput.value !== originalStart)) {
            if (startVal < now) {
                showError(startInput, "Start date cannot be in the past.");
                valid = false;
            }
        }

        // End date: must be in the future (skip if unchanged on edit)
        if (endVal && (!isEdit || endInput.value !== originalEnd)) {
            if (endVal <= now) {
                showError(endInput, "End date must be in the future.");
                valid = false;
            }
        }

        // End date must be after start date
        if (startVal && endVal && startVal >= endVal) {
            showError(endInput, "End date must be after start date.");
            valid = false;
        }

        if (!valid) e.preventDefault();
    });
})();
