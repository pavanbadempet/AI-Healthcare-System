"""AI Healthcare System - Backend API"""
import sys
import os
import uuid
import logging
import time

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Imports ---
from . import models, database, auth, chat, explanation, prediction, report, admin, payments, security, telemetry
from . import streaming_chat
from .pdf_service import generate_medical_report

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

from sqlalchemy import inspect

def run_migrations():
    """
    Smart migration script: Checks for missing columns before trying to add them.
    This prevents Postgres transaction aborts if a column already exists.
    SECURITY: Column names are validated against whitelist.
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
        "subscription_expiry": "TIMESTAMP",
        "razorpay_customer_id": "VARCHAR",
        "created_at": "TIMESTAMP",
        "role": "VARCHAR",
        "consultation_fee": "FLOAT",
        "specialization": "VARCHAR",
    }
    
    # SECURITY: Whitelist of allowed columns to prevent SQL injection
    ALLOWED_COLUMNS = {
        "about_me", "diet", "activity_level", "sleep_hours", 
        "stress_level", "psych_profile", "plan_tier", "subscription_expiry",
        "razorpay_customer_id", "created_at", "role", "consultation_fee", "specialization"
    }
    
    try:
        inspector = inspect(database.engine)
        if not inspector.has_table("users"):
            return

        existing_columns = {col['name'] for col in inspector.get_columns("users")}
        
        with database.engine.connect() as conn:
            count = 0
            for col_name, col_type in required_columns.items():
                # SECURITY: Validate column name against whitelist
                if col_name not in ALLOWED_COLUMNS:
                    logger.error(f"Migration: Rejected invalid column '{col_name}'")
                    continue
                    
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

# --- Security Middleware ---

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Prevent request body DoS attacks. SECURITY: Limit request size to 1MB."""
    MAX_SIZE = 1_000_000  # 1MB limit
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request entity too large (max 1MB)"}
                    )
            except (ValueError, TypeError):
                pass
        return await call_next(request)

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
        if request.url.path not in ["/", "/docs", "/openapi.json", "/healthz"]:
            try:
                security.limiter.check(request, request.client.host if request.client else "unknown")
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # SECURITY: HSTS only for non-localhost (allow local development)
        if "127.0.0.1" not in request.url.hostname:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        return response

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            error_id = str(uuid.uuid4())[:8]
            logger.error("Unhandled server error %s", error_id)
            # SECURITY: Return generic error to client, full error logged server-side
            return JSONResponse(status_code=500, content={"detail": f"Error: {error_id}"})

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        ms = (time.time() - start) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({ms:.0f}ms)")
        return response

# Add middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
if not os.getenv("TESTING"):
    app.add_middleware(ExceptionMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)  # SECURITY: Added request size limit
app.add_middleware(CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000"],
    allow_credentials=True, 
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # SECURITY: Explicit methods
    allow_headers=["Content-Type", "Authorization"],  # SECURITY: Explicit headers
    expose_headers=["Content-Disposition"],
    max_age=600)  # Cache preflight
app.add_middleware(TrustedHostMiddleware, 
    allowed_hosts=["127.0.0.1", "aio-health-backend.onrender.com"])
app.add_middleware(RateLimitMiddleware)

# --- Routes ---
app.include_router(auth.router, tags=["Auth"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(streaming_chat.router)
app.include_router(prediction.router, tags=["Prediction"])
app.include_router(explanation.router)
app.include_router(report.router, tags=["Reports"])
app.include_router(admin.router)
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
    _current_user: models.User = Depends(auth.get_current_user),
):
    data = await request.json()
    pdf = generate_medical_report(
        user_name=data.get("user_name", "Patient"),
        report_type=data.get("report_type", "General"),
        prediction=data.get("prediction", "N/A"),
        data=data.get("data", {}),
        advice=data.get("advice", [])
    )
    return Response(content=pdf, media_type="application/pdf")

# --- Static Files (WebLLM AI Copilot page) ---
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")
