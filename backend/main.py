import sys
import os

# Add root directory to path to ensure modules can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress Warnings
import app_warnings

from fastapi import FastAPI
from . import models, database, auth, chat, explanation, prediction, report

from sqlalchemy import text  # Required for raw SQL execution

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

# Optimize: Add Indices & Schema Migration
try:
    with database.engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_health_records_timestamp ON health_records (timestamp)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_logs_timestamp ON chat_logs (timestamp)"))
        
        # Schema Migration (Add Lifestyle Columns if missing)
        # Schema Migration (Add Lifestyle Columns if missing)
        # We must try each one independently. If one fails (already exists), the others must still run.
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN about_me TEXT"))
        except Exception: pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN diet TEXT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN activity_level TEXT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN sleep_hours FLOAT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN stress_level TEXT"))
        except Exception: pass
            
        conn.commit()
except Exception as e:
    print(f"Index/Schema Creation Warning: {e}")

app = FastAPI(title="AIO Healthcare System API")

# --- SECURITY HARDENING ---
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# 1. Trusted Host (Prevents Host Header Attacks)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "::1"])

# 2. CORS (Restrict to Frontend Origins)
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Security Headers Middleware
# 3. Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 4. Global Exception Handler (Resilience)
from fastapi.responses import JSONResponse
import traceback
import logging

# Configure File Logging
logging.basicConfig(filename='app.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s:%(message)s')

class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # Generate Reference ID (for user support) - simplistic UUID
            import uuid
            error_id = str(uuid.uuid4())
            
            # Log the full error internally
            logging.error(f"Unhandled Exception ID {error_id}: {str(e)}")
            logging.error(traceback.format_exc())
            
            # Return safe error to client
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal Server Error. Reference ID: {error_id}"}
            )

# Only enable Global Exception Handler in Production/Dev, NOT in Automated Tests
# In tests, we want the raw exception to bubble up so pytest shows the traceback.
if not os.getenv("TESTING"):
    app.add_middleware(CatchExceptionsMiddleware)

# Enable Gzip Compression for Performance
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include Routers
app.include_router(auth.router, tags=["Authentication"]) # Endpoint: /users, /token
app.include_router(chat.router, tags=["Chat & Records"])
app.include_router(prediction.router, tags=["AI Prediction"])
app.include_router(explanation.router) # New GenAI Explainer
app.include_router(report.router, tags=["Smart Lab Analyzer"])

@app.get("/")
def read_root():
    return {"message": "Healthcare System API is running"}
