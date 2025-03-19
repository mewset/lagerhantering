// @ts-nocheck

document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
});

function loadDashboard() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = '';

            // Gruppera data först per Brand, sedan per product_family
            const brands = {};
            data.forEach(item => {
                const brand = item.Brand || 'Okänd'; // Hantera fall där Brand saknas
                if (!brands[brand]) {
                    brands[brand] = {};
                }
                if (!brands[brand][item.product_family]) {
                    brands[brand][item.product_family] = [];
                }
                brands[brand][item.product_family].push(item);
            });

            // Rendera varje Brand separat
            Object.keys(brands).forEach(brand => {
                const brandDiv = document.createElement('div');
                brandDiv.className = 'mb-4';

                const brandTitle = document.createElement('h2');
                brandTitle.textContent = brand;
                brandDiv.appendChild(brandTitle);

                const familyKeys = Object.keys(brands[brand]);
                for (let i = 0; i < familyKeys.length; i += 3) {
                    const rowGroup = familyKeys.slice(i, i + 3);
                    const rowDiv = document.createElement('div');
                    rowDiv.className = 'row mb-3';

                    rowGroup.forEach(family => {
                        const items = brands[brand][family];
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
                                (Low: ${item.low_status}, High: ${item.high_status})
                            `;
                            familyDiv.appendChild(spareDiv);
                        });

                        colDiv.appendChild(familyDiv);
                        rowDiv.appendChild(colDiv);
                    });

                    brandDiv.appendChild(rowDiv);
                }

                dashboard.appendChild(brandDiv);
            });
        })
        .catch(error => {
            console.error('Fel vid laddning av dashboard:', error);
            document.getElementById('dashboard').innerHTML = '<p class="text-danger">Kunde inte ladda dashboard.</p>';
        });
}