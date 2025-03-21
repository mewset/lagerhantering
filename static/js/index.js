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
            updateBrandDropdown(); // Uppdatera dropdown för kunder
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

// Uppdatera dropdown för kunder
function updateBrandDropdown() {
    const brandDropdown = document.getElementById('brand');
    if (!brandDropdown) return; // Om dropdown inte finns, avbryt

    // Hämta unika kunder från inventariet
    const brands = [...new Set(inventoryData.map(item => item.Brand || 'Okänd'))];
    brandDropdown.innerHTML = '<option value="" disabled selected>Välj kund</option>';

    // Lägg till varje kund i dropdown
    brands.forEach(brand => {
        const option = document.createElement('option');
        option.value = brand;
        option.textContent = brand;
        brandDropdown.appendChild(option);
    });

    // Uppdatera produktfamilj och reservdel när kund ändras
    brandDropdown.addEventListener('change', () => {
        updateProductFamilyDropdown();
        updateSparePartDropdown();
        
        // Visuell feedback när kund väljs
        brandDropdown.classList.add('is-valid');
        
        // Visa tom lagerstatus tills komplett val gjorts
        updateStockStatusInForm();
    });
}

// Uppdatera dropdown för produktfamiljer baserat på vald kund
function updateProductFamilyDropdown() {
    const productFamilyDropdown = document.getElementById('product_family');
    if (!productFamilyDropdown) return; // Om dropdown inte finns, avbryt

    const selectedBrand = document.getElementById('brand').value;
    const productFamilies = [...new Set(
        inventoryData
            .filter(item => item.Brand === selectedBrand)
            .map(item => item.product_family)
    )];
    productFamilyDropdown.innerHTML = '<option value="" disabled selected>Välj produktfamilj</option>';

    // Lägg till varje produktfamilj i dropdown
    productFamilies.forEach(family => {
        const option = document.createElement('option');
        option.value = family;
        option.textContent = family;
        productFamilyDropdown.appendChild(option);
    });

    // Uppdatera reservdel när produktfamilj ändras
    productFamilyDropdown.addEventListener('change', () => {
        updateSparePartDropdown();
        
        // Visuell feedback när produktfamilj väljs
        productFamilyDropdown.classList.add('is-valid');
        
        // Visa tom lagerstatus tills komplett val gjorts
        updateStockStatusInForm();
    });
}

// Uppdatera dropdown för reservdelar baserat på vald produktfamilj
function updateSparePartDropdown() {
    const sparePartDropdown = document.getElementById('spare_part');
    if (!sparePartDropdown) return; // Om dropdown inte finns, avbryt

    const selectedProductFamily = document.getElementById('product_family').value;
    const spareParts = [...new Set(
        inventoryData
            .filter(item => item.product_family === selectedProductFamily)
            .map(item => item.spare_part)
    )];
    sparePartDropdown.innerHTML = '<option value="" disabled selected>Välj reservdel</option>';

    // Lägg till varje reservdel i dropdown
    spareParts.forEach(part => {
        const option = document.createElement('option');
        option.value = part;
        option.textContent = part;
        sparePartDropdown.appendChild(option);
    });
    
    // Lägg till händelseavlyssnare för att visa lagerstatus när reservdel väljs
    sparePartDropdown.addEventListener('change', () => {
        // Visuell feedback när reservdel väljs
        sparePartDropdown.classList.add('is-valid');
        
        // Visa aktuell lagerstatus för vald artikel
        updateStockStatusInForm();
    });
}

// Ny funktion: Visa aktuell lagerstatus i formuläret
function updateStockStatusInForm() {
    const stockDisplay = document.getElementById('currentStock');
    const brand = document.getElementById('brand').value;
    const productFamily = document.getElementById('product_family').value;
    const sparePart = document.getElementById('spare_part').value;
    
    // Endast visa lagerstatus om alla val är gjorda
    if (brand && productFamily && sparePart) {
        // Hitta artikeln i inventariedata
        const selectedItem = inventoryData.find(item => 
            item.Brand === brand && 
            item.product_family === productFamily && 
            item.spare_part === sparePart
        );
        
        if (selectedItem) {
            // Bestäm statusnivå och CSS-klass
            let statusClass = '';
            let statusText = '';
            
            if (selectedItem.quantity <= selectedItem.low_status) {
                statusClass = 'stock-low';
                statusText = 'Lågt lager';
            } else if (selectedItem.quantity >= selectedItem.high_status) {
                statusClass = 'stock-high';
                statusText = 'Högt lager';
            } else {
                statusClass = 'stock-medium';
                statusText = 'Medel lager';
            }
            
            // Visa lagerstatus i formuläret
            stockDisplay.innerHTML = `
                <span class="stock-indicator ${statusClass}">
                    <i class="bi bi-box"></i> ${selectedItem.quantity} st (${statusText})
                </span>`;
        } else {
            stockDisplay.innerHTML = '<span class="text-muted">Ingen information tillgänglig</span>';
        }
    } else {
        // Töm statusmeddelandet om inte alla val är gjorda
        stockDisplay.innerHTML = '';
    }
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

// Lägg till funktion för att ta reservdel från formuläret
function subtractFromForm() {
    const brand = document.getElementById('brand').value;
    const product_family = document.getElementById('product_family').value;
    const spare_part = document.getElementById('spare_part').value;
    
    if (!brand || !product_family || !spare_part) {
        showToast('Välj kund, produktfamilj och reservdel först');
        return;
    }
    
    // Hitta artikel i lager
    const item = inventoryData.find(item => 
        item.Brand === brand && 
        item.product_family === product_family && 
        item.spare_part === spare_part
    );
    
    if (item) {
        subtractItem(item.id);
    } else {
        showToast('Kunde inte hitta artikeln i lager');
    }
}

// Lägg till reservdel
document.getElementById('inventoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const brand = document.getElementById('brand').value;
    const product_family = document.getElementById('product_family').value;
    const spare_part = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const id = Date.now();

    fetch('/api/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Brand: brand, product_family, spare_part, quantity })
    }).then(() => {
        loadInventory();
        showToast(`Lagt till: ${product_family} - ${spare_part} - ${quantity}`, 'success');
        
        // Uppdatera lagerstatus i formuläret
        setTimeout(updateStockStatusInForm, 500);
    });
});

// Visa toast-meddelande med ikon och färg
function showToast(message, type = 'info') {
    const toastElement = document.getElementById('successToast');
    const toastBody = document.getElementById('toastMessage');
    const toastIcon = document.getElementById('toastIcon') || document.createElement('i');
    
    if (!document.getElementById('toastIcon')) {
        toastIcon.id = 'toastIcon';
        toastIcon.className = 'bi me-2';
        toastBody.prepend(toastIcon);
    }

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
    // Lägg tillbaka ikonen efter att vi satt textContent
    toastBody.prepend(toastIcon);
    
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
}

// Ladda inventariet vid start
window.onload = loadInventory;