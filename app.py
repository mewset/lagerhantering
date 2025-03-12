from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import schedule
import time
import threading
import shutil
import logging

app = Flask(__name__)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "inventory.json")
BACKUP_DIR = "db_backup"

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
    return render_template("dashboard.html", current_date=datetime.now().strftime("%Y-%m-%d"))

@app.route("/logs")
def logs():
    try:
        with open('app.log', 'r') as f:
            log_lines = f.readlines()
        return render_template("logs.html", logs=log_lines, current_date=datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        logger.error(f"Fel vid läsning av loggar: {e}")
        return render_template("logs.html", logs=[], current_date=datetime.now().strftime("%Y-%m-%d"))

@app.route("/api/inventory", methods=["GET"])
def get_inventory():
    return jsonify(read_inventory())

@app.route("/api/inventory", methods=["POST"])
def add_item():
    inventory = read_inventory()
    new_item = request.json
    for item in inventory:
        if item["product_family"] == new_item["product_family"] and item["spare_part"] == new_item["spare_part"]:
            old_quantity = item["quantity"]
            item["quantity"] += int(new_item["quantity"])
            write_inventory(inventory)
            logger.info(f"Lade till {new_item['quantity']} {new_item['spare_part']} till {new_item['product_family']} (tidigare: {old_quantity}, nu: {item['quantity']})")
            return jsonify({"message": "Quantity updated"}), 200
    new_item["id"] = int(new_item.get("id", 0)) or max([item["id"] for item in inventory] + [0]) + 1
    new_item["low_status"] = new_item.get("low_status", 5)
    new_item["high_status"] = new_item.get("high_status", 15)  # Tagit bort mid_status
    inventory.append(new_item)
    write_inventory(inventory)
    logger.info(f"Lade till ny post: {new_item['quantity']} {new_item['spare_part']} till {new_item['product_family']}")
    return jsonify({"message": "Item added"}), 201

@app.route("/api/inventory/<int:item_id>/subtract", methods=["POST"])
def subtract_item(item_id):
    inventory = read_inventory()
    quantity_to_subtract = int(request.json.get("quantity", 1))
    for item in inventory:
        if item["id"] == item_id:
            old_quantity = item["quantity"]
            item["quantity"] -= quantity_to_subtract
            if item["quantity"] <= 0:
                inventory.remove(item)
                logger.info(f"Tog bort {item['spare_part']} från {item['product_family']} (antal blev <= 0)")
            else:
                logger.info(f"Subtraherade {quantity_to_subtract} {item['spare_part']} från {item['product_family']} (tidigare: {old_quantity}, nu: {item['quantity']})")
            write_inventory(inventory)
            return jsonify({"message": "Quantity subtracted"}), 200
    logger.warning(f"Försökte subtrahera från ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

@app.route("/api/inventory/<int:item_id>", methods=["PATCH"])
def update_item(item_id):
    inventory = read_inventory()
    updates = request.json
    for item in inventory:
        if item["id"] == item_id:
            old_quantity = item["quantity"]
            if "quantity" in updates:
                item["quantity"] = int(updates["quantity"])
            if "low_status" in updates:
                item["low_status"] = int(updates["low_status"])
            if "high_status" in updates:
                item["high_status"] = int(updates["high_status"]) 
            if item["quantity"] <= 0:
                inventory.remove(item)
                logger.info(f"Tog bort {item['spare_part']} från {item['product_family']} (antal blev <= 0 efter uppdatering)")
            else:
                logger.info(f"Uppdaterade {item['spare_part']} i {item['product_family']} (antal ändrat från {old_quantity} till {item['quantity']})")
            write_inventory(inventory)
            return jsonify({"message": "Item updated"}), 200
    logger.warning(f"Försökte uppdatera ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

@app.route("/api/inventory/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    inventory = read_inventory()
    original_len = len(inventory)
    for item in inventory:
        if item["id"] == item_id:
            inventory.remove(item)
            logger.info(f"Raderade {item['spare_part']} från {item['product_family']} (ID: {item_id})")
            write_inventory(inventory)
            return jsonify({"message": "Item deleted"}), 200
    logger.warning(f"Försökte radera ID {item_id} som inte finns")
    return jsonify({"message": "Item not found"}), 404

if __name__ == "__main__":
    import sys
    debug = '--debug' in sys.argv
    logger.info("Läser in modul: Schemaläggning")
    start_scheduler()
    logger.info("Servern är redo!")
    app.run(debug=debug, host="0.0.0.0", port=5000)