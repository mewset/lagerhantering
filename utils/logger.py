import logging
import os
from typing import Optional


def setup_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    add_console: bool = False
) -> logging.Logger:
    if format_string is None:
        format_string = '%(asctime)s [%(levelname)s] %(message)s'

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        logger.handlers.clear()

    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)

    formatter = logging.Formatter(format_string)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    if add_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def get_app_logger(log_file: str = 'app.log') -> logging.Logger:
    return setup_logger(
        name='app',
        log_file=log_file,
        level=logging.INFO,
        format_string='%(asctime)s [%(levelname)s] %(message)s'
    )


def get_updater_logger(log_file: str = 'updater.log') -> logging.Logger:
    return setup_logger(
        name='updater',
        log_file=log_file,
        level=logging.INFO,
        format_string='%(asctime)s [%(levelname)s] %(message)s',
        add_console=True
    )