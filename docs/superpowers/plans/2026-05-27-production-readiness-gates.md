# Production Readiness Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-shortcuts production readiness gate that verifies backend, database, lakehouse/data processing, monitoring, security, AI safety, and operational runbooks before any deployment is attempted.

**Architecture:** Keep production readiness as an explicit release gate, not as deployment automation. Add one script that runs deterministic local checks, one backend unit test file that proves the gate blocks missing critical configuration, and one operator-facing checklist document that records the human signoffs needed before cloud rollout.

**Tech Stack:** Python, pytest, FastAPI backend configuration, PowerShell-friendly CLI commands, Markdown runbooks.

---

## File Structure

- Create: `scripts/production_readiness_check.py`
  - Owns deterministic pre-deployment checks for required env vars, unit test command availability, backend route uniqueness, and required operational docs.
- Create: `tests/unit/test_production_readiness_check.py`
  - Tests the readiness checker without requiring external services or real secrets.
- Create: `docs/PRODUCTION_READINESS_GATE.md`
  - Human-readable gate for database, migrations, Delta/lakehouse, data processing, monitoring, security, privacy, AI safety, rollback, support, and launch approvals.
- Modify: `README.md`
  - Adds a short pointer to the readiness gate without changing product claims.

---

### Task 1: Readiness Checker Skeleton

**Files:**
- Create: `scripts/production_readiness_check.py`
- Test: `tests/unit/test_production_readiness_check.py`

- [ ] **Step 1: Write the failing test**

```python
from scripts.production_readiness_check import CheckResult, summarize_results


def test_summarize_results_fails_when_any_required_check_fails():
    results = [
        CheckResult(name="unit tests", passed=True, detail="430 passed"),
        CheckResult(name="DATABASE_URL", passed=False, detail="missing"),
    ]

    summary = summarize_results(results)

    assert summary.passed is False
    assert "DATABASE_URL" in summary.failed_checks
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_summarize_results_fails_when_any_required_check_fails -q`

Expected: FAIL because `scripts.production_readiness_check` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReadinessSummary:
    passed: bool
    failed_checks: list[str]


def summarize_results(results: list[CheckResult]) -> ReadinessSummary:
    failed = [result.name for result in results if not result.passed]
    return ReadinessSummary(passed=not failed, failed_checks=failed)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_summarize_results_fails_when_any_required_check_fails -q`

Expected: PASS.

---

### Task 2: Critical Environment Gate

**Files:**
- Modify: `scripts/production_readiness_check.py`
- Modify: `tests/unit/test_production_readiness_check.py`

- [ ] **Step 1: Write the failing test**

```python
from scripts.production_readiness_check import check_required_environment


def test_required_environment_blocks_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "production-grade-secret-value-long-enough")

    result = check_required_environment()

    assert result.passed is False
    assert result.name == "required environment"
    assert "DATABASE_URL" in result.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_required_environment_blocks_missing_database_url -q`

Expected: FAIL because `check_required_environment` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
import os


REQUIRED_ENV_VARS = ("DATABASE_URL", "SECRET_KEY")


def check_required_environment() -> CheckResult:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        return CheckResult(
            name="required environment",
            passed=False,
            detail=f"Missing required env vars: {', '.join(missing)}",
        )
    return CheckResult(name="required environment", passed=True, detail="required env vars are set")
```

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests\unit\test_production_readiness_check.py -q`

Expected: all tests in the file pass.

---

### Task 3: Route Uniqueness Gate

**Files:**
- Modify: `scripts/production_readiness_check.py`
- Modify: `tests/unit/test_production_readiness_check.py`

- [ ] **Step 1: Write the failing test**

```python
from scripts.production_readiness_check import find_duplicate_routes


def test_find_duplicate_routes_reports_duplicate_method_path_pairs():
    routes = [
        ("GET", "/admin/users"),
        ("POST", "/admin/users"),
        ("GET", "/admin/users"),
    ]

    duplicates = find_duplicate_routes(routes)

    assert duplicates == ["GET /admin/users"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_find_duplicate_routes_reports_duplicate_method_path_pairs -q`

Expected: FAIL because `find_duplicate_routes` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
from collections import Counter


def find_duplicate_routes(routes: list[tuple[str, str]]) -> list[str]:
    counts = Counter(routes)
    return [
        f"{method} {path}"
        for (method, path), count in sorted(counts.items())
        if count > 1
    ]
```

- [ ] **Step 4: Add the app route check**

```python
def check_duplicate_routes() -> CheckResult:
    from backend.main import app

    routes: list[tuple[str, str]] = []
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        if not methods or not path:
            continue
        for method in methods:
            if method not in {"HEAD", "OPTIONS"}:
                routes.append((method, path))

    duplicates = find_duplicate_routes(routes)
    if duplicates:
        return CheckResult(
            name="duplicate routes",
            passed=False,
            detail=", ".join(duplicates),
        )
    return CheckResult(name="duplicate routes", passed=True, detail="no duplicate method/path routes")
```

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests\unit\test_production_readiness_check.py -q`

Expected: all tests in the file pass.

---

### Task 4: Required Runbook Gate

**Files:**
- Modify: `scripts/production_readiness_check.py`
- Modify: `tests/unit/test_production_readiness_check.py`
- Create: `docs/PRODUCTION_READINESS_GATE.md`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from scripts.production_readiness_check import check_required_docs


def test_required_docs_blocks_missing_gate_file(tmp_path):
    result = check_required_docs(repo_root=tmp_path)

    assert result.passed is False
    assert "docs/PRODUCTION_READINESS_GATE.md" in result.detail
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_required_docs_blocks_missing_gate_file -q`

Expected: FAIL because `check_required_docs` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path


REQUIRED_DOCS = ("docs/PRODUCTION_READINESS_GATE.md",)


def check_required_docs(repo_root: Path | None = None) -> CheckResult:
    root = repo_root or Path(__file__).resolve().parents[1]
    missing = [path for path in REQUIRED_DOCS if not (root / path).exists()]
    if missing:
        return CheckResult(name="required docs", passed=False, detail=", ".join(missing))
    return CheckResult(name="required docs", passed=True, detail="required readiness docs exist")
```

- [ ] **Step 4: Create the gate document**

Create `docs/PRODUCTION_READINESS_GATE.md` with these sections:

```markdown
# Production Readiness Gate

This project must not be deployed to production until every gate below is verified and recorded for the target environment.

## Backend Code Gate

- Unit suite passes with `python -m pytest tests\unit -q`.
- Duplicate route check reports no duplicate method/path pairs.
- `git diff --check -- backend tests scripts docs` passes.

## Database Gate

- Target `DATABASE_URL` points to the intended managed database.
- Migrations/startup schema logic has been tested against a database clone.
- Backup, restore, point-in-time recovery, and retention are documented by the operator.
- No local SQLite database files are used for production.

## Lakehouse And Data Processing Gate

- Raw, curated, and analytics zones are separated by storage path and access policy.
- Delta/lakehouse writes are dry-run tested with synthetic data.
- Batch jobs do not log names, emails, DOBs, tokens, or raw clinical notes.
- Data retention and deletion processes are defined for hospital contracts.

## Monitoring Gate

- Health checks, telemetry, audit logs, and alert channels are configured.
- Admin telemetry is facility-scoped.
- Error logs are reviewed for PII leakage before launch.

## Security Gate

- `SECRET_KEY`, database credentials, payment credentials, AI provider keys, and email credentials are environment-only.
- CORS origins, rate limits, and security headers match the target environment.
- Admin, doctor, nurse, billing, pharmacy, and patient roles are tested in the target environment.
- Facility isolation is tested with at least two synthetic facilities.

## AI Safety Gate

- AI output includes medical disclaimers where health advice is generated.
- AI predictions are presented as review/support information, not autonomous diagnosis.
- Provider calls go through `backend/core_ai.py`.
- External search and logging do not receive patient identifiers.

## Operations Gate

- Rollback procedure is documented and rehearsed.
- Incident response contacts are documented.
- Hospital pilot acceptance criteria are written before go-live.
- Legal/compliance signoff is recorded for the launch country.
```

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests\unit\test_production_readiness_check.py -q`

Expected: all tests in the file pass.

---

### Task 5: CLI Gate Runner

**Files:**
- Modify: `scripts/production_readiness_check.py`
- Modify: `tests/unit/test_production_readiness_check.py`

- [ ] **Step 1: Write the failing test**

```python
from scripts.production_readiness_check import CheckResult, run_checks


def test_run_checks_returns_all_gate_results(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check.check_required_environment",
        lambda: CheckResult("required environment", True, "ok"),
    )
    monkeypatch.setattr(
        "scripts.production_readiness_check.check_required_docs",
        lambda: CheckResult("required docs", True, "ok"),
    )
    monkeypatch.setattr(
        "scripts.production_readiness_check.check_duplicate_routes",
        lambda: CheckResult("duplicate routes", True, "ok"),
    )

    results = run_checks()

    assert [result.name for result in results] == [
        "required environment",
        "required docs",
        "duplicate routes",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\unit\test_production_readiness_check.py::test_run_checks_returns_all_gate_results -q`

Expected: FAIL because `run_checks` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
def run_checks() -> list[CheckResult]:
    return [
        check_required_environment(),
        check_required_docs(),
        check_duplicate_routes(),
    ]
```

- [ ] **Step 4: Add command-line output**

```python
def main() -> int:
    results = run_checks()
    summary = summarize_results(results)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name} - {result.detail}")
    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the gate locally with test env**

Run:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
$env:SECRET_KEY='test-production-readiness-secret-value-long-enough'
$env:TESTING='true'
python scripts\production_readiness_check.py
```

Expected: PASS lines for required environment, required docs, and duplicate routes.

---

### Task 6: README Pointer

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a production-readiness section**

Add this text near the setup or deployment section:

```markdown
## Production Readiness

Do not deploy this system directly from a passing local test run. Before any production rollout, complete the gate in `docs/PRODUCTION_READINESS_GATE.md` and run:

```bash
python scripts/production_readiness_check.py
```

The gate covers backend verification, database readiness, lakehouse/data processing, monitoring, security, AI safety, rollback, and operational signoff.
```

- [ ] **Step 2: Run documentation hygiene check**

Run: `git diff --check -- README.md docs/PRODUCTION_READINESS_GATE.md scripts/production_readiness_check.py tests/unit/test_production_readiness_check.py`

Expected: exit code 0.

---

### Task 7: Final Verification

**Files:**
- Verify: `scripts/production_readiness_check.py`
- Verify: `tests/unit/test_production_readiness_check.py`
- Verify: `docs/PRODUCTION_READINESS_GATE.md`
- Verify: `README.md`

- [ ] **Step 1: Run new readiness tests**

Run: `python -m pytest tests\unit\test_production_readiness_check.py -q`

Expected: all readiness tests pass.

- [ ] **Step 2: Run full backend unit suite**

Run: `python -m pytest tests\unit -q`

Expected: all backend unit tests pass.

- [ ] **Step 3: Run readiness checker**

Run:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
$env:SECRET_KEY='test-production-readiness-secret-value-long-enough'
$env:TESTING='true'
python scripts\production_readiness_check.py
```

Expected: exit code 0 with PASS lines for each gate.

- [ ] **Step 4: Run diff hygiene**

Run: `git diff --check -- scripts tests/unit docs README.md`

Expected: exit code 0.

---

## Self-Review

- Spec coverage: The plan covers backend code, database, Delta/lakehouse data processing, monitoring, security, AI safety, and operations without triggering deployment.
- Placeholder scan: No placeholder words or deferred implementation markers are used.
- Type consistency: `CheckResult`, `ReadinessSummary`, `summarize_results`, `check_required_environment`, `find_duplicate_routes`, `check_duplicate_routes`, `check_required_docs`, `run_checks`, and `main` are named consistently across tasks.
