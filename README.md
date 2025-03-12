# Lagerhantering

En enkel Flask-baserad webbapplikation för att hantera ett lager av reservdelar. Inkluderar funktioner för att lägga till och ta bort reservdelar, visa lagerstatus i en dashboard, automatiska backuper, loggning av händelser och automatisk versionsvalidering mot GitHub.

## Funktioner
- **Huvudsida (`/`)**: Lägg till eller ta bort reservdelar och visa aktuellt lager. Reservdelar behålls med antal 0 vid subtraktion, men kan raderas manuellt.
- **Admin-sida (`/admin`)**: Hantera lagerposter (lägg till, uppdatera, radera) med bekräftelsedialog vid radering.
- **Dashboard (`/dashboard`)**: Översikt av lagerstatus med färgkodning (rött för lågt, gult för mellan, grönt för högt). Visar endast reservdelar med antal > 0.
- **Loggar (`/logs`)**: Visa systemloggar med paginering och filter för nivå (ERROR, WARNING, INFO) och datum.
- **Backup**: Automatiska backuper av lagerdatan varannan dag kl. 17:00 (mån-fre) till `db_backup/`.
- **Versionsvalidering**: Vid uppstart jämförs lokal version med GitHub (`origin/main`). Om en nyare version finns, körs `git pull` och appen startas om automatiskt.

### Designförändringar
- Footern har tagits bort från huvudsida och admin-sida för en renare och mer funktionell användarupplevelse.

## Krav
- **Python**: 3.8 eller senare
- **Beroenden**: Flask, schedule (installeras via `requirements.txt`)
- **Git**: Krävs för versionsvalidering och automatiska uppdateringar

## Installation
Följ dessa steg för att köra applikationen lokalt eller i produktion:

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

## Tilltänkta Förbättringar
- Migrera till en SQL lösning, tex. PostGreSQL för databas och loggning.
- Användarroller och rättighetsvalidering
- Utökad loggningsfunktionalitet
- Utökning av Dashboard att visa tex. grafer och liknande analytiska verktyg
- Centraliserad databaslösning (Azure/AWS) för att kunna ha flera siter som kör applikationen (med multipla databaser beroende på site, rättighetsvalidering för att koppla till relevat databas)

## Utveckling
- För att bidra, skapa en pull request med ändringar