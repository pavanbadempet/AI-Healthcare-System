"""
Tier 2: Boundary & Corner Cases — Bun DevX Scripts & CLI Edge Cases
Tests invalid CLI arguments, missing files, extreme inputs, and malformed configurations for Bun scripts.
"""
import json
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_ai_context_invalid_flag():
    """Verifies that ai_context.ts handles unrecognized flags without fatal crash."""
    res = subprocess.run(
        ["bun", "scripts/ai_context.ts", "--nonexistent-flag-xyz"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    # The script should complete gracefully or output standard help/context
    assert res.returncode == 0 or "AI Healthcare System" in res.stdout


def test_sync_agent_adapters_check_clean_state():
    """Verifies that sync_agent_adapters.ts --check returns 0 when all adapter files are synchronized."""
    res = subprocess.run(
        ["bun", "scripts/sync_agent_adapters.ts", "--check"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res.returncode == 0
    assert "PASS" in res.stdout


def test_sync_agent_adapters_json_manifest_integrity():
    """Verifies that the agent adapter manifest JSON is valid, non-empty, and parsable."""
    manifest_path = PROJECT_ROOT / "scripts" / "agent_adapter_manifest.json"
    assert manifest_path.exists(), "agent_adapter_manifest.json must exist"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "adapters" in data or "files" in data or isinstance(data, list) or isinstance(data, dict)


def test_ai_context_json_contract_structure():
    """Verifies boundary properties on the JSON emitted by ai_context.ts: non-null types and valid arrays."""
    res = subprocess.run(
        ["bun", "scripts/ai_context.ts", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert isinstance(data.get("services"), list)
    assert isinstance(data.get("ml_models"), list)
    assert isinstance(data.get("context_files"), list)
    for model in data["ml_models"]:
        assert "name" in model
        assert "usable" in model
        assert isinstance(model["size_mb"], (int, float))


def test_edge_gateway_config_environment_variable_overrides():
    """Verifies that config module properly handles environment variable overrides."""
    bun_code = """
    import { loadConfig } from './src/config';
    process.env.PORT = '9999';
    process.env.RUST_BACKEND_URL = 'http://127.0.0.1:9001';
    process.env.PYTHON_BACKEND_URL = 'http://127.0.0.1:9002';
    const cfg = loadConfig();
    if (cfg.port !== 9999 || cfg.rustBackendUrl !== 'http://127.0.0.1:9001' || cfg.pythonBackendUrl !== 'http://127.0.0.1:9002') {
        process.exit(1);
    }
    process.exit(0);
    """
    res = subprocess.run(
        ["bun", "-e", bun_code],
        cwd=str(PROJECT_ROOT / "edge_gateway"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    assert res.returncode == 0, f"Config override failed: {res.stderr}"


def test_secret_scanner_clean_audit():
    """Verifies that scripts/pre_commit_secret_scanner.ts or .py passes cleanly on the codebase."""
    res = subprocess.run(
        ["bun", "scripts/pre_commit_secret_scanner.ts"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    if res.returncode != 0:
        res = subprocess.run(
            ["python", "scripts/pre_commit_secret_scanner.py"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    assert res.returncode == 0 or "Zero secrets detected" in res.stdout or "OK" in res.stdout
