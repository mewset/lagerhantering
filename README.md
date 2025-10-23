# Lagerhantering

En modern Flask-baserad webbapplikation för att hantera ett lager av reservdelar. Applikationen har en modulär arkitektur med fokus på säkerhet, prestanda och underhållbarhet.

## 🏗️ Arkitektur

Applikationen använder en modulär arkitektur med tydlig separation av ansvar:

```
├── models/                # Dataåtkomstlager (InventoryModel, InventoryItem)
├── services/              # Affärslogik
│   ├── inventory_service.py   # Inventariehantering och statuslogik
│   ├── backup_service.py      # Automatiska säkerhetskopior
│   ├── updater_service.py     # Git-baserade uppdateringar
│   └── settings_service.py    # Dashboard-inställningar
├── routes/                # API-endpoints (inventory, settings, logs)
├── utils/                 # Verktyg och hjälpfunktioner
│   ├── validation.py          # Input-validering
│   ├── exceptions.py          # Anpassade undantag
│   ├── logger.py              # Strukturerad loggning
│   ├── file_handler.py        # Thread-safe filoperationer
│   └── decorators.py          # Felhantering och validering
├── config.py              # Centraliserad konfiguration (Singleton)
├── app.py                 # Huvudapplikation med dependency injection
├── updater.py             # Fristående uppdateringstjänst
├── static/                # Statiska resurser (CSS, JS)
├── templates/             # HTML-mallar
└── data/                  # Datalagring (inventory.json, dashboard_settings.json)
```

### Huvudkomponenter

**Models** - Dataåtkomst och cachning
- `InventoryModel`: Thread-safe CRUD-operationer med atomiska skrivningar och in-memory cache
- `InventoryItem`: Type-safe dataklasser för inventarieobjekt

**Services** - Affärslogik
- `InventoryService`: Statusberäkningar, validering och detaljerad logging
- `BackupService`: Automatiska säkerhetskopior varannan dag kl. 17:00 (mån-fre)
- `UpdaterService`: Git-baserade uppdateringar med processhantering och graceful restart
- `SettingsService`: Hantering av dashboard-inställningar

**Routes** - API-endpoints med validering
- `inventory.py`: CRUD-operationer för inventarieobjekt
- `settings.py`: Dashboard-konfiguration
- `logs.py`: Effektiv loggvisning med paginering och filtrering
- Omfattande input-validering med detaljerade felmeddelanden
- Konsistenta API-svar med korrekta HTTP-statuskoder
- Robust felhantering med anpassade undantag

**Utils** - Delade verktyg
- `validation.py`: Scheman för input-validering
- `exceptions.py`: Anpassad undantagshierarki
- `logger.py`: Strukturerad loggning för app och updater
- `file_handler.py`: Thread-safe filoperationer med atomiska skrivningar
- `decorators.py`: Återanvändbara decorators för felhantering

## Funktioner

### Webbgränssnitt

- **Huvudsida (`/`)**: Lägg till eller subtrahera kvantitet för reservdelar och visa aktuellt lager
- **Admin-sida (`/admin`)**: Hantera lagerposter (lägg till, uppdatera, radera objekt)
- **Dashboard (`/dashboard`)**: Visuell översikt av lagerstatus med färgkodning baserad på statusnivåer
  - Rött: Låg status (quantity ≤ low_status) - "Slakta enheter för att addera saldo"
  - Gult: Mellan-status - "Se över saldot"
  - Grönt: Hög status (quantity ≥ high_status) - "Ingen åtgärd krävs"
- **Loggar (`/logs`)**: Visa systemloggar med effektiv paginering och filtrering för stora loggfiler

### Automatiska Funktioner

- **Backup**: Automatiska säkerhetskopior av lagerdatan varannan dag kl. 17:00 (endast vardagar)
  - Behåller max 5 backuper (äldsta raderas automatiskt)
  - Backuper sparas i `db_backup/`
- **Uppdateringar**: Fristående uppdateringstjänst (`updater.py`) med Git-integration
  - Schemalagda kontroller varje måndag kl. 02:00 (daemon-läge)
  - Skapar versionsbackuper innan uppdateringar
  - Graceful restart av Flask-applikationen efter uppdatering
  - Lockfil-mekanism för att förhindra samtidiga uppdateringar

### API-endpoints

**Inventarie**
- `GET /api/inventory` - Hämta alla inventarieobjekt
- `POST /api/inventory` - Lägg till nytt objekt eller uppdatera kvantitet för befintligt
- `PATCH /api/inventory/<id>` - Uppdatera objektegenskaper (brand, spare_part, thresholds)
- `DELETE /api/inventory/<id>` - Ta bort objekt från inventariet
- `POST /api/inventory/<id>/subtract` - Subtrahera kvantitet från objekt

**Dashboard-inställningar**
- `GET /api/settings` - Hämta sparade dashboard-inställningar
- `POST /api/settings` - Spara nya dashboard-inställningar

**System**
- `GET /api/check_version` - Kontrollera uppdateringsstatus (returnerar info om updater.py)

## Krav

- **Python**: 3.8 eller senare
- **Beroenden**: Flask 3.0.3, schedule 1.2.2
- **Git**: Krävs för automatiska uppdateringar via `updater.py`

## Installation

1. **Klona repot**:
   ```bash
   git clone https://github.com/mewset/lagerhantering.git
   cd lagerhantering
   ```

2. **Skapa en virtuell miljö (rekommenderat)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Installera beroenden**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Kör applikationen**:
   ```bash
   # Produktion
   python app.py

   # Utveckling (med debug-läge och detaljerad loggning)
   python app.py --debug
   ```

5. **Kör uppdateringstjänsten** (valfritt, för automatiska uppdateringar):
   ```bash
   # Manuell kontroll av uppdateringar
   python updater.py --check

   # Som daemon (schemalagda kontroller varje måndag kl. 02:00)
   python updater.py --daemon

   # Windows: Använd batch-skript
   start_updater_daemon.bat     # Startar daemon
   test_updater.bat              # Testar uppdateringsmekanism
   ```

6. **Öppna webbläsaren**: http://localhost:5000/

## Konfiguration

Konfiguration hanteras centralt i `config.py` med en Singleton-pattern för att säkerställa en enda konfigurationsinstans.

### Huvudinställningar

```python
# Kataloger och filer
DATA_DIR = "data"                      # Datakatalog (inventory.json, settings.json)
BACKUP_DIR = "db_backup"               # Säkerhetskopiekatalog
VERSION_BACKUP_DIR = "version_backup"  # Versionsbackuper före uppdateringar
LOG_FILE = "app.log"                   # Huvudloggfil
UPDATER_LOG_FILE = "updater.log"       # Loggfil för uppdateringstjänst
LOCK_FILE = "updater.lock"             # Lockfil för uppdateringar

# Server
HOST = "0.0.0.0"                       # Serveradress (tillåter externa anslutningar)
PORT = 5000                            # Serverport
DEBUG = False                          # Debug-läge (sätts via --debug flagga)

# Backup och uppdateringar
BACKUP_MAX_FILES = 5                   # Max antal backuper att behålla
VERSION_BACKUP_MAX_FILES = 3           # Max antal versionsbackuper
BACKUP_SCHEDULE_TIME = "17:00"         # Daglig backuptid
UPDATE_SCHEDULE_DAY = "monday"         # Dag för automatiska uppdateringar
UPDATE_SCHEDULE_TIME = "02:00"         # Tid för automatiska uppdateringar

# Prestanda
CACHE_TTL_SECONDS = 1.0                # Cache-livslängd för InventoryModel
```

### Åtkomst till konfiguration

```python
from config import get_config

config = get_config()  # Hämta singleton-instans
data_file = config.data_file  # Returnerar "data/inventory.json"
settings_file = config.settings_file  # Returnerar "data/dashboard_settings.json"
```

## Datastruktur

### Inventarieobjekt

```json
{
  "id": "unique_timestamp_id",
  "Brand": "Apple",
  "product_family": "iPhone",
  "spare_part": "Display",
  "quantity": 15,
  "low_status": 5,
  "high_status": 20
}
```

**Fält**:
- `id`: Unik identifierare (genereras automatiskt med tidsstämpel)
- `Brand`: Tillverkare/märke
- `product_family`: Produktfamilj
- `spare_part`: Reservdelsnamn
- `quantity`: Aktuellt lagersaldo
- `low_status`: Tröskelvärde för låg status (rött)
- `high_status`: Tröskelvärde för hög status (grönt)

### Statuslogik

Objekt klassificeras automatiskt baserat på kvantitet och tröskelvärden:

| Status | Villkor | Färg | Rekommenderad åtgärd |
|--------|---------|------|----------------------|
| **Låg** | `quantity <= low_status` | Röd | "Slakta enheter för att addera saldo" |
| **Mellan** | `low_status < quantity < high_status` | Gul | "Se över saldot" |
| **Hög** | `quantity >= high_status` | Grön | "Ingen" |

### Filstruktur

```
lagerhantering/
├── data/
│   ├── inventory.json           # Huvuddatabas (JSON-baserad)
│   └── dashboard_settings.json  # Dashboard-inställningar
├── db_backup/
│   └── inventory_YYYYMMDD_HHMMSS.json  # Automatiska backuper
├── version_backup/
│   └── backup_YYYYMMDD_HHMMSS/  # Kod-backuper före uppdateringar
├── app.log                      # Huvudloggfil
├── updater.log                  # Uppdateringstjänst-logg
└── updater.lock                 # Lockfil (skapas under uppdateringar)
```

## Loggning

All aktivitet loggas strukturerat med olika nivåer:

### app.log
- Inventarieändringar med före/efter-tillstånd
- Statusklassificeringar och rekommenderade åtgärder
- API-förfrågningar och svar
- System-händelser och fel
- Backup-operationer

### updater.log
- Uppdateringskontroller
- Git-operationer (fetch, pull, stash)
- Backup-skapande innan uppdateringar
- Process-hantering (stop/start av app.py)
- Fel under uppdateringsprocessen

**Exempel loggpost**:
```
2025-09-30 14:23:45 - INFO - Lagersaldo ändrat: iPhone Display - Från: 10 → Till: 15
2025-09-30 14:23:45 - INFO - Status: Mellan (quantity: 15, low: 5, high: 20) → Åtgärd: Se över saldot
```

## Utveckling

### Projektstruktur
Följ den modulära arkitekturen när du lägger till nya funktioner:
- **Models** (`models/`): Lägg till nya datamodeller och dataåtkomstklasser
- **Services** (`services/`): Implementera affärslogik och beräkningar
- **Routes** (`routes/`): Skapa nya API-endpoints med Blueprint-pattern
- **Utils** (`utils/`): Lägg till återanvändbara verktyg och hjälpfunktioner

### Kodstil
- Använd type hints för funktionsparametrar och returvärden
- Dokumentera funktioner med docstrings
- Hantera fel med anpassade undantag från `utils.exceptions`
- Använd strukturerad loggning via `utils.logger`
- Thread-safe filoperationer via `utils.file_handler`

### Bidra
1. Forka repot
2. Skapa en feature-branch (`git checkout -b feature/ny-funktion`)
3. Följ befintlig kodstil och arkitektur
4. Testa ändringarna lokalt
5. Committa med beskrivande meddelanden
6. Skapa en pull request

## Tilltänkta Förbättringar

- **Databas**: Migrera från JSON till PostgreSQL eller SQLite för bättre prestanda
- **Autentisering**: Användarroller och rättighetshantering
- **Analytics**: Utökad dashboard med historiska grafer och trendanalys
- **API-dokumentation**: OpenAPI/Swagger-specifikation
- **Tester**: Omfattande test-suite med pytest och coverage
- **Deployment**: Docker-container och CI/CD-pipeline
- **Monitoring**: Health checks, metrics och alerting
- **Export/Import**: CSV/Excel-export av inventariedata
- **Notifikationer**: Email/SMS-notiser vid låga lagernivåer
