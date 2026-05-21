"""AI Healthcare System - Backend API"""
import sys
import os
import uuid
import logging
import time
import re

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager
from jose import JWTError, jwt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
GENERATE_REPORT_FAILURE_DETAIL = "Failed to generate report"
REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _safe_request_id(header_value: str | None) -> str:
    candidate = (header_value or "").strip()
    if candidate and _SAFE_REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


def _load_allowed_hosts() -> list[str]:
    configured_hosts = [
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]
    if configured_hosts:
        return configured_hosts
    if os.getenv("TESTING", "").strip().lower() in {"1", "true", "yes", "on"}:
        return ["127.0.0.1", "testserver"]
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
from . import models, database, auth, chat, explanation, prediction, report, admin, payments, security, telemetry, sales_readiness, hospital_operations, monitoring, diagnostics, pharmacy, billing, discharge, nursing, care_events, interoperability
from . import streaming_chat
from .pdf_service import generate_medical_report

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

from sqlalchemy import inspect

def run_migrations():
    """
    Smart migration script: Checks for missing columns before trying to add them.
    This prevents Postgres transaction aborts if a column already exists.
    """
    # Map of column_name -> definition
    required_columns = {
        "about_me": "TEXT",
        "diet": "TEXT", 
        "activity_level": "TEXT",
        "sleep_hours": "FLOAT",
        "stress_level": "TEXT", 
        "psych_profile": "TEXT", 
        "plan_tier": "VARCHAR", 
        "subscription_expiry": "TIMESTAMP", # Changed from DATETIME for Postgres compat
        "razorpay_customer_id": "VARCHAR",
        "created_at": "TIMESTAMP",
        "role": "VARCHAR",
        "consultation_fee": "FLOAT",
        "specialization": "VARCHAR",
        "facility_id": "INTEGER",
        # Note: Foreign keys are harder to add via simple script, assuming basic column add for now
        "doctor_id": "INTEGER" 
    }
    
    try:
        inspector = inspect(database.engine)
        if not inspector.has_table("users"):
            # Tables created by create_all, skip
            return

        existing_columns = {col['name'] for col in inspector.get_columns("users")}
        
        with database.engine.connect() as conn:
            # Enable autocommit for schema changes if supported (converts simple executes)
            # or just execute one by one.
            count = 0
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    try:
                        logger.info(f"Migration: Adding missing column '{col_name}'...")
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        count += 1
                    except Exception:
                        logger.error("Failed to add column %s", col_name)
            
            if count > 0:
                conn.commit()
                logger.info(f"Migration: Successfully added {count} columns.")

            if inspector.has_table("interoperability_exports"):
                export_columns = {col['name'] for col in inspector.get_columns("interoperability_exports")}
                export_required_columns = {
                    "consent_id": "INTEGER",
                    "profile_id": "INTEGER",
                    "filter_summary": "TEXT",
                    "bundle_sha256": "VARCHAR",
                    "manifest_signature": "VARCHAR",
                    "signature_algorithm": "VARCHAR",
                }
                export_count = 0
                for col_name, col_type in export_required_columns.items():
                    if col_name not in export_columns:
                        try:
                            logger.info("Migration: Adding missing column '%s' to interoperability_exports...", col_name)
                            conn.execute(text(f"ALTER TABLE interoperability_exports ADD COLUMN {col_name} {col_type}"))
                            export_count += 1
                        except Exception:
                            logger.error("Failed to add interoperability_exports.%s", col_name)
                if export_count > 0:
                    conn.commit()

            table_required_columns = {
                "audit_logs": {"facility_id": "INTEGER"},
                "departments": {"facility_id": "INTEGER"},
                "appointments": {"facility_id": "INTEGER"},
                "beds": {"facility_id": "INTEGER"},
                "encounters": {"facility_id": "INTEGER"},
                "admissions": {"facility_id": "INTEGER"},
                "clinical_orders": {"facility_id": "INTEGER"},
                "care_events": {"facility_id": "INTEGER"},
                "billable_services": {"facility_id": "INTEGER"},
                "invoices": {"facility_id": "INTEGER"},
                "billing_payments": {"facility_id": "INTEGER"},
                "medication_inventory": {"facility_id": "INTEGER"},
                "prescriptions": {"facility_id": "INTEGER"},
                "dispense_records": {"facility_id": "INTEGER"},
                "diagnostic_results": {"facility_id": "INTEGER"},
                "vital_observations": {"facility_id": "INTEGER"},
                "monitoring_signals": {"facility_id": "INTEGER"},
                "nursing_tasks": {"facility_id": "INTEGER"},
                "discharge_summaries": {"facility_id": "INTEGER"},
                "interoperability_consents": {
                    "facility_id": "INTEGER",
                    "abdm_request_id": "VARCHAR",
                    "abdm_consent_id": "VARCHAR",
                    "abdm_status": "VARCHAR",
                    "abdm_last_event_at": "TIMESTAMP",
                },
                "interoperability_export_profiles": {"facility_id": "INTEGER"},
                "interoperability_exports": {"facility_id": "INTEGER"},
            }
            for table_name, columns in table_required_columns.items():
                if not inspector.has_table(table_name):
                    continue
                existing_table_columns = {col["name"] for col in inspector.get_columns(table_name)}
                added_count = 0
                for col_name, col_type in columns.items():
                    if col_name not in existing_table_columns:
                        try:
                            logger.info("Migration: Adding missing column '%s' to %s...", col_name, table_name)
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                            added_count += 1
                        except Exception:
                            logger.error("Failed to add %s.%s", table_name, col_name)
                if added_count > 0:
                    conn.commit()
                
    except Exception:
        logger.warning("Migration check failed")

run_migrations()

# --- Seeding ---
def create_default_admin():
    """Create a configured admin user if explicit bootstrap credentials are provided."""
    default_username = os.getenv("DEFAULT_ADMIN_USERNAME")
    default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
    if not default_username or not default_password:
        logger.info("Default admin seeding skipped; bootstrap credentials are not configured.")
        return

    session = database.SessionLocal()
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
        logger.error("Failed to seed admin")
    finally:
        session.close()

# --- App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Seeding
    create_default_admin()
    
    logger.info("Loading AI models...")
    prediction.initialize_models()
    yield
    logger.info("Shutting down...")

app = FastAPI(title="AI Healthcare API", default_response_class=JSONResponse, lifespan=lifespan)

# --- Middleware ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("TESTING"):
            return await call_next(request)
        if request.url.path not in ["/", "/docs", "/openapi.json", "/healthz"]:
            try:
                identifier = self._identifier_for_request(request)
                security.limiter.check(request, identifier)
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)

    @staticmethod
    def _identifier_for_request(request: Request) -> str:
        """
        Prefer user identity (JWT subject) over raw IP address.
        This improves fairness and reduces accidental global throttling behind proxies/NAT.
        """
        authz = request.headers.get("authorization", "") or ""
        if authz.lower().startswith("bearer "):
            token = authz.split(" ", 1)[1].strip()
            if token:
                try:
                    payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
                    sub = payload.get("sub")
                    if sub:
                        return f"user:{sub}"
                except JWTError:
                    # Fall back to IP-based limiting if token is invalid/expired.
                    pass
        return request.client.host if request.client else "unknown"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            error_id = str(uuid.uuid4())[:8]
            logger.error("Unhandled server error %s", error_id)
            return JSONResponse(status_code=500, content={"detail": f"Error: {error_id}"})


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = _safe_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        ms = (time.time() - start) * 1000
        request_id = getattr(request.state, "request_id", "-")
        logger.info(
            "%s %s - %s (%.0fms) request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            ms,
            request_id,
        )
        return response

# Add middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
if not os.getenv("TESTING"):
    app.add_middleware(ExceptionMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CORSMiddleware,
    allow_origins=_load_cors_origins(),
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_load_allowed_hosts())
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestTracingMiddleware)

# --- Routes ---
app.include_router(auth.router, tags=["Auth"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(streaming_chat.router)
app.include_router(prediction.router, tags=["Prediction"])
app.include_router(explanation.router)
app.include_router(report.router, tags=["Reports"])
app.include_router(admin.router)
app.include_router(sales_readiness.router)
app.include_router(hospital_operations.router)
app.include_router(monitoring.router)
app.include_router(diagnostics.router)
app.include_router(pharmacy.router)
app.include_router(billing.router)
app.include_router(discharge.router)
app.include_router(nursing.router)
app.include_router(care_events.router)
app.include_router(interoperability.router)
app.include_router(payments.router)
app.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
from . import appointments, ollama_routes
app.include_router(appointments.router, tags=["Appointments"])
app.include_router(ollama_routes.router)

@app.get("/")
def root():
    return {"message": "AI Healthcare API"}

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/generate_report")
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

# --- Static Files (WebLLM AI Copilot page) ---
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")
