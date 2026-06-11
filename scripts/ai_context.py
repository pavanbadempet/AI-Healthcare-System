"""
Session context snapshot for AI agents.

Run at the start of any AI coding session to get a quick overview
of the current project state:

    python scripts/ai_context.py
    python scripts/ai_context.py --json

Prints: database status, ML model files, recent git activity, running services,
and pointers to the agent-guidance surface.

Ported from Universe Dex DevX Agent Infrastructure, adapted for Healthcare domain.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVICE_PORTS = [
    ("Backend (FastAPI)", 8000),
    ("Frontend (Next.js)", 3000),
]
CONTEXT_FILES = [
    "AGENTS.md",
    "backend/AGENTS.md",
    "frontend/AGENTS.md",
    "tests/AGENTS.md",
    "backend/CONTEXT.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/00-root.mdc",
    ".kiro/steering/structure.md",
    "docs/AI_AGENT_ARCHITECTURE.md",
    "scripts/agent_adapter_manifest.json",
    "scripts/sync_agent_adapters.py",
]
ML_MODEL_FILES = [
    "backend/diabetes_model.pkl",
    "backend/heart_disease_model.pkl",
    "backend/liver_disease_model.pkl",
    "backend/liver_scaler.pkl",
    "backend/kidney_model.pkl",
    "backend/kidney_scaler.pkl",
    "backend/lungs_model.pkl",
    "backend/lungs_scaler.pkl",
]

def plugin_info() -> dict[str, object]:
    """Check Antigravity plugin status to help manage token usage."""
    plugins_dir = pathlib.Path.home() / ".gemini" / "config" / "plugins"
    if not plugins_dir.exists():
        return {"exists": False, "plugins": []}
    
    plugins = []
    heavy_enabled = []
    for item in plugins_dir.iterdir():
        if item.is_dir():
            name = item.name
            if name.startswith("_") and name.endswith("_DISABLED"):
                plugins.append({"name": name[1:-9], "enabled": False})
            else:
                plugins.append({"name": name, "enabled": True})
                if name.lower() in ("science", "android-cli-plugin"):
                    heavy_enabled.append(name)
                    
    return {
        "exists": True,
        "plugins": plugins,
        "heavy_enabled_warnings": heavy_enabled
    }


def _run(cmd: list[str], cwd: pathlib.Path | None = None) -> str:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or ROOT,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def database_info() -> dict[str, object]:
    """Detect active database configuration."""
    db_url = os.getenv("DATABASE_URL", "sqlite:///./healthcare.db")
    info: dict[str, object] = {
        "url": db_url,
        "type": "postgresql" if "postgresql" in db_url else "sqlite",
    }

    if info["type"] == "sqlite":
        # Extract path from sqlite URL
        db_path_str = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path_str.startswith("./"):
            db_path = ROOT / db_path_str[2:]
        else:
            db_path = pathlib.Path(db_path_str)

        info["path"] = str(db_path)
        info["exists"] = db_path.exists()
        if db_path.exists():
            info["size_mb"] = round(db_path.stat().st_size / (1024 * 1024), 1)

    return info


def git_info() -> dict[str, object]:
    branch = _run(["git", "branch", "--show-current"]) or "(detached)"
    log = _run(["git", "log", "--oneline", "-5", "--no-decorate"])
    dirty = _run(["git", "status", "--porcelain", "-s"])
    return {
        "branch": branch,
        "dirty_count": len(dirty.splitlines()) if dirty else 0,
        "recent_commits": log.splitlines()[:5] if log else [],
    }


def service_info() -> list[dict[str, object]]:
    services = []
    for name, port in SERVICE_PORTS:
        running = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(("127.0.0.1", port))
            sock.close()
            running = True
        except Exception:
            running = False
        services.append(
            {
                "name": name,
                "host": "127.0.0.1",
                "port": port,
                "running": running,
            }
        )
    return services


def ml_model_info() -> list[dict[str, object]]:
    """Check presence and basic validity of runtime ML artifacts."""
    models = []
    for model_file in ML_MODEL_FILES:
        path = ROOT / model_file
        if path.exists():
            size_bytes = path.stat().st_size
            models.append({
                "name": path.name,
                "path": str(path.relative_to(ROOT)),
                "exists": True,
                "usable": size_bytes > 0,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
            })
        else:
            models.append({
                "name": pathlib.Path(model_file).name,
                "path": model_file,
                "exists": False,
                "usable": False,
            })
    return models


def context_files() -> list[dict[str, object]]:
    items = []
    for rel_path in CONTEXT_FILES:
        path = ROOT / rel_path
        items.append({"path": rel_path, "exists": path.exists()})
    return items


def build_snapshot() -> dict[str, object]:
    return {
        "project": "AI Healthcare System",
        "database": database_info(),
        "git": git_info(),
        "services": service_info(),
        "ml_models": ml_model_info(),
        "context_files": context_files(),
        "plugins": plugin_info(),
        "guidance_order": [
            "Read AGENTS.md first.",
            "Then read the nearest scoped AGENTS.md.",
            "Then read the matching CONTEXT.md only if you need deeper local detail.",
        ],
    }


def _print_text(snapshot: dict[str, object]) -> None:
    print("=" * 60)
    print("  AI HEALTHCARE SYSTEM - AI Session Context Snapshot")
    print("=" * 60)
    print()

    # Database
    db = snapshot["database"]
    db_label = f"{db.get('type', 'unknown').upper()}"
    if db.get("type") == "sqlite":
        db_label += f" - {db.get('path', '?')}"
        if db.get("exists") and "size_mb" in db:
            db_label += f" ({db['size_mb']:.1f} MB)"
        elif not db.get("exists"):
            db_label += " (NOT FOUND)"
    else:
        db_label += f" - {db.get('url', '?')}"
    print(f"Database: {db_label}")
    print()

    # Git
    print("Git Status:")
    print(f"  Branch: {snapshot['git']['branch']}")
    if snapshot["git"]["dirty_count"]:
        print(f"  Uncommitted changes: {snapshot['git']['dirty_count']} files")
    print("  Recent commits:")
    for line in snapshot["git"]["recent_commits"] or ["(no commits)"]:
        print(f"    {line}")
    print()

    # Services
    print("Services:")
    for service in snapshot["services"]:
        status = "[OK]" if service["running"] else "[--]"
        state = "running" if service["running"] else "not running"
        print(f"  {service['name']}: {status} {state} on {service['host']}:{service['port']}")
    print()

    # ML Models
    print("ML Models:")
    for model in snapshot["ml_models"]:
        if model["exists"] and model.get("usable"):
            print(f"  [OK] {model['path']} ({model.get('size_mb', '?')} MB)")
        elif model["exists"]:
            print(f"  [!!] {model['path']} - EMPTY/INVALID (run training scripts)")
        else:
            print(f"  [!!] {model['path']} - MISSING (run training scripts)")
    print()

    # Context Files
    print("Context Files:")
    for item in snapshot["context_files"]:
        status = "[OK]" if item["exists"] else "[!!] MISSING"
        print(f"  {status} {item['path']}")
    print()

    # Plugins
    plugins = snapshot.get("plugins", {})
    if plugins.get("exists"):
        print("Antigravity Plugins & Token Impact:")
        for p in plugins.get("plugins", []):
            status = "[OK] ENABLED " if p["enabled"] else "[--] DISABLED"
            print(f"  {status} {p['name']}")
        warnings = plugins.get("heavy_enabled_warnings", [])
        if warnings:
            print()
            print("  ⚠️  WARNING: Heavy plugins are active!")
            print(f"      {', '.join(warnings)} are loaded and costing significant tokens per turn.")
            print("      Run: python scripts/toggle_plugins.py --disable <name>")
        print()


    print("=" * 60)
    print("  Read AGENTS.md first, then the nearest scoped AGENTS.md")
    print("=" * 60)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AI Healthcare System - Session context snapshot for AI agents."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    snapshot = build_snapshot()
    if args.json:
        print(json.dumps(snapshot, indent=2))
        return 0

    _print_text(snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
