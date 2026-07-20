import os
from typing import List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .licensing import LicenseManager


class LicenseValidationMiddleware(BaseHTTPMiddleware):
    """Verifies that a valid cryptographic license key is provided in B2B deployments."""

    def __init__(
        self,
        app,
        license_manager: LicenseManager,
        exclude_paths: Optional[List[str]] = None,
        exclude_prefixes: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.license_manager = license_manager
        self.exclude_paths = exclude_paths or []
        self.exclude_prefixes = exclude_prefixes or []

    async def dispatch(self, request: Request, call_next):
        # Bypass checks during tests if needed
        testing_var = self.license_manager.testing_env_var
        if os.getenv(testing_var) == "1" or os.getenv(testing_var) == "true":
            return await call_next(request)

        path = request.url.path

        # 1. Exact match exclusions
        if path in self.exclude_paths:
            return await call_next(request)

        # 2. Prefix match exclusions
        for prefix in self.exclude_prefixes:
            if path.startswith(prefix):
                return await call_next(request)

        # 3. Check license key
        license_key = os.getenv(self.license_manager.env_var_name, "").strip()
        if not license_key:
            return JSONResponse(
                status_code=402,
                content={
                    "detail": f"License Key is missing. Please set the {self.license_manager.env_var_name} environment variable."
                },
            )

        is_valid, reason = self.license_manager.verify_license_key(license_key)
        if not is_valid:
            return JSONResponse(
                status_code=402,
                content={"detail": f"License Key is invalid or expired: {reason}"},
            )

        return await call_next(request)
