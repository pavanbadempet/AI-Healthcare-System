"""
Data & AI Apps Runtime — Composable Clinical Application Framework.

Provides:
- Declarative app registration with typed inputs/outputs
- App lifecycle management (deploy, stop, health check)
- Built-in integration with lakehouse tables, catalog, and BI engine
- Cloud-native data app migration-compatible interface
"""

import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class AppStatus(str, Enum):
    REGISTERED = "REGISTERED"
    DEPLOYING = "DEPLOYING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class AppDefinition(BaseModel):
    """Definition of a deployable data/AI app."""
    app_id: str = Field(default_factory=lambda: f"APP-{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    version: str = "1.0.0"
    app_type: str = "DATA_APP"  # "DATA_APP", "ML_APP", "BI_APP", "AGENT_APP"
    status: AppStatus = AppStatus.REGISTERED
    input_schema: Dict[str, str] = Field(default_factory=dict)
    output_schema: Dict[str, str] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    deployed_at: Optional[float] = None


class AppExecutionResult(BaseModel):
    """Result of invoking an app."""
    app_id: str
    app_name: str
    output: Any = None
    execution_time_ms: float = 0.0
    status: str = "SUCCESS"
    error: Optional[str] = None


class DataAIAppsRuntime:
    """
    Manages registration, deployment, and execution of data & AI apps.
    """

    def __init__(self) -> None:
        self._apps: Dict[str, AppDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_app(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str = "",
        app_type: str = "DATA_APP",
        input_schema: Optional[Dict[str, str]] = None,
        output_schema: Optional[Dict[str, str]] = None,
    ) -> AppDefinition:
        """Register a new app with its handler."""
        app_def = AppDefinition(
            name=name,
            description=description,
            app_type=app_type,
            input_schema=input_schema or {},
            output_schema=output_schema or {},
        )
        self._apps[app_def.app_id] = app_def
        self._handlers[app_def.app_id] = handler
        return app_def

    def deploy(self, app_id: str) -> AppDefinition:
        """Deploy an app (transition to RUNNING)."""
        app = self._apps.get(app_id)
        if app is None:
            raise KeyError(f"App '{app_id}' not found.")
        app.status = AppStatus.RUNNING
        app.deployed_at = time.time()
        return app

    def stop(self, app_id: str) -> AppDefinition:
        """Stop a running app."""
        app = self._apps.get(app_id)
        if app is None:
            raise KeyError(f"App '{app_id}' not found.")
        app.status = AppStatus.STOPPED
        return app

    def invoke(self, app_id: str, **kwargs: Any) -> AppExecutionResult:
        """Invoke an app's handler."""
        app = self._apps.get(app_id)
        if app is None:
            return AppExecutionResult(
                app_id=app_id, app_name="unknown",
                status="FAILED", error=f"App '{app_id}' not found.",
            )

        handler = self._handlers.get(app_id)
        if handler is None:
            return AppExecutionResult(
                app_id=app_id, app_name=app.name,
                status="FAILED", error="No handler registered.",
            )

        start = time.time()
        try:
            output = handler(**kwargs)
            elapsed = (time.time() - start) * 1000
            return AppExecutionResult(
                app_id=app_id, app_name=app.name,
                output=output, execution_time_ms=round(elapsed, 3),
                status="SUCCESS",
            )
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return AppExecutionResult(
                app_id=app_id, app_name=app.name,
                execution_time_ms=round(elapsed, 3),
                status="FAILED", error=str(exc),
            )

    def list_apps(self, status: Optional[AppStatus] = None) -> List[AppDefinition]:
        """List registered apps, optionally filtered by status."""
        apps = list(self._apps.values())
        if status:
            apps = [a for a in apps if a.status == status]
        return apps

    def health_check(self, app_id: str) -> Dict[str, Any]:
        """Check app health."""
        app = self._apps.get(app_id)
        if app is None:
            return {"app_id": app_id, "healthy": False, "reason": "Not found"}
        return {
            "app_id": app_id,
            "name": app.name,
            "status": app.status.value,
            "healthy": app.status == AppStatus.RUNNING,
        }


data_ai_apps_runtime = DataAIAppsRuntime()
