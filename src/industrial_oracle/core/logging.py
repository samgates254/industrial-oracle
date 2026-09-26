"""Structured JSON logging with request and correlation context."""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for tracing request lifecycle
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
org_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("org_id", default="")
actor_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("actor_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Tracing context
        req_id = request_id_ctx.get()
        if req_id:
            log_entry["request_id"] = req_id

        org_id = org_id_ctx.get()
        if org_id:
            log_entry["organization_id"] = org_id

        actor_id = actor_id_ctx.get()
        if actor_id:
            log_entry["actor_id"] = actor_id

        # Source code location for warnings and errors
        if record.levelno >= logging.WARNING:
            log_entry["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Exception information
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Extra metadata passed to logger
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> logging.Logger:
    """Configures structured logging across all root and framework loggers."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        text_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(text_fmt)

    root_logger.addHandler(handler)

    # Silence verbose 3rd party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    return root_logger


logger = logging.getLogger("industrial_oracle")
