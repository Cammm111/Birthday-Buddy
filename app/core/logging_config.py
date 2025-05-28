# app/core/logging_config.py

import logging
from logging.config import dictConfig
import os
from datetime import datetime

# ──────────────────────────────────Logging setup──────────────────────────────────
def setup_logging() -> None: # Make log directory if not already created
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create a unique log file with timestamp on every run
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"birthday_buddy_{timestamp}.log")

    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": log_file,
                "level": "INFO",
                "encoding": "utf-8",
                "mode": "a",  # append mode
            },
        },

        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },

        "loggers": {
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    })