import json
import os
import logging
from typing import Dict, Any
from utils.exceptions import FileOperationError, ValidationError


class SettingsService:
    """Service för att hantera dashboard-inställningar"""

    DEFAULT_SETTINGS = {
        "scale": 100,
        "columns": 3,
        "brandPriority": "",
        "compact": False,
        "horizontal": False,
        "brandsPerRow": 3,
        "sparePartsPerRow": 5
    }

    def __init__(self, settings_file: str, logger: logging.Logger):
        self.settings_file = settings_file
        self.logger = logger

    def get_settings(self) -> Dict[str, Any]:
        """
        Läser inställningar från fil eller returnerar standardinställningar.

        Returns:
            Dict med inställningar
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding='utf-8') as f:
                    settings = json.load(f)
                    self.logger.debug(f"Läste inställningar från {self.settings_file}")
                    return settings
            else:
                self.logger.info("Ingen settings-fil hittad, returnerar standardinställningar")
                return self.DEFAULT_SETTINGS.copy()
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON-fel vid läsning av {self.settings_file}: {e}")
            return self.DEFAULT_SETTINGS.copy()
        except Exception as e:
            self.logger.error(f"Fel vid läsning av {self.settings_file}: {e}")
            raise FileOperationError("read", self.settings_file, e)

    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validerar och sparar inställningar till fil.

        Args:
            settings: Dict med nya inställningar

        Returns:
            Dict med validerade och sparade inställningar

        Raises:
            ValidationError: Om inställningarna inte är giltiga
            FileOperationError: Om filskrivningen misslyckas
        """
        validated_settings = self._validate_and_sanitize(settings)

        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, "w", encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Dashboard-inställningar sparade: {validated_settings}")
            return validated_settings
        except Exception as e:
            self.logger.error(f"Fel vid skrivning till {self.settings_file}: {e}")
            raise FileOperationError("write", self.settings_file, e)

    def _validate_and_sanitize(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validerar och sanerar inställningar.

        Args:
            settings: Dict med inställningar att validera

        Returns:
            Dict med validerade inställningar

        Raises:
            ValidationError: Om inställningarna inte är giltiga
        """
        validated = {}

        # Validera scale
        if "scale" in settings:
            try:
                scale = int(settings["scale"])
                validated["scale"] = max(50, min(200, scale))
                if validated["scale"] != scale:
                    self.logger.warning(f"Scale justerad från {scale} till {validated['scale']}")
            except (ValueError, TypeError):
                raise ValidationError("scale", "Scale must be a valid integer between 50 and 200")
        else:
            validated["scale"] = self.DEFAULT_SETTINGS["scale"]

        # Validera columns
        if "columns" in settings:
            try:
                columns = int(settings["columns"])
                validated["columns"] = max(1, min(6, columns))
                if validated["columns"] != columns:
                    self.logger.warning(f"Columns justerad från {columns} till {validated['columns']}")
            except (ValueError, TypeError):
                raise ValidationError("columns", "Columns must be a valid integer between 1 and 6")
        else:
            validated["columns"] = self.DEFAULT_SETTINGS["columns"]

        # Validera brandPriority
        if "brandPriority" in settings:
            if isinstance(settings["brandPriority"], str):
                validated["brandPriority"] = settings["brandPriority"].strip()
            else:
                raise ValidationError("brandPriority", "BrandPriority must be a string")
        else:
            validated["brandPriority"] = self.DEFAULT_SETTINGS["brandPriority"]

        # Validera compact
        if "compact" in settings:
            if not isinstance(settings["compact"], bool):
                raise ValidationError("compact", "Compact must be a boolean value")
            validated["compact"] = settings["compact"]
        else:
            validated["compact"] = self.DEFAULT_SETTINGS["compact"]

        # Validera horizontal
        if "horizontal" in settings:
            if not isinstance(settings["horizontal"], bool):
                raise ValidationError("horizontal", "Horizontal must be a boolean value")
            validated["horizontal"] = settings["horizontal"]
        else:
            validated["horizontal"] = self.DEFAULT_SETTINGS["horizontal"]

        # Validera brandsPerRow
        if "brandsPerRow" in settings:
            try:
                brandsPerRow = int(settings["brandsPerRow"])
                validated["brandsPerRow"] = max(1, min(6, brandsPerRow))
                if validated["brandsPerRow"] != brandsPerRow:
                    self.logger.warning(f"BrandsPerRow justerad från {brandsPerRow} till {validated['brandsPerRow']}")
            except (ValueError, TypeError):
                raise ValidationError("brandsPerRow", "BrandsPerRow must be a valid integer between 1 and 6")
        else:
            validated["brandsPerRow"] = self.DEFAULT_SETTINGS["brandsPerRow"]

        # Validera sparePartsPerRow
        if "sparePartsPerRow" in settings:
            try:
                sparePartsPerRow = int(settings["sparePartsPerRow"])
                validated["sparePartsPerRow"] = max(1, min(10, sparePartsPerRow))
                if validated["sparePartsPerRow"] != sparePartsPerRow:
                    self.logger.warning(f"SparePartsPerRow justerad från {sparePartsPerRow} till {validated['sparePartsPerRow']}")
            except (ValueError, TypeError):
                raise ValidationError("sparePartsPerRow", "SparePartsPerRow must be a valid integer between 1 and 10")
        else:
            validated["sparePartsPerRow"] = self.DEFAULT_SETTINGS["sparePartsPerRow"]

        return validated