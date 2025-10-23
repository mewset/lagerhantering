from functools import wraps
from flask import jsonify
import logging
from utils.exceptions import InventoryError, ValidationError


def handle_errors(logger: logging.Logger = None):
    """
    Decorator för att hantera fel i route handlers.

    Args:
        logger: Optional logger för att logga fel

    Returns:
        Decorator funktion
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                if logger:
                    logger.warning(f"Validation error in {func.__name__}: {str(e)}")
                return jsonify({"error": "Validation failed", "details": str(e)}), 400
            except InventoryError as e:
                if logger:
                    logger.error(f"Inventory error in {func.__name__}: {str(e)}")
                return jsonify({"error": str(e)}), 400
            except Exception as e:
                if logger:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                return jsonify({"error": "Internal server error", "details": str(e)}), 500
        return wrapper
    return decorator