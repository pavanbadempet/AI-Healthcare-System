import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


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


REQUIRED_ENV_VARS = ("DATABASE_URL", "SECRET_KEY")
REQUIRED_DOCS = (
    "docs/PRODUCTION_READINESS_GATE.md",
    "docs/OPERATIONAL_HEALTH.md",
    "docs/PRIVACY_OPERATIONS.md",
    "docs/BACKUP_AND_RESTORE_READINESS.md",
    "docs/INCIDENT_RESPONSE_READINESS.md",
    "docs/RETENTION_POLICY_READINESS.md",
    "docs/SECURITY_ASSURANCE_READINESS.md",
)
REQUIRED_READINESS_SECTIONS = (
    "Backend Code Gate",
    "Database Gate",
    "Lakehouse And Data Processing Gate",
    "Monitoring Gate",
    "Security Gate",
    "AI Safety Gate",
    "Operations Gate",
)
ROUTE_CHECK_SECRET_KEY = "test-production-readiness-route-check-secret-value"
ROUTE_CHECK_CODE = r"""
import json

from backend.main import app

routes = []
for route in app.routes:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    if not methods or not path:
        continue
    for method in methods:
        if method not in {"HEAD", "OPTIONS"}:
            routes.append((method, path))

print("ROUTES_JSON:" + json.dumps(routes))
"""


def _is_testing() -> bool:
    return os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes"}


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.strip().lower().startswith("sqlite")


def _has_production_grade_secret(secret_key: str) -> bool:
    normalized = secret_key.strip().lower()
    if len(secret_key.strip()) < 32:
        return False
    return not any(marker in normalized for marker in ("test", "dev", "changeme", "secret-key"))


def check_required_environment() -> CheckResult:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    failures = [f"missing {name}" for name in missing]
    testing = _is_testing()
    database_url = os.getenv("DATABASE_URL", "")
    secret_key = os.getenv("SECRET_KEY", "")

    if database_url and not testing and _is_sqlite_url(database_url):
        failures.append("DATABASE_URL must not use SQLite outside TESTING=true")
    if secret_key and not testing and not _has_production_grade_secret(secret_key):
        failures.append("SECRET_KEY must be production-grade outside TESTING=true")

    if failures:
        return CheckResult(
            name="required environment",
            passed=False,
            detail="; ".join(failures),
        )
    return CheckResult(
        name="required environment",
        passed=True,
        detail="required environment is present and production-safe",
    )


def find_duplicate_routes(routes: list[tuple[str, str]]) -> list[str]:
    counts = Counter(routes)
    return [
        f"{method} {path}"
        for (method, path), count in sorted(counts.items())
        if count > 1
    ]


def classify_route_auth(method: str, path: str) -> str:
    """Classify route exposure for readiness review.

    This is a conservative inventory aid, not an authorization proof. Focused
    route tests still own behavior-level access verification.
    """
    normalized_method = method.upper()
    normalized_path = path.rstrip("/") or "/"
    public_paths = {
        "/",
        "/healthz",
        "/signup",
        "/token",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    if normalized_path in public_paths:
        return "public"
    if normalized_path.startswith("/static"):
        return "public"
    if normalized_path.startswith("/billing/admin"):
        return "billing_or_admin"
    if normalized_path == "/billing/invoices/{invoice_id}/payments":
        return "billing_or_admin"
    if normalized_path.startswith("/pharmacy/admin"):
        return "pharmacy_or_admin"
    if normalized_path == "/pharmacy/prescriptions/{prescription_id}/dispense":
        return "pharmacy_or_admin"
    if normalized_path == "/nursing/tasks/{task_id}/complete":
        return "nurse_or_admin"
    if normalized_path == "/records/{record_id}":
        return "owner"
    if normalized_path.startswith("/appointments/{appointment_id}"):
        return "owner_or_admin"
    if normalized_path == "/interop/exports/{export_id}/manifest":
        return "scoped_export"
    if normalized_path == "/users/{user_id}/full":
        return "admin"
    if normalized_path.startswith("/admin") or normalized_path == "/admin/reload_models":
        return "admin"
    if "/admin/" in normalized_path:
        return "admin"
    if normalized_path.startswith("/ai/models"):
        return "admin"
    if normalized_path.startswith("/telemetry"):
        return "admin"
    if normalized_path.startswith("/interop/patient"):
        return "patient"
    if normalized_path.startswith("/interop/doctor"):
        return "doctor_or_admin"
    if normalized_path == "/predict/reviews":
        return "doctor_or_admin"
    if normalized_path in {
        "/monitoring/signals/{signal_id}/resolve",
        "/diagnostics/results/{result_id}/review",
        "/discharge/summaries/{summary_id}/finalize",
    }:
        return "doctor_or_admin"
    if "/patient/" in normalized_path or normalized_path.endswith("/patient"):
        return "patient"
    if "/doctor/" in normalized_path or normalized_path.endswith("/doctor"):
        return "doctor_or_admin"
    if normalized_method == "WEBSOCKET":
        return "system_websocket"
    return "authenticated"


def _ensure_repo_root_on_path(repo_root: Path | None = None) -> None:
    root = repo_root or Path(__file__).resolve().parents[1]
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)


def _build_route_check_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["DATABASE_URL"] = "sqlite:///:memory:"
    env["SECRET_KEY"] = ROUTE_CHECK_SECRET_KEY
    env["TESTING"] = "true"
    return env


def _parse_routes_from_stdout(stdout: str) -> list[tuple[str, str]]:
    for line in reversed(stdout.splitlines()):
        if line.startswith("ROUTES_JSON:"):
            payload = json.loads(line.removeprefix("ROUTES_JSON:"))
            return [(method, path) for method, path in payload]
    raise RuntimeError("route output missing")


def _collect_backend_routes() -> list[tuple[str, str]]:
    repo_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, "-c", ROUTE_CHECK_CODE],
        cwd=str(repo_root),
        env=_build_route_check_env(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("backend route subprocess failed")
    return _parse_routes_from_stdout(completed.stdout)


def check_duplicate_routes() -> CheckResult:
    try:
        routes = _collect_backend_routes()
    except Exception:
        return CheckResult(
            name="duplicate routes",
            passed=False,
            detail="backend route collection failed; run required environment check first",
        )

    duplicates = find_duplicate_routes(routes)
    if duplicates:
        return CheckResult(
            name="duplicate routes",
            passed=False,
            detail=", ".join(duplicates),
        )
    return CheckResult(
        name="duplicate routes",
        passed=True,
        detail="no duplicate method/path routes",
    )


def check_route_inventory() -> CheckResult:
    try:
        routes = _collect_backend_routes()
    except Exception:
        return CheckResult(
            name="route inventory",
            passed=False,
            detail="backend route inventory collection failed",
        )
    if not routes:
        return CheckResult(
            name="route inventory",
            passed=False,
            detail="no backend routes found",
        )
    counts = Counter(classify_route_auth(method, path) for method, path in routes)
    detail = ", ".join(
        f"{auth_class}={count}"
        for auth_class, count in sorted(counts.items())
    )
    return CheckResult(
        name="route inventory",
        passed=True,
        detail=detail,
    )


def extract_object_identifier_params(path: str) -> list[str]:
    params = re.findall(r"{([^{}]+)}", path)
    return [param for param in params if param == "id" or param.endswith("_id")]


def _object_identifier_bucket(param: str) -> str:
    if param in {"patient_id", "user_id"}:
        return param
    return "domain_object_id"


def check_object_identifier_inventory() -> CheckResult:
    try:
        routes = _collect_backend_routes()
    except Exception:
        return CheckResult(
            name="object identifier inventory",
            passed=False,
            detail="backend object identifier inventory collection failed",
        )

    object_id_routes = [
        (method, path, extract_object_identifier_params(path))
        for method, path in routes
    ]
    object_id_routes = [
        (method, path, params)
        for method, path, params in object_id_routes
        if params
    ]
    public_object_routes = [
        f"{method} {path}"
        for method, path, _ in object_id_routes
        if classify_route_auth(method, path) == "public"
    ]
    if public_object_routes:
        return CheckResult(
            name="object identifier inventory",
            passed=False,
            detail="public object identifier route: " + ", ".join(public_object_routes),
        )
    unclassified_object_routes = [
        f"{method} {path}"
        for method, path, _ in object_id_routes
        if classify_route_auth(method, path) == "authenticated"
    ]
    if unclassified_object_routes:
        return CheckResult(
            name="object identifier inventory",
            passed=False,
            detail="unclassified object identifier route: " + ", ".join(unclassified_object_routes),
        )
    param_counts = Counter(
        _object_identifier_bucket(param)
        for _, _, params in object_id_routes
        for param in params
    )
    detail_parts = [f"object_id_routes={len(object_id_routes)}"]
    detail_parts.extend(
        f"{bucket}={count}"
        for bucket, count in sorted(param_counts.items())
    )
    return CheckResult(
        name="object identifier inventory",
        passed=True,
        detail=", ".join(detail_parts),
    )


def check_required_docs(repo_root: Path | None = None) -> CheckResult:
    root = repo_root or Path(__file__).resolve().parents[1]
    missing_paths = [path for path in REQUIRED_DOCS if not (root / path).exists()]
    if missing_paths:
        return CheckResult(
            name="required docs",
            passed=False,
            detail=", ".join(missing_paths),
        )

    gate_text = (root / "docs/PRODUCTION_READINESS_GATE.md").read_text(encoding="utf-8")
    missing_sections = [
        section for section in REQUIRED_READINESS_SECTIONS if f"## {section}" not in gate_text
    ]
    if missing_sections:
        return CheckResult(
            name="required docs",
            passed=False,
            detail="Missing readiness sections: " + ", ".join(missing_sections),
        )
    return CheckResult(
        name="required docs",
        passed=True,
        detail="required readiness docs and sections exist",
    )


def run_checks() -> list[CheckResult]:
    return [
        check_required_environment(),
        check_required_docs(),
        check_duplicate_routes(),
        check_route_inventory(),
        check_object_identifier_inventory(),
    ]


def main() -> int:
    results = run_checks()
    summary = summarize_results(results)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name} - {result.detail}")
    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
