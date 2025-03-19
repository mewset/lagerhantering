// Lyssna på när sidan har laddat klart
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard(); // Ladda dashboarden direkt när sidan laddas

    // Uppdatera dashboarden var 3:e sekund
    setInterval(loadDashboard, 3000);
});

// Funktion för att ladda och rendera dashboarden
function loadDashboard() {
    // Hämta lagerdata från API:et
    fetch('/api/inventory')
        .then(response => response.json()) // Konvertera svaret till JSON
        .then(data => {
            // Skapa ett objekt för att gruppera data efter "Brand" och "product_family"
            const brands = {};
            data.forEach(item => {
                const brand = item.Brand || 'Okänd'; // Använd "Okänd" om "Brand" saknas
                if (!brands[brand]) {
                    brands[brand] = {}; // Skapa en ny grupp för detta "Brand" om den inte redan finns
                }
                if (!brands[brand][item.product_family]) {
                    brands[brand][item.product_family] = []; // Skapa en ny grupp för produktfamiljen om den inte redan finns
                }
                brands[brand][item.product_family].push(item); // Lägg till produkten i rätt grupp
            });

            // Hämta de två första brandsen från datan
            const brandKeys = Object.keys(brands);
            const brandLeft = brandKeys[0] || 'Inget brand'; // Första brand (eller "Inget brand" om det inte finns något)
            const brandRight = brandKeys[1] || 'Inget brand'; // Andra brand (eller "Inget brand" om det inte finns något)

            // Uppdatera titlarna för vänster och höger del
            document.getElementById('brandLeftTitle').textContent = brandLeft;
            document.getElementById('brandRightTitle').textContent = brandRight;

            // Rendera vänster del (första brand)
            renderBrandSection('brandLeftContent', brands[brandLeft]);

            // Rendera höger del (andra brand)
            renderBrandSection('brandRightContent', brands[brandRight]);
        })
        .catch(error => {
            // Hantera fel vid hämtning av data
            console.error('Fel vid laddning av dashboard:', error);
            document.getElementById('dashboard').innerHTML = '<p class="text-danger">Kunde inte ladda dashboard.</p>';
        });
}

// Funktion för att rendera en brand-sektion med tre kolumner
function renderBrandSection(sectionId, brandData) {
    const section = document.getElementById(sectionId);
    section.innerHTML = ''; // Rensa innehållet i sektionen

    // Hämta alla produktfamiljer för detta brand
    const familyKeys = Object.keys(brandData);

    // Loopa genom produktfamiljerna i grupper om 3
    for (let i = 0; i < familyKeys.length; i += 3) {
        const rowGroup = familyKeys.slice(i, i + 3); // Skapa en grupp med upp till 3 produktfamiljer
        const rowDiv = document.createElement('div');
        rowDiv.className = 'row mb-3'; // Bootstrap-klass för att skapa en rad

        // Loopa genom varje produktfamilj i gruppen
        rowGroup.forEach(family => {
            const items = brandData[family]; // Hämta alla reservdelar för denna produktfamilj
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-4'; // Bootstrap-klass för att skapa en kolumn (3 kolumner per rad)

            const familyDiv = document.createElement('div');
            familyDiv.className = 'family-card'; // CSS-klass för att styla produktfamilj-kortet

            // Lägg till en titel för produktfamiljen
            const title = document.createElement('h3');
            title.textContent = family;
            familyDiv.appendChild(title);

            // Loopa genom alla reservdelar i produktfamiljen
            items.forEach(item => {
                // Bestäm status baserat på kvantitet (låg, normal, hög)
                const status = item.quantity <= item.low_status ? 'low' :
                               item.quantity >= item.high_status ? 'high' : 'mid';

                // Skapa ett element för reservdelen
                const spareDiv = document.createElement('div');
                spareDiv.className = `spare-part ${status}`; // CSS-klass baserat på status
                spareDiv.innerHTML = `
                    <strong>${item.spare_part}</strong>: ${item.quantity} 
                `;
                familyDiv.appendChild(spareDiv); // Lägg till reservdelen i produktfamilj-kortet
            });

            colDiv.appendChild(familyDiv); // Lägg till produktfamilj-kortet i kolumnen
            rowDiv.appendChild(colDiv); // Lägg till kolumnen i raden
        });

        section.appendChild(rowDiv); // Lägg till raden i sektionen
    }
}