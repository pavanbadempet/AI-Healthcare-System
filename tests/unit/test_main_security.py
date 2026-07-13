import re
import uuid
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from backend.main import (
    _load_allowed_hosts,
    app,
)
from backend.middleware import (
    REQUEST_ID_HEADER,
    ExceptionMiddleware,
    RequestTracingMiddleware,
    SecurityHeadersMiddleware,
)


def test_exception_middleware_hides_unhandled_error_details(caplog):
    app = FastAPI()
    app.add_middleware(ExceptionMiddleware)

    sensitive_error = "database failed password=secret-db-password patient_name=Sensitive User"

    @app.get("/boom")
    def boom():
        raise Exception(sensitive_error)

    caplog.set_level("ERROR", logger="backend.main")
    response = TestClient(app, base_url="http://127.0.0.1").get("/boom")

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert re.fullmatch(r"Error: [0-9a-f]{8}", detail)
    assert sensitive_error not in response.text
    assert "secret-db-password" not in response.text
    assert "Sensitive User" not in response.text
    assert sensitive_error not in caplog.text
    assert "secret-db-password" not in caplog.text
    assert "Sensitive User" not in caplog.text


def test_security_headers_include_browser_hardening():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/health")
    def health():
        return {"ok": True}

    response = TestClient(app, base_url="http://127.0.0.1").get("/health")

    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


def test_request_tracing_adds_request_id_header_and_state():
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware)

    @app.get("/trace")
    def trace(request: Request):
        return {"request_id": request.state.request_id}

    response = TestClient(app, base_url="http://127.0.0.1").get("/trace")

    request_id = response.headers[REQUEST_ID_HEADER]
    assert uuid.UUID(request_id)
    assert response.json()["request_id"] == request_id


def test_request_tracing_reuses_safe_client_request_id():
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware)

    @app.get("/trace")
    def trace(request: Request):
        return {"request_id": request.state.request_id}

    response = TestClient(app, base_url="http://127.0.0.1").get(
        "/trace",
        headers={REQUEST_ID_HEADER: "client-trace-123"},
    )

    assert response.headers[REQUEST_ID_HEADER] == "client-trace-123"
    assert response.json()["request_id"] == "client-trace-123"


def test_request_tracing_replaces_unsafe_client_request_id():
    app = FastAPI()
    app.add_middleware(RequestTracingMiddleware)

    @app.get("/trace")
    def trace(request: Request):
        return {"request_id": request.state.request_id}

    unsafe_request_id = "patient_name=Sensitive User token=secret"
    response = TestClient(app, base_url="http://127.0.0.1").get(
        "/trace",
        headers={REQUEST_ID_HEADER: unsafe_request_id},
    )

    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id != unsafe_request_id
    assert "Sensitive User" not in request_id
    assert "secret" not in request_id
    assert uuid.UUID(request_id)


def test_allowed_hosts_from_env():
    with patch.dict("os.environ", {"ALLOWED_HOSTS": "127.0.0.1,api.hospital.example"}, clear=True):
        assert _load_allowed_hosts() == ["127.0.0.1", "api.hospital.example"]


def test_allowed_hosts_testing_default_includes_testserver():
    with patch.dict("os.environ", {"TESTING": "1"}, clear=True):
        assert _load_allowed_hosts() == ["127.0.0.1", "testserver"]


def test_cors_origins_from_env():
    from backend.main import _load_cors_origins

    with patch.dict(
        "os.environ",
        {"CORS_ORIGINS": "http://127.0.0.1:3000,https://app.hospital.example"},
        clear=True,
    ):
        assert _load_cors_origins() == ["http://127.0.0.1:3000", "https://app.hospital.example"]


def test_cors_origins_default_to_local_frontend():
    from backend.main import _load_cors_origins

    with patch.dict("os.environ", {}, clear=True):
        assert _load_cors_origins() == ["http://127.0.0.1:3000"]


def test_rate_limit_from_env():
    from backend.security import _load_rate_limit_requests_per_minute

    with patch.dict("os.environ", {"RATE_LIMIT_REQUESTS_PER_MINUTE": "120"}, clear=True):
        assert _load_rate_limit_requests_per_minute() == 120


def test_rate_limit_rejects_invalid_env():
    from backend.security import _load_rate_limit_requests_per_minute

    with patch.dict("os.environ", {"RATE_LIMIT_REQUESTS_PER_MINUTE": "0"}, clear=True):
        try:
            _load_rate_limit_requests_per_minute()
        except RuntimeError as exc:
            assert "RATE_LIMIT_REQUESTS_PER_MINUTE" in str(exc)
        else:
            raise AssertionError("Expected invalid rate limit config to fail")


def test_api_routes_do_not_register_duplicate_method_paths():
    seen: dict[tuple[str, str], str] = {}
    duplicates = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods:
            key = (method, route.path)
            if key in seen:
                duplicates.append((key, seen[key], route.name))
            else:
                seen[key] = route.name

    assert duplicates == []
