"""Structured application logging setup (docs/17_SECURITY_AND_PRIVACY.md)."""

import logging
import sys

def setup_logging() -> None:
    logger = logging.getLogger("scalebridge")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

logger = logging.getLogger("scalebridge")
