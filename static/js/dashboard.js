// Lyssna på när sidan har laddat klart
document.addEventListener('DOMContentLoaded', function() {
    initializeSettings(); // Initiera settings-funktionalitet
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

            // Rendera alla brands dynamiskt
            const brandKeys = Object.keys(brands);
            const container = document.getElementById('brandsContainer');
            container.innerHTML = ''; // Rensa befintligt innehåll

            // Skapa en sektion för varje brand
            brandKeys.forEach(brandName => {
                const brandSection = document.createElement('div');
                brandSection.className = 'brand-section';
                brandSection.innerHTML = `
                    <h2>${brandName}</h2>
                    <div class="brand-content" id="brand-${brandName.replace(/\s+/g, '-')}"></div>
                `;
                container.appendChild(brandSection);

                // Rendera brand-sektionen
                renderBrandSection(`brand-${brandName.replace(/\s+/g, '-')}`, brands[brandName]);
            });
        })
        .catch(error => {
            // Hantera fel vid hämtning av data
            console.error('Fel vid laddning av dashboard:', error);
            document.getElementById('brandsContainer').innerHTML = '<p class="text-danger">Kunde inte ladda dashboard.</p>';
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

// Settings-funktionalitet
function initializeSettings() {
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsPanel = document.getElementById('settingsPanel');
    const scaleSlider = document.getElementById('scaleSlider');
    const scaleValue = document.getElementById('scaleValue');
    const columnsSlider = document.getElementById('columnsSlider');
    const columnsValue = document.getElementById('columnsValue');
    const compactMode = document.getElementById('compactMode');
    const resetSettings = document.getElementById('resetSettings');

    // Ladda sparade inställningar
    loadSettings();

    // Toggle settings panel
    settingsBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        settingsPanel.classList.toggle('show');
    });

    // Stäng panel när man klickar utanför
    document.addEventListener('click', function(e) {
        if (!settingsPanel.contains(e.target) && !settingsBtn.contains(e.target)) {
            settingsPanel.classList.remove('show');
        }
    });

    // Skalning
    scaleSlider.addEventListener('input', function() {
        const scale = this.value / 100;
        scaleValue.textContent = this.value + '%';
        document.documentElement.style.setProperty('--scale', scale);
        saveSettings();
    });

    // Kolumner
    columnsSlider.addEventListener('input', function() {
        const columns = this.value;
        columnsValue.textContent = columns;
        document.documentElement.style.setProperty('--columns', columns);
        saveSettings();
    });

    // Kompakt läge
    compactMode.addEventListener('change', function() {
        document.body.classList.toggle('compact-mode', this.checked);
        saveSettings();
    });

    // Återställ inställningar
    resetSettings.addEventListener('click', function() {
        scaleSlider.value = 100;
        columnsSlider.value = 3;
        compactMode.checked = false;
        
        scaleValue.textContent = '100%';
        columnsValue.textContent = '3';
        
        document.documentElement.style.setProperty('--scale', 1);
        document.documentElement.style.setProperty('--columns', 3);
        document.body.classList.remove('compact-mode');
        
        saveSettings();
    });
}

// Spara inställningar på servern
function saveSettings() {
    const settings = {
        scale: parseInt(document.getElementById('scaleSlider').value),
        columns: parseInt(document.getElementById('columnsSlider').value),
        compact: document.getElementById('compactMode').checked
    };
    
    fetch('/api/settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'Settings saved') {
            console.log('Inställningar sparade på servern');
        } else {
            console.error('Fel vid sparning av inställningar:', data);
        }
    })
    .catch(error => {
        console.error('Fel vid kommunikation med servern:', error);
    });
}

// Ladda inställningar från servern
function loadSettings() {
    fetch('/api/settings')
        .then(response => response.json())
        .then(settings => {
            // Uppdatera UI-kontroller
            document.getElementById('scaleSlider').value = settings.scale || 100;
            document.getElementById('columnsSlider').value = settings.columns || 3;
            document.getElementById('compactMode').checked = settings.compact || false;
            
            // Uppdatera värde-display
            document.getElementById('scaleValue').textContent = (settings.scale || 100) + '%';
            document.getElementById('columnsValue').textContent = settings.columns || 3;
            
            // Tillämpa inställningarna
            applySettings(settings);
            
            console.log('Inställningar laddade från servern');
        })
        .catch(error => {
            console.error('Fel vid laddning av inställningar från servern:', error);
            // Fallback till standardinställningar
            applySettings({
                scale: 100,
                columns: 3,
                compact: false
            });
        });
}

// Tillämpa inställningar på UI
function applySettings(settings) {
    document.documentElement.style.setProperty('--scale', (settings.scale || 100) / 100);
    document.documentElement.style.setProperty('--columns', settings.columns || 3);
    
    if (settings.compact) {
        document.body.classList.add('compact-mode');
    } else {
        document.body.classList.remove('compact-mode');
    }
}