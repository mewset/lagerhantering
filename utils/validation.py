from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class ValidationError:
    field: str
    message: str
    value: Any = None


class ValidationResult:
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.is_valid = True

    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(ValidationError(field, message, value))
        self.is_valid = False

    def has_errors(self) -> bool:
        return not self.is_valid

    def get_error_messages(self) -> Dict[str, str]:
        return {error.field: error.message for error in self.errors}


class InventoryItemValidator:
    @staticmethod
    def validate_add_item(data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("data", "Request data must be a JSON object")
            return result

        brand = data.get("Brand", "")
        if not isinstance(brand, str):
            result.add_error("Brand", "Brand must be a string")

        product_family = data.get("product_family", "")
        if not isinstance(product_family, str) or not product_family.strip():
            result.add_error("product_family", "Product family is required and must be a non-empty string")

        spare_part = data.get("spare_part", "")
        if not isinstance(spare_part, str) or not spare_part.strip():
            result.add_error("spare_part", "Spare part is required and must be a non-empty string")

        quantity = data.get("quantity")
        if quantity is None:
            result.add_error("quantity", "Quantity is required")
        else:
            try:
                quantity_int = int(quantity)
                if quantity_int < 0:
                    result.add_error("quantity", "Quantity must be non-negative")
            except (ValueError, TypeError):
                result.add_error("quantity", "Quantity must be a valid integer")

        low_status = data.get("low_status")
        if low_status is not None:
            try:
                low_status_int = int(low_status)
                if low_status_int < 0:
                    result.add_error("low_status", "Low status must be non-negative")
            except (ValueError, TypeError):
                result.add_error("low_status", "Low status must be a valid integer")

        high_status = data.get("high_status")
        if high_status is not None:
            try:
                high_status_int = int(high_status)
                if high_status_int < 0:
                    result.add_error("high_status", "High status must be non-negative")

                if (low_status is not None and high_status is not None and
                    isinstance(low_status, (int, str)) and isinstance(high_status, (int, str))):
                    try:
                        if int(high_status) <= int(low_status):
                            result.add_error("high_status", "High status must be greater than low status")
                    except (ValueError, TypeError):
                        pass
            except (ValueError, TypeError):
                result.add_error("high_status", "High status must be a valid integer")

        return result

    @staticmethod
    def validate_update_item(data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("data", "Request data must be a JSON object")
            return result

        if not data:
            result.add_error("data", "At least one field must be provided for update")
            return result

        if "Brand" in data and not isinstance(data["Brand"], str):
            result.add_error("Brand", "Brand must be a string")

        if "product_family" in data:
            if not isinstance(data["product_family"], str) or not data["product_family"].strip():
                result.add_error("product_family", "Product family must be a non-empty string")

        if "spare_part" in data:
            if not isinstance(data["spare_part"], str) or not data["spare_part"].strip():
                result.add_error("spare_part", "Spare part must be a non-empty string")

        if "quantity" in data:
            try:
                quantity_int = int(data["quantity"])
                if quantity_int < 0:
                    result.add_error("quantity", "Quantity must be non-negative")
            except (ValueError, TypeError):
                result.add_error("quantity", "Quantity must be a valid integer")

        if "low_status" in data:
            try:
                low_status_int = int(data["low_status"])
                if low_status_int < 0:
                    result.add_error("low_status", "Low status must be non-negative")
            except (ValueError, TypeError):
                result.add_error("low_status", "Low status must be a valid integer")

        if "high_status" in data:
            try:
                high_status_int = int(data["high_status"])
                if high_status_int < 0:
                    result.add_error("high_status", "High status must be non-negative")
            except (ValueError, TypeError):
                result.add_error("high_status", "High status must be a valid integer")

        return result

    @staticmethod
    def validate_subtract_quantity(data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("data", "Request data must be a JSON object")
            return result

        quantity = data.get("quantity", 1)
        try:
            quantity_int = int(quantity)
            if quantity_int <= 0:
                result.add_error("quantity", "Quantity to subtract must be positive")
        except (ValueError, TypeError):
            result.add_error("quantity", "Quantity must be a valid integer")

        return result


class SettingsValidator:
    @staticmethod
    def validate_settings(data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()

        if not isinstance(data, dict):
            result.add_error("data", "Request data must be a JSON object")
            return result

        if "scale" in data:
            try:
                scale = int(data["scale"])
                if scale < 50 or scale > 200:
                    result.add_error("scale", "Scale must be between 50 and 200")
            except (ValueError, TypeError):
                result.add_error("scale", "Scale must be a valid integer")

        if "columns" in data:
            try:
                columns = int(data["columns"])
                if columns < 1 or columns > 6:
                    result.add_error("columns", "Columns must be between 1 and 6")
            except (ValueError, TypeError):
                result.add_error("columns", "Columns must be a valid integer")

        if "compact" in data:
            if not isinstance(data["compact"], bool):
                result.add_error("compact", "Compact must be a boolean value")

        return result