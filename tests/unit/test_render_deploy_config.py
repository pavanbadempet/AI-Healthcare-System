from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RENDER_HOSTS = {"aio-health-backend.onrender.com", "aio-health-backend-gdzi.onrender.com"}
PUBLIC_FRONTEND_ORIGIN = "https://ai-healthcare-system.streamlit.app"
RENDER_PYTHON_VERSION = "3.12.8"


def _render_env_vars() -> dict[str, str]:
    config = yaml.safe_load((REPO_ROOT / "render.yaml").read_text(encoding="utf-8"))
    try:
        service = next(
            item for item in config["services"] if item["type"] == "web" and item["name"] == "aio-health-backend"
        )
    except StopIteration:
        return {}
    return {item["key"]: item["value"] for item in service["envVars"] if "value" in item}


def test_render_backend_accepts_render_health_check_hosts():
    env_vars = _render_env_vars()
    if not env_vars:
        return
    allowed_hosts = {host.strip() for host in env_vars["ALLOWED_HOSTS"].split(",") if host.strip()}

    assert RENDER_HOSTS <= allowed_hosts


def test_render_backend_uses_supported_python_for_dependency_wheels():
    env_vars = _render_env_vars()
    if not env_vars:
        return
    assert env_vars["PYTHON_VERSION"] == RENDER_PYTHON_VERSION


def test_render_backend_allows_public_frontend_origin():
    env_vars = _render_env_vars()
    if not env_vars:
        return
    cors_origins = {origin.strip() for origin in env_vars["CORS_ORIGINS"].split(",") if origin.strip()}

    assert PUBLIC_FRONTEND_ORIGIN in cors_origins
