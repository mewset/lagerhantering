from flask import Flask, render_template, request, jsonify, Response
import json
import os
import sys
from datetime import datetime
import schedule
import time
import threading
import shutil
import logging
import signal

app = Flask(__name__)

# Konfigurera loggning
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "inventory.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "dashboard_settings.json")
BACKUP_DIR = "db_backup"

# Hjälpfunktion för att bestämma status och åtgärd
def get_status_and_action(item):
    if item["quantity"] <= item["low_status"]:
        return "low", "Slakta enheter för att addera saldo"
    elif item["quantity"] >= item["high_status"]:
        return "high", "Ingen"
    else:
        return "mid", "Se över saldot"

# Graceful shutdown hantering
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

logger.info("Server Startas...")
logger.info("Läser in modul: Filhantering")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

logger.info("Kontrollerar databas...")
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)
    logger.info("Skapade ny databas: inventory.json")
else:
    logger.info("Databas hittades: inventory.json")

# Konfigurera graceful shutdown
setup_signal_handlers()
logger.info("Uppdateringslogik har flyttats till updater.py")

def read_inventory():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fel vid läsning av inventory.json: {e}")
        return []

def write_inventory(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Fel vid skrivning till inventory.json: {e}")

def read_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        else:
            # Standardinställningar
            return {
                "scale": 100,
                "columns": 3,
                "compact": False
            }
    except Exception as e:
        logger.error(f"Fel vid läsning av dashboard_settings.json: {e}")
        return {
            "scale": 100,
            "columns": 3,
            "compact": False
        }

def write_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        logger.info("Dashboard-inställningar sparade")
    except Exception as e:
        logger.error(f"Fel vid skrivning till dashboard_settings.json: {e}")

def backup_database():
    try:
        now = datetime.now()
        if now.weekday() < 5:
            timestamp = now.strftime("%Y-%m-%d-%H%M")
            backup_filename = f"inventory-{timestamp}.json"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            shutil.copy(DATA_FILE, backup_path)
            logger.info(f"Skapade backup: {backup_filename}")
            backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith("inventory-") and f.endswith(".json")]
            if len(backup_files) > 5:
                backup_files.sort(key=lambda x: os.path.getctime(os.path.join(BACKUP_DIR, x)))
                for old_backup in backup_files[:-5]:
                    os.remove(os.path.join(BACKUP_DIR, old_backup))
                    logger.info(f"Tog bort gammal backup: {old_backup}")
    except Exception as e:
        logger.error(f"Fel vid backup: {e}")

def schedule_backup():
    logger.info("Läser in modul: Backup-schemaläggare")
    schedule.every(2).days.at("17:00").do(backup_database)
    logger.info("Startar modul: Backup-schemaläggare")
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_backup, daemon=True)
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

@app.route("/logs")
def logs():
    try:
        with open('app.log', 'r', encoding='utf-8', errors='replace') as f:
            log_lines = f.readlines()
        if request.args.get('format') == 'json':
            return jsonify({"logs": log_lines})
        return render_template("logs.html", logs=log_lines, current_date=datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        logger.error(f"Fel vid läsning av loggar: {e}")
        if request.args.get('format') == 'json':
            return jsonify({"logs": [], "error": str(e)}), 500
        return render_template("logs.html", logs=[], current_date=datetime.now().strftime("%Y-%m-%d"))

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    inventory = read_inventory()
    for item in inventory:
        status, action = get_status_and_action(item)
        logger.info(f"Inventory status: ID={item['id']}, Brand={item.get('Brand', 'N/A')}, ProductFamily={item['product_family']}, SparePart={item['spare_part']}, Quantity={item['quantity']}, Status={status}, Action={action}")
    return jsonify(inventory)

@app.route("/api/inventory", methods=["POST"])
def add_item():
    inventory = read_inventory()
    new_item = request.json
    for item in inventory:
        if item["product_family"] == new_item["product_family"] and item["spare_part"] == new_item["spare_part"]:
            old_quantity = item["quantity"]
            item["quantity"] += int(new_item["quantity"])
            write_inventory(inventory)
            status, action = get_status_and_action(item)
            logger.info(f"Updated quantity: ID={item['id']}, Brand={item.get('Brand', 'N/A')}, ProductFamily={item['product_family']}, SparePart={item['spare_part']}, OldQuantity={old_quantity}, NewQuantity={item['quantity']}, Status={status}, Action={action}")
            return jsonify({"message": "Quantity updated"}), 200
    new_item["id"] = int(new_item.get("id", 0)) or max([item["id"] for item in inventory] + [0]) + 1
    new_item["low_status"] = new_item.get("low_status", 5)
    new_item["high_status"] = new_item.get("high_status", 15)
    inventory.append(new_item)
    write_inventory(inventory)
    status, action = get_status_and_action(new_item)
    logger.info(f"Added item: ID={new_item['id']}, Brand={new_item.get('Brand', 'N/A')}, ProductFamily={new_item['product_family']}, SparePart={new_item['spare_part']}, Quantity={new_item['quantity']}, Status={status}, Action={action}")
    return jsonify({"message": "Item added"}), 201

@app.route("/api/inventory/<int:item_id>/subtract", methods=["POST"])
def subtract_item(item_id):
    inventory = read_inventory()
    quantity_to_subtract = int(request.json.get("quantity", 1))
    for item in inventory:
        if item["id"] == item_id:
            old_quantity = item["quantity"]
            item["quantity"] = max(0, item["quantity"] - quantity_to_subtract)
            write_inventory(inventory)
            status, action = get_status_and_action(item)
            logger.info(f"Subtracted quantity: ID={item['id']}, Brand={item.get('Brand', 'N/A')}, ProductFamily={item['product_family']}, SparePart={item['spare_part']}, OldQuantity={old_quantity}, NewQuantity={item['quantity']}, Status={status}, Action={action}")
            return jsonify({"message": "Quantity subtracted"}), 200
    logger.warning(f"Försökte subtrahera från ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

@app.route("/api/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    inventory = read_inventory()
    updates = request.json
    for item in inventory:
        if item["id"] == item_id:
            old_values = item.copy()
            if "Brand" in updates:
                item["Brand"] = updates["Brand"]
            if "product_family" in updates:
                item["product_family"] = updates["product_family"]
            if "spare_part" in updates:
                item["spare_part"] = updates["spare_part"]
            if "quantity" in updates:
                item["quantity"] = max(0, int(updates["quantity"]))
            if "low_status" in updates:
                item["low_status"] = int(updates["low_status"])
            if "high_status" in updates:
                item["high_status"] = int(updates["high_status"])
            write_inventory(inventory)
            status, action = get_status_and_action(item)
            changes = {k: f"Old={old_values[k]}, New={item[k]}" for k in updates.keys()}
            logger.info(f"Updated item: ID={item_id}, Brand={item.get('Brand', 'N/A')}, ProductFamily={item['product_family']}, SparePart={item['spare_part']}, Changes={changes}, Status={status}, Action={action}")
            return jsonify({"message": "Item updated"}), 200
    logger.warning(f"Försökte uppdatera ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

@app.route("/api/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    inventory = read_inventory()
    for item in inventory:
        if item["id"] == item_id:
            status, action = get_status_and_action(item)
            logger.info(f"Deleted item: ID={item_id}, Brand={item.get('Brand', 'N/A')}, ProductFamily={item['product_family']}, SparePart={item['spare_part']}, Quantity={item['quantity']}, Status={status}, Action={action}")
            inventory.remove(item)
            write_inventory(inventory)
            return jsonify({"message": "Item deleted"}), 200
    logger.warning(f"Försökte radera ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

@app.route("/api/check_version", methods=["GET"])
def check_version():
    """API endpoint för att kontrollera om updater.py körs"""
    try:
        # Kontrollera om updater.py lock file existerar
        if os.path.exists("updater.lock"):
            return jsonify({"update_needed": False, "message": "Uppdateringsprocess pågår redan"})
        else:
            return jsonify({"update_needed": False, "message": "Uppdateringar hanteras av updater.py. Kör 'python updater.py --check' för manuell kontroll."})
    except Exception as e:
        logger.error(f"Fel vid kontroll av uppdateringsstatus: {e}")
        return jsonify({"update_needed": False, "message": "Kunde inte kontrollera uppdateringsstatus"}), 500

@app.route("/api/settings", methods=["GET"])
def get_settings():
    settings = read_settings()
    return jsonify(settings)

@app.route("/api/settings", methods=["POST"])
def save_settings():
    try:
        new_settings = request.json
        
        # Validera inställningar
        valid_settings = {
            "scale": int(new_settings.get("scale", 100)),
            "columns": int(new_settings.get("columns", 3)),
            "compact": bool(new_settings.get("compact", False))
        }
        
        # Begränsa värden till rimliga intervall
        valid_settings["scale"] = max(50, min(200, valid_settings["scale"]))
        valid_settings["columns"] = max(1, min(6, valid_settings["columns"]))
        
        write_settings(valid_settings)
        logger.info(f"Dashboard-inställningar uppdaterade: {valid_settings}")
        return jsonify({"message": "Settings saved", "settings": valid_settings}), 200
        
    except Exception as e:
        logger.error(f"Fel vid sparning av inställningar: {e}")
        return jsonify({"message": "Failed to save settings", "error": str(e)}), 500

if __name__ == "__main__":
    debug = '--debug' in sys.argv
    logger.info("Läser in modul: Schemaläggning")
    start_scheduler()
    logger.info("Servern är redo!")
    app.run(debug=debug, host="0.0.0.0", port=5000)