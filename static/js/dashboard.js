let inventoryData = [];

function loadDashboard() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            inventoryData = data;

            // Hämta unika varumärken och sortera alfabetiskt
            const brands = [...new Set(inventoryData.map(item => item.Brand))].sort();
            if (brands.length > 2) {
                console.warn('Fler än 2 kunder hittades, endast de första två visas.');
            }

            // Dela upp data per varumärke
            const brand1Data = inventoryData.filter(item => item.Brand === brands[0]);
            const brand2Data = brands[1] ? inventoryData.filter(item => item.Brand === brands[1]) : [];

            // Hantera första varumärket (vänster kolumn)
            const brand1Column = document.getElementById('brand1');
            brand1Column.innerHTML = `<h1 class="brand-title">${brands[0]}</h1>`;
            renderBrandData(brand1Column, brand1Data);

            // Hantera andra varumärket (höger kolumn)
            const brand2Column = document.getElementById('brand2');
            brand2Column.innerHTML = brands[1] ? `<h1 class="brand-title">${brands[1]}</h1>` : '<p class="text-center">Inget andra kunder tillgängligt</p>';
            if (brands[1]) {
                renderBrandData(brand2Column, brand2Data);
            }
        })
        .catch(error => {
            console.error('Fel vid laddning av dashboard:', error);
            const dashboardContent = document.getElementById('dashboardContent');
            dashboardContent.innerHTML = '<p class="text-center" style="font-size: 2rem;">Fel vid laddning av data.</p>';
        });
}

function renderBrandData(container, data) {
    const families = {};
    data.forEach(item => {
        if (item.quantity > 0) { // Visa bara om quantity > 0
            if (!families[item.product_family]) {
                families[item.product_family] = [];
            }
            families[item.product_family].push(item);
        }
    });

    const sortedFamilies = Object.keys(families).sort();
    sortedFamilies.forEach(family => {
        const familyContainer = document.createElement('div');
        familyContainer.className = 'family-container';
        familyContainer.innerHTML = `<h1 class="family-title">${family}</h1>`;
        const sortedSpareParts = families[family].sort((a, b) => a.spare_part.localeCompare(b.spare_part));
        sortedSpareParts.forEach(item => {
            let statusClass = 'mid'; // Standard är gult
            if (item.quantity < item.low_status) {
                statusClass = 'low'; // Rött
            } else if (item.quantity >= item.high_status) {
                statusClass = 'high'; // Grönt
            }
            familyContainer.innerHTML += `<div class="spare-part ${statusClass}">${item.spare_part}: ${item.quantity} st</div>`;
        });
        container.appendChild(familyContainer);
    });

    if (sortedFamilies.length === 0) {
        container.innerHTML += '<p class="text-center">Inga lagerdata för denna kund.</p>';
    }
}

window.onload = function() {
    loadDashboard();
    setInterval(loadDashboard, 5000);
    window.addEventListener('resize', loadDashboard);
};