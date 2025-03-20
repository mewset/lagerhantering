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
            updateBrandDropdown(); // Uppdatera brand-dropdownen
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

// Returnera en CSS-klass baserat på lagernivån
function getStatusClass(item) {
    if (item.quantity <= item.low_status) return 'table-danger'; // Rött för lågt lager
    if (item.quantity >= item.high_status) return 'table-success'; // Grönt för högt lager
    return 'table-warning'; // Gult för normalt lager
}

// Uppdatera brand-dropdownen
function updateBrandDropdown() {
    const brandSelect = document.getElementById('brand');
    const uniqueBrands = [...new Set(inventoryData.map(item => item.Brand))].sort(); // Hämta unika brands
    brandSelect.innerHTML = '<option value="" disabled selected>Välj kund</option>'; // Återställ dropdownen

    // Lägg till varje brand som ett alternativ i dropdownen
    uniqueBrands.forEach(brand => {
        if (brand) { // Se till att brand inte är null eller undefined
            brandSelect.innerHTML += `<option value="${brand}">${brand}</option>`;
        }
    });

    // Lyssna på ändringar i brand-dropdownen
    brandSelect.addEventListener('change', updateProductFamilyDropdown);
}

// Uppdatera product_family-dropdownen baserat på valt brand
function updateProductFamilyDropdown() {
    const brand = document.getElementById('brand').value;
    const productFamilySelect = document.getElementById('product_family');
    productFamilySelect.innerHTML = '<option value="" disabled selected>Välj produktfamilj</option>'; // Återställ dropdownen

    if (brand) {
        // Hämta unika produktfamiljer för det valda brandet
        const uniqueFamilies = [...new Set(inventoryData
            .filter(item => item.Brand === brand)
            .map(item => item.product_family))]
            .sort();

        // Lägg till varje produktfamilj som ett alternativ i dropdownen
        uniqueFamilies.forEach(family => {
            productFamilySelect.innerHTML += `<option value="${family}">${family}</option>`;
        });
    }

    // Lyssna på ändringar i product_family-dropdownen
    productFamilySelect.addEventListener('change', updateSparePartDropdown);
}

// Uppdatera spare_part-dropdownen baserat på vald product_family
function updateSparePartDropdown() {
    const productFamily = document.getElementById('product_family').value;
    const sparePartSelect = document.getElementById('spare_part');
    sparePartSelect.innerHTML = '<option value="" disabled selected>Välj reservdel</option>'; // Återställ dropdownen

    if (productFamily) {
        // Hämta unika reservdelar för den valda produktfamiljen
        const spareParts = inventoryData
            .filter(item => item.product_family === productFamily)
            .map(item => item.spare_part)
            .sort();

        // Lägg till varje reservdel som ett alternativ i dropdownen
        spareParts.forEach(part => {
            sparePartSelect.innerHTML += `<option value="${part}">${part}</option>`;
        });
    }
}

// Minska antalet för en reservdel
function subtractItem(id) {
    fetch(`/api/inventory/${id}/subtract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: 1 }) // Minska med 1
    })
    .then(response => {
        if (response.ok) {
            loadInventory(); // Ladda om inventariet efter ändring
        } else {
            console.error('Fel vid minskning av reservdel');
        }
    })
    .catch(error => {
        console.error('Fel vid minskning av reservdel:', error);
    });
}

// Minska antalet för en reservdel från formuläret
function subtractFromForm() {
    const productFamily = document.getElementById('product_family').value;
    const sparePart = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);

    // Hitta reservdelen i inventariet
    const item = inventoryData.find(i => i.product_family === productFamily && i.spare_part === sparePart);
    if (item) {
        fetch(`/api/inventory/${item.id}/subtract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity }) // Minska med angivet antal
        }).then(() => loadInventory()); // Ladda om inventariet efter ändring
    } else {
        alert("Reservdelen finns inte i lagret!"); // Visa felmeddelande om reservdelen inte hittas
    }
}

// Visa en toast för att bekräfta radering
function showDeleteToast(id) {
    deleteId = id; // Spara ID för radering
    deleteToast.show(); // Visa toasten
}

// Bekräfta radering av en post
function confirmDelete() {
    if (deleteId) {
        fetch(`/api/inventory/${deleteId}`, { method: 'DELETE' })
            .then(() => {
                deleteId = null; // Återställ deleteId
                deleteToast.hide(); // Dölj toasten
                loadInventory(); // Ladda om inventariet
            });
    }
}

// Hantera formulär för att lägga till en ny post
document.getElementById('inventoryForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Förhindra standardformulärsubmit

    // Hämta värden från formuläret
    const product_family = document.getElementById('product_family').value;
    const spare_part = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const id = Date.now(); // Skapa ett unikt ID baserat på tidstämpel

    // Skicka en POST-förfrågan för att lägga till en ny post
    fetch('/api/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, product_family, spare_part, quantity })
    }).then(() => loadInventory()); // Ladda om inventariet efter tillägg
});

// Uppdatera reservdels-dropdownen när produktfamilj ändras
document.getElementById('product_family').addEventListener('change', updateSparePartDropdown);

// Uppdatera tabellen när sökfältet ändras
document.getElementById('searchInput').addEventListener('input', function(e) {
    updateTable(e.target.value); // Uppdatera tabellen med filtrerad data
});

// Ladda inventariet när sidan laddas
window.onload = loadInventory;