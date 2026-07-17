"""AI Healthcare System - Backend API"""
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

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

    # If running in Hugging Face Spaces, allow all hosts to prevent header routing blocks
    if os.getenv("SPACE_ID") or os.getenv("SPACE_NAME") or os.getenv("HF_SPACE") or os.getenv("RUNNING_IN_HF_SPACE"):
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
    fhir_endpoints,
    hospital_operations,
    interoperability,
    longitudinal_prediction,
    middleware,
    models,
    monitoring,
    nursing,
    payments,
    pharmacy,
    prediction,
    report,
    sales_readiness,
    smart_fhir_endpoints,
    streaming_chat,
    telemetry,
    i18n_audio,
    fhir_compression,
)
from .pdf_service import generate_medical_report


def run_migrations():
    """
    Run Alembic database migrations programmatically on startup.
    Hides exception details to prevent leaking database credentials/info.
    """
    # Programmatic migrations are disabled during testing to allow clean sqlite:memory setup.
    if os.getenv("TESTING"):
        return

    try:
        logger.info("Running database migrations via Alembic...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ini_path = os.path.join(base_dir, "alembic.ini")

        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(ini_path)
        alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "backend", "migrations"))
        from sqlalchemy import inspect, text

        inspector = inspect(database.engine)
        table_names = set(inspector.get_table_names())
        application_tables = table_names - {"alembic_version"}
        current_revision = None
        if "alembic_version" in table_names:
            with database.engine.connect() as connection:
                current_revision = connection.scalar(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )

        if application_tables and current_revision is None:
            logger.info("Adopting existing unversioned database at baseline revision.")
            models.Base.metadata.create_all(bind=database.engine)
            command.stamp(alembic_cfg, "0001_baseline")

        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully.")
    except Exception:
        logger.warning("Migration check failed")


# --- Seeding ---
def create_default_admin():
    """Create a configured admin user if explicit bootstrap credentials are provided."""
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if not default_username or not default_password:
        logger.info("Default admin seeding skipped; bootstrap credentials are not configured.")
        return

    with database.get_db_context() as session:
        try:
            # Check if any admin exists
            admin = session.query(models.User).filter(models.User.role == "admin").first()
            if not admin:
                logger.warning("No admin found. Creating configured bootstrap admin user...")

                hashed_pw = auth.get_password_hash(default_password)
                default_admin = models.User(
                    username=default_username,
                    hashed_password=hashed_pw,
                    email=os.getenv("DEFAULT_ADMIN_EMAIL", ""),
                    role="admin",
                    full_name=os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator"),
                    allow_data_collection=0
                )
                session.add(default_admin)
                session.commit()
                logger.info("Default admin created from configured bootstrap credentials.")
            else:
                logger.info("Admin account already exists.")
        except Exception:
            session.rollback()
            logger.error("Failed to seed admin")


startup_diagnostics = {}


def _uses_sqlite_database() -> bool:
    return str(database.SQLALCHEMY_DATABASE_URL).startswith("sqlite")


def restore_sqlite_backup() -> bool:
    if not _uses_sqlite_database():
        return False

    from .supabase_backup import restore_database

    return restore_database()


def backup_sqlite_database() -> bool:
    if not _uses_sqlite_database():
        return False

    from .supabase_backup import backup_database

    return backup_database()


# --- App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global startup_diagnostics
    try:
        from .axiom_logger import setup_axiom_logging
        setup_axiom_logging()
    except Exception as e:
        logger.warning("Failed to initialize Axiom logging: %s", e)

    # Restore SQLite database from Supabase Storage backup if configured
    try:
        restore_sqlite_backup()
    except Exception as e:
        logger.warning("Failed to restore database from Supabase: %s", e)
    # Mask any sensitive database passwords in URL for logging/diagnostics
    db_url = str(database.SQLALCHEMY_DATABASE_URL)
    if "@" in db_url:
        # e.g., postgresql://user:password@host/db -> postgresql://user:***@host/db
        parts = db_url.split("@")
        prefix = parts[0].rsplit(":", 1)[0]
        startup_diagnostics["database_url"] = f"{prefix}:***@{parts[1]}"
    else:
        startup_diagnostics["database_url"] = db_url

    startup_diagnostics["engine"] = str(database.engine)

    # Database initialization (runs here instead of module level to avoid
    # side effects during import and to support test isolation)
    try:
        from sqlalchemy import text
        with database.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to primary database successfully.")
        startup_diagnostics["primary_conn"] = "success"
    except Exception as e:
        logger.warning("Primary database connection failed: %s. Falling back to SQLite.", e)
        startup_diagnostics["primary_conn"] = f"failed: {str(e)}"
        database.fallback_to_sqlite()
        restore_sqlite_backup()
        startup_diagnostics["fallback_engine"] = str(database.engine)

    try:
        # run_migrations()
        models.Base.metadata.create_all(bind=database.engine)
        startup_diagnostics["schema_creation"] = "success"
    except Exception as err:
        logger.warning("File-based SQLite creation/migration failed: %s. Falling back to in-memory SQLite.", err)
        startup_diagnostics["schema_creation"] = f"failed: {str(err)}"
        database.fallback_to_memory()
        startup_diagnostics["fallback_memory_engine"] = str(database.engine)
        try:
            # run_migrations()
            models.Base.metadata.create_all(bind=database.engine)
            startup_diagnostics["schema_creation_fallback"] = "success"
        except Exception as err2:
            startup_diagnostics["schema_creation_fallback"] = f"failed: {str(err2)}"

    # Seeding
    try:
        create_default_admin()
        startup_diagnostics["seeding"] = "success"
    except Exception as seed_err:
        startup_diagnostics["seeding"] = f"failed: {str(seed_err)}"

    logger.info("Loading AI models...")
    try:
        prediction.initialize_models()
        startup_diagnostics["models_loaded"] = "success"
    except Exception as model_err:
        startup_diagnostics["models_loaded"] = f"failed: {str(model_err)}"

    logger.info("Starting Clinical Event Bus...")
    try:
        from .clinical_intelligence import register_intelligence_event_handlers
        from .event_bus import event_bus
        from .prediction import register_prediction_event_handlers

        await event_bus.start()
        register_intelligence_event_handlers()
        register_prediction_event_handlers()
        startup_diagnostics["event_bus"] = "success"
    except Exception as eb_err:
        startup_diagnostics["event_bus"] = f"failed: {str(eb_err)}"

    logger.info("*" * 60)
    logger.info(" ClinOS LEGAL & MEDICAL DISCLAIMER ACTIVE")
    logger.info(" Provided 'AS IS' for Clinical Decision Support only.")
    logger.info(" Ult Diagnostic Responsibility lies with the Licensed Clinician.")
    logger.info("*" * 60)

    yield
    logger.info("Shutting down...")

    # Stop Clinical Event Bus
    try:
        from .event_bus import event_bus
        await event_bus.stop()
        logger.info("Clinical Event Bus stopped.")
    except Exception as eb_stop_err:
        logger.warning("Failed to stop Event Bus: %s", eb_stop_err)

    # Backup SQLite database to Supabase Storage backup if configured
    try:
        backup_sqlite_database()
    except Exception as e:
        logger.warning("Failed to backup database to Supabase: %s", e)


app = FastAPI(title="AI Healthcare API", default_response_class=JSONResponse, lifespan=lifespan)

# --- API Versioning ---
API_V1_PREFIX = "/v1"


# Add middleware (order matters - last added runs first)
app.add_middleware(middleware.LoggingMiddleware)
if not os.getenv("TESTING"):
    app.add_middleware(middleware.ExceptionMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(middleware.SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=_load_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_load_allowed_hosts())
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.limiter = limiter

app.add_middleware(middleware.RequestTracingMiddleware)
app.add_middleware(middleware.PrometheusMetricsMiddleware)
app.add_middleware(middleware.LicenseValidationMiddleware)
app.add_middleware(middleware.APIVersioningMiddleware)

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
app.include_router(payments.router, prefix=API_V1_PREFIX)
app.include_router(telemetry.router, prefix=f"{API_V1_PREFIX}/telemetry", tags=["Telemetry"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
from . import appointments, ollama_routes

app.include_router(appointments.router, prefix=API_V1_PREFIX, tags=["Appointments"])
app.include_router(ollama_routes.router, prefix=API_V1_PREFIX)
app.include_router(longitudinal_prediction.router, prefix=API_V1_PREFIX)
app.include_router(smart_fhir_endpoints.router, prefix=API_V1_PREFIX)
app.include_router(fhir_endpoints.router, prefix=API_V1_PREFIX)
app.include_router(federated_sync.router, prefix=API_V1_PREFIX)
app.include_router(clinical_intelligence.router, prefix=API_V1_PREFIX)
app.include_router(consent_gate.router, prefix=API_V1_PREFIX)
app.include_router(i18n_audio.router, prefix=API_V1_PREFIX)
app.include_router(fhir_compression.router, prefix=API_V1_PREFIX)

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

    except Exception as e:
        timings["error"] = str(e)
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

# --- SOTA Prometheus Monitoring Endpoint ---
@app.get("/metrics")
def get_prometheus_metrics():
    """Exposes structured Prometheus telemetry metrics."""
    try:
        from backend.enterprise_features import EnterpriseMetrics
        metrics_collector = EnterpriseMetrics()
        metrics_collector.update_system_metrics()
    except Exception as e:
        logger.warning("Failed to update system metrics: %s", e)

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
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

    # Catch-all route to serve the React SPA and let React Router handle routing
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str, request: Request):
        frontend_root = Path(_frontend_dist).resolve()
        requested_path = (frontend_root / catchall).resolve()
        try:
            requested_path.relative_to(frontend_root)
        except ValueError:
            raise HTTPException(status_code=404)

        # Serve specific file if it exists inside the dist directory (e.g., favicon.ico)
        if requested_path.is_file():
            return FileResponse(str(requested_path))

        # If requesting a file (with extension) that does not exist, return 404
        if "." in os.path.basename(catchall):
            raise HTTPException(status_code=404)

        # Fallback to index.html for browser client-side routing
        index_file = os.path.join(_frontend_dist, "index.html")
        if os.path.exists(index_file):
            # Prevent browser caching of index.html so clients always load newly deployed JS/CSS bundles
            return FileResponse(index_file, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

        raise HTTPException(status_code=404)
