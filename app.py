from flask import Flask, render_template, jsonify
from datetime import datetime
import schedule
import time
import threading
import signal
import sys
import os

from config import get_config
from utils.logger import get_app_logger
from models.inventory import InventoryModel
from services.inventory_service import InventoryService
from services.backup_service import BackupService
from routes.inventory import create_inventory_routes
from routes.settings import create_settings_routes
from routes.logs import create_logs_routes

app = Flask(__name__)
config = get_config()
logger = get_app_logger(config.LOG_FILE)


def setup_signal_handlers():
    """Konfigurera signal handlers för graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Mottagen signal {signum}. Stänger av gracefully...")
        logger.info("Sparar eventuella pågående transaktioner...")
        logger.info("Flask-server stängs av")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Signal handlers konfigurerade för graceful shutdown")


def initialize_app():
    """Initialize the application components"""
    logger.info("Server Startas...")
    logger.info("Läser in modul: Filhantering")

    # Ensure directories exist
    config.__post_init__()

    logger.info("Kontrollerar databas...")
    if not os.path.exists(config.data_file):
        with open(config.data_file, "w", encoding='utf-8') as f:
            import json
            json.dump([], f)
        logger.info("Skapade ny databas: inventory.json")
    else:
        logger.info("Databas hittades: inventory.json")

    setup_signal_handlers()
    logger.info("Uppdateringslogik har flyttats till updater.py")

    return create_services()


def create_services():
    """Create and configure all services"""
    inventory_model = InventoryModel(config.data_file, config.CACHE_TTL_SECONDS)
    inventory_service = InventoryService(inventory_model, logger)
    backup_service = BackupService(config.DATA_DIR, config.BACKUP_DIR, logger)

    return inventory_service, backup_service


def schedule_backup(backup_service: BackupService):
    logger.info("Läser in modul: Backup-schemaläggare")
    schedule.every(2).days.at(config.BACKUP_SCHEDULE_TIME).do(backup_service.backup_database)
    logger.info("Startar modul: Backup-schemaläggare")
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler(backup_service: BackupService):
    scheduler_thread = threading.Thread(target=lambda: schedule_backup(backup_service), daemon=True)
    scheduler_thread.start()


@app.route("/")
def index():
    return render_template("index.html", current_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/admin")
def admin():
    return render_template("admin.html", current_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/dashboard")
def dashboard():
    logger.info("Renderar dashboard.html")
    return render_template("dashboard.html", current_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/changelog")
def changelog():
    logger.info("Renderar changelog.html")
    return render_template("changelog.html", current_date=datetime.now().strftime("%Y-%m-%d"))


@app.route("/api/check_version", methods=["GET"])
def check_version():
    """API endpoint för att kontrollera om updater.py körs"""
    try:
        if os.path.exists(config.LOCK_FILE):
            return jsonify({"update_needed": False, "message": "Uppdateringsprocess pågår redan"})
        else:
            return jsonify({"update_needed": False, "message": "Uppdateringar hanteras av updater.py. Kör 'python updater.py --check' för manuell kontroll."})
    except Exception as e:
        logger.error(f"Fel vid kontroll av uppdateringsstatus: {e}")
        return jsonify({"update_needed": False, "message": "Kunde inte kontrollera uppdateringsstatus"}), 500


def register_routes(inventory_service: InventoryService, backup_service: BackupService):
    """Register all route blueprints"""
    inventory_bp = create_inventory_routes(inventory_service)
    settings_bp = create_settings_routes(config.settings_file, logger)
    logs_bp = create_logs_routes(config.LOG_FILE, logger)

    app.register_blueprint(inventory_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(logs_bp)


if __name__ == "__main__":
    debug = '--debug' in sys.argv
    config.DEBUG = debug

    inventory_service, backup_service = initialize_app()
    register_routes(inventory_service, backup_service)

    logger.info("Läser in modul: Schemaläggning")
    start_scheduler(backup_service)
    logger.info("Servern är redo!")

    app.run(debug=debug, host=config.HOST, port=config.PORT)