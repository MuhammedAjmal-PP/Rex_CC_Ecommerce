/**
 * Order Detail — Review Modal
 * Handles star picker, AJAX form submission, and UI updates.
 */
document.addEventListener('DOMContentLoaded', () => {
  const backdrop = document.getElementById('reviewModalBackdrop');
  const closeBtn = document.getElementById('reviewModalClose');
  const form = document.getElementById('reviewForm');
  const productNameEl = document.getElementById('reviewProductName');
  const ratingInput = document.getElementById('reviewRatingInput');
  const stars = document.querySelectorAll('.od-star-pick');
  const submitBtn = document.getElementById('reviewSubmitBtn');

  if (!backdrop || !form) return;

  let currentProductId = null;
  let triggerBtn = null;

  // ── Open modal ──
  document.querySelectorAll('.od-review-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentProductId = btn.dataset.productId;
      triggerBtn = btn;
      productNameEl.textContent = btn.dataset.productName;

      // Reset form
      form.reset();
      ratingInput.value = '';
      stars.forEach(s => { s.textContent = 'star_border'; s.classList.remove('active'); });
      document.querySelectorAll('.od-review-error').forEach(e => e.textContent = '');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Review';

      backdrop.classList.add('od-visible');
      document.body.style.overflow = 'hidden';
    });
  });

  // ── Close modal ──
  function closeModal() {
    backdrop.classList.remove('od-visible');
    document.body.style.overflow = '';
    currentProductId = null;
  }

  closeBtn.addEventListener('click', closeModal);
  backdrop.addEventListener('click', e => { if (e.target === backdrop) closeModal(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && backdrop.classList.contains('od-visible')) closeModal();
  });

  // ── Star picker ──
  stars.forEach(star => {
    star.addEventListener('mouseenter', () => {
      const val = parseInt(star.dataset.value);
      stars.forEach(s => {
        const sv = parseInt(s.dataset.value);
        s.textContent = sv <= val ? 'star' : 'star_border';
        s.classList.toggle('active', sv <= val);
      });
    });

    star.addEventListener('click', () => {
      ratingInput.value = star.dataset.value;
    });
  });

  document.getElementById('starSelect').addEventListener('mouseleave', () => {
    const selected = parseInt(ratingInput.value) || 0;
    stars.forEach(s => {
      const sv = parseInt(s.dataset.value);
      s.textContent = sv <= selected ? 'star' : 'star_border';
      s.classList.toggle('active', sv <= selected);
    });
  });

  // ── Submit ──
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    document.querySelectorAll('.od-review-error').forEach(el => el.textContent = '');

    if (!ratingInput.value || ratingInput.value === '0') {
      document.getElementById('ratingError').textContent = 'Please select a rating.';
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData(form);
    const url = `/review/${currentProductId}/submit/`;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        closeModal();

        // Replace the "Write a Review" button with a "Reviewed" badge
        if (triggerBtn) {
          const badge = document.createElement('span');
          badge.className = 'od-reviewed-badge';
          badge.innerHTML = '<span class="material-icons">check_circle</span> Reviewed';
          triggerBtn.replaceWith(badge);
        }

        // Show success toast if available
        if (typeof showMessage === 'function') {
          showMessage('Review submitted successfully!', 'success');
        }
      } else if (data.errors) {
        if (data.errors.rating) document.getElementById('ratingError').textContent = data.errors.rating;
        if (data.errors.title) document.getElementById('titleError').textContent = data.errors.title;
        if (data.errors.comment) document.getElementById('commentError').textContent = data.errors.comment;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Review';
      } else {
        document.getElementById('ratingError').textContent = data.message || 'Something went wrong.';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Review';
      }
    } catch (err) {
      console.error('Review submit error:', err);
      document.getElementById('ratingError').textContent = 'Network error. Please try again.';
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Review';
    }
  });
});
