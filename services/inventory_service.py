from typing import List, Optional, Tuple, Dict, Any
import logging
from dataclasses import dataclass

from models.inventory import InventoryModel, InventoryItem


@dataclass
class StatusInfo:
    status: str
    action: str


class InventoryService:
    def __init__(self, inventory_model: InventoryModel, logger: logging.Logger):
        self.inventory_model = inventory_model
        self.logger = logger

    def get_status_and_action(self, item: InventoryItem) -> StatusInfo:
        if item.quantity <= item.low_status:
            return StatusInfo("low", "Slakta enheter för att addera saldo")
        elif item.quantity >= item.high_status:
            return StatusInfo("high", "Ingen")
        else:
            return StatusInfo("mid", "Se över saldot")

    def get_all_items(self) -> List[InventoryItem]:
        items = self.inventory_model.get_all()
        for item in items:
            status_info = self.get_status_and_action(item)
            self._log_item_status(item, status_info)
        return items

    def get_item_by_id(self, item_id: int) -> Optional[InventoryItem]:
        return self.inventory_model.get_by_id(item_id)

    def add_or_update_item(self, item_data: Dict[str, Any]) -> Tuple[InventoryItem, bool, str]:
        try:
            new_item = InventoryItem.from_dict(item_data)

            existing_item = self.inventory_model.find_by_product(
                new_item.product_family,
                new_item.spare_part
            )

            if existing_item:
                old_quantity = existing_item.quantity
                existing_item.quantity += new_item.quantity

                if self.inventory_model.update(existing_item):
                    status_info = self.get_status_and_action(existing_item)
                    self.logger.info(
                        f"Updated quantity: ID={existing_item.id}, "
                        f"Brand={existing_item.Brand}, "
                        f"ProductFamily={existing_item.product_family}, "
                        f"SparePart={existing_item.spare_part}, "
                        f"OldQuantity={old_quantity}, "
                        f"NewQuantity={existing_item.quantity}, "
                        f"Status={status_info.status}, "
                        f"Action={status_info.action}"
                    )
                    return existing_item, True, "Quantity updated"
                else:
                    return existing_item, False, "Failed to update quantity"
            else:
                if new_item.id == 0:
                    new_item.low_status = new_item.low_status or 5
                    new_item.high_status = new_item.high_status or 15

                added_item = self.inventory_model.add(new_item)
                status_info = self.get_status_and_action(added_item)
                self.logger.info(
                    f"Added item: ID={added_item.id}, "
                    f"Brand={added_item.Brand}, "
                    f"ProductFamily={added_item.product_family}, "
                    f"SparePart={added_item.spare_part}, "
                    f"Quantity={added_item.quantity}, "
                    f"Status={status_info.status}, "
                    f"Action={status_info.action}"
                )
                return added_item, True, "Item added"

        except Exception as e:
            self.logger.error(f"Error adding/updating item: {e}")
            raise

    def subtract_quantity(self, item_id: int, quantity_to_subtract: int = 1) -> Tuple[Optional[InventoryItem], bool, str]:
        try:
            item = self.inventory_model.get_by_id(item_id)
            if not item:
                self.logger.warning(f"Försökte subtrahera från ID {item_id} som inte finns")
                return None, False, "Item not found"

            old_quantity = item.quantity
            item.quantity = max(0, item.quantity - quantity_to_subtract)

            if self.inventory_model.update(item):
                status_info = self.get_status_and_action(item)
                self.logger.info(
                    f"Subtracted quantity: ID={item.id}, "
                    f"Brand={item.Brand}, "
                    f"ProductFamily={item.product_family}, "
                    f"SparePart={item.spare_part}, "
                    f"OldQuantity={old_quantity}, "
                    f"NewQuantity={item.quantity}, "
                    f"Status={status_info.status}, "
                    f"Action={status_info.action}"
                )
                return item, True, "Quantity subtracted"
            else:
                return item, False, "Failed to update quantity"

        except Exception as e:
            self.logger.error(f"Error subtracting quantity: {e}")
            raise

    def update_item(self, item_id: int, updates: Dict[str, Any]) -> Tuple[Optional[InventoryItem], bool, str]:
        try:
            item = self.inventory_model.get_by_id(item_id)
            if not item:
                self.logger.warning(f"Försökte uppdatera ID {item_id} som inte finns")
                return None, False, "Item not found"

            old_values = item.to_dict()

            if "Brand" in updates:
                item.Brand = updates["Brand"]
            if "product_family" in updates:
                item.product_family = updates["product_family"]
            if "spare_part" in updates:
                item.spare_part = updates["spare_part"]
            if "quantity" in updates:
                item.quantity = max(0, int(updates["quantity"]))
            if "low_status" in updates:
                item.low_status = int(updates["low_status"])
            if "high_status" in updates:
                item.high_status = int(updates["high_status"])

            if self.inventory_model.update(item):
                status_info = self.get_status_and_action(item)
                changes = {k: f"Old={old_values[k]}, New={getattr(item, k)}"
                          for k in updates.keys() if k in old_values}
                self.logger.info(
                    f"Updated item: ID={item_id}, "
                    f"Brand={item.Brand}, "
                    f"ProductFamily={item.product_family}, "
                    f"SparePart={item.spare_part}, "
                    f"Changes={changes}, "
                    f"Status={status_info.status}, "
                    f"Action={status_info.action}"
                )
                return item, True, "Item updated"
            else:
                return item, False, "Failed to update item"

        except Exception as e:
            self.logger.error(f"Error updating item: {e}")
            raise

    def delete_item(self, item_id: int) -> Tuple[bool, str]:
        try:
            item = self.inventory_model.get_by_id(item_id)
            if not item:
                self.logger.warning(f"Försökte radera ID {item_id} som inte finns")
                return False, "Item not found"

            status_info = self.get_status_and_action(item)

            if self.inventory_model.delete(item_id):
                self.logger.info(
                    f"Deleted item: ID={item_id}, "
                    f"Brand={item.Brand}, "
                    f"ProductFamily={item.product_family}, "
                    f"SparePart={item.spare_part}, "
                    f"Quantity={item.quantity}, "
                    f"Status={status_info.status}, "
                    f"Action={status_info.action}"
                )
                return True, "Item deleted"
            else:
                return False, "Failed to delete item"

        except Exception as e:
            self.logger.error(f"Error deleting item: {e}")
            raise

    def _log_item_status(self, item: InventoryItem, status_info: StatusInfo) -> None:
        self.logger.info(
            f"Inventory status: ID={item.id}, "
            f"Brand={item.Brand}, "
            f"ProductFamily={item.product_family}, "
            f"SparePart={item.spare_part}, "
            f"Quantity={item.quantity}, "
            f"Status={status_info.status}, "
            f"Action={status_info.action}"
        )