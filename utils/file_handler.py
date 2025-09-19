import json
import os
import threading
from typing import Any, Dict, List


class FileHandler:
    def __init__(self):
        self._locks = {}

    def _get_lock(self, file_path: str) -> threading.RLock:
        if file_path not in self._locks:
            self._locks[file_path] = threading.RLock()
        return self._locks[file_path]

    def read_json(self, file_path: str, default: Any = None) -> Any:
        lock = self._get_lock(file_path)
        with lock:
            try:
                if not os.path.exists(file_path):
                    return default if default is not None else {}

                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return default if default is not None else {}

    def write_json(self, file_path: str, data: Any) -> None:
        lock = self._get_lock(file_path)
        with lock:
            temp_file = f"{file_path}.tmp"
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                if os.path.exists(file_path):
                    backup_file = f"{file_path}.backup"
                    os.replace(file_path, backup_file)

                os.replace(temp_file, file_path)

                if os.path.exists(f"{file_path}.backup"):
                    os.remove(f"{file_path}.backup")

            except Exception as e:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e

    def ensure_directory(self, directory: str) -> None:
        if not os.path.exists(directory):
            os.makedirs(directory)

    def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def create_empty_file(self, file_path: str, default_content: Any = None) -> None:
        if not os.path.exists(file_path):
            self.ensure_directory(os.path.dirname(file_path))

            if default_content is not None:
                self.write_json(file_path, default_content)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)


_file_handler_instance = FileHandler()


def get_file_handler() -> FileHandler:
    return _file_handler_instance