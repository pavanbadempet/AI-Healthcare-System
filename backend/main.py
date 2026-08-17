"""AI Healthcare System - Backend API"""
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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
    payments,
    pharmacy,
    prediction,
    report,
    sales_readiness,
    smart_fhir_endpoints,
    streaming_chat,
    telemetry,
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
    except Exception as mig_err:
        logger.warning("Migration check failed: %s. Ensuring database schema via metadata.create_all...", mig_err)
        models.Base.metadata.create_all(bind=database.engine)


# --- Seeding ---
def create_default_admin():
    """Create a configured admin user if explicit bootstrap credentials are provided."""
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if not default_username or not default_password:
        logger.info("Default admin seeding skipped; bootstrap credentials are not configured.")
        return

    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL") or f"{default_username}@system.local"

    with database.get_db_context() as session:
        try:
            # Check if username, email, or admin role already exists
            existing_user = session.query(models.User).filter(
                (models.User.username == default_username) |
                (models.User.email == admin_email) |
                (models.User.role == "admin")
            ).first()

            if not existing_user:
                logger.warning("No admin user found. Creating configured bootstrap admin user...")
                hashed_pw = auth.get_password_hash(default_password)
                default_admin = models.User(
                    username=default_username,
                    hashed_password=hashed_pw,
                    email=admin_email,
                    role="admin",
                    full_name=os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator"),
                    allow_data_collection=0
                )
                session.add(default_admin)
                session.commit()
                logger.info("Default admin created from configured bootstrap credentials.")
            else:
                logger.info("Admin or matching bootstrap account already exists (%s).", existing_user.username)
        except Exception as seed_err:
            session.rollback()
            logger.warning("Default admin seeding skipped due to existing constraint: %s", seed_err)


def seed_hospital_operations_data():
    """Seeds default facility, departments, and beds if the database has none."""
    with database.get_db_context() as session:
        try:
            facility = session.query(models.HospitalFacility).first()
            if not facility:
                facility = models.HospitalFacility(
                    name="Central General Hospital",
                    facility_type="hospital",
                    country="US",
                    region="North America",
                    status="active"
                )
                session.add(facility)
                session.commit()
                session.refresh(facility)

            existing_depts = session.query(models.Department).count()
            if existing_depts == 0:
                dept_list = [
                    ("Intensive Care Unit (ICU-A)", "IPD", "Building A - 3rd Floor"),
                    ("Med-Surg Ward 4B", "IPD", "Building B - 4th Floor"),
                    ("Cardiac Care Unit", "IPD", "Building A - 2nd Floor"),
                    ("Pediatric Ward", "IPD", "Building C - 1st Floor"),
                    ("Emergency Department", "Emergency", "Building A - Ground Floor"),
                ]
                for name, dtype, loc in dept_list:
                    existing_d = session.query(models.Department).filter(models.Department.name == name).first()
                    if not existing_d:
                        dept = models.Department(
                            facility_id=facility.id,
                            name=name,
                            department_type=dtype,
                            location=loc,
                            status="active"
                        )
                        session.add(dept)
                session.commit()

            existing_beds = session.query(models.Bed).count()
            if existing_beds == 0:
                icu_dept = session.query(models.Department).filter(models.Department.name.like("%ICU%")).first()
                med_dept = session.query(models.Department).filter(models.Department.name.like("%Med-Surg%")).first()
                car_dept = session.query(models.Department).filter(models.Department.name.like("%Cardiac%")).first()
                ped_dept = session.query(models.Department).filter(models.Department.name.like("%Pediatric%")).first()

                dept_map = [
                    (icu_dept, "ICU", 20),
                    (med_dept, "MED", 40),
                    (car_dept, "CAR", 16),
                    (ped_dept, "PED", 24),
                ]
                for dept_obj, prefix, count in dept_map:
                    if not dept_obj:
                        continue
                    for i in range(1, count + 1):
                        bed_code = f"{prefix}-{i:02d}"
                        existing_b = session.query(models.Bed).filter(
                            models.Bed.facility_id == facility.id,
                            models.Bed.bed_number == bed_code
                        ).first()
                        if not existing_b:
                            status = "occupied" if i <= int(count * 0.8) else ("cleaning" if i == int(count * 0.8) + 1 else "available")
                            bed = models.Bed(
                                facility_id=facility.id,
                                department_id=dept_obj.id,
                                bed_number=bed_code,
                                ward=dept_obj.name,
                                status=status
                            )
                            session.add(bed)
                session.commit()
                logger.info("Default hospital facility, departments, and beds seeded.")

            existing_patients = session.query(models.User).filter(models.User.role == "patient").count()
            if existing_patients == 0:
                # Find or create a default doctor user
                doctor = session.query(models.User).filter(models.User.role == "doctor").first()
                if not doctor:
                    doctor = models.User(
                        username="dr_smith",
                        hashed_password=auth.get_password_hash("Doctor123!"),
                        email="dr.smith@hospital.local",
                        role="doctor",
                        full_name="Dr. Sarah Smith, MD",
                        facility_id=facility.id,
                        specialization="Internal Medicine",
                        allow_data_collection=0
                    )
                    session.add(doctor)
                    session.commit()
                    session.refresh(doctor)

                demo_patients = [
                    ("sarah_jenkins", "Sarah Jenkins", "sarah@patient.local", 28, "F", 72.0, 120.0, 80.0, 98.0, 36.8, "ICU", "ICU-01"),
                    ("marcus_thorne", "Marcus Thorne", "marcus@patient.local", 54, "M", 118.0, 145.0, 95.0, 94.0, 38.2, "CAR", "CAR-01"),
                    ("linda_zhao", "Linda Zhao", "linda@patient.local", 42, "F", 64.0, 115.0, 75.0, 99.0, 36.7, "MED", "MED-01"),
                    ("robert_g", "Robert Garcia", "robert@patient.local", 61, "M", 85.0, 132.0, 84.0, 97.0, 37.0, "MED", "MED-02"),
                    ("emily_watson", "Emily Watson", "emily@patient.local", 19, "F", 68.0, 112.0, 68.0, 98.0, 36.6, "PED", "PED-01"),
                    ("oscar_meyer", "Oscar Meyer", "oscar@patient.local", 67, "M", 76.0, 128.0, 82.0, 96.0, 36.9, "ICU", "ICU-02"),
                ]

                for uname, fname, email, age, gender, hr, sbp, dbp, spo2, temp, dept_pref, bed_num in demo_patients:
                    puser = models.User(
                        username=uname,
                        hashed_password=auth.get_password_hash("Patient123!"),
                        email=email,
                        role="patient",
                        full_name=fname,
                        facility_id=facility.id,
                        allow_data_collection=0
                    )
                    session.add(puser)
                    session.commit()
                    session.refresh(puser)

                    dept_match = session.query(models.Department).filter(models.Department.name.like(f"%{dept_pref}%")).first()
                    dept_id = dept_match.id if dept_match else 1

                    # Create Encounter
                    encounter = models.Encounter(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        doctor_id=doctor.id,
                        department_id=dept_id,
                        encounter_type="IPD",
                        reason="Inpatient clinical monitoring and diagnostic evaluation",
                        priority="urgent" if hr > 100 or spo2 < 95 else "routine",
                        status="open",
                        started_at=datetime.now(timezone.utc)
                    )
                    session.add(encounter)
                    session.commit()
                    session.refresh(encounter)

                    # Create Vital Observation
                    vital = models.VitalObservation(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        recorded_by_id=doctor.id,
                        encounter_id=encounter.id,
                        department_id=dept_id,
                        source="device",
                        heart_rate=hr,
                        systolic_bp=sbp,
                        diastolic_bp=dbp,
                        spo2=spo2,
                        temperature_c=temp,
                        respiratory_rate=16.0 if hr <= 100 else 24.0,
                        blood_glucose=95.0 if uname != "marcus_thorne" else 145.0,
                        observed_at=datetime.now(timezone.utc)
                    )
                    session.add(vital)

                    # Link bed and create admission
                    bed_match = session.query(models.Bed).filter(
                        models.Bed.facility_id == facility.id,
                        models.Bed.bed_number == bed_num
                    ).first()
                    if bed_match:
                        bed_match.current_patient_id = puser.id
                        bed_match.status = "occupied"

                    admission = models.Admission(
                        facility_id=facility.id,
                        encounter_id=encounter.id,
                        patient_id=puser.id,
                        doctor_id=doctor.id,
                        department_id=dept_id,
                        bed_id=bed_match.id if bed_match else None,
                        reason="Inpatient Care & Telemetry",
                        status="active",
                        admitted_at=datetime.now(timezone.utc)
                    )
                    session.add(admission)

                    # Create Care Event
                    event = models.CareEvent(
                        facility_id=facility.id,
                        patient_id=puser.id,
                        actor_user_id=doctor.id,
                        encounter_id=encounter.id,
                        department_id=dept_id,
                        event_type="ADMISSION",
                        title=f"Inpatient Admission to {dept_pref}",
                        summary=f"Patient admitted with initial vitals: HR {hr} bpm, BP {sbp}/{dbp}, SpO2 {spo2}%.",
                        severity="warning" if hr > 100 or spo2 < 95 else "info",
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(event)

                session.commit()
                logger.info("Demo patient profiles, encounters, vitals, and admissions seeded successfully.")
        except Exception as seed_err:
            session.rollback()
            logger.warning("Hospital operations seeding failed: %s", seed_err)


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
        models.Base.metadata.create_all(bind=database.engine)
        startup_diagnostics["schema_creation"] = "success"
    except Exception as err:
        logger.warning("Primary database schema creation failed: %s. Falling back to local SQLite WAL.", err)
        startup_diagnostics["schema_creation"] = f"failed: {str(err)}"
        database.fallback_to_sqlite()
        restore_sqlite_backup()
        try:
            models.Base.metadata.create_all(bind=database.engine)
            startup_diagnostics["schema_creation_sqlite"] = "success"
        except Exception as err_sqlite:
            logger.warning("File-based SQLite creation failed: %s. Falling back to in-memory SQLite.", err_sqlite)
            database.fallback_to_memory()
            try:
                models.Base.metadata.create_all(bind=database.engine)
                startup_diagnostics["schema_creation_memory"] = "success"
            except Exception as err_mem:
                startup_diagnostics["schema_creation_memory"] = f"failed: {str(err_mem)}"

    # Seeding
    try:
        create_default_admin()
        seed_hospital_operations_data()
        startup_diagnostics["seeding"] = "success"
    except Exception as seed_err:
        logger.warning("Primary database seeding failed: %s. Retrying seed on local fallback database...", seed_err)
        database.fallback_to_sqlite()
        try:
            models.Base.metadata.create_all(bind=database.engine)
            create_default_admin()
            seed_hospital_operations_data()
            startup_diagnostics["seeding"] = "success_fallback"
        except Exception as seed_fallback_err:
            startup_diagnostics["seeding"] = f"failed: {str(seed_fallback_err)}"

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
    logger.info(" AI Healthcare System LEGAL & MEDICAL DISCLAIMER ACTIVE")
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
app.add_middleware(middleware.LicenseValidationMiddleware)
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
app.include_router(payments.router, prefix=API_V1_PREFIX)
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

from backend.routes.data_engineering_routes import router as data_engineering_router
from backend.routes.data_platform_routes import router as data_platform_router
from backend.routes.four_eye_routes import router as four_eye_router
from backend.routes.mesh_routes import router as mesh_router
from backend.routes.peak_healthcare_routes import router as peak_healthcare_router
from backend.routes.recommendation_routes import router as recommendation_router

app.include_router(data_platform_router)
app.include_router(recommendation_router)
app.include_router(peak_healthcare_router)
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

# --- B2B Licensing & Platform Activation Endpoints ---
class LicenseActivationPayload(BaseModel):
    license_key: str

@app.get("/v1/licensing/status")
def get_licensing_status():
    """Retrieve active platform licensing status, tier, and module grants."""
    from backend import licensing
    raw_key = os.getenv("LICENSE_KEY")
    key = "CLINIC-TRIAL-2026" if raw_key is None else raw_key.strip()
    tier = licensing.get_active_license_tier()
    is_valid, holder_reason = licensing.verify_license_key(key)
    modules = licensing.get_active_license_modules()
    return {
        "active_key": key[:12] + "..." if len(key) > 12 else key,
        "is_valid": is_valid,
        "tier": tier,
        "details": holder_reason,
        "modules": modules,
        "perpetual": tier == "enterprise" and "Trial" not in holder_reason
    }

@app.post("/v1/licensing/activate")
def activate_license_key(payload: LicenseActivationPayload):
    """Validate and activate a B2B enterprise license key."""
    from backend import licensing
    clean_key = payload.license_key.strip()
    is_valid, reason = licensing.verify_license_key(clean_key)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"License activation failed: {reason}")

    os.environ["LICENSE_KEY"] = clean_key
    tier = licensing.get_active_license_tier()
    return {
        "status": "activated",
        "tier": tier,
        "details": reason,
        "modules": licensing.get_active_license_modules()
    }

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

