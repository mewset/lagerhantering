let inventoryData = [];
let deleteId = null;
const deleteToast = new bootstrap.Toast(document.getElementById('deleteToast'));

function loadInventory() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            inventoryData = data.sort((a, b) => a.product_family.localeCompare(b.product_family) || a.spare_part.localeCompare(b.spare_part));
            updateTable();
            updateProductFamilyDropdown();
        })
        .catch(error => console.error('Fel vid laddning av inventarie:', error));
}

function updateTable() {
    const tableBody = document.getElementById('inventoryTable');
    tableBody.innerHTML = '';
    inventoryData.forEach(item => {
        const row = `<tr>
            <td>${item.id}</td>
            <td>${item.product_family}</td>
            <td>${item.spare_part}</td>
            <td>${item.quantity}</td>
            <td>
                <button class="btn btn-warning btn-sm me-2" onclick="subtractItem(${item.id})">Ta bort</button>
                <button class="btn btn-danger btn-sm" onclick="showDeleteToast(${item.id})">Radera</button>
            </td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

function updateProductFamilyDropdown() {
    const productFamilySelect = document.getElementById('product_family');
    const uniqueFamilies = [...new Set(inventoryData.map(item => item.product_family))].sort();
    productFamilySelect.innerHTML = '<option value="" disabled selected>Välj produktfamilj</option>';
    uniqueFamilies.forEach(family => {
        productFamilySelect.innerHTML += `<option value="${family}">${family}</option>`;
    });
    updateSparePartDropdown();
}

function updateSparePartDropdown() {
    const productFamily = document.getElementById('product_family').value;
    const sparePartSelect = document.getElementById('spare_part');
    sparePartSelect.innerHTML = '<option value="" disabled selected>Välj reservdel</option>';
    if (productFamily) {
        const spareParts = inventoryData
            .filter(item => item.product_family === productFamily)
            .map(item => item.spare_part)
            .sort();
        spareParts.forEach(part => {
            sparePartSelect.innerHTML += `<option value="${part}">${part}</option>`;
        });
    }
}

function subtractItem(id) {
    fetch(`/api/inventory/${id}/subtract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: 1 })
    }).then(() => loadInventory());
}

function subtractFromForm() {
    const productFamily = document.getElementById('product_family').value;
    const sparePart = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const item = inventoryData.find(i => i.product_family === productFamily && i.spare_part === sparePart);
    if (item) {
        fetch(`/api/inventory/${item.id}/subtract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity })
        }).then(() => loadInventory());
    } else {
        alert("Reservdelen finns inte i lagret!");
    }
}

function showDeleteToast(id) {
    deleteId = id;
    deleteToast.show();
}

function confirmDelete() {
    if (deleteId) {
        fetch(`/api/inventory/${deleteId}`, { method: 'DELETE' })
            .then(() => {
                deleteId = null;
                deleteToast.hide();
                loadInventory();
            });
    }
}

document.getElementById('inventoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const product_family = document.getElementById('product_family').value;
    const spare_part = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const id = Date.now();
    fetch('/api/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, product_family, spare_part, quantity })
    }).then(() => loadInventory());
});

document.getElementById('product_family').addEventListener('change', updateSparePartDropdown);

window.onload = loadInventory;