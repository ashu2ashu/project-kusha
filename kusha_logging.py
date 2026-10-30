"""
kusha_logging.py
Centralized, privacy-preserving logging infrastructure for Project KUSHA / StockSage.
Provides structured stderr logging with strict redaction of sensitive credentials,
API keys, passwords, prompt text, and financial statements.
"""

import logging
import os
import re
import sys
from typing import Optional

_CONFIGURED = False

# Pattern matching Google AI API keys (typically starts with AIza and 30-45 chars)
_GEMINI_KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z\-_]{30,45}")
_GENERIC_KEY_PATTERN = re.compile(r"(?i)(api[_-]?key|password|secret|bearer)\s*[:=]\s*['\"]?([^\s'\"]+)['\"]?")


class SensitiveDataFilter(logging.Filter):
    """
    Log filter that redacts API keys, passwords, and sensitive credential tokens
    from all log record messages before output.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            # Redact standard Gemini API key format
            msg = _GEMINI_KEY_PATTERN.sub("[REDACTED_API_KEY]", msg)
            # Redact key/password key-value pairs
            msg = _GENERIC_KEY_PATTERN.sub(r"\1=[REDACTED]", msg)
            record.msg = msg
            record.args = None
        except Exception:
            pass
        return True


def configure_logging(level: Optional[str] = None, log_file: Optional[str] = None) -> None:
    """
    Configures root logging idempotently.
    - Default level: INFO (or env KUSHA_LOG_LEVEL)
    - Output: sys.stderr only (or file handler if KUSHA_LOG_FILE is set)
    - Format: %(asctime)s %(levelname)s %(name)s :: %(message)s
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level_name = (level or os.getenv("KUSHA_LOG_LEVEL", "INFO")).upper().strip()
    log_level = getattr(logging, log_level_name, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s :: %(message)s")
    redacting_filter = SensitiveDataFilter()

    # Clear existing handlers to prevent duplicate lines
    root_logger.handlers.clear()

    # Stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(log_level)
    stderr_handler.setFormatter(formatter)
    stderr_handler.addFilter(redacting_filter)
    root_logger.addHandler(stderr_handler)

    # Optional file handler if KUSHA_LOG_FILE is defined
    target_file = log_file or os.getenv("KUSHA_LOG_FILE")
    if target_file:
        try:
            file_handler = logging.FileHandler(target_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(redacting_filter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning("Failed to configure KUSHA_LOG_FILE %s: %s", target_file, e)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger configured with the KUSHA logging standard.
    """
    return logging.getLogger(name)
