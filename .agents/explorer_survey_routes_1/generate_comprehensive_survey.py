import json
import os
from collections import defaultdict

def generate_survey():
    with open(".agents/explorer_survey_routes_1/openapi.json", "r", encoding="utf-8") as f:
        openapi = json.load(f)

    with open(".agents/explorer_survey_routes_1/frontend_api_calls.json", "r", encoding="utf-8") as f:
        frontend_data = json.load(f)

    paths = openapi.get("paths", {})
    schemas = openapi.get("components", {}).get("schemas", {})

    # Group by tag
    tag_groups = defaultdict(list)
    for path_str, path_item in paths.items():
        for method_str, op in path_item.items():
            if method_str.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
            tags = op.get("tags", ["Top-Level & System"])
            tag = tags[0] if tags else "Top-Level & System"
            tag_groups[tag].append({
                "path": path_str,
                "method": method_str.upper(),
                "op_id": op.get("operationId", ""),
                "summary": op.get("summary", ""),
                "description": op.get("description", ""),
                "parameters": op.get("parameters", []),
                "request_body": op.get("requestBody", {}),
                "responses": op.get("responses", {}),
                "security": op.get("security", []),
            })

    lines = []
    lines.append("# AI Healthcare System — Route & API Contract Specification Survey")
    lines.append("")
    lines.append("> Authoritative API specification compiled for the Rust (Axum/Tokio) + Bun (ElysiaJS) backend migration.")
    lines.append("")
    lines.append("## 1. Executive Summary & System Overview")
    lines.append("")
    lines.append("- **Total Logical Domains / Routers**: 40 router modules registered in `backend/main.py` + top-level routes")
    lines.append(f"- **Total Unique REST Paths**: {len(paths)}")
    total_ops = sum(len(ops) for ops in tag_groups.values())
    lines.append(f"- **Total HTTP Operations (Method + Path)**: {total_ops}")
    lines.append(f"- **Total Component Schemas (Pydantic / OpenAPI)**: {len(schemas)}")
    lines.append("- **WebSocket Endpoints**: 4 route bindings (2 unique handlers: Telemetry Operations Stream, Patient Vitals Stream)")
    lines.append("- **Server-Sent Events (SSE) Endpoints**: 2 streaming channels (`/v1/chat/stream`, `/v1/appointments/agent-stream`)")
    lines.append("- **Authentication & Security Schemes**: OAuth2 Password Bearer (`/v1/token`), HTTP Bearer JWT tokens (HS256), TOTP 2FA, Multi-Tenant Facility Scoping (`facility_id`), B2B Enterprise Licensing Gate (`enforce_license_tier`)")
    lines.append("")
    lines.append("### Router Domain Breakdown")
    lines.append("| Tag / Domain | Operation Count | Primary Prefix | Target Migration Module |")
    lines.append("| --- | --- | --- | --- |")
    for tag, ops in sorted(tag_groups.items(), key=lambda x: len(x[1]), reverse=True):
        sample_path = ops[0]["path"] if ops else ""
        parts = sample_path.strip("/").split("/")
        prefix = f"/{parts[0]}/{parts[1]}" if len(parts) > 1 and parts[0] == "v1" else f"/{parts[0]}" if parts else "/"
        lines.append(f"| {tag} | {len(ops)} | `{prefix}` | `rust_gateway::routes::{tag.lower().replace(' ', '_').replace('-', '_')}` |")
    lines.append("")

    lines.append("---")
    lines.append("## 2. Exhaustive Domain & Router Catalog")
    lines.append("")

    tag_idx = 1
    for tag, ops in sorted(tag_groups.items(), key=lambda x: len(x[1]), reverse=True):
        lines.append(f"### 2.{tag_idx} {tag} ({len(ops)} Endpoints)")
        lines.append("")
        lines.append("| Method | Full Route Path | Summary / Description | Auth & Security | Request Body / Params | Response Codes & Schema |")
        lines.append("| --- | --- | --- | --- | --- | --- |")

        for op in sorted(ops, key=lambda x: (x["path"], x["method"])):
            method = op["method"]
            path = op["path"]
            summary = op["summary"] or op["description"] or op["op_id"]
            summary = summary.replace("\n", " ").replace("|", "\\|")[:80]

            # Security
            sec_list = []
            if op["security"]:
                for s in op["security"]:
                    sec_list.extend(list(s.keys()))
            sec_str = ", ".join(sec_list) if sec_list else "Public / None"

            # Params & Request Body
            param_parts = []
            for p in op["parameters"]:
                p_name = p.get("name", "")
                p_in = p.get("in", "")
                p_req = "req" if p.get("required") else "opt"
                p_type = p.get("schema", {}).get("type", "any")
                param_parts.append(f"`{p_name}` ({p_in}:{p_type}:{p_req})")
            
            req_body_str = ""
            if op["request_body"]:
                content = op["request_body"].get("content", {})
                for ctype, cobj in content.items():
                    schema_obj = cobj.get("schema", {})
                    if "$ref" in schema_obj:
                        ref_name = schema_obj["$ref"].split("/")[-1]
                        req_body_str = f"Body: `{ref_name}`"
                    elif "items" in schema_obj and "$ref" in schema_obj["items"]:
                        ref_name = schema_obj["items"]["$ref"].split("/")[-1]
                        req_body_str = f"Body: `List[{ref_name}]`"
                    else:
                        req_body_str = f"Body: `{schema_obj.get('type', 'json')}`"

            input_str = "<br>".join(filter(None, [", ".join(param_parts) if param_parts else "", req_body_str]))
            if not input_str:
                input_str = "None"

            # Responses
            res_parts = []
            for code, robj in op["responses"].items():
                r_desc = robj.get("description", "")
                r_schema = "any"
                content = robj.get("content", {})
                for ctype, cobj in content.items():
                    schema_obj = cobj.get("schema", {})
                    if "$ref" in schema_obj:
                        r_schema = schema_obj["$ref"].split("/")[-1]
                    elif "items" in schema_obj and "$ref" in schema_obj["items"]:
                        r_schema = "List[" + schema_obj["items"]["$ref"].split("/")[-1] + "]"
                    else:
                        r_schema = schema_obj.get("type", "json")
                res_parts.append(f"`{code}`: `{r_schema}`")
            res_str = "<br>".join(res_parts) if res_parts else "`200`: `OK`"

            lines.append(f"| `{method}` | `{path}` | {summary} | {sec_str} | {input_str} | {res_str} |")
        
        lines.append("")
        tag_idx += 1

    lines.append("---")
    lines.append("## 3. Real-Time Streaming & WebSocket Specifications")
    lines.append("")
    lines.append("### 3.1 Telemetry Streaming WebSockets")
    lines.append("- **Routes**: `/v1/telemetry/stream` and `/telemetry/stream`")
    lines.append("- **Protocol**: WebSocket (`ws://` / `wss://`)")
    lines.append("- **Authentication**: Query parameter `?token=<JWT_ACCESS_TOKEN>`")
    lines.append("- **Authorization**: Admin only (`auth.is_admin(current_user) == True`). Rejects unauthorized clients with WebSocket Close code `1008` (Policy Violation).")
    lines.append("- **Push Frequency**: Emits real-time hospital telemetry snapshot every 2.0 seconds.")
    lines.append("- **Message Payload Schema (JSON)**:")
    lines.append("```json")
    lines.append(json.dumps({
        "timestamp": "2026-08-21T05:15:00.000Z",
        "facility_id": 1,
        "source": "database",
        "active_census": 42,
        "total_capacity": 100,
        "open_monitoring_signals": 3,
        "system_latency_ms": 12,
        "spark_batch_id": 1024,
        "spark_records_processed": 16,
        "spark_ml_latency_ms": 3.2,
        "is_real_stream": False,
        "ai_nodes_active": 12,
        "cpu_percent": 14.5,
        "ram_percent": 45.2,
        "hl7_logs": [{"id": "1724217300.12", "time": "10:45:00", "msg": "[REDACTED] ADT^A01..."}],
        "ed_boarding": 14,
        "ed_avg_wait_min": 115,
        "pending_discharges": 6,
        "confirmed_discharges": 3,
        "surge_prediction_pct": 15,
        "department_loads": [{"dept": "ICU-A", "load": 90, "status": "Critical"}],
        "bed_units": [{"unit": "ICU-A", "total": 20, "occupied": 18, "cleaning": 1, "available": 1}]
    }, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("### 3.2 Patient Vitals Live Stream WebSocket")
    lines.append("- **Routes**: `/v1/telemetry/vitals/{patient_id}` and `/telemetry/vitals/{patient_id}`")
    lines.append("- **Protocol**: WebSocket (`ws://` / `wss://`)")
    lines.append("- **Authentication**: Query parameter `?token=<JWT_ACCESS_TOKEN>`")
    lines.append("- **Push Behavior**: Checks for newly recorded `VitalObservation` records every 2.0 seconds and pushes update if `observed_at` timestamp changed.")
    lines.append("- **Message Payload Schema (JSON)**:")
    lines.append("```json")
    lines.append(json.dumps({
        "heart_rate": 78.0,
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "spo2": 98.5,
        "temperature_c": 36.8,
        "blood_glucose": 95.0,
        "observed_at": "2026-08-21T05:15:00.000Z"
    }, indent=2))
    lines.append("```")
    lines.append("")

    lines.append("### 3.3 Server-Sent Events (SSE) AI Streaming Chat")
    lines.append("- **Route**: `POST /v1/chat/stream`")
    lines.append("- **Headers**: `Content-Type: application/json`, `Authorization: Bearer <token>`, optional `x-ai-provider: <str>`, `x-ai-api-key: <str>`")
    lines.append("- **Response Media Type**: `text/event-stream`")
    lines.append("- **SSE Event Sequence**:")
    lines.append("  1. Metadata chunk: `data: {\"sources\": [...], \"model\": \"llama3\", \"status\": \"starting\"}`")
    lines.append("  2. Optional Tool Call: `data: {\"status\": \"tool_call\", \"tool\": \"Clinical Analyzer\", \"details\": \"...\"}`")
    lines.append("  3. Token stream chunks: `data: {\"reply\": \"token_chunk\"}`")
    lines.append("  4. Heartbeat keepalives (every 15s idle): `:heartbeat (keepalive)`")
    lines.append("  5. Completion event: `data: {\"reply\": \"\\n\\n*Medical Disclaimer*\"}` followed by `data: {\"status\": \"complete\"}`")
    lines.append("")

    lines.append("---")
    lines.append("## 4. Authentication, Authorization & Security Architecture")
    lines.append("")
    lines.append("### 4.1 Token Issuance & Verification")
    lines.append("- **Token Endpoint**: `POST /v1/token`")
    lines.append("- **Payload Format**: Form URL Encoded (`OAuth2PasswordRequestForm`: `username`, `password`, optional `totp_code`)")
    lines.append("- **Brute-Force Guard**: 5 consecutive failed attempts trigger a 15-minute account lockout.")
    lines.append("- **Token Format**: JWT with `HS256` signature.")
    lines.append("- **Claims**: `{\"sub\": \"<username>\", \"exp\": <timestamp>}`")
    lines.append("- **Expiration**: Default 525,600 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).")
    lines.append("- **Header Scheme**: `Authorization: Bearer <access_token>`")
    lines.append("")
    lines.append("### 4.2 Multi-Factor Authentication (2FA / TOTP)")
    lines.append("- `POST /v1/2fa/setup`: Generates Base32 TOTP secret & PNG QR Code data URI (`schemas.TOTPSetupResponse`).")
    lines.append("- `POST /v1/2fa/enable`: Accepts 6-digit TOTP code (`schemas.TOTPVerifyRequest`), validates against secret, enables 2FA flag on user.")
    lines.append("")
    lines.append("### 4.3 Multi-Tenant Isolation & Role Hierarchy")
    lines.append("- **Roles**: `admin`, `doctor`, `nurse`, `patient`, `auditor`, `billing_specialist`")
    lines.append("- **Facility Scoping**: Users, Beds, Departments, Encounters, Admissions, Orders, Diagnostics, Prescriptions are tagged with `facility_id`.")
    lines.append("- **Licensing Gate**: `licensing.enforce_license_tier(...)` checks `LICENSE_KEY` for tiers (`community`, `clinical`, `enterprise`).")
    lines.append("")

    lines.append("---")
    lines.append("## 5. Frontend API Contract Matrix")
    lines.append("")
    lines.append("The React SPA (`frontend/src/`) communicates via `frontend/src/lib/apiCore.ts` (base URL `http://127.0.0.1:8000/v1`).")
    lines.append("")
    lines.append("| Frontend Module | UI Consumer Pages | Primary Backend Endpoints Called |")
    lines.append("| --- | --- | --- |")
    lines.append("| `apiAuth.ts` | Login, Signup, Profile, Settings | `/v1/token`, `/v1/signup`, `/v1/profile`, `/v1/me`, `/v1/2fa/*`, `/v1/forgot-password`, `/v1/reset-password` |")
    lines.append("| `apiPredictions.ts` | Disease Predictor Pages | `/v1/predict/heart`, `/v1/predict/diabetes`, `/v1/predict/kidney`, `/v1/predict/liver`, `/v1/predict/lungs`, `/v1/predict/stroke`, `/v1/predict/multi-organ`, `/v1/predict/advisory-board/*`, `/v1/predict/consensus/*`, `/v1/predict/scribe/*` |")
    lines.append("| `apiHospital.ts` | Hospital Operations, Admissions, Beds | `/v1/hospital/departments`, `/v1/hospital/beds`, `/v1/hospital/encounters`, `/v1/hospital/admissions`, `/v1/hospital/orders`, `/v1/hospital/doctor/patients`, `/v1/hospital/triage-queue`, `/v1/hospital/admin/operations` |")
    lines.append("| `apiAdmin.ts` | Admin Dashboard, Governance, Audit | `/v1/admin/stats`, `/v1/admin/users`, `/v1/admin/patients`, `/v1/admin/audit-logs`, `/v1/admin/model-cards`, `/v1/admin/maintenance`, `/v1/admin/agents/*` |")
    lines.append("| `apiBilling.ts` | Billing, Claims, Licensing | `/v1/billing/admin/metrics`, `/v1/billing/claims/submit`, `/v1/billing/estimate`, `/v1/licensing/status`, `/v1/licensing/activate` |")
    lines.append("| `apiChat.ts` | AI Copilot Chat | `/v1/chat`, `/v1/chat/stream`, `/v1/chat/context`, `/v1/chat/suggestions`, `/v1/chat/history` |")
    lines.append("| `apiIntelligence.ts` | Clinical Studio, Alerts | `/v1/intelligence/alerts`, `/v1/intelligence/insights/*`, `/v1/intelligence/explainability/*` |")
    lines.append("| `apiLakehouse.ts` | Data Lakehouse Studio | `/api/v1/data-platform/sql/execute`, `/api/v1/data-platform/bi/ask`, `/v1/lakehouse/*` |")
    lines.append("| `useTelemetry.ts` | Dashboard Telemetry Signals | WebSocket `/v1/telemetry/stream`, `/v1/telemetry/snapshot`, `/v1/telemetry/health` |")
    lines.append("")

    lines.append("---")
    lines.append("## 6. Target Rust + Bun Migration Architecture")
    lines.append("")
    lines.append("### 6.1 Bun ElysiaJS Edge Entrypoint (PID 1)")
    lines.append("- Handles routing, CORS, Gzip compression, JWT validation middleware, request caching (10s TTL on GET), and static asset serving for `frontend/dist`.")
    lines.append("- Proxies API requests `/v1/*` to Rust Axum backend on `127.0.0.1:8001`.")
    lines.append("- Upgrades and transparently proxies WebSocket connections `/v1/telemetry/stream` and `/v1/telemetry/vitals/:patient_id` directly to Axum.")
    lines.append("")
    lines.append("### 6.2 Rust Axum Core Backend")
    lines.append("- Implements all 305 HTTP operations with typed Axum extractors (`Json<T>`, `Query<T>`, `Path<T>`, `State<AppState>`).")
    lines.append("- Uses `sqlx` with connection pooling supporting SQLite (`DATABASE_URL=sqlite:///./healthcare.db`) and PostgreSQL.")
    lines.append("- ML disease prediction endpoints (`/v1/predict/*`) run native ONNX Runtime Rust (`ort` crate) loading `.onnx` models.")
    lines.append("")

    with open(".agents/explorer_survey_routes_1/routes_survey.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated comprehensive routes_survey.md ({len(lines)} lines).")

if __name__ == "__main__":
    generate_survey()
