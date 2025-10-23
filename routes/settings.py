from flask import Blueprint, request, jsonify
import logging
from services.settings_service import SettingsService
from utils.decorators import handle_errors

settings_bp = Blueprint('settings', __name__)


def create_settings_routes(settings_file: str, logger: logging.Logger):
    settings_service = SettingsService(settings_file, logger)

    @settings_bp.route("/api/settings", methods=["GET"])
    @handle_errors(logger)
    def get_settings():
        settings = settings_service.get_settings()
        return jsonify(settings)

    @settings_bp.route("/api/settings", methods=["POST"])
    @handle_errors(logger)
    def save_settings():
        new_settings = request.json
        if not new_settings:
            return jsonify({"error": "No settings provided"}), 400

        validated_settings = settings_service.save_settings(new_settings)
        return jsonify({"message": "Settings saved", "settings": validated_settings}), 200

    return settings_bp