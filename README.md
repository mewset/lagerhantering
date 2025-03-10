# Lagerhantering

En enkel Flask-baserad webbapplikation för att hantera ett lager av reservdelar. Inkluderar funktioner för att lägga till/ta bort reservdelar, visa lagerstatus i en dashboard, automatiska backuper och en loggsida för att spåra händelser.

## Funktioner
- **Huvudsida (`/`)**: Lägg till eller ta bort reservdelar och visa aktuellt lager.
- **Admin-sida (`/admin`)**: Hantera lagerposter (lägg till, uppdatera, radera).
- **Dashboard (`/dashboard`)**: Översikt av lagerstatus med färgkodning (rött för lågt, gult för mellan, grönt för högt).
- **Loggar (`/logs`)**: Visa systemloggar med paginering och filter för nivå (ERROR, WARNING, INFO) och datum.
- **Backup**: Automatiska backuper av lagerdatan varannan dag kl. 17:00 (Mån-Fre) till `db_backup/`.

## Krav
- **Python**: 3.8 eller senare
- **Beroenden**: Flask, schedule (anges i `requirements.txt`)

## Installation
Följ dessa steg för att köra applikationen lokalt:

1. **Klona repot**:
   ```bash
   git clone https://github.com/mewset/lagerhantering.git
   cd lagerhantering

2. **Skapa en virtuell miljö (valfritt, men rekommenderat)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows

3. **Installera beroenden**:
    ```bash
    pip install -r requirements.txt

4. **Kör Applikationen**:
- För produktion (utan debug)
    ```bash
    python app.py
- För utveckling (med debug)
    ```bash
    python app.py --debug

5. Öppna en webbläsare och gå till: http://localhost:5000/.

