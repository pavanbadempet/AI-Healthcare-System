"""AI Healthcare System - Backend API"""
import logging
import os
import re
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

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
from . import (
    admin,
    auth,
    billing,
    care_events,
    chat,
    database,
    demo_readiness,
    diagnostics,
    discharge,
    explanation,
    hospital_operations,
    interoperability,
    models,
    monitoring,
    nursing,
    payments,
    pharmacy,
    prediction,
    report,
    sales_readiness,
    security,
    streaming_chat,
    telemetry,
)
from .pdf_service import generate_medical_report

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

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
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully.")
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
            logger.error("Failed to seed admin")

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
        # Hugging Face Spaces embeds the application inside an iframe.
        # If running in a Hugging Face Space (detected by SPACES_ID),
        # allow framing from HF domains via CSP frame-ancestors instead of X-Frame-Options: DENY.
        if os.getenv("SPACES_ID"):
            response.headers["Content-Security-Policy"] = (
                "frame-ancestors 'self' https://*.huggingface.co https://huggingface.co"
            )
        else:
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
app.include_router(demo_readiness.router)
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
    _frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
    index_file = os.path.join(_frontend_dist, "index.html")
    if os.path.exists(index_file):
        from fastapi.responses import FileResponse
        return FileResponse(index_file)
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

# --- Serve React Frontend SPA ---
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    # Serve static assets folder
    assets_dir = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    from fastapi.responses import FileResponse

    # Catch-all route to serve the React SPA and let React Router handle routing
    @app.get("/{catchall:path}")
    async def serve_frontend(catchall: str, request: Request):
        # Allow API endpoints, docs, openapi.json, and health check to pass through
        first_segment = catchall.split("/")[0] if catchall else ""
        if (
            catchall.startswith("api/") or
            catchall in ("docs", "redoc", "openapi.json", "healthz") or
            any(route.path.strip("/").split("/")[0] == first_segment for route in request.app.routes if route.path.startswith("/"))
        ):
            raise HTTPException(status_code=404)

        # Serve specific file if it exists directly in the dist directory (e.g., favicon.ico)
        file_path = os.path.join(_frontend_dist, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for browser client-side routing
        index_file = os.path.join(_frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

        raise HTTPException(status_code=404)
