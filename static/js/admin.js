// ...new file...

let deleteId = null;
const deleteToast = new bootstrap.Toast(document.getElementById('deleteToast'));
const toastContainer = document.querySelector('.toast-container');
const loadingSpinner = document.getElementById('loadingSpinner');

// Hjälpfunktion för XSS-skydd
function escapeHTML(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Visa/dölj laddningsindikator
function showSpinner() { loadingSpinner.classList.remove('d-none'); }
function hideSpinner() { loadingSpinner.classList.add('d-none'); }

// Visa toast för feedback
function showToast(message, type = "info") {
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${escapeHTML(message)}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Stäng"></button>
        </div>
    `;
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Skapa tabellrad (DRY)
function createTableRow(item) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${escapeHTML(item.id)}</td>
        <td><input type="text" class="form-control" value="${escapeHTML(item.Brand || '')}" data-id="${item.id}" data-field="Brand"></td>
        <td><input type="text" class="form-control" value="${escapeHTML(item.product_family)}" data-id="${item.id}" data-field="product_family"></td>
        <td><input type="text" class="form-control" value="${escapeHTML(item.spare_part)}" data-id="${item.id}" data-field="spare_part"></td>
        <td><input type="number" class="form-control" value="${escapeHTML(item.quantity)}" min="0" data-id="${item.id}" data-field="quantity"></td>
        <td><input type="number" class="form-control" value="${escapeHTML(item.low_status)}" min="1" data-id="${item.id}" data-field="low_status"></td>
        <td><input type="number" class="form-control" value="${escapeHTML(item.high_status)}" min="1" data-id="${item.id}" data-field="high_status"></td>
        <td><button class="btn btn-danger btn-sm delete-btn" data-id="${item.id}">Radera</button></td>
    `;
    return row;
}

// Ladda inventarielista
function loadInventory() {
    showSpinner();
    fetch('/api/inventory')
        .then(response => {
            if (!response.ok) throw new Error("Kunde inte hämta data");
            return response.json();
        })
        .then(data => {
            const tableBody = document.getElementById('inventoryTable');
            tableBody.innerHTML = '';
            data.sort((a, b) => a.product_family.localeCompare(b.product_family) || a.spare_part.localeCompare(b.spare_part))
                .forEach(item => {
                    tableBody.appendChild(createTableRow(item));
                });
        })
        .catch(() => showToast("Fel vid hämtning av lagerdata", "danger"))
        .finally(hideSpinner);
}

// Formulärvalidering
function validateForm(brand, product_family, spare_part, quantity, low_status, high_status) {
    if (!brand || !product_family || !spare_part) return "Alla fält måste fyllas i.";
    if (isNaN(quantity) || isNaN(low_status) || isNaN(high_status)) return "Antal och nivåer måste vara siffror.";
    if (low_status >= high_status) return "Hög nivå måste vara större än låg nivå.";
    return null;
}

// Lägg till ny post
document.getElementById('addForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const brand = document.getElementById('brand').value.trim();
    const product_family = document.getElementById('product_family').value.trim();
    const spare_part = document.getElementById('spare_part').value.trim();
    const quantity = parseInt(document.getElementById('quantity').value);
    const low_status = parseInt(document.getElementById('low_status').value);
    const high_status = parseInt(document.getElementById('high_status').value);

    const error = validateForm(brand, product_family, spare_part, quantity, low_status, high_status);
    if (error) {
        showToast(error, "warning");
        return;
    }

    showSpinner();
    fetch('/api/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Brand: brand, product_family, spare_part, quantity, low_status, high_status })
    })
    .then(response => {
        if (!response.ok) throw new Error("Kunde inte lägga till post");
        loadInventory();
        this.reset();
        showToast("Post tillagd!", "success");
    })
    .catch(() => showToast("Fel vid tillägg av post", "danger"))
    .finally(hideSpinner);
});

// Event delegation för ändringar i tabellen
document.getElementById('inventoryTable').addEventListener('change', function(e) {
    const target = e.target;
    if (target.tagName === "INPUT") {
        const id = target.dataset.id;
        const field = target.dataset.field;
        let value = target.value;
        if (["quantity", "low_status", "high_status"].includes(field)) value = parseInt(value);

        // Validering för nivåer
        if (field === "high_status" || field === "low_status") {
            const row = target.closest('tr');
            const low = parseInt(row.querySelector('input[data-field="low_status"]').value);
            const high = parseInt(row.querySelector('input[data-field="high_status"]').value);
            if (low >= high) {
                showToast("Hög nivå måste vara större än låg nivå.", "warning");
                loadInventory();
                return;
            }
        }

        showSpinner();
        fetch(`/api/inventory/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [field]: value })
        })
        .then(response => {
            if (!response.ok) throw new Error("Kunde inte uppdatera post");
            showToast("Post uppdaterad!", "success");
            loadInventory();
        })
        .catch(() => showToast("Fel vid uppdatering", "danger"))
        .finally(hideSpinner);
    }
});

// Event delegation för radering
document.getElementById('inventoryTable').addEventListener('click', function(e) {
    if (e.target.classList.contains('delete-btn')) {
        deleteId = e.target.dataset.id;
        deleteToast.show();
    }
});

// Bekräfta radering
document.getElementById('confirmDelete').addEventListener('click', function() {
    if (deleteId) {
        showSpinner();
        fetch(`/api/inventory/${deleteId}`, { method: 'DELETE' })
            .then(response => {
                if (!response.ok) throw new Error("Kunde inte radera post");
                showToast("Post raderad!", "success");
                loadInventory();
            })
            .catch(() => showToast("Fel vid radering", "danger"))
            .finally(() => {
                hideSpinner();
                deleteId = null;
                deleteToast.hide();
            });
    }
});

// Dölj toast-container vid stängning av radering
document.querySelectorAll('#deleteToast .btn-close, #deleteToast .btn-secondary').forEach(btn => {
    btn.addEventListener('click', () => {
        deleteToast.hide();
    });
});

// Ladda data vid sidladdning
window.onload = loadInventory;