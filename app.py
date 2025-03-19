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
import subprocess
import psutil

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
BACKUP_DIR = "db_backup"

# Hjälpfunktion för att bestämma status och åtgärd (din version)
def get_status_and_action(item):
    if item["quantity"] <= item["low_status"]:
        return "low", "Slakta enheter för att addera saldo"
    elif item["quantity"] >= item["high_status"]:
        return "high", "Ingen"
    else:
        return "mid", "Se över saldot"

def kill_processes_using_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.pid:
            try:
                proc = psutil.Process(conn.pid)
                proc.terminate()
                logger.info(f"Avslutade process {proc.pid} som använde port {port}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

def check_git_version(manual=False):
    try:
        logger.info("Startar versionsvalidering mot GitHub...")
        local_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        logger.info(f"Lokal commit-hash: {local_commit}")
        
        subprocess.run(["git", "fetch", "origin"], check=True)
        remote_commit = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
        logger.info(f"Remote commit-hash (GitHub): {remote_commit}")
        
        if local_commit != remote_commit:
            logger.warning("Lokala och remote versioner skiljer sig.")
            if manual:
                logger.info("Manuell kontroll hittade ny version. Förbereder omstart för uppdatering.")
                return {"update_needed": True, "message": "Ny version hittades. Servern startas om för att uppdatera."}
            status = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
            if status:
                logger.error("Lokala ändringar detekterade. Kan inte uppdatera automatiskt.")
                return False if not manual else {"update_needed": False, "message": "Lokala ändringar hindrar uppdatering."}
            logger.info("Kör 'git pull origin main'...")
            result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Uppdatering lyckades:\n" + result.stdout)
                logger.info("Startar om applikationen...")
                kill_processes_using_port(5000)
                subprocess.Popen([sys.executable, "app.py"], cwd=os.getcwd())
                sys.exit(0)
            else:
                logger.error("Misslyckades med att uppdatera:\n" + result.stderr)
                return False if not manual else {"update_needed": False, "message": "Uppdatering misslyckades."}
        else:
            logger.info("Lokala och remote versioner är identiska.")
            return True if not manual else {"update_needed": False, "message": "Ingen ny version hittades."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Fel vid Git-kommando: {e.output}")
        return False if not manual else {"update_needed": False, "message": "Fel vid versionskontroll."}
    except Exception as e:
        logger.error(f"Oväntat fel vid versionsvalidering: {str(e)}")
        return False if not manual else {"update_needed": False, "message": "Ett oväntat fel inträffade."}

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

if not check_git_version():
    logger.error("Versionsvalidering misslyckades vid uppstart. Startar med lokal version.")

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
        with open('app.log', 'r', encoding='utf-8') as f:
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
    result = check_git_version(manual=True)
    if result["update_needed"]:
        logger.info("Ny version hittades via manuell kontroll. Kör git pull och startar om servern.")
        try:
            pull_result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            if pull_result.returncode == 0:
                logger.info("Uppdatering lyckades:\n" + pull_result.stdout)
                response = Response(
                    json.dumps({"update_needed": True, "message": "Ny version hittades. Servern startas om för att uppdatera."}),
                    status=200,
                    mimetype='application/json'
                )
                def restart_server():
                    time.sleep(1)
                    kill_processes_using_port(5000)
                    subprocess.Popen(['cmd.exe', '/k', sys.executable, 'app.py'], cwd=os.getcwd())
                    sys.exit(0)
                threading.Thread(target=restart_server, daemon=True).start()
                return response
            else:
                logger.error("Misslyckades med att uppdatera:\n" + pull_result.stderr)
                result = {"update_needed": False, "message": "Uppdatering misslyckades."}
        except Exception as e:
            logger.error(f"Fel vid manuell uppdatering: {str(e)}")
            result = {"update_needed": False, "message": "Ett oväntat fel inträffade vid uppdatering."}
    return jsonify(result)

if __name__ == "__main__":
    debug = '--debug' in sys.argv
    logger.info("Läser in modul: Schemaläggning")
    start_scheduler()
    logger.info("Servern är redo!")
    app.run(debug=debug, host="0.0.0.0", port=5000)