let inventoryData = [];
let deleteId = null;
const deleteToast = new bootstrap.Toast(document.getElementById('deleteToast'));

// Ladda inventariet när sidan laddas
function loadInventory() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            inventoryData = data.sort((a, b) => a.product_family.localeCompare(b.product_family) || a.spare_part.localeCompare(b.spare_part));
            updateTable();
            updateProductFamilyDropdown();
            updateBrandDropdown(); // Uppdatera kund-dropdownen
        })
        .catch(error => console.error('Fel vid laddning av inventarie:', error));
}

// Uppdatera tabellen med filtrerad data
function updateTable(filter = '') {
    const tableBody = document.getElementById('inventoryTable');
    tableBody.innerHTML = '';
    const filteredData = filter 
        ? inventoryData.filter(item => 
            item.product_family.toLowerCase().includes(filter.toLowerCase()) || 
            item.spare_part.toLowerCase().includes(filter.toLowerCase()))
        : inventoryData;
    filteredData.forEach(item => {
        const row = `<tr class="${getStatusClass(item)}">
            <td>${item.id}</td>
            <td>${item.product_family}</td>
            <td>${item.spare_part}</td>
            <td>${item.quantity}</td>
            <td>
                <button class="btn btn-warning btn-sm me-2" onclick="subtractItem(${item.id})"><i class="bi bi-dash"></i>Ta reservdel</button>
            </td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

// Hämta statusklass baserat på kvantitet
function getStatusClass(item) {
    if (item.quantity <= item.low_status) return 'table-danger'; // Rött för lågt
    if (item.quantity >= item.high_status) return 'table-success'; // Grönt för högt
    return 'table-warning'; // Gult för normalt
}

// Uppdatera produktfamilj-dropdownen
function updateProductFamilyDropdown() {
    const productFamilySelect = document.getElementById('product_family');
    const uniqueFamilies = [...new Set(inventoryData.map(item => item.product_family))].sort();
    productFamilySelect.innerHTML = '<option value="" disabled selected>Välj produktfamilj</option>';
    uniqueFamilies.forEach(family => {
        productFamilySelect.innerHTML += `<option value="${family}">${family}</option>`;
    });
    updateSparePartDropdown(); // Uppdatera reservdels-dropdownen
}

// Uppdatera reservdels-dropdownen baserat på vald produktfamilj
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

// Uppdatera kund-dropdownen
function updateBrandDropdown() {
    const brandSelect = document.getElementById('brand');
    const uniqueBrands = [...new Set(inventoryData.map(item => item.Brand))].sort();
    brandSelect.innerHTML = '<option value="" disabled selected>Välj kund</option>';
    uniqueBrands.forEach(brand => {
        if (brand) { // Se till att brand inte är null eller undefined
            brandSelect.innerHTML += `<option value="${brand}">${brand}</option>`;
        }
    });
}

// Ta bort en reservdel från lagret
function subtractItem(id) {
    fetch(`/api/inventory/${id}/subtract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: 1 })
    }).then(() => loadInventory());
}

// Ta bort en reservdel från formuläret
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

// Visa en toast för att bekräfta radering
function showDeleteToast(id) {
    deleteId = id;
    deleteToast.show();
}

// Bekräfta radering av en post
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

// Hantera formulär för att lägga till en ny post
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

// Uppdatera reservdels-dropdownen när produktfamilj ändras
document.getElementById('product_family').addEventListener('change', updateSparePartDropdown);

// Uppdatera tabellen när sökfältet ändras
document.getElementById('searchInput').addEventListener('input', function(e) {
    updateTable(e.target.value);
});

// Ladda inventariet när sidan laddas
window.onload = loadInventory;