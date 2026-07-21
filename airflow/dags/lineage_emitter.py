"""
OpenLineage Event Emitter for Airflow DAGs.

Emits data lineage events (START, COMPLETE, FAIL) in the OpenLineage
specification format. Events are persisted as timestamped JSON files under
``data/lineage/events/`` and, when ``OPENLINEAGE_URL`` is set, forwarded
to an external lineage collector.

Usage inside a DAG task::

    from lineage_emitter import OpenLineageEmitter, create_dataset_facet

    emitter = OpenLineageEmitter()
    inp = create_dataset_facet("raw_patients", {"id": "integer", "name": "string"})
    out = create_dataset_facet("clean_patients", {"id": "integer", "name_hash": "string"})
    emitter.emit_start_event("etl_dag", "clean_task", run_id, [inp], [out])
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENLINEAGE_URL: Optional[str] = os.getenv("OPENLINEAGE_URL")
"""Optional remote OpenLineage API endpoint.  When unset, events are only
persisted locally."""

LINEAGE_EVENTS_DIR = Path(
    os.getenv(
        "LINEAGE_EVENTS_DIR",
        str(Path(__file__).resolve().parents[2] / "data" / "lineage" / "events"),
    )
)

PRODUCER = "https://github.com/AI-Healthcare-System/airflow"
"""URI identifying this application as the event producer."""

_HTTP_TIMEOUT_SECONDS = 10


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class DatasetFacet:
    """Describes an input or output dataset for lineage tracking.

    Attributes:
        namespace: Logical grouping, e.g. ``"healthcare_db"`` or ``"s3://bucket"``.
        name: Fully-qualified dataset name such as a table or file path.
        schema_fields: List of ``{"name": ..., "type": ...}`` dicts describing
            the dataset schema.
        data_source: Human-readable identifier of the upstream source system
            (e.g. ``"postgres"``).
    """

    namespace: str
    name: str
    schema_fields: List[Dict[str, str]] = field(default_factory=list)
    data_source: str = ""


@dataclass
class LineageEvent:
    """Represents a single OpenLineage-compatible event.

    Attributes:
        event_type: One of ``START``, ``COMPLETE``, ``FAIL``.
        event_time: ISO-8601 timestamp of the event.
        producer: URI of the application that produced this event.
        job: Dict with ``namespace`` and ``name`` keys identifying the job.
        inputs: List of input :class:`DatasetFacet` instances.
        outputs: List of output :class:`DatasetFacet` instances.
        run_facets: Arbitrary metadata attached to the run (metrics, errors, …).
    """

    event_type: str
    event_time: str
    producer: str
    job: Dict[str, str]
    inputs: List[DatasetFacet] = field(default_factory=list)
    outputs: List[DatasetFacet] = field(default_factory=list)
    run_facets: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def create_dataset_facet(
    table_name: str,
    schema_dict: Dict[str, str],
    *,
    namespace: str = "healthcare_db",
    data_source: str = "postgres",
) -> DatasetFacet:
    """Create a :class:`DatasetFacet` from a table name and column-type mapping.

    Args:
        table_name: Name of the database table or file path.
        schema_dict: Mapping of column name → column type, e.g.
            ``{"id": "integer", "name": "text"}``.
        namespace: Logical namespace for the dataset.
        data_source: Origin system label.

    Returns:
        A populated :class:`DatasetFacet`.
    """
    schema_fields = [
        {"name": col_name, "type": col_type}
        for col_name, col_type in schema_dict.items()
    ]
    return DatasetFacet(
        namespace=namespace,
        name=table_name,
        schema_fields=schema_fields,
        data_source=data_source,
    )


# ---------------------------------------------------------------------------
# Emitter
# ---------------------------------------------------------------------------


class OpenLineageEmitter:
    """Emit OpenLineage events for Airflow DAG tasks.

    Events are **always** written to local JSON files under
    :data:`LINEAGE_EVENTS_DIR`.  If :data:`OPENLINEAGE_URL` is configured,
    events are also ``POST``-ed to that endpoint (best-effort — failures are
    logged but do not raise).

    Args:
        events_dir: Override the default local storage directory.
        remote_url: Override the ``OPENLINEAGE_URL`` env var.
    """

    def __init__(
        self,
        events_dir: Optional[Path] = None,
        remote_url: Optional[str] = None,
    ) -> None:
        self._events_dir = events_dir or LINEAGE_EVENTS_DIR
        self._remote_url = remote_url or OPENLINEAGE_URL
        self._events_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "OpenLineageEmitter initialised — local_dir=%s, remote_url=%s",
            self._events_dir,
            self._remote_url or "(none, local-only)",
        )

    # -- public API ---------------------------------------------------------

    def emit_start_event(
        self,
        dag_id: str,
        task_id: str,
        run_id: str,
        input_datasets: Optional[List[DatasetFacet]] = None,
        output_datasets: Optional[List[DatasetFacet]] = None,
    ) -> LineageEvent:
        """Emit a ``START`` lineage event.

        Args:
            dag_id: Airflow DAG identifier.
            task_id: Airflow task identifier within the DAG.
            run_id: Unique run identifier (typically the Airflow run id).
            input_datasets: Datasets consumed by this task.
            output_datasets: Datasets produced by this task.

        Returns:
            The emitted :class:`LineageEvent`.
        """
        event = self._build_event(
            event_type="START",
            dag_id=dag_id,
            task_id=task_id,
            run_id=run_id,
            inputs=input_datasets or [],
            outputs=output_datasets or [],
            run_facets={"run_id": run_id},
        )
        self._persist(event)
        logger.info("Lineage START emitted for %s.%s (run=%s)", dag_id, task_id, run_id)
        return event

    def emit_complete_event(
        self,
        dag_id: str,
        task_id: str,
        run_id: str,
        output_datasets: Optional[List[DatasetFacet]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> LineageEvent:
        """Emit a ``COMPLETE`` lineage event.

        Args:
            dag_id: Airflow DAG identifier.
            task_id: Airflow task identifier within the DAG.
            run_id: Unique run identifier.
            output_datasets: Datasets produced upon completion.
            metrics: Arbitrary completion metrics (rows processed, duration, …).

        Returns:
            The emitted :class:`LineageEvent`.
        """
        run_facets: Dict[str, Any] = {"run_id": run_id}
        if metrics:
            run_facets["metrics"] = metrics

        event = self._build_event(
            event_type="COMPLETE",
            dag_id=dag_id,
            task_id=task_id,
            run_id=run_id,
            inputs=[],
            outputs=output_datasets or [],
            run_facets=run_facets,
        )
        self._persist(event)
        logger.info(
            "Lineage COMPLETE emitted for %s.%s (run=%s, metrics=%s)",
            dag_id,
            task_id,
            run_id,
            list((metrics or {}).keys()),
        )
        return event

    def emit_fail_event(
        self,
        dag_id: str,
        task_id: str,
        run_id: str,
        error_message: str,
    ) -> LineageEvent:
        """Emit a ``FAIL`` lineage event.

        Args:
            dag_id: Airflow DAG identifier.
            task_id: Airflow task identifier within the DAG.
            run_id: Unique run identifier.
            error_message: Human-readable description of the failure.

        Returns:
            The emitted :class:`LineageEvent`.
        """
        event = self._build_event(
            event_type="FAIL",
            dag_id=dag_id,
            task_id=task_id,
            run_id=run_id,
            inputs=[],
            outputs=[],
            run_facets={
                "run_id": run_id,
                "error": {
                    "message": error_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )
        self._persist(event)
        logger.error(
            "Lineage FAIL emitted for %s.%s (run=%s): %s",
            dag_id,
            task_id,
            run_id,
            error_message,
        )
        return event

    # -- internals ----------------------------------------------------------

    def _build_event(
        self,
        *,
        event_type: str,
        dag_id: str,
        task_id: str,
        run_id: str,
        inputs: List[DatasetFacet],
        outputs: List[DatasetFacet],
        run_facets: Dict[str, Any],
    ) -> LineageEvent:
        """Construct a :class:`LineageEvent`."""
        return LineageEvent(
            event_type=event_type,
            event_time=datetime.now(timezone.utc).isoformat(),
            producer=PRODUCER,
            job={"namespace": "airflow", "name": f"{dag_id}.{task_id}"},
            inputs=inputs,
            outputs=outputs,
            run_facets=run_facets,
        )

    def _persist(self, event: LineageEvent) -> None:
        """Write event to local JSON and optionally to a remote endpoint."""
        try:
            payload = asdict(event)
        except Exception:
            payload = event.__dict__ if hasattr(event, "__dict__") else str(event)

        # --- local file ---
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
        filename = f"{event.event_type}_{event.job['name']}_{timestamp}.json"
        filepath = self._events_dir / filename
        try:
            filepath.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            logger.debug("Lineage event written to %s", filepath)
        except OSError:
            logger.exception("Failed to write lineage event to %s", filepath)

        # --- remote endpoint (best-effort) ---
        if self._remote_url:
            self._post_remote(payload)

    def _post_remote(self, payload: Dict[str, Any]) -> None:
        """POST event JSON to the configured OpenLineage endpoint."""
        url = f"{self._remote_url.rstrip('/')}/api/v1/lineage"
        try:
            resp = requests.post(
                url,
                json=payload,
                timeout=_HTTP_TIMEOUT_SECONDS,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            logger.debug("Lineage event sent to %s (status=%s)", url, resp.status_code)
        except requests.RequestException:
            logger.warning(
                "Failed to send lineage event to %s — event is still stored locally",
                url,
                exc_info=True,
            )
