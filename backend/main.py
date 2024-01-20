"""
AIO Healthcare System - Backend API Entrypoint
==============================================

Orchestrates the FastAPI application.

Modules:
- Database Connection
- Security Middleware (CORS, TrustedHost, Headers)
- Global Exception Handling
- API Router Inclusion

Author: Pavan Badempet
"""
import sys
import os
import uuid
import traceback
import logging
import time
from sqlalchemy import text
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Add root directory to path to ensure modules can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

from . import app_warnings, models, database, auth, chat, explanation, prediction, report
from .pdf_service import generate_medical_report

# --- Database Initialization ---
models.Base.metadata.create_all(bind=database.engine)

def run_migrations():
    """Run lightweight schema migrations on startup."""
    try:
        with database.engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_health_records_timestamp ON health_records (timestamp)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_logs_timestamp ON chat_logs (timestamp)"))
            
            # Add Lifestyle Columns if missing
            columns = [
                ("about_me", "TEXT"),
                ("diet", "TEXT"),
                ("activity_level", "TEXT"),
                ("sleep_hours", "FLOAT"),
                ("stress_level", "TEXT"),
                ("psych_profile", "TEXT"), # NEW: AI derived psychological/medical summary
                ("last_analysis_date", "DATETIME")
            ]
            
            for col_name, col_type in columns:
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass # Column likely exists
                
            conn.commit()
    except Exception as e:
        logger.warning(f"Index/Schema Creation Warning: {e}")

run_migrations()

# --- App Definition ---
app = FastAPI(title="AIO Healthcare System API", default_response_class=ORJSONResponse)

# --- Middleware ---

# 1. Trusted Host
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "::1"])

# 2. CORS
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://aiohealthcare.streamlit.app",
    "https://share.streamlit.io",
    "*", 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Security Headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 4. Global Exception Handler
class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    """
    Catches unhandled exceptions, logs them with a reference ID, 
    and returns a safe 500 JSON response to the client.
    """
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(f"Unhandled Exception ID {error_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return ORJSONResponse(
                status_code=500,
                content={"detail": f"Internal Server Error. Reference ID: {error_id}"}
            )

# Only enable in Production/Live Dev (Skip in pytest to see tracebacks)
if not os.getenv("TESTING"):
    app.add_middleware(CatchExceptionsMiddleware)

# 5. Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 6. Advanced Request Logging & Monitoring Middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Add request ID to headers for tracing
        # We can't easily modify request headers here without recreating the request, 
        # so we just pass it in the logging context if we had one.
        logger.info(f"Incoming Request: {request.method} {request.url.path} | ReqID: {request_id} | IP: {request.client.host}")
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log successful response metrics
            logger.info(
                f"Request Completed: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Latency: {process_time:.2f}ms | "
                f"ReqID: {request_id}"
            )
            
            # Add X-Process-Time header for client monitoring
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request Failed: {request.method} {request.url.path} | "
                f"Latency: {process_time:.2f}ms | "
                f"ReqID: {request_id} | Error: {str(e)}"
            )
            raise e

app.add_middleware(RequestLoggingMiddleware)

# --- Routes ---
app.include_router(auth.router, tags=["Authentication"])
app.include_router(chat.router, tags=["Chat & Records"])
app.include_router(prediction.router, tags=["AI Prediction"])
app.include_router(explanation.router)
app.include_router(report.router, tags=["Smart Lab Analyzer"])

@app.get("/")
def read_root():
    return {"message": "Healthcare System API is running"}

@app.post("/generate_report")
async def get_medical_report(request: Request):
    """Generates a downloadable PDF medical report."""
    try:
        data = await request.json()
        pdf_bytes = generate_medical_report(
            user_name=data.get("user_name", "Valued Patient"),
            report_type=data.get("report_type", "General Health"),
            prediction=data.get("prediction", "N/A"),
            data=data.get("data", {}),
            advice=data.get("advice", [])
        )
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"PDF Gen Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
