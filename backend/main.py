"""AI Healthcare System - Backend API"""
import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Normalize TESTING environment variable to prevent "false" string truthiness bugs
if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
    os.environ["TESTING"] = "1"
else:
    os.environ["TESTING"] = ""

# Configure Structured JSON Logging with PII Redaction
from backend.logging_config import setup_structured_logging

setup_structured_logging()

from backend.security_decorators import no_log_zone_async

logger = logging.getLogger(__name__)

# Configure Rate Limiter
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# Use global limiter for all components to import
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
if os.getenv("TESTING") == "1":
    limiter.enabled = False
GENERATE_REPORT_FAILURE_DETAIL = "Failed to generate report"


def _load_allowed_hosts() -> list[str]:
    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        return ["127.0.0.1", "testserver"]

    # If running in Hugging Face Spaces, Render, or Containerized cloud, allow all host headers
    if (
        os.getenv("SPACE_ID")
        or os.getenv("SPACE_NAME")
        or os.getenv("HF_SPACE")
        or os.getenv("RUNNING_IN_HF_SPACE")
        or os.getenv("PORT")
        or os.getenv("RENDER")
        or os.getenv("DOCKER_CONTAINER")
    ):
        return ["*"]

    configured_hosts = [
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
    if configured_hosts:
        return configured_hosts
    return ["127.0.0.1"]


def _load_cors_origins() -> list[str]:
    configured_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if configured_origins:
        return configured_origins
    return ["http://127.0.0.1:3000"]

# --- Imports ---
from . import (
    admin,
    auth,
    billing,
    care_events,
    chat,
    clinical_intelligence,
    consent_gate,
    database,
    demo_readiness,
    diagnostics,
    discharge,
    explanation,
    federated_sync,
    fhir_compression,
    fhir_endpoints,
    hospital_operations,
    i18n_audio,
    interoperability,
    longitudinal_prediction,
    middleware,
    models,
    monitoring,
    nursing,
    pharmacy,
    prediction,
    report,
    sales_readiness,
    smart_fhir_endpoints,
    streaming_chat,
    telemetry,
)
from .lifecycle import (
    backup_sqlite_database,
    lifespan,
    restore_sqlite_backup,
    run_migrations,
    startup_diagnostics,
)
from .pdf_service import generate_medical_report
from .seeding import (
    create_default_admin,
    seed_hospital_operations_data,
)

try:
    from fastapi.responses import ORJSONResponse
    fast_json_response = ORJSONResponse
except ImportError:
    fast_json_response = JSONResponse

app = FastAPI(title="AI Healthcare API", default_response_class=fast_json_response, lifespan=lifespan)

# --- API Versioning ---
API_V1_PREFIX = "/v1"


# Add middleware (order matters - last added runs first on incoming requests)
app.add_middleware(middleware.LoggingMiddleware)
if not os.getenv("TESTING"):
    app.add_middleware(middleware.ExceptionMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_load_allowed_hosts())
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.limiter = limiter

app.add_middleware(middleware.RequestTracingMiddleware)
app.add_middleware(middleware.PrometheusMetricsMiddleware)
app.add_middleware(middleware.APIVersioningMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(middleware.SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=_load_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


# --- Routes (versioned under /v1) ---
app.include_router(auth.router, prefix=API_V1_PREFIX, tags=["Auth"])
app.include_router(chat.router, prefix=API_V1_PREFIX, tags=["Chat"])
app.include_router(streaming_chat.router, prefix=API_V1_PREFIX)
app.include_router(prediction.router, prefix=API_V1_PREFIX, tags=["Prediction"])
app.include_router(explanation.router, prefix=API_V1_PREFIX)
app.include_router(report.router, prefix=API_V1_PREFIX, tags=["Reports"])
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(sales_readiness.router, prefix=API_V1_PREFIX)
app.include_router(demo_readiness.router, prefix=API_V1_PREFIX)
app.include_router(hospital_operations.router, prefix=API_V1_PREFIX)
app.include_router(monitoring.router, prefix=API_V1_PREFIX)
app.include_router(diagnostics.router, prefix=API_V1_PREFIX)
app.include_router(pharmacy.router, prefix=API_V1_PREFIX)
app.include_router(billing.router, prefix=API_V1_PREFIX)
app.include_router(discharge.router, prefix=API_V1_PREFIX)
app.include_router(nursing.router, prefix=API_V1_PREFIX)
app.include_router(care_events.router, prefix=API_V1_PREFIX)
app.include_router(interoperability.router, prefix=API_V1_PREFIX)
app.include_router(telemetry.router, prefix=f"{API_V1_PREFIX}/telemetry", tags=["Telemetry"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
from . import abdm_sandbox, appointments, dicomweb, ollama_routes

app.include_router(appointments.router, prefix=API_V1_PREFIX, tags=["Appointments"])
app.include_router(dicomweb.router, prefix=API_V1_PREFIX)
app.include_router(ollama_routes.router, prefix=API_V1_PREFIX)
app.include_router(longitudinal_prediction.router, prefix=API_V1_PREFIX)
app.include_router(smart_fhir_endpoints.router, prefix=API_V1_PREFIX)
app.include_router(fhir_endpoints.router, prefix=API_V1_PREFIX)
app.include_router(federated_sync.router, prefix=API_V1_PREFIX)
app.include_router(clinical_intelligence.router, prefix=API_V1_PREFIX)
app.include_router(consent_gate.router, prefix=API_V1_PREFIX)
app.include_router(i18n_audio.router, prefix=API_V1_PREFIX)
app.include_router(fhir_compression.router, prefix=API_V1_PREFIX)
app.include_router(abdm_sandbox.router, prefix=API_V1_PREFIX, tags=["ABDM Sandbox"])

from backend.routes.advanced_intelligence_routes import router as advanced_intelligence_router
from backend.routes.agentic_routes import router as agentic_router
from backend.routes.confidential_data_systems_routes import router as confidential_data_systems_router
from backend.routes.data_engineering_routes import router as data_engineering_router
from backend.routes.data_platform_routes import router as data_platform_router
from backend.routes.durability_routes import router as durability_router
from backend.routes.four_eye_routes import router as four_eye_router
from backend.routes.frontier_backend_resilience_routes import router as frontier_backend_resilience_router
from backend.routes.frontier_clinical_ai_routes import router as frontier_clinical_ai_router
from backend.routes.frontier_data_systems_routes import router as frontier_data_systems_router
from backend.routes.frontier_security_privacy_routes import router as frontier_security_privacy_router
from backend.routes.history_routes import router as history_router
from backend.routes.mesh_routes import router as mesh_router
from backend.routes.peak_data_engineering_routes import router as peak_data_engineering_router
from backend.routes.peak_healthcare_routes import router as peak_healthcare_router
from backend.routes.recommendation_routes import router as recommendation_router
from backend.routes.versioning_routes import router as versioning_router

app.include_router(data_platform_router)
app.include_router(recommendation_router)
app.include_router(peak_healthcare_router)
app.include_router(advanced_intelligence_router)
app.include_router(peak_data_engineering_router)
app.include_router(frontier_data_systems_router)
app.include_router(confidential_data_systems_router)
app.include_router(frontier_clinical_ai_router)
app.include_router(frontier_backend_resilience_router)
app.include_router(frontier_security_privacy_router)
app.include_router(durability_router)
app.include_router(history_router)
app.include_router(versioning_router)
app.include_router(agentic_router)
app.include_router(data_engineering_router)
app.include_router(mesh_router)
app.include_router(four_eye_router)

@app.get("/")
def root():
    if not os.getenv("TESTING"):
        _frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
        index_file = os.path.join(_frontend_dist, "index.html")
        if os.path.exists(index_file):
            from fastapi.responses import FileResponse
            # Prevent browser caching of index.html so clients always load newly deployed JS/CSS bundles
            return FileResponse(index_file, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
    return {"message": "AI Healthcare API"}

@app.get("/healthz")
def health():
    return {
        "status": "ok",
        "diagnostics": startup_diagnostics
    }

@app.get("/healthz/live")
def healthz_live():
    return {
        "status": "alive",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/healthz/ready")
def healthz_ready():
    return {
        "status": "ready",
        "service": "backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/healthz/env")
async def healthz_env():
    import os
    return {"DATABASE_URL": os.getenv("DATABASE_URL"), "DOPPLER_TOKEN": bool(os.getenv("DOPPLER_TOKEN")), "ALL_KEYS": list(os.environ.keys())}

@app.get("/healthz/circuit_breaker")
def circuit_breaker():
    from backend import core_ai
    return {
        "gemini_disabled": getattr(core_ai, "_gemini_disabled", None),
        "has_gemini_key": core_ai.has_gemini_api_key(),
        "google_api_key_configured": bool(core_ai.GOOGLE_API_KEY)
    }

@app.get("/healthz/time_predict")
async def time_predict(background_tasks: BackgroundTasks):
    import time

    from backend import database
    from backend import features as _features
    from backend import prediction as pred

    timings = {}

    # 1. DB Session
    start = time.time()
    db = next(database.get_db())
    timings["db_session_init"] = time.time() - start

    # Payload
    input_list = [67, 1, 0, 160, 286, 0, 0, 108, 1, 1.5, 1, 3, 2]

    try:
        # 2. Imputer
        start = time.time()
        imputer, conformal_q = pred._get_imputer_and_conformal("heart", pred.heart_model)
        if imputer is not None:
            imputed_arr = imputer.transform([input_list])
            imputed_list = imputed_arr[0].tolist()
        else:
            imputed_list = [0.0 if x is None else x for x in input_list]
        timings["imputer_and_conformal"] = time.time() - start

        # 3. Model predict
        start = time.time()
        raw, confidence, risk_level, proba = pred._run_model_prediction_scaled("heart", imputed_list)
        prediction = "Heart Disease Detected" if raw == 1 else "Healthy Heart"
        timings["model_prediction"] = time.time() - start

        # 4. Conformal / Triage / Risk
        start = time.time()
        proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])
        conformal_metrics = pred._calculate_adaptive_conformal_prediction(
            proba_pos, conformal_q, imputed_list, raw, risk_level
        )
        pred._get_triage_recommendation(raw, conformal_metrics["conformal_prediction_set"])
        pred._get_top_risk_factors(pred.heart_model, imputed_list, _features.HEART_FEATURES)
        clinical_indices = {"framingham_risk": {}, **conformal_metrics}
        timings["conformal_triage_factors"] = time.time() - start

        # 5. SHAP Logging
        start = time.time()
        attributions = pred._log_feature_attributions(
            background_tasks, "heart", "2.1.0-onnx",
            imputed_list, _features.HEART_FEATURES, raw, pred.heart_model
        )
        timings["shap_logging"] = time.time() - start

        # 6. Narrative and Explanation
        start = time.time()
        import asyncio
        narrative, patient_explanation = await asyncio.gather(
            pred._generate_clinical_narrative(
                "heart", prediction, confidence, risk_level, clinical_indices
            ),
            pred._generate_patient_explanation(
                "heart", prediction, confidence, risk_level, attributions or {}
            )
        )
        timings["narrative_and_explanation"] = time.time() - start

    except Exception:
        timings["error"] = "Benchmark execution encountered an internal error"
    finally:
        db.close()

    return timings

@app.post("/generate_report")
@no_log_zone_async
async def generate_report(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        data = await request.json()
        report_user_name = current_user.full_name or current_user.username
        pdf = generate_medical_report(
            user_name=report_user_name,
            report_type=data.get("report_type", "General"),
            prediction=data.get("prediction", "N/A"),
            data=data.get("data", {}),
            advice=data.get("advice", [])
        )
        return Response(content=pdf, media_type="application/pdf")
    except HTTPException:
        raise
    except Exception:
        logger.error("Generate report failed")
        raise HTTPException(status_code=500, detail=GENERATE_REPORT_FAILURE_DETAIL)


# --- Prometheus Monitoring Endpoint ---
@app.get("/metrics")
def get_prometheus_metrics():
    """Exposes structured Prometheus telemetry metrics."""
    try:
        from backend.enterprise_features import EnterpriseMetrics
        metrics_collector = EnterpriseMetrics()
        metrics_collector.update_system_metrics()
    except Exception as e:
        logger.warning("Failed to update system metrics: %s", e)

    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- Static Files (WebLLM AI Copilot page) ---
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")

# --- Serve React Frontend SPA ---
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    class ImmutableStaticFiles(StaticFiles):
        """Custom StaticFiles subclass to add Cache-Control: immutable headers for hashed production assets."""
        def file_response(self, *args, **kwargs):
            response = super().file_response(*args, **kwargs)
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

    # Serve static assets folder
    assets_dir = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", ImmutableStaticFiles(directory=assets_dir), name="assets")

    from fastapi.responses import FileResponse

    # Pre-index allowed static files to avoid any dynamic path construction
    _ALLOWED_STATIC_FILES: dict[str, str] = {}
    if os.path.isdir(_frontend_dist):
        for entry in os.listdir(_frontend_dist):
            full_p = os.path.abspath(os.path.join(_frontend_dist, entry))
            if os.path.isfile(full_p):
                _ALLOWED_STATIC_FILES[entry] = full_p
    _ALLOWED_STATIC_FILES["index.html"] = os.path.abspath(os.path.join(_frontend_dist, "index.html"))

    _INDEX_HTML_CACHE: str | None = None

    # Catch-all route to serve the React SPA and let React Router handle routing
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str, request: Request):
        filename = os.path.basename(catchall)
        if "." in filename:
            # Look up purely from statically verified dictionary (zero tainted path joins)
            target_path = _ALLOWED_STATIC_FILES.get(filename)
            if target_path and os.path.isfile(target_path):
                return FileResponse(target_path)
            raise HTTPException(status_code=404)

        # Fallback to index.html for browser client-side routing
        global _INDEX_HTML_CACHE
        if _INDEX_HTML_CACHE is None:
            index_file = _ALLOWED_STATIC_FILES.get("index.html") or os.path.join(_frontend_dist, "index.html")
            if os.path.isfile(index_file):
                with open(index_file, "r", encoding="utf-8") as f:
                    _INDEX_HTML_CACHE = f.read()

        if _INDEX_HTML_CACHE:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=_INDEX_HTML_CACHE, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

        raise HTTPException(status_code=404)


__all__ = [
    "app",
    "database",
    "backup_sqlite_database",
    "create_default_admin",
    "lifespan",
    "restore_sqlite_backup",
    "run_migrations",
    "seed_hospital_operations_data",
    "startup_diagnostics",
]
