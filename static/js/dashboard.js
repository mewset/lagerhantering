document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

function loadDashboard() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '';

            // Gruppera data per produktfamilj
            const families = {};
            data.forEach(item => {
                if (!families[item.product_family]) {
                    families[item.product_family] = [];
                }
                families[item.product_family].push(item);
            });

            // Skapa grupper om upp till 3 familjer
            const familyKeys = Object.keys(families);
            for (let i = 0; i < familyKeys.length; i += 3) {
                const rowGroup = familyKeys.slice(i, i + 3);
                const rowDiv = document.createElement('div');
                rowDiv.className = 'row mb-3';

                rowGroup.forEach(family => {
                    const items = families[family];
                    const colDiv = document.createElement('div');
                    colDiv.className = 'col-md-4';

                    const familyDiv = document.createElement('div');
                    familyDiv.className = 'family-card';

                    const title = document.createElement('h3');
                    title.textContent = family;
                    familyDiv.appendChild(title);

                    items.forEach(item => {
                        const status = item.quantity <= item.low_status ? 'low' :
                                       item.quantity >= item.high_status ? 'high' : 'mid';
                        const spareDiv = document.createElement('div');
                        spareDiv.className = `spare-part ${status}`;
                        spareDiv.innerHTML = `
                            <strong>${item.spare_part}</strong>: ${item.quantity} 
                        `;
                        familyDiv.appendChild(spareDiv);
                    });

                    colDiv.appendChild(familyDiv);
                    rowDiv.appendChild(colDiv);
                });

                dashboard.appendChild(rowDiv);
            }
        })
        .catch(error => {
            console.error('Fel vid laddning av dashboard:', error);
            document.getElementById('dashboard').innerHTML = '<p class="text-danger">Kunde inte ladda dashboard.</p>';
        });
}