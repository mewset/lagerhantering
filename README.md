# Lagerhantering

En modern Flask-baserad webbapplikation för att hantera ett lager av reservdelar. Inkluderar funktioner för att lägga till och ta bort reservdelar, visa lagerstatus i en dashboard, automatiska backuper, loggning av händelser och automatisk versionsvalidering mot GitHub.

## 🏗️ Arkitektur

Applikationen använder en modulär arkitektur med tydlig separation av ansvar:

```
├── models/           # Dataåtkomstlager (InventoryModel, InventoryItem)
├── services/         # Affärslogik (InventoryService, BackupService, UpdaterService)
├── routes/           # API-endpoints (inventory, settings, logs)
├── utils/            # Verktyg (validation, exceptions, logger, file_handler)
├── config.py         # Centraliserad konfiguration
├── app.py            # Huvudapplikation med dependency injection
├── updater.py        # Förenklad uppdateringstjänst
├── static/           # Statiska resurser (CSS, JS)
├── templates/        # HTML-mallar
└── data/             # Datalagring (inventory.json, settings.json)
```

### Huvudkomponenter

**Models** - Dataåtkomst och cachning
- `InventoryModel`: Thread-safe CRUD-operationer med atomiska skrivningar
- `InventoryItem`: Type-safe dataklasser för inventarieobjekt

**Services** - Affärslogik
- `InventoryService`: Statusberäkningar, validering och logging
- `BackupService`: Automatiska säkerhetskopior med versionshantering
- `UpdaterService`: Git-baserade uppdateringar med processhantering

**Routes** - API-endpoints med validering
- Omfattande input-validering med detaljerade felmeddelanden
- Konsistenta API-svar med korrekta HTTP-statuskoder
- Robust felhantering med anpassade undantag

**Utils** - Delade verktyg
- `validation.py`: Scheman för input-validering
- `exceptions.py`: Anpassad undantagshierarki
- `logger.py`: Strukturerad loggning
- `file_handler.py`: Thread-safe filoperationer

## Funktioner

- **Huvudsida (`/`)**: Lägg till eller ta bort reservdelar och visa aktuellt lager
- **Admin-sida (`/admin`)**: Hantera lagerposter (lägg till, uppdatera, radera)
- **Dashboard (`/dashboard`)**: Översikt av lagerstatus med färgkodning (rött för lågt, gult för mellan, grönt för högt)
- **Loggar (`/logs`)**: Visa systemloggar med effektiv paginering och filtrering
- **Backup**: Automatiska säkerhetskopior av lagerdatan varannan dag kl. 17:00 (mån-fre)
- **Versionsvalidering**: Automatiska uppdateringar via `updater.py` med Git-integration

### API-endpoints

**Inventarie**
- `GET /api/inventory` - Hämta alla objekt
- `POST /api/inventory` - Lägg till nytt objekt eller uppdatera kvantitet
- `PATCH /api/inventory/<id>` - Uppdatera objektegenskaper
- `DELETE /api/inventory/<id>` - Ta bort objekt
- `POST /api/inventory/<id>/subtract` - Subtrahera kvantitet

**Inställningar**
- `GET /api/settings` - Hämta dashboard-inställningar
- `POST /api/settings` - Spara dashboard-inställningar

**System**
- `GET /api/check_version` - Kontrollera uppdateringsstatus

## Krav

- **Python**: 3.8 eller senare
- **Beroenden**: Flask 3.0.3, schedule 1.2.2, psutil 6.0.0
- **Git**: Krävs för versionsvalidering och automatiska uppdateringar

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

   # Utveckling (med debug)
   python app.py --debug
   ```

5. **Kör uppdateringstjänsten** (valfritt):
   ```bash
   # Engångskontroll
   python updater.py --check

   # Som daemon (kontinuerlig övervakning)
   python updater.py --daemon
   ```

6. Öppna webbläsaren och gå till: http://localhost:5000/


## Konfiguration

Konfiguration hanteras centralt i `config.py`. Huvudinställningar:

```python
DATA_DIR = "data"              # Datakatalog
BACKUP_DIR = "db_backup"       # Säkerhetskopiekatalog
LOG_FILE = "app.log"          # Loggfil
HOST = "0.0.0.0"              # Serveradress
PORT = 5000                   # Serverport
CACHE_TTL_SECONDS = 1.0       # Cache-livslängd
```

## Utveckling

### Projektstruktur
Följ den modulära arkitekturen när du lägger till nya funktioner:
- Lägg till nya datamodeller i `models/`
- Implementera affärslogik i `services/`
- Skapa API-endpoints i `routes/`
- Använd `utils/` för delade verktyg

### Bidrag
1. Forka repot
2. Skapa en feature-branch
3. Följ den befintliga kodstilen
4. Lägg till tester för nya funktioner
5. Skapa en pull request

## Tilltänkta Förbättringar

- **Databas**: Migrera till PostgreSQL för bättre prestanda och skalbarhet
- **Autentisering**: Användarroller och rättighetsvalidering
- **Analytics**: Utökad dashboard med grafer och trendanalys
- **API**: REST API-dokumentation med OpenAPI/Swagger
- **Tester**: Omfattande test-suite med pytest
- **Deployment**: Docker-container och CI/CD-pipeline
- **Monitoring**: Hälsokontroller och prestanda-metrics

## Licens

Detta projekt är öppen källkod och tillgängligt under MIT-licensen.