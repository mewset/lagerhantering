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
            updateBrandDropdown();
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
                <button class="btn btn-warning btn-sm me-2" onclick="subtractItem(${item.id})"><i class="bi bi-dash"></i> Ta reservdel</button>
            </td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

// Returnera en CSS-klass baserat på lagernivån
function getStatusClass(item) {
    if (item.quantity <= item.low_status) return 'table-danger';
    if (item.quantity >= item.high_status) return 'table-success';
    return 'table-warning';
}

// Minska antalet för en reservdel
function subtractItem(id) {
    fetch(`/api/inventory/${id}/subtract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: 1 }) 
    })
    .then(response => {
        if (response.ok) {
            loadInventory();
            const item = inventoryData.find(item => item.id === id);
            if (item) {
                showToast(`Tagit: ${item.product_family} - ${item.spare_part} - 1`, 'error'); 
            }
        } else {
            console.error('Fel vid minskning av reservdel');
        }
    })
    .catch(error => console.error('Fel vid minskning av reservdel:', error));
}

// Lägg till reservdel
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
    }).then(() => {
        loadInventory();
        showToast(`Lagt till: ${product_family} - ${spare_part} - ${quantity}`, 'success');
    });
});

// Visa toast-meddelande med ikon och färg
function showToast(message, type = 'info') {
    const toastElement = document.getElementById('successToast');
    const toastBody = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon');

    // Ta bort gamla färgklasser
    toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning');

    // Sätt ikon och bakgrundsfärg baserat på typ
    if (type === 'success') {
        toastElement.style.backgroundColor = '#d4edda';
        toastIcon.className = 'bi bi-check-circle-fill me-2'; // Grön checkmark
    } else if (type === 'error') {
        toastElement.style.backgroundColor = '#f8d7da';
        toastIcon.className = 'bi bi-trash-fill me-2'; // Röd skräpkorg
    } else {
        toastElement.style.backgroundColor = '#fff3cd';
        toastIcon.className = 'bi bi-exclamation-triangle-fill me-2'; // Gul varning
    }

    toastBody.textContent = message;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// Ladda inventariet vid start
window.onload = loadInventory;
