import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    DATA_DIR: str = "data"
    BACKUP_DIR: str = "db_backup"
    VERSION_BACKUP_DIR: str = "version_backup"
    LOG_FILE: str = "app.log"
    UPDATER_LOG_FILE: str = "updater.log"
    LOCK_FILE: str = "updater.lock"
    APP_SCRIPT: str = "app.py"

    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = False

    BACKUP_MAX_FILES: int = 5
    VERSION_BACKUP_MAX_FILES: int = 3
    BACKUP_SCHEDULE_TIME: str = "17:00"
    UPDATE_SCHEDULE_DAY: str = "monday"
    UPDATE_SCHEDULE_TIME: str = "02:00"

    CACHE_TTL_SECONDS: float = 1.0

    @property
    def data_file(self) -> str:
        return os.path.join(self.DATA_DIR, "inventory.json")

    @property
    def settings_file(self) -> str:
        return os.path.join(self.DATA_DIR, "dashboard_settings.json")

    def __post_init__(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.BACKUP_DIR, exist_ok=True)


def get_config() -> AppConfig:
    return AppConfig()