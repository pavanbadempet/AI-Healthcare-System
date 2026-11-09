"""
Adversarial Stress Test Suite for Milestone 2: Production Runtime Lockout.

Empirically challenges:
1. Environment variable permutations (case, whitespace, shorthand).
2. Lockout non-bypassability (cannot be bypassed by TESTING=1, DEBUG=1, etc.).
3. Negative allowance (dev, test, local, staging, false flags must NOT lock out).
4. Subprocess execution (standalone python and uvicorn processes must fail fast).
5. AST / Manifest static integrity (Dockerfile.enterprise, docker-compose.enterprise.yml, render.yaml, run_servers.py, run_prod.bat).
"""
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


# ── 1. Production Variable Permutations (Positive Lockout) ───────────

@pytest.mark.parametrize(
    "env_val",
    [
        "production",
        "prod",
        "PRODUCTION",
        "PROD",
        "Production",
        "Prod",
        "  production  ",
        "  prod  ",
        "\tproduction\n",
    ],
)
def test_adversarial_env_permutations_lockout(monkeypatch, env_val):
    """Verify all variations of ENV=production trigger immediate RuntimeError."""
    monkeypatch.setenv("ENV", env_val)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore safe state
    monkeypatch.setenv("ENV", "test")
    importlib.reload(backend.main)


@pytest.mark.parametrize(
    "environment_val",
    [
        "production",
        "prod",
        "PRODUCTION",
        "PROD",
        "Production",
        "Prod",
        "  production  ",
        "  prod  ",
        "\tenvironment\n" if False else " production ",
    ],
)
def test_adversarial_environment_permutations_lockout(monkeypatch, environment_val):
    """Verify all variations of ENVIRONMENT=production trigger immediate RuntimeError."""
    monkeypatch.setenv("ENVIRONMENT", environment_val)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore safe state
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    importlib.reload(backend.main)


@pytest.mark.parametrize(
    "prod_val",
    [
        "1",
        "true",
        "yes",
        "True",
        "TRUE",
        "Yes",
        "YES",
        " 1 ",
        " true ",
        " yes ",
    ],
)
def test_adversarial_production_flag_permutations_lockout(monkeypatch, prod_val):
    """Verify all truthy variations of PRODUCTION trigger immediate RuntimeError."""
    monkeypatch.setenv("PRODUCTION", prod_val)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore safe state
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("PRODUCTION", raising=False)
    importlib.reload(backend.main)


# ── 2. Adversarial Bypass Resistance ────────────────────────────────

@pytest.mark.parametrize(
    "bypass_env",
    [
        {"TESTING": "1", "ENV": "production"},
        {"TESTING": "true", "ENV": "production"},
        {"DEBUG": "1", "ENV": "production"},
        {"FASTAPI_ENV": "development", "ENV": "production"},
        {"CI": "true", "ENV": "production"},
        {"TESTING": "1", "PRODUCTION": "1"},
    ],
)
def test_adversarial_bypass_resistance(monkeypatch, bypass_env):
    """Lockout MUST NOT be bypassable by setting conflicting debug/test flags."""
    for k, v in bypass_env.items():
        monkeypatch.setenv(k, v)

    import backend.main
    with pytest.raises(RuntimeError, match="Python execution is disabled in live production mode"):
        importlib.reload(backend.main)

    # Restore
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("PRODUCTION", raising=False)
    importlib.reload(backend.main)


# ── 3. Negative Allowance (Non-Production Safe Execution) ─────────────

@pytest.mark.parametrize(
    "safe_env",
    [
        {"ENV": "development"},
        {"ENV": "test"},
        {"ENV": "local"},
        {"ENV": ""},
        {"ENVIRONMENT": "development"},
        {"ENVIRONMENT": "staging"},
        {"ENVIRONMENT": ""},
        {"PRODUCTION": "0"},
        {"PRODUCTION": "false"},
        {"PRODUCTION": "no"},
        {"PRODUCTION": ""},
    ],
)
def test_adversarial_safe_environments_allowed(monkeypatch, safe_env):
    """Non-production environments must NOT trigger lockout and must load FastAPI normally."""
    # Clear out production triggers first
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)

    for k, v in safe_env.items():
        monkeypatch.setenv(k, v)

    import backend.main
    reloaded = importlib.reload(backend.main)
    assert reloaded.app is not None
    assert reloaded.app.title == "AI Healthcare API"


# ── 4. Subprocess Isolation Tests (Empirical OS Execution) ───────────

def test_subprocess_standalone_python_invocation_fails_fast():
    """Launching python -c 'import backend.main' in production exits non-zero with RuntimeError."""
    env = os.environ.copy()
    env["ENV"] = "production"
    env.pop("ENVIRONMENT", None)
    env.pop("PRODUCTION", None)

    cmd = [sys.executable, "-c", "import backend.main"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(ROOT_DIR))

    assert res.returncode != 0, f"Expected non-zero exit code, got {res.returncode}"
    assert "RuntimeError: Python execution is disabled in live production mode" in res.stderr


def test_subprocess_standalone_uvicorn_launch_fails_fast():
    """Launching uvicorn backend.main:app in production exits non-zero."""
    env = os.environ.copy()
    env["ENV"] = "production"
    env.pop("ENVIRONMENT", None)
    env.pop("PRODUCTION", None)

    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8999"]
    res = subprocess.run(
        cmd, env=env, capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=10
    )

    assert res.returncode != 0, f"Uvicorn should have failed, got exit code {res.returncode}"
    combined_output = res.stderr + res.stdout
    assert "Python execution is disabled in live production mode" in combined_output


def test_subprocess_dev_mode_loads_cleanly():
    """Launching python -c 'import backend.main; print(backend.main.app.title)' in test mode succeeds."""
    env = os.environ.copy()
    env["ENV"] = "test"
    env.pop("ENVIRONMENT", None)
    env.pop("PRODUCTION", None)

    cmd = [sys.executable, "-c", "import backend.main; print(backend.main.app.title)"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(ROOT_DIR))

    assert res.returncode == 0, f"Failed with: {res.stderr}"
    assert "AI Healthcare API" in res.stdout


# ── 5. Manifest Static AST & Shell Scrutiny ──────────────────────────

def test_manifest_dockerfile_enterprise_no_python_runtime():
    """Dockerfile.enterprise must not install or invoke python in runtime container."""
    dockerfile = ROOT_DIR / "Dockerfile.enterprise"
    content = dockerfile.read_text(encoding="utf-8")

    # Split into stages
    stages = content.split("FROM ")
    assert len(stages) >= 3, "Expected at least 2 stages (builder and runtime)"
    runtime_stage = stages[-1]

    # Scrutinize runtime stage
    for banned in ["python", "pip", "uvicorn", "gunicorn", "python3"]:
        assert banned not in runtime_stage.lower(), f"Banned token '{banned}' found in runtime stage"

    assert 'CMD ["/app/rust_gateway"]' in runtime_stage


def test_manifest_docker_compose_enterprise_backend_service():
    """docker-compose.enterprise.yml backend service must run rust_gateway directly."""
    compose_file = ROOT_DIR / "docker-compose.enterprise.yml"
    content = compose_file.read_text(encoding="utf-8")

    # Check backend service section
    assert "healthcare_backend_enterprise" in content
    assert "command: /app/rust_gateway" in content
    assert "ENV=production" in content
    assert "ENVIRONMENT=production" in content
    # Ensure no python source mounting in backend container
    assert "./backend:/app/backend" not in content


def test_manifest_render_yaml_rust_service():
    """render.yaml must declare rust runtime and execute rust_gateway if present."""
    render_file = ROOT_DIR / "render.yaml"
    if not render_file.exists():
        pytest.skip("render.yaml has been decommissioned in favor of Hugging Face Spaces production container.")
    content = render_file.read_text(encoding="utf-8")

    assert "env: rust" in content
    assert "rust_gateway" in content
    assert "uvicorn" not in content


def test_manifest_run_prod_bat_sets_prod_and_runs_rust():
    """scripts/runners/run_prod.bat must set ENV=production and run rust_gateway."""
    bat_file = ROOT_DIR / "scripts" / "runners" / "run_prod.bat"
    content = bat_file.read_text(encoding="utf-8")

    assert "set ENV=production" in content
    assert "set ENVIRONMENT=production" in content
    assert "rust_gateway" in content
    assert "uvicorn" not in content
