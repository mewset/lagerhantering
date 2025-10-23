import os
import shutil
import logging
from datetime import datetime
from typing import Optional


class BackupService:
    def __init__(self, data_dir: str, backup_dir: str, logger: logging.Logger):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.logger = logger

    def backup_database(self, max_backups: int = 5) -> bool:
        from utils.exceptions import BackupError

        try:
            now = datetime.now()
            if now.weekday() >= 5:
                self.logger.info("Backup skipped - weekend")
                return True

            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            timestamp = now.strftime("%Y-%m-%d-%H%M")
            backup_filename = f"inventory-{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            data_file = os.path.join(self.data_dir, "inventory.json")
            if os.path.exists(data_file):
                shutil.copy(data_file, backup_path)
                self.logger.info(f"Skapade backup: {backup_filename}")

                self._cleanup_old_backups("inventory-", max_backups)
                return True
            else:
                self.logger.warning("Ingen databas att backup:a")
                return True

        except Exception as e:
            self.logger.error(f"Fel vid backup: {e}")
            raise BackupError("database backup", str(e))

    def backup_for_update(self) -> bool:
        from utils.exceptions import BackupError

        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
            backup_filename = f"inventory-update-{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            data_file = os.path.join(self.data_dir, "inventory.json")
            if os.path.exists(data_file):
                shutil.copy(data_file, backup_path)
                self.logger.info(f"Databas backup skapad: {backup_filename}")
                return True
            else:
                self.logger.warning("Ingen databas att backup:a")
                return True

        except Exception as e:
            self.logger.error(f"Fel vid databas backup: {e}")
            raise BackupError("update backup", str(e))

    def create_version_backup(self, version_backup_dir: str, files_to_backup: list) -> Optional[str]:
        try:
            if not os.path.exists(version_backup_dir):
                os.makedirs(version_backup_dir)
                self.logger.info(f"Skapade backup-mapp: {version_backup_dir}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(version_backup_dir, f"version_{timestamp}")

            os.makedirs(backup_path)

            for item in files_to_backup:
                if os.path.exists(item):
                    dest = os.path.join(backup_path, item)
                    if os.path.isdir(item):
                        shutil.copytree(item, dest)
                        self.logger.info(f"Backupade mapp: {item}")
                    else:
                        if not os.path.exists(os.path.dirname(dest)):
                            os.makedirs(os.path.dirname(dest))
                        shutil.copy2(item, dest)
                        self.logger.info(f"Backupade fil: {item}")
                else:
                    self.logger.warning(f"Kunde inte hitta: {item}")

            self._cleanup_old_version_backups(version_backup_dir, max_backups=3)

            self.logger.info(f"Version backup skapad: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Fel vid skapande av version backup: {e}")
            return None

    def _cleanup_old_backups(self, prefix: str, max_backups: int) -> None:
        try:
            backup_files = [
                f for f in os.listdir(self.backup_dir)
                if f.startswith(prefix) and f.endswith(".json")
            ]

            if len(backup_files) > max_backups:
                backup_files.sort(key=lambda x: os.path.getctime(
                    os.path.join(self.backup_dir, x)
                ))
                for old_backup in backup_files[:-max_backups]:
                    old_path = os.path.join(self.backup_dir, old_backup)
                    os.remove(old_path)
                    self.logger.info(f"Tog bort gammal backup: {old_backup}")

        except Exception as e:
            self.logger.error(f"Fel vid cleanup av backuper: {e}")

    def _cleanup_old_version_backups(self, version_backup_dir: str, max_backups: int) -> None:
        try:
            backups = [
                d for d in os.listdir(version_backup_dir)
                if d.startswith("version_") and os.path.isdir(os.path.join(version_backup_dir, d))
            ]

            backups.sort()
            if len(backups) > max_backups:
                for old_backup in backups[:-max_backups]:
                    old_path = os.path.join(version_backup_dir, old_backup)
                    shutil.rmtree(old_path)
                    self.logger.info(f"Tog bort gammal backup: {old_backup}")

        except Exception as e:
            self.logger.error(f"Fel vid cleanup av version backuper: {e}")