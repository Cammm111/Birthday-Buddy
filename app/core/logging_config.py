# app/core/logging_config.py

import logging
from logging.config import dictConfig

def setup_logging() -> None:
    """
    Configure Python’s logging module for the whole application,
    including Uvicorn/Starlette logs.
    """
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,  # keep Uvicorn’s default handlers

        "formatters": {
            "default": {
                "fmt": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
        },

        "loggers": {
            # root logger
            "": {
                "handlers": ["console"],
                "level": "INFO",
            },
            # Uvicorn and Starlette logs
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    })
