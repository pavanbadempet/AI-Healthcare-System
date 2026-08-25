"""
Opaque-Box E2E HTTP Client.
Seamlessly routes requests to either live HTTP servers (Rust / Bun / FastAPI via E2E_API_URL)
or in-process FastAPI TestClient for zero-config local testing.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class E2EResponse:
    status_code: int
    _json_data: Any = None
    text: str = ""
    headers: Dict[str, str] = None
    elapsed_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if self._json_data is not None:
            return self._json_data
        import json
        try:
            return json.loads(self.text)
        except Exception:
            return {}


class E2EClient:
    """Opaque-box test client for the AI Healthcare System APIs."""

    def __init__(self, base_url: Optional[str] = None, auth_token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("E2E_API_URL", "")).rstrip("/")
        self.auth_token = auth_token
        self._test_client = None

        if not self.base_url:
            self._init_in_process_client()

    def _init_in_process_client(self):
        try:
            from fastapi.testclient import TestClient
            from backend.main import app
            from backend.database import Base, engine
            from backend.prediction import initialize_models
            from e2e_tests.harness.auth import TestAuthManager

            # Ensure tables exist and test users are seeded
            Base.metadata.create_all(bind=engine)
            TestAuthManager.seed_test_users()

            try:
                initialize_models()
            except Exception:
                pass
            self._test_client = TestClient(app, base_url="http://127.0.0.1")
        except Exception as e:
            self.base_url = "http://127.0.0.1:8000"

    def _merge_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = {}
        if self.auth_token:
            merged["Authorization"] = f"Bearer {self.auth_token}"
        if headers:
            merged.update(headers)
        return merged

    def _normalize_path(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return path

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> E2EResponse:
        path = self._normalize_path(path)
        req_headers = self._merge_headers(headers)
        start_time = time.perf_counter()

        if self.base_url:
            import requests

            url = f"{self.base_url}{path}"
            try:
                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    headers=req_headers,
                    timeout=timeout,
                )
                elapsed = (time.perf_counter() - start_time) * 1000.0
                json_val = None
                try:
                    json_val = resp.json()
                except Exception:
                    pass
                return E2EResponse(
                    status_code=resp.status_code,
                    _json_data=json_val,
                    text=resp.text,
                    headers=dict(resp.headers),
                    elapsed_ms=elapsed,
                )
            except Exception as exc:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return E2EResponse(
                    status_code=503,
                    _json_data={"error": str(exc)},
                    text=str(exc),
                    headers={},
                    elapsed_ms=elapsed,
                )
        else:
            try:
                resp = self._test_client.request(
                    method=method.upper(),
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=req_headers,
                )
                elapsed = (time.perf_counter() - start_time) * 1000.0
                json_val = None
                try:
                    json_val = resp.json()
                except Exception:
                    pass
                return E2EResponse(
                    status_code=resp.status_code,
                    _json_data=json_val,
                    text=resp.text,
                    headers=dict(resp.headers),
                    elapsed_ms=elapsed,
                )
            except Exception as exc:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return E2EResponse(
                    status_code=500,
                    _json_data={"error": str(exc)},
                    text=str(exc),
                    headers={},
                    elapsed_ms=elapsed,
                )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> E2EResponse:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> E2EResponse:
        return self.request("POST", path, params=params, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> E2EResponse:
        return self.request("PUT", path, params=params, json=json, data=data, headers=headers)

    def patch(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> E2EResponse:
        return self.request("PATCH", path, params=params, json=json, data=data, headers=headers)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> E2EResponse:
        return self.request("DELETE", path, params=params, headers=headers)
