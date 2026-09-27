"""
Logging utility for AI Personal Knowledge Assistant.
Sets up file and console loggers with formatted output.
"""

import logging
import sys
from pathlib import Path
import config


def get_logger(name: str = "AI_Assistant") -> logging.Logger:
    """Configures and returns a logger instance.

    Args:
        name (str): Name of the logger module.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    log_file = config.LOGS_DIR / "app.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
