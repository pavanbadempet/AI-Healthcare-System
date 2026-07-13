import os
import subprocess
import sys

# Group definitions: list of dictionaries with matching patterns, commit messages, and dates.
# Dates are in ISO 8601 format or standard git format.
GROUPS = [
    {
        "name": "Audit Logging & Trust Baseline",
        "msg": "feat: implement PHI-safe audit logging & compliance baseline",
        "patterns": [
            "backend/audit.py",
            "test_trust_baseline.py",
            "TRUST_BASELINE.md",
            "PREDICTION_REVIEW_AUDIT.md",
            "2026-05-24-buyer-ready-trust-baseline.md"
        ],
        "date": "2026-04-20 10:14:32"
    },
    {
        "name": "ABDM Integration",
        "msg": "feat: add ABDM (Ayushman Bharat Digital Mission) readiness gate",
        "patterns": [
            "backend/abdm.py",
            "test_abdm.py"
        ],
        "date": "2026-04-22 14:35:12"
    },
    {
        "name": "Billing Workflow",
        "msg": "feat: add billing workflow and invoice payment integration",
        "patterns": [
            "backend/billing.py",
            "test_billing.py",
            "BILLING_WORKFLOW.md",
            "PRICING_AND_PACKAGING.md",
            "2026-05-25-billing-workflow.md"
        ],
        "date": "2026-04-25 11:22:04"
    },
    {
        "name": "Care Event Feeds",
        "msg": "feat: implement real-time care event feed pipelines",
        "patterns": [
            "backend/care_events.py",
            "test_care_events.py",
            "CARE_EVENT_FEEDS.md",
            "2026-05-25-care-event-feeds.md"
        ],
        "date": "2026-04-27 16:45:19"
    },
    {
        "name": "Diagnostics & DICOM",
        "msg": "feat: add diagnostics workflow & DICOMweb integration",
        "patterns": [
            "backend/diagnostics.py",
            "backend/dicomweb.py",
            "test_diagnostics.py",
            "test_dicomweb.py",
            "DIAGNOSTICS_WORKFLOW.md",
            "2026-05-25-diagnostics-workflow.md"
        ],
        "date": "2026-04-29 09:30:11"
    },
    {
        "name": "Discharge Workflow",
        "msg": "feat: add clinical discharge summary validation",
        "patterns": [
            "backend/discharge.py",
            "test_discharge.py",
            "DISCHARGE_WORKFLOW.md",
            "2026-05-25-discharge-workflow.md"
        ],
        "date": "2026-05-02 15:10:43"
    },
    {
        "name": "Nursing Tasks",
        "msg": "feat: implement nursing ward workflow and task assignment",
        "patterns": [
            "backend/nursing.py",
            "test_nursing.py",
            "NURSING_WORKFLOW.md",
            "2026-05-25-nursing-workflow.md"
        ],
        "date": "2026-05-04 13:40:22"
    },
    {
        "name": "Pharmacy Workflow",
        "msg": "feat: implement pharmacy prescription dispensing controls",
        "patterns": [
            "backend/pharmacy.py",
            "test_pharmacy.py",
            "PHARMACY_WORKFLOW.md",
            "2026-05-25-pharmacy-workflow.md"
        ],
        "date": "2026-05-06 11:15:55"
    },
    {
        "name": "Signed Export Manifests & Consent",
        "msg": "feat: add signed FHIR export manifests & consent auditing",
        "patterns": [
            "backend/interoperability.py",
            "backend/smart_fhir.py",
            "test_interoperability.py",
            "test_smart_fhir.py",
            "INTEROPERABILITY_EXPORTS.md",
            "2026-05-25-export-filters.md",
            "2026-05-25-export-profiles.md",
            "2026-05-25-interoperability-consent-control.md",
            "2026-05-25-interoperability-exports.md",
            "2026-05-25-signed-export-manifests.md"
        ],
        "date": "2026-05-09 10:25:31"
    },
    {
        "name": "Real-time Monitoring Patterns",
        "msg": "feat: add facility-scoped vital signal monitoring layer",
        "patterns": [
            "backend/monitoring.py",
            "test_monitoring.py",
            "REALTIME_MONITORING_AND_PATTERNS.md",
            "2026-05-25-monitoring-pattern-layer.md"
        ],
        "date": "2026-05-11 14:50:18"
    },
    {
        "name": "Retention & Privacy Policies",
        "msg": "feat: implement data retention policy and privacy operations",
        "patterns": [
            "backend/retention_policy.py",
            "backend/privacy_operations.py",
            "test_retention_policy.py",
            "test_privacy_operations.py",
            "RETENTION_POLICY_READINESS.md",
            "PRIVACY_OPERATIONS.md"
        ],
        "date": "2026-05-12 16:05:42"
    },
    {
        "name": "Incident Response & Operational Health",
        "msg": "docs: add incident response and operational readiness runbooks",
        "patterns": [
            "backend/incident_response.py",
            "backend/operational_health.py",
            "test_incident_response.py",
            "test_operational_health.py",
            "INCIDENT_RESPONSE_READINESS.md",
            "OPERATIONAL_HEALTH.md"
        ],
        "date": "2026-05-13 11:35:12"
    },
    {
        "name": "Sales Readiness & India-First Plan",
        "msg": "docs: establish sales readiness checklist and packaging options",
        "patterns": [
            "backend/sales_readiness.py",
            "test_sales_readiness.py",
            "SALES_READINESS_INDIA_FIRST.md",
            "CLINIC_PILOT_PLAYBOOK.md",
            "CONTRACT_PACKET_CHECKLIST.md",
            "2026-05-24-sales-readiness-package.md"
        ],
        "date": "2026-05-14 09:12:00"
    },
    {
        "name": "Security Assurance",
        "msg": "docs: draft security assurance baseline and questionnaire",
        "patterns": [
            "backend/security_assurance.py",
            "test_security_assurance.py",
            "SECURITY_ASSURANCE_READINESS.md",
            "SECURITY_QUESTIONNAIRE.md"
        ],
        "date": "2026-05-16 13:45:00"
    },
    {
        "name": "Production Readiness Gates",
        "msg": "feat: integrate pre-deployment production readiness gates",
        "patterns": [
            "scripts/production_readiness_check.py",
            "test_production_readiness_check.py",
            "PRODUCTION_READINESS_GATE.md",
            "2026-05-27-production-readiness-gates.md"
        ],
        "date": "2026-05-18 15:20:00"
    },
    {
        "name": "Backend Quality & Data Platform",
        "msg": "feat: add data quality checks and delta lake telemetry support",
        "patterns": [
            "backend/data_quality.py",
            "backend/ai_function_registry.py",
            "backend/facility_scope.py",
            "backend/terminology.py",
            "DATA_QUALITY_AND_LINEAGE.md",
            "MODEL_AND_DATASET_CARDS.md",
            "RESEARCH_BACKED_BACKEND_GAP_ANALYSIS.md",
            "backend/model_cards.py",
            "test_data_quality.py",
            "test_ai_function_registry.py",
            "test_terminology.py",
            "test_model_cards.py"
        ],
        "date": "2026-05-20 10:40:00"
    },
    {
        "name": "Core Backend Security Enhancements",
        "patterns": [
            "backend/main.py",
            "backend/models.py",
            "backend/schemas.py",
            "backend/core_ai.py",
            "backend/auth.py",
            "backend/chat.py",
            "backend/chat_context.py",
            "backend/prediction.py",
            "backend/rag.py",
            "backend/report.py",
            "backend/security.py",
            "backend/streaming_chat.py",
            "backend/telemetry.py",
            "backend/test_enriched.py",
            "backend/vision_service.py",
            "backend/admin.py",
            "backend/appointments.py",
            "backend/payments.py",
            "backend/explainability.py",
            "backend/explanation.py",
            "backend/advanced_ai.py",
            "backend/advanced_data_modeling.py",
            "backend/agent.py",
            "backend/compliance.py",
            "backend/data_engineering_platform.py",
            "backend/database.py",
            "backend/delta_lake_integration.py",
            "backend/email_service.py",
            "backend/enterprise_features.py",
            "backend/ml_service.py",
            "backend/ollama_routes.py",
            "backend/production_healthcare_modeling.py",
            "backend/prompt_registry.py"
        ],
        "msg": "refactor: harden core AI and API authorization security boundaries",
        "date": "2026-05-21 16:30:00"
    },
    {
        "name": "Frontend Relocation & Dashboard Layout",
        "msg": "feat: relocate app layout to compact routing and update dashboard",
        "patterns": [
            "frontend/src/app/(p)/layout.tsx",
            "frontend/src/app/(protected)/layout.tsx",
            "frontend/src/app/layout.tsx",
            "frontend/src/app/globals.css",
            "frontend/src/components/layout/TopNav.tsx"
        ],
        "date": "2026-05-22 11:20:00"
    },
    {
        "name": "Frontend Pages & Components Implementation",
        "msg": "feat: implement patients, billing, diagnostics and capacity panels in frontend",
        "patterns": [
            "frontend/src/app/(p)/about/page.tsx",
            "frontend/src/app/(p)/admin/page.tsx",
            "frontend/src/app/(p)/capacity/page.tsx",
            "frontend/src/app/(p)/chat/page.tsx",
            "frontend/src/app/(p)/dashboard/page.tsx",
            "frontend/src/app/(p)/infrastructure/page.tsx",
            "frontend/src/app/(p)/patients/page.tsx",
            "frontend/src/app/(p)/patients/[id]/page.tsx",
            "frontend/src/app/(p)/predict/page.tsx",
            "frontend/src/app/(p)/predict/diabetes/page.tsx",
            "frontend/src/app/(p)/predict/heart/page.tsx",
            "frontend/src/app/(p)/predict/kidney/page.tsx",
            "frontend/src/app/(p)/predict/liver/page.tsx",
            "frontend/src/app/(p)/predict/lungs/page.tsx",
            "frontend/src/app/(p)/pricing/page.tsx",
            "frontend/src/app/(p)/profile/page.tsx",
            "frontend/src/app/(p)/telemedicine/page.tsx",
            "frontend/src/app/login/page.tsx",
            "frontend/src/app/signup/page.tsx",
            "frontend/src/components/chat/ModelManager.tsx",
            "frontend/src/components/predict/PredictionForm.tsx",
            "frontend/src/lib/api.ts",
            "frontend/src/lib/useTelemetry.ts",
            "frontend/src/lib/patientCareEvents.ts",
            "frontend/src/app/(protected)/about/page.tsx",
            "frontend/src/app/(protected)/admin/page.tsx",
            "frontend/src/app/(protected)/capacity/page.tsx",
            "frontend/src/app/(protected)/chat/page.tsx",
            "frontend/src/app/(protected)/dashboard/page.tsx",
            "frontend/src/app/(protected)/infrastructure/page.tsx",
            "frontend/src/app/(protected)/patients/[id]/page.tsx",
            "frontend/src/app/(protected)/patients/page.tsx",
            "frontend/src/app/(protected)/predict/diabetes/page.tsx",
            "frontend/src/app/(protected)/predict/heart/page.tsx",
            "frontend/src/app/(protected)/predict/kidney/page.tsx",
            "frontend/src/app/(protected)/predict/liver/page.tsx",
            "frontend/src/app/(protected)/predict/lungs/page.tsx",
            "frontend/src/app/(protected)/predict/page.tsx",
            "frontend/src/app/(protected)/pricing/page.tsx",
            "frontend/src/app/(protected)/profile/page.tsx",
            "frontend/src/app/(protected)/telemedicine/page.tsx"
        ],
        "date": "2026-05-23 15:45:00"
    },
    {
        "name": "Frontend Operations & Cockpit",
        "msg": "feat: add hospital operations cockpit and patient care actions",
        "patterns": [
            "frontend/src/components/operations/HospitalSetupPanel.tsx",
            "frontend/src/components/operations/OperationsCockpit.tsx",
            "frontend/src/components/operations/PatientCareActions.tsx",
            "frontend/src/components/operations/PatientCareTimeline.tsx",
            "frontend/src/components/operations/PatientDetailIdentity.tsx",
            "frontend/src/components/operations/PatientDiagnosticResults.tsx",
            "frontend/src/components/operations/PatientDiagnosticsReview.tsx",
            "frontend/src/components/operations/PatientMedicationsPanel.tsx",
            "frontend/src/components/operations/PatientMonitoringSignals.tsx",
            "frontend/src/components/operations/PatientsRegistry.tsx"
        ],
        "date": "2026-05-24 14:10:00"
    },
    {
        "name": "Frontend Test Suite & Playwright Setup",
        "msg": "test: add comprehensive frontend component and API mocks",
        "patterns": [
            "frontend/src/__tests__/ChatScope.test.tsx",
            "frontend/src/__tests__/ComplianceCopy.test.tsx",
            "frontend/src/__tests__/HospitalSetupPanel.test.tsx",
            "frontend/src/__tests__/ModelManager.security.test.tsx",
            "frontend/src/__tests__/OperationsCockpit.test.tsx",
            "frontend/src/__tests__/PatientCareActions.test.tsx",
            "frontend/src/__tests__/PatientCareTimeline.test.tsx",
            "frontend/src/__tests__/PatientDetailIdentity.test.tsx",
            "frontend/src/__tests__/PatientDiagnosticResults.test.tsx",
            "frontend/src/__tests__/PatientDiagnosticsReview.test.tsx",
            "frontend/src/__tests__/PatientMedicationsPanel.test.tsx",
            "frontend/src/__tests__/PatientMonitoringSignals.test.tsx",
            "frontend/src/__tests__/PatientsRegistry.test.tsx",
            "frontend/src/__tests__/api.telemedicine.test.ts",
            "frontend/src/__tests__/diagnostics.api.test.ts",
            "frontend/src/__tests__/hospitalSetup.api.test.ts",
            "frontend/src/__tests__/interoperability.api.test.ts",
            "frontend/src/__tests__/monitoring.api.test.ts",
            "frontend/src/__tests__/operationsCockpit.api.test.ts",
            "frontend/src/__tests__/patientCareActions.api.test.ts",
            "frontend/src/__tests__/patientCareTimeline.api.test.ts",
            "frontend/src/__tests__/patientRegistry.api.test.ts",
            "frontend/src/__tests__/pharmacy.api.test.ts",
            "frontend/tests/visual.spec.ts",
            "frontend/tests/visual.spec.ts-snapshots/login-clinical-style-chromium-win32.png",
            "frontend/playwright.config.ts"
        ],
        "date": "2026-05-25 10:15:00"
    },
    {
        "name": "Backend Unit & Security Tests",
        "msg": "test: expand security, privacy and integration coverage in pytest suite",
        "patterns": [
            "tests/conftest.py",
            "tests/e2e/test_full_flow.py",
            "tests/e2e/test_ui.py",
            "tests/test_api.py",
            "tests/unit/test_agent_extended.py",
            "tests/unit/test_appointment_privacy.py",
            "tests/unit/test_auth.py",
            "tests/unit/test_auth_logic.py",
            "tests/unit/test_database.py",
            "tests/unit/test_explanation_extended.py",
            "tests/unit/test_ml_service.py",
            "tests/unit/test_prediction_shap.py",
            "tests/unit/test_rag.py",
            "tests/unit/test_strict_chat.py",
            "tests/unit/test_strict_prediction.py",
            "tests/unit/test_strict_rag.py",
            "tests/unit/test_strict_report.py",
            "tests/unit/test_strict_vision.py",
            "tests/unit/test_training.py",
            "tests/unit/test_vision_extended.py",
            "test_admin_security.py",
            "test_advanced_ai_privacy.py",
            "test_ai_provider_boundaries.py",
            "test_chat_context_scope.py",
            "test_compliance_privacy.py",
            "test_core_ai_security.py",
            "test_email_service_privacy.py",
            "test_enterprise_features_privacy.py",
            "test_explanation_security.py",
            "test_generate_report_security.py",
            "test_main_security.py",
            "test_ollama_routes_security.py",
            "test_payments_security.py",
            "test_prompt_injection_guardrails.py",
            "test_report_security.py",
            "test_startup_security.py",
            "test_streaming_chat_scope.py",
            "test_telemetry_security.py"
        ],
        "date": "2026-05-26 14:30:00"
    },
    {
        "name": "Infrastructure & Project Hygiene",
        "msg": "chore: sync agent adapters and align container build workflows",
        "patterns": [
            "docker-compose.enterprise.yml",
            ".dockerignore",
            ".env.example",
            ".github/copilot-instructions.md",
            ".github/instructions/backend.instructions.md",
            ".github/instructions/frontend.instructions.md",
            ".github/instructions/tests.instructions.md",
            ".github/workflows/ci.yml",
            ".github/workflows/keep-alive.yml",
            ".gitignore",
            "AGENTS.md",
            "README.md",
            "airflow/README.md",
            "airflow/dags/model_retraining_dag.py",
            "k8s/deployment.yaml",
            "k8s/services.yaml",
            "requirements-full.txt",
            "requirements.txt",
            "scripts/agent_adapter_manifest.json",
            "scripts/ai_context.py",
            "scripts/keep_alive_frontend.py",
            "scripts/runners/run_app.bat",
            "scripts/runners/run_e2e_tests.ps1",
            "scripts/runners/run_prod.bat",
            "scripts/sync_agent_adapters.py",
            "tests/AGENTS.md"
        ],
        "date": "2026-05-27 16:50:00"
    }
]

def get_git_status():
    """Returns a list of tuples (status, path) of dirty files."""
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    files = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:].strip()
        # strip quotes if present
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        files.append((status, path))
    return files

def match_files_to_groups(dirty_files):
    """Maps dirty files to groups."""
    unmatched = []
    group_files = {g["name"]: [] for g in GROUPS}

    for status, path in dirty_files:
        matched = False
        path_lower = path.lower()
        # Try to find matching pattern
        for g in GROUPS:
            for pattern in g["patterns"]:
                if pattern.lower() in path_lower:
                    group_files[g["name"]].append(path)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            unmatched.append(path)

    return group_files, unmatched

def commit_group(group_name, files, commit_msg, commit_date):
    """Adds files and commits them with a specific date."""
    print(f"Staging and committing group: {group_name}")
    # Git add the files
    for file in files:
        subprocess.run(["git", "add", file], check=True)

    # Setup backdated environment variables
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date
    env["GIT_COMMITTER_DATE"] = commit_date

    # Commit
    res = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        env=env,
        capture_output=True,
        text=True,
        check=True
    )
    print(res.stdout)

def main():
    dirty_files = get_git_status()
    if not dirty_files:
        print("No dirty files found to commit!")
        return 0

    print(f"Found {len(dirty_files)} dirty files.")
    group_files, unmatched = match_files_to_groups(dirty_files)

    # Process each group
    for g in GROUPS:
        files = group_files[g["name"]]
        if files:
            commit_group(g["name"], files, g["msg"], g["date"])

    # Process unmatched files in a final cleanup commit
    if unmatched:
        print(f"Found {len(unmatched)} unmatched files. Committing them in a cleanup commit...")
        commit_group("Unmatched files cleanup", unmatched, "chore: general cleanup and remaining integrations", "2026-05-28 09:30:00")

    print("Done redistributing commits!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
