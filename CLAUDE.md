# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Development mode**: `python app.py --debug`
- **Production mode**: `python app.py`
- **Install dependencies**: `pip install -r requirements.txt`
- **Test updater manually**: `python updater.py --check`
- **Run updater as daemon**: `python updater.py --daemon`

### Windows Batch Scripts
- **Start updater daemon**: `start_updater_daemon.bat`
- **Test updater**: `test_updater.bat`

## Architecture Overview

This is a Flask-based inventory management system for spare parts with automatic updates and backup functionality.

### Core Components

**Main Application (`app.py`)**
- Flask web server running on port 5000
- RESTful API endpoints under `/api/`
- Template-based web interface with Bootstrap styling
- Automatic database backups every 2 days at 17:00 (weekdays only)
- Graceful shutdown handling with signal handlers

**Auto-Updater Service (`updater.py`)**
- Standalone service for automatic GitHub updates
- Weekly update checks (Mondays at 02:00)
- Git-based version control with backup functionality
- Process management for graceful app restarts
- Can run as daemon or manual checks

### Data Structure

**Primary Data Store**: JSON-based inventory system
- **Location**: `data/inventory.json`
- **Backup Directory**: `db_backup/`
- **Version Backups**: `version_backup/`

**Inventory Item Schema**:
```json
{
  "id": "unique_timestamp_id",
  "Brand": "string",
  "product_family": "string",
  "spare_part": "string",
  "quantity": "integer",
  "low_status": "integer",
  "high_status": "integer"
}
```

### API Endpoints Structure

- `GET /api/inventory` - Retrieve all items
- `POST /api/inventory` - Add new item or update quantity
- `POST /api/inventory/<id>/subtract` - Subtract quantity
- `PATCH /api/inventory/<id>` - Update item properties
- `DELETE /api/inventory/<id>` - Remove item
- `GET/POST /api/settings` - Dashboard configuration
- `GET /api/check_version` - Update status check

### Web Interface Pages

- **`/`**: Main inventory interface (add/remove items)
- **`/admin`**: Administrative interface for managing items
- **`/dashboard`**: Visual status overview with color-coded quantities
- **`/logs`**: System log viewer with pagination and filtering

### Status Logic

Items are automatically classified based on quantity thresholds:
- **Low status**: `quantity <= low_status` (red, action: "Slakta enheter för att addera saldo")
- **High status**: `quantity >= high_status` (green, action: "Ingen")
- **Mid status**: Between thresholds (yellow, action: "Se över saldot")

### File Organization

```
├── app.py              # Main Flask application
├── updater.py          # Auto-update service
├── requirements.txt    # Python dependencies
├── data/               # Data storage directory
│   ├── inventory.json  # Main inventory database
│   └── dashboard_settings.json # UI settings
├── templates/          # HTML templates
├── static/             # CSS/JS assets
├── db_backup/          # Automatic database backups
└── version_backup/     # Code version backups
```

### Logging

All operations are logged to `app.log` with structured format including:
- Inventory changes with before/after states
- Status classifications and recommended actions
- System events and errors
- Update process activities (logged to `updater.log`)

### Dependencies

- **Flask 3.0.3**: Web framework
- **schedule 1.2.2**: Task scheduling
- **psutil**: Process management (updater only)
- Standard library modules for file handling, datetime, threading

### Auto-Update Mechanism

The application uses Git for version control and automatic updates:
1. Weekly checks compare local vs remote commits
2. Creates backups before updating
3. Gracefully stops app.py, pulls changes, restarts
4. Lock file prevents concurrent updates
5. Stashes local changes if necessary