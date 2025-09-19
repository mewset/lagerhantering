#!/usr/bin/env python3
import sys
from config import get_config
from utils.logger import get_updater_logger
from services.backup_service import BackupService
from services.updater_service import UpdaterService


def main():
    config = get_config()
    logger = get_updater_logger(config.UPDATER_LOG_FILE)

    backup_service = BackupService(config.DATA_DIR, config.BACKUP_DIR, logger)
    updater_service = UpdaterService(
        config.APP_SCRIPT,
        config.LOCK_FILE,
        backup_service,
        logger
    )

    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            updater_service.run_update_check()
        elif sys.argv[1] == "--daemon":
            updater_service.run_daemon()
        else:
            print("Användning: python updater.py [--check|--daemon]")
            sys.exit(1)
    else:
        updater_service.run_update_check()


if __name__ == "__main__":
    main()