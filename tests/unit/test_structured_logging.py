import json
import logging
import io
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.logging_config import (
    setup_structured_logging,
    correlation_id_var,
    StructuredJSONFormatter,
    PIIRedactingFilter
)
from backend.middleware import RequestTracingMiddleware

def test_json_logging_format_and_redaction():
    # 1. Capture logger outputs
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(StructuredJSONFormatter())
    handler.addFilter(PIIRedactingFilter())
    
    test_logger = logging.getLogger("test_structured_logger")
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False

    # 2. Log normal message
    test_logger.info("Structured logging test")
    log_line = log_capture.getvalue().strip()
    assert log_line.startswith("{") and log_line.endswith("}")
    
    log_data = json.loads(log_line)
    assert log_data["message"] == "Structured logging test"
    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "test_structured_logger"
    assert "timestamp" in log_data

    # 3. Log sensitive message (PII Redaction check)
    log_capture.seek(0)
    log_capture.truncate(0)
    
    test_logger.info("Contact patient John at john.doe@example.com or 123-456-7890.")
    redacted_line = log_capture.getvalue().strip()
    redacted_data = json.loads(redacted_line)
    
    assert "[EMAIL_REDACTED]" in redacted_data["message"]
    assert "[PHONE_REDACTED]" in redacted_data["message"]
    assert "john.doe@example.com" not in redacted_data["message"]
    assert "123-456-7890" not in redacted_data["message"]

def test_correlation_id_context_propagation():
    # Set correlation ID context
    token = correlation_id_var.set("test-correlation-12345")
    try:
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredJSONFormatter())
        
        test_logger = logging.getLogger("test_correlation_logger")
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        test_logger.propagate = False
        
        test_logger.info("Testing correlation propagation")
        log_line = log_capture.getvalue().strip()
        log_data = json.loads(log_line)
        
        assert log_data["correlation_id"] == "test-correlation-12345"
    finally:
        correlation_id_var.reset(token)

def test_request_tracing_middleware_headers():
    # Setup test FastAPI app with RequestTracingMiddleware
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware)
    
    @app.get("/test-trace")
    def dummy_route():
        return {"status": "ok"}
        
    client = TestClient(app)
    
    # Request without correlation header (should generate one)
    res = client.get("/test-trace")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert "X-Correlation-ID" in res.headers
    assert res.headers["X-Request-ID"] == res.headers["X-Correlation-ID"]
    assert len(res.headers["X-Request-ID"]) >= 32

    # Request with custom correlation header (should preserve it)
    custom_id = "custom-trace-id-8899"
    res_custom = client.get("/test-trace", headers={"X-Correlation-ID": custom_id})
    assert res_custom.status_code == 200
    assert res_custom.headers["X-Request-ID"] == custom_id
    assert res_custom.headers["X-Correlation-ID"] == custom_id
