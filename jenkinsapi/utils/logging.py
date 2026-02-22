"""
Helpers for configuring JenkinsAPI logging without clobbering user settings.
"""

from __future__ import annotations

import logging
import os


def _resolve_level(level) -> int | None:
    if level is None:
        return None
    if isinstance(level, int):
        return level
    if not isinstance(level, str):
        return None
    level_value = logging.getLevelName(level.upper())
    if isinstance(level_value, str):
        return None
    return level_value


def configure_logging(level: str | int | None = None) -> bool:
    """
    Configure JenkinsAPI logging if the user hasn't already.

    If level is None, the environment variable JENKINSAPI_LOG_LEVEL is used.
    Returns True when logging was configured.
    """
    if level is None:
        level = os.getenv("JENKINSAPI_LOG_LEVEL")
    level_value = _resolve_level(level)
    if level_value is None:
        return False

    logger = logging.getLogger("jenkinsapi")
    logger.setLevel(level_value)

    root = logging.getLogger()
    if logger.handlers or root.handlers:
        return True

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return True
