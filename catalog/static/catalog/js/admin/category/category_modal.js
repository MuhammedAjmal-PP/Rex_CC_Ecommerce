/**
 * REX CC ADMIN - Category Modal JavaScript
 * File: catalog/static/catalog/js/admin/category/category_modal.js
 * Handles the Add and Edit Category modal form submissions via AJAX
 */

document.addEventListener('DOMContentLoaded', function () {
    // ==========================================
    // ADD CATEGORY MODAL
    // ==========================================
    const addForm = document.getElementById('addCategoryForm');
    const addModal = document.getElementById('addCategoryModal');
    const addNameInput = document.getElementById('id_name');
    const addNameError = document.getElementById('nameError');
    const addSubmitBtn = document.getElementById('submitCategoryBtn');

    if (addForm && addModal) {
        // Get the CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Focus on name input when modal opens
        addModal.addEventListener('show.bs.modal', function () {
            setTimeout(() => addNameInput.focus(), 300);
        });

        // Reset form when modal is closed
        addModal.addEventListener('hidden.bs.modal', function () {
            resetAddForm();
        });

        // Handle add form submission
        addForm.addEventListener('submit', function (e) {
            e.preventDefault();
            clearAddErrors();

            if (!addNameInput.value.trim()) {
                showAddError('Category name is required');
                return;
            }

            setAddLoading(true);
            const formData = new FormData(addForm);
            const actionUrl = addForm.dataset.actionUrl;

            axios.post(actionUrl, formData, {
                headers: { 'X-CSRFToken': csrfToken }
            })
                .then(function (response) {
                    if (response.data.success) {
                        addSubmitBtn.innerHTML = '<span class="material-icons">check</span> Added!';
                        addSubmitBtn.style.background = '#56ab2f';
                        addSubmitBtn.style.borderColor = '#56ab2f';

                        setTimeout(() => {
                            bootstrap.Modal.getInstance(addModal).hide();
                            window.location.reload();
                        }, 800);
                    }
                })
                .catch(function (error) {
                    setAddLoading(false);
                    if (error.response && error.response.data.errors) {
                        const errors = error.response.data.errors;
                        if (errors.name) {
                            showAddError(errors.name);
                        }
                    } else {
                        showAddError('An error occurred. Please try again.');
                    }
                });
        });

        // Clear errors when typing
        addNameInput.addEventListener('input', clearAddErrors);
    }

    // ==========================================
    // EDIT CATEGORY MODAL
    // ==========================================
    const editModal = document.getElementById('editCategoryModal');
    const editForm = document.getElementById('editCategoryForm');
    const editCategoryId = document.getElementById('editCategoryId');
    const editNameInput = document.getElementById('editCategoryName');
    const editActiveCheckbox = document.getElementById('editCategoryActive');
    const editNameError = document.getElementById('editNameError');
    const editSubmitBtn = document.getElementById('submitEditCategoryBtn');

    if (editModal && editForm) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Populate form when edit modal is shown
        editModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const categoryId = button.getAttribute('data-category-id');
            const categoryName = button.getAttribute('data-category-name');
            const categoryActive = button.getAttribute('data-category-active') === 'true';

            editCategoryId.value = categoryId;
            editNameInput.value = categoryName;
            editActiveCheckbox.checked = categoryActive;

            setTimeout(() => editNameInput.focus(), 300);
        });

        // Reset when modal is closed
        editModal.addEventListener('hidden.bs.modal', function () {
            resetEditForm();
        });

        // Handle edit form submission
        editForm.addEventListener('submit', function (e) {
            e.preventDefault();
            clearEditErrors();

            if (!editNameInput.value.trim()) {
                showEditError('Category name is required');
                return;
            }

            setEditLoading(true);
            const formData = new FormData(editForm);
            const categoryId = editCategoryId.value;

            // Build the edit URL using the template
            const actionUrl = CATEGORY_EDIT_URL_TEMPLATE.replace('{id}', categoryId);

            axios.post(actionUrl, formData, {
                headers: { 'X-CSRFToken': csrfToken }
            })
                .then(function (response) {
                    if (response.data.success) {
                        editSubmitBtn.innerHTML = '<span class="material-icons">check</span> Saved!';
                        editSubmitBtn.style.background = '#56ab2f';
                        editSubmitBtn.style.borderColor = '#56ab2f';

                        setTimeout(() => {
                            bootstrap.Modal.getInstance(editModal).hide();
                            window.location.reload();
                        }, 800);
                    }
                })
                .catch(function (error) {
                    setEditLoading(false);
                    if (error.response && error.response.data.errors) {
                        const errors = error.response.data.errors;
                        if (errors.name) {
                            showEditError(errors.name);
                        }
                    } else {
                        showEditError('An error occurred. Please try again.');
                    }
                });
        });

        // Clear errors when typing
        editNameInput.addEventListener('input', clearEditErrors);
    }

    // ==========================================
    // HELPER FUNCTIONS - ADD MODAL
    // ==========================================
    function resetAddForm() {
        addForm.reset();
        clearAddErrors();
        setAddLoading(false);
        addSubmitBtn.style.background = '';
        addSubmitBtn.style.borderColor = '';
    }

    function clearAddErrors() {
        addNameError.style.display = 'none';
        addNameError.innerHTML = '';
        addNameInput.classList.remove('is-invalid');
    }

    function showAddError(message) {
        addNameError.innerHTML = '<span class="material-icons">error</span> ' + message;
        addNameError.style.display = 'flex';
        addNameInput.classList.add('is-invalid');
        addNameInput.focus();
    }

    function setAddLoading(loading) {
        if (loading) {
            addSubmitBtn.disabled = true;
            addSubmitBtn.innerHTML = '<span class="spinner"></span> Adding...';
        } else {
            addSubmitBtn.disabled = false;
            addSubmitBtn.innerHTML = '<span class="material-icons">add</span> Add Category';
        }
    }

    // ==========================================
    // HELPER FUNCTIONS - EDIT MODAL
    // ==========================================
    function resetEditForm() {
        editForm.reset();
        clearEditErrors();
        setEditLoading(false);
        editSubmitBtn.style.background = '';
        editSubmitBtn.style.borderColor = '';
    }

    function clearEditErrors() {
        editNameError.style.display = 'none';
        editNameError.innerHTML = '';
        editNameInput.classList.remove('is-invalid');
    }

    function showEditError(message) {
        editNameError.innerHTML = '<span class="material-icons">error</span> ' + message;
        editNameError.style.display = 'flex';
        editNameInput.classList.add('is-invalid');
        editNameInput.focus();
    }

    function setEditLoading(loading) {
        if (loading) {
            editSubmitBtn.disabled = true;
            editSubmitBtn.innerHTML = '<span class="spinner"></span> Saving...';
        } else {
            editSubmitBtn.disabled = false;
            editSubmitBtn.innerHTML = '<span class="material-icons">check</span> Save Changes';
        }
    }
});
