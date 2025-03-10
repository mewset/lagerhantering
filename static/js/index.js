let inventoryData = [];
let previousInventoryData = [];
let deleteId = null;
const deleteToast = new bootstrap.Toast(document.getElementById('deleteToast'));
const toastContainer = document.querySelector('.toast-container');

function getStatus(item) {
    if (item.quantity < item.low_status) return 'low';
    if (item.quantity < item.mid_status) return 'mid';
    return 'high';
}

function showStatusNotification(message, newStatus) {
    const notificationContainer = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `alert status-notification alert-dismissible fade show`;
    
    let iconId = 'exclamation-triangle-fill';
    if (newStatus === 'low') {
        notification.classList.add('alert-danger');
    } else if (newStatus === 'high') {
        notification.classList.add('alert-success');
        iconId = 'check-circle-fill';
    } else {
        notification.classList.add('alert-warning');
    }

    notification.innerHTML = `
        <svg class="bi flex-shrink-0 me-2" width="24" height="24" role="img" aria-label="${newStatus}:">
            <use xlink:href="#${iconId}"/>
        </svg>
        <span>${message}</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    notificationContainer.appendChild(notification);
    setTimeout(() => {
        notification.remove();
    }, 30000);
}

function loadInventory() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            if (previousInventoryData.length > 0) {
                data.forEach(newItem => {
                    const oldItem = previousInventoryData.find(i => i.id === newItem.id);
                    if (oldItem) {
                        const oldStatus = getStatus(oldItem);
                        const newStatus = getStatus(newItem);
                        if (oldStatus !== newStatus) {
                            const statusText = newStatus === 'low' ? 'låg' : newStatus === 'mid' ? 'mellan' : 'hög';
                            showStatusNotification(`${newItem.product_family} - ${newItem.spare_part} har nu ${statusText} status (${newItem.quantity} st).`, newStatus);
                        }
                    }
                });
            }

            inventoryData = data.sort((a, b) => a.product_family.localeCompare(b.product_family) || a.spare_part.localeCompare(b.spare_part));
            previousInventoryData = JSON.parse(JSON.stringify(inventoryData));

            const tableBody = document.getElementById('inventoryTable');
            tableBody.innerHTML = '';
            inventoryData.forEach(item => {
                const row = `<tr>
                    <td>${item.id}</td>
                    <td>${item.product_family}</td>
                    <td>${item.spare_part}</td>
                    <td>${item.quantity}</td>
                    <td>
                        <button class="btn btn-warning btn-sm me-2" onclick="takeSparePart(${item.id})">Ta reservdel</button>
                        <button class="btn btn-danger btn-sm" onclick="confirmDelete(${item.id})">Radera</button>
                    </td>
                </tr>`;
                tableBody.innerHTML += row;
            });
            updateProductFamilyDropdown();
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

document.getElementById('product_family').addEventListener('change', updateSparePartDropdown);

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
    });
});

document.getElementById('subtractButton').addEventListener('click', function() {
    const product_family = document.getElementById('product_family').value;
    const spare_part = document.getElementById('spare_part').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    const item = inventoryData.find(i => i.product_family === product_family && i.spare_part === spare_part);
    if (item) {
        fetch(`/api/inventory/${item.id}/subtract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity })
        }).then(() => {
            loadInventory();
        });
    } else {
        alert("Posten finns inte i lagret!");
    }
});

function takeSparePart(id) {
    fetch(`/api/inventory/${id}/subtract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: 1 })
    }).then(() => {
        loadInventory();
    });
}

function confirmDelete(id) {
    deleteId = id;
    toastContainer.classList.add('show');
    deleteToast.show();
}

function deleteItem() {
    if (deleteId) {
        fetch(`/api/inventory/${deleteId}`, { method: 'DELETE' })
            .then(() => {
                loadInventory();
                deleteId = null;
                toastContainer.classList.remove('show');
            });
    }
}

function openDashboard() {
    window.open('/dashboard', '_blank', 'width=800,height=600');
}

document.getElementById('confirmDelete').addEventListener('click', function() {
    deleteItem();
    deleteToast.hide();
});

document.querySelector('.btn-close').addEventListener('click', function() {
    toastContainer.classList.remove('show');
});
document.querySelector('.btn-secondary').addEventListener('click', function() {
    toastContainer.classList.remove('show');
});

window.onload = loadInventory;