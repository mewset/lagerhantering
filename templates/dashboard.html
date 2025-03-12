let inventoryData = [];

function loadDashboard() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            inventoryData = data;
            const dashboardContent = document.getElementById('dashboardContent');
            dashboardContent.innerHTML = '';

            const families = {};
            inventoryData.forEach(item => {
                if (item.quantity > 0) {  // Visa bara om quantity > 0
                    if (!families[item.product_family]) {
                        families[item.product_family] = [];
                    }
                    families[item.product_family].push(item);
                }
            });

            const sortedFamilies = Object.keys(families).sort();
            sortedFamilies.forEach(family => {
                const container = document.createElement('div');
                container.className = 'family-container';
                container.innerHTML = `<h1 class="family-title">${family}</h1>`;
                const sortedSpareParts = families[family].sort((a, b) => a.spare_part.localeCompare(b.spare_part));
                sortedSpareParts.forEach(item => {
                    let statusClass = 'mid'; // Standard är gult
                    if (item.quantity < item.low_status) {
                        statusClass = 'low'; // Rött
                    } else if (item.quantity >= item.high_status) {
                        statusClass = 'high'; // Grönt
                    }
                    container.innerHTML += `<div class="spare-part ${statusClass}">${item.spare_part}: ${item.quantity} st</div>`;
                });
                dashboardContent.appendChild(container);
            });

            if (sortedFamilies.length === 0) {
                dashboardContent.innerHTML = '<p class="text-center" style="font-size: 2rem;">Inga lagerdata tillgängliga ännu.</p>';
            }
        });
}

window.onload = function() {
    loadDashboard();
    setInterval(loadDashboard, 5000);
    window.addEventListener('resize', loadDashboard);
};