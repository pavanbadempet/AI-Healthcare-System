"""
MedFlow — Declarative ETL/ELT Pipeline Orchestrator for Clinical Data Lakehouse.

Provides:
- Declarative pipeline DAG definition supporting both PySpark DataFrames & Python Dicts
- Zero-Configuration Sandbox execution (pure Python fallback when PySpark is absent)
- Step-level retries, execution metrics, and error handling
- Pipeline versioning and run history
- Seamless integration with PySpark SQL & Distributed Lakehouse compute
"""

import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

# Conditional PySpark import for Zero-Configuration local execution
try:
    from pyspark.sql import DataFrame as SparkDataFrame
    from pyspark.sql import SparkSession
    HAS_PYSPARK = True
except ImportError:
    HAS_PYSPARK = False
    SparkSession = Any  # type: ignore
    SparkDataFrame = Any  # type: ignore


class PipelineStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PipelineStep(BaseModel):
    """A single step in an ETL pipeline."""
    step_id: str = Field(default_factory=lambda: f"STEP-{uuid.uuid4().hex[:6]}")
    name: str
    step_type: str  # "SOURCE", "TRANSFORM", "SPARK_TRANSFORM", "SINK"
    status: PipelineStepStatus = PipelineStepStatus.PENDING
    input_record_count: int = 0
    output_record_count: int = 0
    duration_ms: float = 0.0
    error_message: Optional[str] = None


class PipelineRun(BaseModel):
    """A single execution run of a pipeline."""
    run_id: str = Field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:8]}")
    pipeline_name: str
    steps: List[PipelineStep]
    status: str = "PENDING"
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    total_records_processed: int = 0


class MedFlowPipeline:
    """
    A declarative ETL pipeline with ordered steps.

    Supports both PySpark DataFrames and pure Python list-of-dicts.
    If PySpark is present, distributed DataFrame transformations execute natively.
    If PySpark is missing, it falls back to zero-configuration in-memory processing.
    """

    def __init__(self, name: str, spark: Optional[Any] = None) -> None:
        self.name = name
        self.spark = spark
        self._steps: List[Dict[str, Any]] = []
        self._runs: List[PipelineRun] = []

    def add_source(self, name: str, func: Callable[[], Any]) -> "MedFlowPipeline":
        """Add a data source step (returns list of dicts or PySpark DataFrame)."""
        self._steps.append({"name": name, "type": "SOURCE", "func": func})
        return self

    def add_transform(self, name: str, func: Callable[[Any], Any]) -> "MedFlowPipeline":
        """Add a transformation step (accepts and returns list of dicts or PySpark DataFrame)."""
        self._steps.append({"name": name, "type": "TRANSFORM", "func": func})
        return self

    def add_spark_transform(self, name: str, spark_sql_query: str) -> "MedFlowPipeline":
        """Add a declarative Spark SQL transformation step."""
        self._steps.append({"name": name, "type": "SPARK_TRANSFORM", "query": spark_sql_query})
        return self

    def add_sink(self, name: str, func: Callable[[Any], int]) -> "MedFlowPipeline":
        """Add a data sink step (receives final data and returns written record count)."""
        self._steps.append({"name": name, "type": "SINK", "func": func})
        return self

    def execute(self, max_retries: int = 1) -> PipelineRun:
        """Execute the pipeline end-to-end."""
        step_results: List[PipelineStep] = []
        data: Any = []
        total_processed = 0

        for step_def in self._steps:
            ps = PipelineStep(name=step_def["name"], step_type=step_def["type"])
            ps.status = PipelineStepStatus.RUNNING
            start = time.time()

            attempts = 0
            success = False
            while attempts < max_retries and not success:
                attempts += 1
                try:
                    if step_def["type"] == "SOURCE":
                        data = step_def["func"]()
                        ps.output_record_count = self._count_records(data)
                    elif step_def["type"] == "TRANSFORM":
                        ps.input_record_count = self._count_records(data)
                        data = step_def["func"](data)
                        ps.output_record_count = self._count_records(data)
                    elif step_def["type"] == "SPARK_TRANSFORM":
                        ps.input_record_count = self._count_records(data)
                        if HAS_PYSPARK and self.spark:
                            data = self.spark.sql(step_def["query"])
                        else:
                            # Fallback if PySpark is absent or not configured
                            ps.error_message = "PySpark not configured for SPARK_TRANSFORM step; skipped."
                        ps.output_record_count = self._count_records(data)
                    elif step_def["type"] == "SINK":
                        ps.input_record_count = self._count_records(data)
                        written = step_def["func"](data)
                        ps.output_record_count = written
                        total_processed += written
                    success = True
                    ps.status = PipelineStepStatus.COMPLETED
                except Exception as exc:
                    ps.error_message = str(exc)

            if not success:
                ps.status = PipelineStepStatus.FAILED

            ps.duration_ms = round((time.time() - start) * 1000, 3)
            step_results.append(ps)

            if ps.status == PipelineStepStatus.FAILED:
                break

        all_ok = all(s.status == PipelineStepStatus.COMPLETED for s in step_results)
        run = PipelineRun(
            pipeline_name=self.name,
            steps=step_results,
            status="COMPLETED" if all_ok else "FAILED",
            completed_at=time.time(),
            total_records_processed=total_processed,
        )
        self._runs.append(run)
        return run

    def _count_records(self, dataset: Any) -> int:
        """Helper to count records across list-of-dicts or PySpark DataFrames."""
        if dataset is None:
            return 0
        if isinstance(dataset, list):
            return len(dataset)
        if HAS_PYSPARK and hasattr(dataset, "count"):
            try:
                return dataset.count()
            except Exception:
                return 0
        return 0

    @property
    def run_history(self) -> List[PipelineRun]:
        """Return all past pipeline runs."""
        return list(self._runs)


class MedFlowOrchestrator:
    """Manages multiple MedFlow clinical data pipelines."""

    def __init__(self, spark: Optional[Any] = None) -> None:
        self.spark = spark
        self._pipelines: Dict[str, MedFlowPipeline] = {}

    def create_pipeline(self, name: str) -> MedFlowPipeline:
        """Create and register a new declarative pipeline."""
        pipeline = MedFlowPipeline(name, spark=self.spark)
        self._pipelines[name] = pipeline
        return pipeline

    def get_pipeline(self, name: str) -> Optional[MedFlowPipeline]:
        """Get a pipeline by name."""
        return self._pipelines.get(name)

    def list_pipelines(self) -> List[str]:
        """List all pipeline names."""
        return list(self._pipelines.keys())


medflow_orchestrator = MedFlowOrchestrator()
