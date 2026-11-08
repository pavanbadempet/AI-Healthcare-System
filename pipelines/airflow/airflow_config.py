"""
Airflow CeleryExecutor Configuration Module.

Centralises all Airflow configuration for the AI Healthcare System's
production deployment.  Import this module in ``airflow.cfg`` overrides
or use its attributes to programmatically configure the scheduler,
worker pool, queue routing, and remote logging.

Broker connectivity uses Redis on the container network; the result
backend uses the shared PostgreSQL instance.  Container/service DNS
names (``redis``, ``postgres``) are used because these services run
inside the same Docker Compose / Kubernetes network.

Example — referencing in a DAG file::

    from airflow_config import AirflowConfig

    queue = AirflowConfig.CELERY_QUEUES["ml_training"]["queue"]
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AirflowConfig:
    """Declarative Airflow configuration for the AI Healthcare System.

    All values are exposed as **class attributes** so they can be read
    without instantiation.  Environment variables override defaults
    where noted.
    """

    # ------------------------------------------------------------------
    # Core settings
    # ------------------------------------------------------------------

    EXECUTOR: str = "CeleryExecutor"
    """Executor backend.  CeleryExecutor distributes tasks across a pool
    of workers via an AMQP-compatible broker (here Redis)."""

    PARALLELISM: int = 32
    """Maximum number of task instances that can run concurrently across
    the **entire** Airflow installation, regardless of DAG or worker."""

    MAX_ACTIVE_TASKS_PER_DAG: int = 16
    """Maximum number of task instances allowed to run concurrently
    within a single DAG.  Prevents a single busy DAG from starving
    other DAGs."""

    MAX_ACTIVE_RUNS_PER_DAG: int = 3
    """Maximum number of active (running) DAG runs per DAG.  Limits
    back-fill or catch-up pressure."""

    DEFAULT_TIMEZONE: str = "UTC"
    """Scheduler / UI display timezone."""

    LOAD_EXAMPLES: bool = False
    """Disable the built-in example DAGs in production."""

    # ------------------------------------------------------------------
    # Celery broker & result backend
    # ------------------------------------------------------------------

    CELERY_BROKER_URL: str = os.getenv(
        "AIRFLOW__CELERY__BROKER_URL",
        "redis://redis:6379/1",
    )
    """Message broker URL.  Redis DB 1 is reserved for Celery to avoid
    collisions with the application cache on DB 0."""

    CELERY_RESULT_BACKEND: str = os.getenv(
        "AIRFLOW__CELERY__RESULT_BACKEND",
        "db+postgresql://airflow:airflow@postgres:5432/airflow",
    )
    """Result backend connection string.  Stores task state/results in
    the shared Airflow metadata PostgreSQL database."""

    WORKER_CONCURRENCY: int = int(
        os.getenv("AIRFLOW__CELERY__WORKER_CONCURRENCY", "8")
    )
    """Number of concurrent task slots per Celery worker process.  Tune
    based on available CPU / memory on worker nodes — 8 is a sensible
    default for 4-core machines running mixed I/O + CPU tasks."""

    # ------------------------------------------------------------------
    # Queue definitions
    # ------------------------------------------------------------------

    CELERY_QUEUES: Dict[str, Dict[str, Any]] = {
        "default": {
            "queue": "default",
            "exchange": "default",
            "routing_key": "default",
            "description": (
                "General-purpose queue for lightweight orchestration tasks, "
                "sensors, and notifications."
            ),
        },
        "ml_training": {
            "queue": "ml_training",
            "exchange": "ml",
            "routing_key": "ml.training",
            "description": (
                "Dedicated queue for model training jobs.  Workers on this "
                "queue should be provisioned with GPU / high-memory nodes."
            ),
        },
        "data_quality": {
            "queue": "data_quality",
            "exchange": "data",
            "routing_key": "data.quality",
            "description": (
                "Queue for data-quality validation tasks (Great Expectations, "
                "schema checks, anomaly detection)."
            ),
        },
        "etl": {
            "queue": "etl",
            "exchange": "data",
            "routing_key": "data.etl",
            "description": (
                "Queue for ETL / ELT extraction and transformation jobs "
                "that may involve heavy I/O or Spark submissions."
            ),
        },
    }
    """Named queues with exchange and routing-key bindings.  Map tasks
    to queues via ``queue='ml_training'`` in ``PythonOperator(…)``."""

    DEFAULT_QUEUE: str = "default"
    """Fall-back queue when a task does not specify one explicitly."""

    # ------------------------------------------------------------------
    # Flower (Celery monitoring UI)
    # ------------------------------------------------------------------

    FLOWER_PORT: int = int(os.getenv("AIRFLOW__CELERY__FLOWER_PORT", "5555"))
    """HTTP port for the Flower monitoring dashboard."""

    FLOWER_BASIC_AUTH: str = os.getenv(
        "AIRFLOW__CELERY__FLOWER_BASIC_AUTH",
        "admin:admin",
    )
    """``user:password`` pair for Flower HTTP Basic authentication.
    **Override via environment variable in production.**"""

    # ------------------------------------------------------------------
    # Logging — remote logging to S3 / GCS
    # ------------------------------------------------------------------

    REMOTE_LOGGING: bool = os.getenv(
        "AIRFLOW__LOGGING__REMOTE_LOGGING", "False"
    ).lower() in ("true", "1", "yes")
    """Enable shipping task logs to a cloud object store.  Set to
    ``True`` and configure ``REMOTE_LOG_CONN_ID`` + ``REMOTE_BASE_LOG_FOLDER``
    for production."""

    REMOTE_LOG_CONN_ID: str = os.getenv(
        "AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID",
        "aws_default",
    )
    """Airflow connection ID for the cloud storage backend used for
    remote log shipping.  Must be pre-configured in the Airflow
    Connections UI or via environment variables."""

    REMOTE_BASE_LOG_FOLDER: str = os.getenv(
        "AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER",
        "s3://healthcare-airflow-logs/logs",
    )
    """Base URI in S3 or GCS where task logs are stored.  Examples:

    * S3:  ``s3://bucket/prefix/logs``
    * GCS: ``gs://bucket/prefix/logs``
    """

    LOGGING_LEVEL: str = os.getenv("AIRFLOW__LOGGING__LOGGING_LEVEL", "INFO")
    """Root logging level for the Airflow scheduler and workers."""

    ENCRYPT_S3_LOGS: bool = os.getenv(
        "AIRFLOW__LOGGING__ENCRYPT_S3_LOGS", "True"
    ).lower() in ("true", "1", "yes")
    """Whether to encrypt log objects at rest in S3 (SSE-S3).  Ignored
    when using GCS."""

    # ------------------------------------------------------------------
    # Scheduler tuning
    # ------------------------------------------------------------------

    MIN_FILE_PROCESS_INTERVAL: int = 30
    """Seconds between re-scanning DAG files for changes.  Lower values
    increase DAG-parsing CPU usage."""

    DAG_DIR_LIST_INTERVAL: int = 120
    """Seconds between listing the DAGs directory for new/removed files."""

    SCHEDULER_HEARTBEAT_SEC: int = 5
    """Interval for the scheduler heartbeat.  A shorter interval
    improves scheduling responsiveness at the cost of slightly higher
    CPU usage."""

    # ------------------------------------------------------------------
    # Webserver
    # ------------------------------------------------------------------

    WEBSERVER_HOST: str = "0.0.0.0"  # noqa: S104 — intentional bind-all for containers
    WEBSERVER_PORT: int = 8080
    RBAC: bool = True
    """Role-Based Access Control — always enabled in production."""

    # ------------------------------------------------------------------
    # Convenience: export as dict
    # ------------------------------------------------------------------

    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """Return all public configuration attributes as a plain dict.

        Useful for injecting into ``airflow.cfg`` overrides or for
        diagnostics logging at scheduler start-up.
        """
        return {
            key: value
            for key, value in vars(cls).items()
            if not key.startswith("_") and key.isupper()
        }

    @classmethod
    def log_summary(cls) -> None:
        """Log a one-line summary of critical settings (no secrets)."""
        logger.info(
            "AirflowConfig — executor=%s, parallelism=%d, "
            "workers=%d, queues=%s, remote_logging=%s",
            cls.EXECUTOR,
            cls.PARALLELISM,
            cls.WORKER_CONCURRENCY,
            list(cls.CELERY_QUEUES.keys()),
            cls.REMOTE_LOGGING,
        )
