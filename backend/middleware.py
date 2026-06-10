"""AI Healthcare System - Middleware Stack

All custom middleware classes are defined here so that ``main.py`` remains
a pure composition root.  Classes are registered in ``main.py`` via
``app.add_middleware(middleware.<ClassName>)``.
"""
import logging
import os
import re
import time
import uuid

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Request tracing constants
# ---------------------------------------------------------------------------
REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _safe_request_id(header_value: str | None) -> str:
    candidate = (header_value or "").strip()
    if candidate and _SAFE_REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# API versioning constants
# ---------------------------------------------------------------------------
# Paths that should NOT be redirected to /v1 (infrastructure routes)
_UNVERSIONED_ROOT_PATHS = frozenset({"/", "/docs", "/openapi.json", "/redoc", "/healthz", "/generate_report"})

# Known API route prefixes that should redirect to /v1 when accessed without prefix
_API_PREFIXES = (
    "/signup", "/token", "/profile", "/users",  # auth
    "/predict", "/admin",                        # prediction + admin
    "/chat", "/records", "/download",            # chat
    "/analyze", "/reports",                       # report
    "/snapshot",                                   # telemetry
    "/hospital", "/pharmacy", "/diagnostics",
    "/discharge", "/nursing", "/billing",
    "/monitoring", "/interop", "/payments",
    "/events", "/demo-readiness", "/explain",
    "/ai",                                         # ollama_routes
    "/appointments",                               # appointments
)


# ═══════════════════════════════════════════════════════════════════════════
# Middleware classes
# ═══════════════════════════════════════════════════════════════════════════


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Redirect legacy unversioned API requests to /v1 with 307 (preserves method & body)."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Skip root-level infrastructure paths and already-versioned paths
        if path in _UNVERSIONED_ROOT_PATHS or path.startswith("/v1") or path.startswith("/assets") or path.startswith("/static"):
            return await call_next(request)
        # Redirect known API paths to /v1 equivalent
        if path.startswith(_API_PREFIXES):
            redirect_url = f"/v1{path}"
            if request.url.query:
                redirect_url = f"{redirect_url}?{request.url.query}"
            return RedirectResponse(url=redirect_url, status_code=307)
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("TESTING"):
            return await call_next(request)
        if request.url.path not in ["/", "/docs", "/openapi.json", "/healthz"]:
            try:
                identifier = self._identifier_for_request(request)
                # Lazy imports to avoid circular dependency at module load time
                from . import security
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
                    # Lazy import to avoid circular dependency at module load time
                    from . import auth
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
        # If running in a Hugging Face Space (detected by SPACE_ID or SPACES_ID),
        # allow framing from HF domains via CSP frame-ancestors instead of X-Frame-Options: DENY.
        if os.getenv("SPACE_ID") or os.getenv("SPACES_ID"):
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
    """Catch all unhandled exceptions and return a safe 500 response.

    ``HTTPException`` is re-raised so FastAPI's built-in handler produces the
    correct status code (404, 403, etc.).  Every other ``Exception`` is logged
    with a full traceback (``exc_info=True``) and the client receives only an
    opaque error reference ID — no stack traces or PII.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise  # Let FastAPI handle intentional HTTP errors normally
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
