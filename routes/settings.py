from flask import Blueprint, request, jsonify
import json
import os
import logging
from utils.validation import SettingsValidator
from utils.exceptions import InventoryError

settings_bp = Blueprint('settings', __name__)


def create_settings_routes(settings_file: str, logger: logging.Logger):
    def read_settings():
        try:
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            else:
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
            with open(settings_file, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("Dashboard-inställningar sparade")
        except Exception as e:
            logger.error(f"Fel vid skrivning till dashboard_settings.json: {e}")
            raise e

    @settings_bp.route("/api/settings", methods=["GET"])
    def get_settings():
        try:
            settings = read_settings()
            return jsonify(settings)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @settings_bp.route("/api/settings", methods=["POST"])
    def save_settings():
        try:
            new_settings = request.json
            if not new_settings:
                return jsonify({"error": "No settings provided"}), 400

            validation_result = SettingsValidator.validate_settings(new_settings)
            if validation_result.has_errors():
                return jsonify({"error": "Validation failed", "details": validation_result.get_error_messages()}), 400

            valid_settings = {
                "scale": int(new_settings.get("scale", 100)),
                "columns": int(new_settings.get("columns", 3)),
                "compact": bool(new_settings.get("compact", False))
            }

            valid_settings["scale"] = max(50, min(200, valid_settings["scale"]))
            valid_settings["columns"] = max(1, min(6, valid_settings["columns"]))

            write_settings(valid_settings)
            logger.info(f"Dashboard-inställningar uppdaterade: {valid_settings}")
            return jsonify({"message": "Settings saved", "settings": valid_settings}), 200

        except InventoryError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Fel vid sparning av inställningar: {e}")
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    return settings_bp