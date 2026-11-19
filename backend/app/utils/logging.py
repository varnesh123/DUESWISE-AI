"""Basic application logging configuration."""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure standard library logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
