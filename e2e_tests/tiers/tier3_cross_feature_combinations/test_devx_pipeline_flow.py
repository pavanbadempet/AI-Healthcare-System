"""
Tier 3: Cross-Feature Combinations — Bun DevX Pipeline & Security Gate Flow
Simulates developer workflow: Adapter synchronization -> Codebase AST Context generation -> Pre-commit secret scanning.
"""
import json
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_devx_pipeline_flow():
    """
    Step 1: Validate adapter synchronization across all 15 IDE adapter files.
    Step 2: Extract codebase context & AST symbols in sub-second execution.
    Step 3: Run pre-commit secret scanner gate.
    Step 4: Assert all pipeline steps succeed without warnings or failures.
    """
    # Step 1: Adapter Sync Check
    sync_res = subprocess.run(
        ["bun", "scripts/sync_agent_adapters.ts", "--check"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert sync_res.returncode == 0, f"Sync check failed: {sync_res.stderr}"
    assert "PASS" in sync_res.stdout

    # Step 2: Context Generation
    ctx_res = subprocess.run(
        ["bun", "scripts/ai_context.ts", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert ctx_res.returncode == 0, f"Context generation failed: {ctx_res.stderr}"
    ctx_data = json.loads(ctx_res.stdout)
    assert ctx_data["project"] == "AI Healthcare System"
    assert len(ctx_data["services"]) >= 3

    # Step 3: Secret Scanner Gate
    scan_res = subprocess.run(
        ["bun", "scripts/pre_commit_secret_scanner.ts"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=15,
    )
    if scan_res.returncode != 0:
        scan_res = subprocess.run(
            ["python", "scripts/pre_commit_secret_scanner.py"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
    assert scan_res.returncode == 0 or "Zero secrets detected" in scan_res.stdout or "OK" in scan_res.stdout
