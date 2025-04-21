"""AI Healthcare System - Backend API"""
import sys
import os
import uuid
import logging
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Imports ---
from . import app_warnings, models, database, auth, chat, explanation, prediction, report, admin, payments, security
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
        "created_at": "TIMESTAMP"
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
                    except Exception as e:
                        logger.error(f"Failed to add column {col_name}: {e}")
            
            if count > 0:
                conn.commit()
                logger.info(f"Migration: Successfully added {count} columns.")
                
    except Exception as e:
        logger.warning(f"Migration check failed: {e}")

run_migrations()

# --- App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading AI models...")
    prediction.initialize_models()
    yield
    logger.info("Shutting down...")

app = FastAPI(title="AI Healthcare API", default_response_class=ORJSONResponse, lifespan=lifespan)

# --- Middleware ---

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path not in ["/", "/docs", "/openapi.json", "/healthz"]:
            try:
                security.limiter.check(request, request.client.host if request.client else "unknown")
            except HTTPException as e:
                return ORJSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            error_id = str(uuid.uuid4())[:8]
            logger.error(f"Error {error_id}: {e}")
            return ORJSONResponse(status_code=500, content={"detail": f"Error: {error_id}"})

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
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://*.streamlit.app"],
    allow_origin_regex=r"https://.*\.streamlit\.app",
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "aio-health-backend.onrender.com", "*"])
app.add_middleware(RateLimitMiddleware)

# --- Routes ---
app.include_router(auth.router, tags=["Auth"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(prediction.router, tags=["Prediction"])
app.include_router(explanation.router)
app.include_router(report.router, tags=["Reports"])
app.include_router(admin.router)
app.include_router(payments.router)

@app.get("/")
def root():
    return {"message": "AI Healthcare API"}

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/generate_report")
async def generate_report(request: Request):
    data = await request.json()
    pdf = generate_medical_report(
        user_name=data.get("user_name", "Patient"),
        report_type=data.get("report_type", "General"),
        prediction=data.get("prediction", "N/A"),
        data=data.get("data", {}),
        advice=data.get("advice", [])
    )
    return Response(content=pdf, media_type="application/pdf")
