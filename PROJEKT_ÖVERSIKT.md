# Lagerhantering - Projektöversikt

## Sammanfattning
En Flask-baserad webbapplikation för hantering av reservdelslager. Applikationen erbjuder CRUD-operationer för lagerinventering, dashboard för statusöversikt, automatiska backuper och loggning.

## Teknisk Stack
- **Backend**: Flask (Python 3.8+)
- **Frontend**: HTML5, Bootstrap 5, vanilla JavaScript
- **Databas**: JSON-fil (`data/inventory.json`)
- **Beroenden**: Flask 3.0.3, schedule 1.2.2

## Projektstruktur
```
Lagerhantering/
├── app.py                 # Huvudapplikation (Flask-server)
├── requirements.txt       # Python-beroenden
├── README.md             # Projektdokumentation
├── app.log               # Applikationsloggar
├── data/
│   └── inventory.json    # JSON-databas för lagerinventering
├── db_backup/            # Automatiska säkerhetskopior
│   └── inventory-*.json  # Backup-filer med timestamp
├── static/
│   └── js/
│       ├── index.js      # JavaScript för huvudsida
│       └── dashboard.js  # JavaScript för dashboard
└── templates/            # HTML-mallar
    ├── index.html        # Huvudsida (CRUD-gränssnitt)
    ├── admin.html        # Administratörssida
    ├── dashboard.html    # Statusdashboard
    ├── logs.html         # Loggsida
    └── footer.html       # Gemensam footer
```

## Funktionalitet

### Webbgränssnitt
- **`/`** - Huvudsida för att lägga till/ta bort reservdelar
- **`/admin`** - Administratörssida för hantering av lagerposter
- **`/dashboard`** - Dashboard med färgkodad statusöversikt
- **`/logs`** - Systemloggar med filtrering och paginering

### API-endpoints
- `GET /api/inventory` - Hämta all lagerinformation
- `POST /api/inventory` - Lägg till ny reservdel eller uppdatera befintlig
- `POST /api/inventory/<id>/subtract` - Subtrahera antal från en post
- `PATCH /api/inventory/<id>` - Uppdatera en specifik post
- `DELETE /api/inventory/<id>` - Ta bort en post

### Datastruktur
```json
{
  "id": 1741597123352,
  "product_family": "E14 G2",
  "spare_part": "Palmrest",
  "quantity": 70,
  "low_status": 5,
  "mid_status": 10,
  "high_status": 15
}
```

### Automatiska Funktioner
- **Backup-system**: Skapar säkerhetskopior varannan dag kl. 17:00 (Mån-Fre)
- **Loggning**: Omfattande loggning av alla aktiviteter till `app.log`
- **Statusnotifieringar**: Färgkodad status baserat på kvantitet

## Tekniska Detaljer

### Backend (app.py)
- **Filhantering**: Hanterar JSON-databas och backup-operationer
- **Schemaläggning**: Använder `schedule`-biblioteket för automatiska backuper
- **Threading**: Backup-schemaläggare körs i separat tråd
- **Felsäker**: Omfattande felhantering med try-catch block
- **Loggning**: Detaljerad loggning på INFO-, WARNING- och ERROR-nivå

### Frontend
- **Bootstrap 5**: Modern och responsiv UI
- **Vanilla JavaScript**: Inga externa JavaScript-ramverk
- **AJAX**: Asynkron kommunikation med backend-API
- **Toast-notifieringar**: Användarfeedback för operationer
- **Statusindikatorer**: Färgkodade statusar (rött/gult/grönt)

### Säkerhetsfunktioner
- **Backup-retention**: Behåller endast 5 senaste backup-filer
- **Felhantering**: Robusta felhanteringsrutiner
- **Loggning**: Spårning av alla systemhändelser
- **Validering**: Server-side validering av inkommande data

## Utvecklingslägen
- **Produktion**: `python app.py`
- **Debug**: `python app.py --debug`

## Nuvarande Status
Applikationen är funktionell och innehåller:
- Grundläggande CRUD-operationer
- Automatiskt backup-system
- Omfattande loggning
- Responsiv webbgränssnitt
- Status-dashboard med färgkodning

## Framtida Förbättringar
Som dokumenterat i README.md:
- Migrera till SQL-databas (PostgreSQL)
- Användarroller och rättighetsvalidering
- Utökad loggningsfunktionalitet
- Dashboard med grafer och analytics
- Centraliserad databaslösning för multi-site deployment

## Git-status
- Aktuell branch: `main`
- Senaste commit: `a80bd18` - "Uppdaterad README.md, fixat och trixat"
- Ändrad fil: `static/js/index.js` (uncommitted)

## Användning
1. Installera beroenden: `pip install -r requirements.txt`
2. Kör applikation: `python app.py`
3. Öppna webbläsare: `http://localhost:5000`

---
*Genererat den 2025-08-27*