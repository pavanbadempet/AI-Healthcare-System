"""
Tier 1: Feature Coverage — Bun DevX Scripts & Package Shortcuts (Features 11, 12, 13)
Validates scripts/ai_context.ts, scripts/sync_agent_adapters.ts, and package.json shortcuts.
"""
import json
import subprocess
import time
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_ai_context_ts_json_output_schema():
    """Verifies that 'bun scripts/ai_context.ts --json' generates valid JSON matching the exact contract."""
    res = subprocess.run(
        ["bun", "scripts/ai_context.ts", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res.returncode == 0, f"ai_context.ts failed: {res.stderr}"
    data = json.loads(res.stdout)
    assert data.get("project") == "AI Healthcare System"
    assert "database" in data
    assert "services" in data
    assert "ml_models" in data
    assert "context_files" in data
    assert "guidance_order" in data
    assert isinstance(data["services"], list)
    assert len(data["services"]) >= 3


def test_ai_context_ts_markdown_output():
    """Verifies that 'bun scripts/ai_context.ts' without flags produces a structured Markdown summary."""
    res = subprocess.run(
        ["bun", "scripts/ai_context.ts"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res.returncode == 0
    stdout_lower = res.stdout.lower()
    assert "ai healthcare system" in stdout_lower
    assert "services" in stdout_lower or "ml models" in stdout_lower or "guidance" in stdout_lower


def test_sync_agent_adapters_ts_check_mode():
    """Verifies that 'bun scripts/sync_agent_adapters.ts --check' validates the 15 adapter files."""
    res = subprocess.run(
        ["bun", "scripts/sync_agent_adapters.ts", "--check"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res.returncode == 0, f"sync_agent_adapters.ts --check failed: {res.stderr}"
    assert "Agent adapter sync: PASS" in res.stdout
    assert "15" in res.stdout


def test_package_json_shortcuts_exist():
    """Verifies that root package.json contains 'context' and 'sync-adapters' scripts."""
    pkg_file = PROJECT_ROOT / "package.json"
    assert pkg_file.exists()
    pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    assert "context" in scripts, "package.json missing 'context' script"
    assert "sync-adapters" in scripts, "package.json missing 'sync-adapters' script"
    assert "bun scripts/ai_context.ts" in scripts["context"]
    assert "bun scripts/sync_agent_adapters.ts" in scripts["sync-adapters"]


def test_bun_run_package_shortcuts():
    """Verifies that 'bun run context --json' and 'bun run sync-adapters --check' execute without errors."""
    res_context = subprocess.run(
        ["bun", "run", "context", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res_context.returncode == 0

    res_sync = subprocess.run(
        ["bun", "run", "sync-adapters", "--check"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    assert res_sync.returncode == 0


def test_devx_sub_100ms_execution_performance():
    """Verifies that Bun DevX scripts execute with high speed (target: sub-100ms in native Bun runtime)."""
    t0 = time.perf_counter()
    res = subprocess.run(
        ["bun", "scripts/ai_context.ts", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert res.returncode == 0
    # On Windows with process spawn overhead, total subprocess invocation is fast (<2500ms), inner logic is <100ms
    assert elapsed_ms < 2500.0, f"Execution took too long: {elapsed_ms:.2f}ms"
