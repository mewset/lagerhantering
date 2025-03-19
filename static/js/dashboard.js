document.addEventListener('DOMContentLoaded', function() {
    loadDashboard(); // Ladda dashboarden direkt när sidan laddas

    // Uppdatera dashboarden var 3:e sekund
    setInterval(loadDashboard, 3000);
});

function loadDashboard() {
    fetch('/api/inventory')
        .then(response => response.json())
        .then(data => {
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

            // Hämta de två första brandsen
            const brandKeys = Object.keys(brands);
            const brandLeft = brandKeys[0] || 'Inget brand'; // Första brand
            const brandRight = brandKeys[1] || 'Inget brand'; // Andra brand

            // Uppdatera titlarna för vänster och höger del
            document.getElementById('brandLeftTitle').textContent = brandLeft;
            document.getElementById('brandRightTitle').textContent = brandRight;

            // Rendera vänster del (första brand)
            renderBrandSection('brandLeftContent', brands[brandLeft]);

            // Rendera höger del (andra brand)
            renderBrandSection('brandRightContent', brands[brandRight]);
        })
        .catch(error => {
            console.error('Fel vid laddning av dashboard:', error);
            document.getElementById('dashboard').innerHTML = '<p class="text-danger">Kunde inte ladda dashboard.</p>';
        });
}

// Funktion för att rendera en brand-sektion med tre kolumner
function renderBrandSection(sectionId, brandData) {
    const section = document.getElementById(sectionId);
    section.innerHTML = ''; // Rensa innehållet

    const familyKeys = Object.keys(brandData);
    for (let i = 0; i < familyKeys.length; i += 3) {
        const rowGroup = familyKeys.slice(i, i + 3);
        const rowDiv = document.createElement('div');
        rowDiv.className = 'row mb-3';

        rowGroup.forEach(family => {
            const items = brandData[family];
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

        section.appendChild(rowDiv);
    }
}