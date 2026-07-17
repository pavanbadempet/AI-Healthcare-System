"""State-of-the-Art Structured JSON Logging & Distributed Tracing.

Configures root logging handlers to format all application outputs as structured JSON lines.
Enforces request tracing via thread-safe/async context propagation of correlation IDs.
"""

import contextvars
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to hold the X-Correlation-ID for the request lifecycle
correlation_id_var = contextvars.ContextVar("correlation_id", default="")

class PIIRedactingFilter(logging.Filter):
    """Filter to automatically strip and redact email and phone numbers from logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', record.msg)
            record.msg = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', record.msg)
        return True

class StructuredJSONFormatter(logging.Formatter):
    """Formats Python logging records as a single structured JSON line."""
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "correlation_id": correlation_id_var.get()
        }

        # Format exceptions if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Include custom extra attributes if supplied
        if hasattr(record, "extra") and isinstance(record.extra, dict): # type: ignore
            log_record.update(record.extra) # type: ignore

        return json.dumps(log_record)

def setup_structured_logging(level: int = logging.INFO) -> None:
    """Configures root logger to output structured JSON with PII redaction."""
    root = logging.getLogger()

    # Remove default handlers to prevent duplicate outputs
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())
    handler.addFilter(PIIRedactingFilter())

    root.addHandler(handler)
    root.setLevel(level)

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to extract or generate request Correlation IDs."""
    async def dispatch(self, request: Request, call_next):
        # Extract X-Correlation-ID header, checking case-insensitively
        corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("x-correlation-id")
        if not corr_id:
            corr_id = f"corr-{uuid.uuid4().hex}"

        # Set correlation ID context for this request thread/async task
        token = correlation_id_var.set(corr_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_var.reset(token)
