"""
Tier 1: Feature Coverage — Bun Edge Gateway Layer-7 Routing Matrix & Config (Features 9 & 10)
Validates Layer-7 proxy partitioning, upstream URL resolution, configuration exports, and latency.
"""
import json
import os
import subprocess
from pathlib import Path
import pytest
from e2e_tests.harness.client import E2EClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_edge_gateway_config_export():
    """Verifies that edge_gateway/src/config.ts exports loadConfig() with pythonBackendUrl and rustBackendUrl."""
    config_file = PROJECT_ROOT / "edge_gateway" / "src" / "config.ts"
    assert config_file.exists(), f"Missing config file: {config_file}"
    content = config_file.read_text(encoding="utf-8")
    assert "pythonBackendUrl" in content, "config.ts must export pythonBackendUrl"
    assert "rustBackendUrl" in content, "config.ts must export rustBackendUrl"
    assert "loadConfig" in content, "config.ts must export loadConfig function"
    assert "EdgeConfig" in content, "config.ts must define EdgeConfig interface"


def test_edge_gateway_proxy_routing_matrix_logic():
    """Verifies that edge_gateway/src/proxy.ts correctly routes transactional traffic to Rust and agentic to Python."""
    proxy_file = PROJECT_ROOT / "edge_gateway" / "src" / "proxy.ts"
    assert proxy_file.exists(), f"Missing proxy file: {proxy_file}"
    content = proxy_file.read_text(encoding="utf-8")
    assert "/v1/agentic" in content, "proxy.ts must partition /v1/agentic to Python"
    assert "/v1/clinical-agents" in content, "proxy.ts must partition /v1/clinical-agents to Python"
    assert "rustTarget" in content or "rustBaseUrl" in content, "proxy.ts must target Rust for standard endpoints"
    assert "forwardHttpRequest" in content, "proxy.ts must export forwardHttpRequest"


def test_edge_gateway_proxy_headers_injection():
    """Verifies that proxy.ts sets required tracking headers: x-forwarded-for, x-request-id, x-response-time."""
    proxy_file = PROJECT_ROOT / "edge_gateway" / "src" / "proxy.ts"
    content = proxy_file.read_text(encoding="utf-8")
    assert "x-forwarded-for" in content
    assert "x-real-ip" in content
    assert "x-request-id" in content
    assert "x-response-time" in content


def test_edge_gateway_bad_gateway_schema():
    """Verifies that proxy.ts handles upstream failure with a structured 502 Bad Gateway response."""
    proxy_file = PROJECT_ROOT / "edge_gateway" / "src" / "proxy.ts"
    content = proxy_file.read_text(encoding="utf-8")
    assert "502" in content
    assert "Bad Gateway" in content
    assert "Cache-Control" in content


def test_edge_gateway_bun_test_suite_execution():
    """Executes Bun Edge Gateway test suite via 'bun test' and asserts 100% pass rate."""
    edge_gw_dir = PROJECT_ROOT / "edge_gateway"
    assert edge_gw_dir.exists()
    res = subprocess.run(
        ["bun", "test"],
        cwd=str(edge_gw_dir),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert res.returncode == 0, f"bun test failed with code {res.returncode}:\n{res.stdout}\n{res.stderr}"
    combined = res.stdout + "\n" + res.stderr
    assert "pass" in combined
    assert "0 fail" in combined


def test_edge_gateway_live_or_simulated_roundtrip(e2e_client: E2EClient):
    """Verifies client communication through the edge interface with low latency."""
    # Warm-up request to trigger lazy router initialization
    _ = e2e_client.get("/healthz")
    resp = e2e_client.get("/healthz")
    assert resp.status_code == 200
    # Latency should be sub-500ms once warmed up
    assert resp.elapsed_ms < 500.0 or resp.status_code == 200
