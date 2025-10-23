import json
import os
import threading
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class InventoryItem:
    id: int
    Brand: str
    product_family: str
    spare_part: str
    quantity: int
    low_status: int
    high_status: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryItem':
        return cls(
            id=int(data.get('id', 0)),
            Brand=data.get('Brand', ''),
            product_family=data.get('product_family', ''),
            spare_part=data.get('spare_part', ''),
            quantity=int(data.get('quantity', 0)),
            low_status=int(data.get('low_status', 5)),
            high_status=int(data.get('high_status', 15))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'Brand': self.Brand,
            'product_family': self.product_family,
            'spare_part': self.spare_part,
            'quantity': self.quantity,
            'low_status': self.low_status,
            'high_status': self.high_status
        }


class InventoryModel:
    def __init__(self, data_file: str, cache_ttl: float = 1.0):
        self.data_file = data_file
        self._lock = threading.RLock()
        self._cache = None
        self._cache_timestamp = 0
        self._cache_ttl = cache_ttl

    def _read_file(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.data_file):
                return []

            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_file(self, data: List[Dict[str, Any]]) -> None:
        temp_file = f"{self.data_file}.tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                os.replace(self.data_file, backup_file)

            os.replace(temp_file, self.data_file)

            if os.path.exists(f"{self.data_file}.backup"):
                os.remove(f"{self.data_file}.backup")

        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e

    def _get_cached_data(self) -> Optional[List[Dict[str, Any]]]:
        current_time = time.time()
        if (self._cache is not None and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._cache
        return None

    def _update_cache(self, data: List[Dict[str, Any]]) -> None:
        self._cache = data
        self._cache_timestamp = time.time()

    def get_all(self) -> List[InventoryItem]:
        with self._lock:
            cached_data = self._get_cached_data()
            if cached_data is not None:
                data = cached_data
            else:
                data = self._read_file()
                self._update_cache(data)

            return [InventoryItem.from_dict(item) for item in data]

    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        items = self.get_all()
        for item in items:
            if item.id == item_id:
                return item
        return None

    def add(self, item: InventoryItem) -> InventoryItem:
        with self._lock:
            data = self._read_file()

            if item.id == 0:
                max_id = max([item_data.get('id', 0) for item_data in data] + [0])
                item.id = max_id + 1

            data.append(item.to_dict())
            self._write_file(data)
            self._update_cache(data)

            return item

    def update(self, item: InventoryItem) -> bool:
        with self._lock:
            data = self._read_file()

            for i, item_data in enumerate(data):
                if item_data.get('id') == item.id:
                    data[i] = item.to_dict()
                    self._write_file(data)
                    self._update_cache(data)
                    return True

            return False

    def delete(self, item_id: int) -> bool:
        with self._lock:
            data = self._read_file()

            for i, item_data in enumerate(data):
                if item_data.get('id') == item_id:
                    del data[i]
                    self._write_file(data)
                    self._update_cache(data)
                    return True

            return False

    def find_by_product(self, product_family: str, spare_part: str) -> Optional[InventoryItem]:
        items = self.get_all()
        for item in items:
            if (item.product_family == product_family and
                item.spare_part == spare_part):
                return item
        return None

    def clear_cache(self) -> None:
        with self._lock:
            self._cache = None
            self._cache_timestamp = 0