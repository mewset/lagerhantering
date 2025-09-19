from flask import Blueprint, request, jsonify
from services.inventory_service import InventoryService
from utils.validation import InventoryItemValidator
from utils.exceptions import InventoryError, ValidationError

inventory_bp = Blueprint('inventory', __name__)


def create_inventory_routes(inventory_service: InventoryService):
    @inventory_bp.route("/api/inventory", methods=["GET"])
    def get_inventory():
        try:
            inventory = inventory_service.get_all_items()
            return jsonify([item.to_dict() for item in inventory])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @inventory_bp.route("/api/inventory", methods=["POST"])
    def add_item():
        try:
            item_data = request.json
            if not item_data:
                return jsonify({"error": "No data provided"}), 400

            validation_result = InventoryItemValidator.validate_add_item(item_data)
            if validation_result.has_errors():
                return jsonify({"error": "Validation failed", "details": validation_result.get_error_messages()}), 400

            item, success, message = inventory_service.add_or_update_item(item_data)

            if success:
                return jsonify({"message": message, "item": item.to_dict()}), 201 if "added" in message else 200
            else:
                return jsonify({"error": message}), 500

        except InventoryError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    @inventory_bp.route("/api/inventory/<int:item_id>/subtract", methods=["POST"])
    def subtract_item(item_id):
        try:
            request_data = request.json or {}
            validation_result = InventoryItemValidator.validate_subtract_quantity(request_data)
            if validation_result.has_errors():
                return jsonify({"error": "Validation failed", "details": validation_result.get_error_messages()}), 400

            quantity_to_subtract = int(request_data.get("quantity", 1))
            item, success, message = inventory_service.subtract_quantity(item_id, quantity_to_subtract)

            if success:
                return jsonify({"message": message, "item": item.to_dict()}), 200
            else:
                status_code = 404 if "not found" in message.lower() else 500
                return jsonify({"error": message}), status_code

        except InventoryError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    @inventory_bp.route("/api/inventory/<int:item_id>", methods=["PATCH"])
    def update_item(item_id):
        try:
            updates = request.json
            if not updates:
                return jsonify({"error": "No updates provided"}), 400

            validation_result = InventoryItemValidator.validate_update_item(updates)
            if validation_result.has_errors():
                return jsonify({"error": "Validation failed", "details": validation_result.get_error_messages()}), 400

            item, success, message = inventory_service.update_item(item_id, updates)

            if success:
                return jsonify({"message": message, "item": item.to_dict()}), 200
            else:
                status_code = 404 if "not found" in message.lower() else 500
                return jsonify({"error": message}), status_code

        except InventoryError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    @inventory_bp.route("/api/inventory/<int:item_id>", methods=["DELETE"])
    def delete_item(item_id):
        try:
            success, message = inventory_service.delete_item(item_id)

            if success:
                return jsonify({"message": message}), 200
            else:
                status_code = 404 if "not found" in message.lower() else 500
                return jsonify({"error": message}), status_code

        except InventoryError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    return inventory_bp