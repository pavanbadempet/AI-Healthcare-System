import sys
from pathlib import Path

from scripts.production_readiness_check import (
    REQUIRED_DOCS,
    CheckResult,
    _build_route_check_env,
    _ensure_repo_root_on_path,
    check_duplicate_routes,
    check_object_identifier_inventory,
    check_required_docs,
    check_required_environment,
    check_route_inventory,
    classify_route_auth,
    extract_object_identifier_params,
    find_duplicate_routes,
    run_checks,
    summarize_results,
)


def test_summarize_results_fails_when_any_required_check_fails():
    results = [
        CheckResult(name="unit tests", passed=True, detail="430 passed"),
        CheckResult(name="DATABASE_URL", passed=False, detail="missing"),
    ]

    summary = summarize_results(results)

    assert summary.passed is False
    assert "DATABASE_URL" in summary.failed_checks


def test_required_environment_blocks_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "production-grade-secret-value-long-enough")

    result = check_required_environment()

    assert result.passed is False
    assert result.name == "required environment"
    assert "DATABASE_URL" in result.detail


def test_required_environment_rejects_sqlite_outside_testing(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///healthcare.db")
    monkeypatch.setenv("SECRET_KEY", "production-grade-secret-value-long-enough")
    monkeypatch.delenv("TESTING", raising=False)

    result = check_required_environment()

    assert result.passed is False
    assert "DATABASE_URL must not use SQLite outside TESTING=true" in result.detail


def test_required_environment_rejects_weak_secret_outside_testing(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com/healthcare")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.delenv("TESTING", raising=False)

    result = check_required_environment()

    assert result.passed is False
    assert "SECRET_KEY must be production-grade outside TESTING=true" in result.detail


def test_find_duplicate_routes_reports_duplicate_method_path_pairs():
    routes = [
        ("GET", "/admin/users"),
        ("POST", "/admin/users"),
        ("GET", "/admin/users"),
    ]

    duplicates = find_duplicate_routes(routes)

    assert duplicates == ["GET /admin/users"]


def test_route_check_env_forces_safe_test_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod-user:prod-pass@prod-db/healthcare")
    monkeypatch.setenv("SECRET_KEY", "real-production-secret-value-that-is-long-enough")
    monkeypatch.delenv("TESTING", raising=False)

    env = _build_route_check_env()

    assert env["DATABASE_URL"] == "sqlite:///:memory:"
    assert env["TESTING"] == "true"
    assert env["SECRET_KEY"].startswith("test-production-readiness-route-check")


def test_duplicate_routes_reports_route_collection_failure(monkeypatch):
    def fail_to_collect_routes():
        raise RuntimeError("DATABASE_URL environment variable is not set")

    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        fail_to_collect_routes,
    )

    result = check_duplicate_routes()

    assert result.passed is False
    assert result.name == "duplicate routes"
    assert "backend route collection failed" in result.detail


def test_duplicate_routes_reports_duplicate_collected_routes(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        lambda: [("GET", "/admin/users"), ("GET", "/admin/users")],
    )

    result = check_duplicate_routes()

    assert result.passed is False
    assert result.detail == "GET /admin/users"


def test_route_auth_classification_for_known_route_families():
    assert classify_route_auth("GET", "/healthz") == "public"
    assert classify_route_auth("GET", "/admin/users") == "admin"
    assert classify_route_auth("POST", "/admin/reload_models") == "admin"
    assert classify_route_auth("GET", "/users/{user_id}/full") == "admin"
    assert classify_route_auth("GET", "/events/admin/patients/{patient_id}/feed") == "admin"
    assert classify_route_auth("GET", "/monitoring/admin/patterns") == "admin"
    assert classify_route_auth("GET", "/billing/admin/invoices") == "billing_or_admin"
    assert classify_route_auth("POST", "/billing/invoices/{invoice_id}/payments") == "billing_or_admin"
    assert classify_route_auth("GET", "/pharmacy/admin/metrics") == "pharmacy_or_admin"
    assert classify_route_auth("POST", "/pharmacy/prescriptions/{prescription_id}/dispense") == "pharmacy_or_admin"
    assert classify_route_auth("PUT", "/monitoring/signals/{signal_id}/resolve") == "doctor_or_admin"
    assert classify_route_auth("PUT", "/diagnostics/results/{result_id}/review") == "doctor_or_admin"
    assert classify_route_auth("PUT", "/discharge/summaries/{summary_id}/finalize") == "doctor_or_admin"
    assert classify_route_auth("PUT", "/nursing/tasks/{task_id}/complete") == "nurse_or_admin"
    assert classify_route_auth("DELETE", "/records/{record_id}") == "owner"
    assert classify_route_auth("PUT", "/appointments/{appointment_id}/cancel") == "owner_or_admin"
    assert classify_route_auth("GET", "/interop/exports/{export_id}/manifest") == "scoped_export"
    assert classify_route_auth("GET", "/interop/patient/fhir-bundle") == "patient"
    assert classify_route_auth("GET", "/interop/doctor/patients/{patient_id}/fhir-bundle") == "doctor_or_admin"
    assert classify_route_auth("POST", "/predict/reviews") == "doctor_or_admin"
    assert classify_route_auth("POST", "/predict/diabetes") == "authenticated"


def test_route_inventory_reports_auth_class_counts(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        lambda: [
            ("GET", "/healthz"),
            ("GET", "/admin/users"),
            ("POST", "/predict/diabetes"),
            ("POST", "/predict/reviews"),
            ("GET", "/billing/admin/invoices"),
            ("GET", "/pharmacy/admin/metrics"),
        ],
    )

    result = check_route_inventory()

    assert result.passed is True
    assert result.name == "route inventory"
    assert "public=1" in result.detail
    assert "admin=1" in result.detail
    assert "authenticated=1" in result.detail
    assert "billing_or_admin=1" in result.detail
    assert "doctor_or_admin=1" in result.detail
    assert "pharmacy_or_admin=1" in result.detail


def test_extract_object_identifier_params_from_route_path():
    assert extract_object_identifier_params("/events/doctor/patients/{patient_id}/feed") == [
        "patient_id"
    ]
    assert extract_object_identifier_params("/admin/users/{user_id}/facility") == ["user_id"]
    assert extract_object_identifier_params("/healthz") == []


def test_object_identifier_inventory_reports_review_counts(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        lambda: [
            ("GET", "/healthz"),
            ("GET", "/events/doctor/patients/{patient_id}/feed"),
            ("PUT", "/admin/users/{user_id}/role"),
            ("POST", "/billing/invoices/{invoice_id}/payments"),
        ],
    )

    result = check_object_identifier_inventory()

    assert result.passed is True
    assert result.name == "object identifier inventory"
    assert "object_id_routes=3" in result.detail
    assert "patient_id=1" in result.detail
    assert "user_id=1" in result.detail
    assert "domain_object_id=1" in result.detail


def test_object_identifier_inventory_fails_public_object_routes(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        lambda: [
            ("GET", "/healthz"),
            ("GET", "/static/patients/{patient_id}"),
        ],
    )

    result = check_object_identifier_inventory()

    assert result.passed is False
    assert "public object identifier route" in result.detail
    assert "GET /static/patients/{patient_id}" in result.detail


def test_object_identifier_inventory_fails_unclassified_authenticated_object_routes(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_readiness_check._collect_backend_routes",
        lambda: [
            ("GET", "/healthz"),
            ("PATCH", "/workflow/items/{item_id}"),
        ],
    )

    result = check_object_identifier_inventory()

    assert result.passed is False
    assert "unclassified object identifier route" in result.detail
    assert "PATCH /workflow/items/{item_id}" in result.detail


def test_ensure_repo_root_on_path_adds_repo_root(monkeypatch, tmp_path: Path):
    scripts_path = tmp_path / "scripts"
    scripts_path.mkdir()
    monkeypatch.setattr(sys, "path", [str(scripts_path)])

    _ensure_repo_root_on_path(repo_root=tmp_path)

    assert sys.path[0] == str(tmp_path)


def test_required_docs_blocks_missing_gate_file(tmp_path: Path):
    result = check_required_docs(repo_root=tmp_path)

    assert result.passed is False
    assert "docs/PRODUCTION_READINESS_GATE.md" in result.detail


def test_required_docs_blocks_missing_required_sections(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    for required_doc in REQUIRED_DOCS:
        if required_doc == "docs/PRODUCTION_READINESS_GATE.md":
            continue
        required_path = tmp_path / required_doc
        required_path.parent.mkdir(parents=True, exist_ok=True)
        required_path.write_text("# Placeholder\n", encoding="utf-8")
    (docs_dir / "PRODUCTION_READINESS_GATE.md").write_text(
        "# Production Readiness Gate\n\n## Backend Code Gate\n",
        encoding="utf-8",
    )

    result = check_required_docs(repo_root=tmp_path)

    assert result.passed is False
    assert "Security Gate" in result.detail
    assert "Lakehouse And Data Processing Gate" in result.detail


def test_required_docs_blocks_missing_operational_readiness_docs(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "PRODUCTION_READINESS_GATE.md").write_text(
        "\n".join([
            "# Production Readiness Gate",
            "## Backend Code Gate",
            "## Database Gate",
            "## Lakehouse And Data Processing Gate",
            "## Monitoring Gate",
            "## Security Gate",
            "## AI Safety Gate",
            "## Operations Gate",
        ]),
        encoding="utf-8",
    )

    result = check_required_docs(repo_root=tmp_path)

    assert result.passed is False
    assert "docs/BACKUP_AND_RESTORE_READINESS.md" in result.detail
    assert "docs/SECURITY_ASSURANCE_READINESS.md" in result.detail


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
    monkeypatch.setattr(
        "scripts.production_readiness_check.check_route_inventory",
        lambda: CheckResult("route inventory", True, "ok"),
    )
    monkeypatch.setattr(
        "scripts.production_readiness_check.check_object_identifier_inventory",
        lambda: CheckResult("object identifier inventory", True, "ok"),
    )

    results = run_checks()

    assert [result.name for result in results] == [
        "required environment",
        "required docs",
        "duplicate routes",
        "route inventory",
        "object identifier inventory",
    ]
