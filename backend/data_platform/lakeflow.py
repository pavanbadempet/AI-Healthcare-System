"""
MedFlow — ETL/ELT Pipeline Orchestrator for Clinical Data Lakehouse.

Provides:
- Declarative pipeline DAG definition
- Step-level retries and error handling
- Pipeline versioning and run history
- Source → Transform → Sink execution model
- Open-standard lakehouse migration-compatible interface
"""

import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


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
    step_type: str  # "SOURCE", "TRANSFORM", "SINK"
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

    Each step receives data from the previous step and passes its output
    to the next. Steps are callables that accept and return list-of-dicts.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: List[Dict[str, Any]] = []
        self._runs: List[PipelineRun] = []

    def add_source(self, name: str, func: Callable[[], List[Dict[str, Any]]]) -> "MedFlowPipeline":
        """Add a data source step."""
        self._steps.append({"name": name, "type": "SOURCE", "func": func})
        return self

    def add_transform(self, name: str, func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]) -> "MedFlowPipeline":
        """Add a transformation step."""
        self._steps.append({"name": name, "type": "TRANSFORM", "func": func})
        return self

    def add_sink(self, name: str, func: Callable[[List[Dict[str, Any]]], int]) -> "MedFlowPipeline":
        """Add a data sink step."""
        self._steps.append({"name": name, "type": "SINK", "func": func})
        return self

    def execute(self, max_retries: int = 1) -> PipelineRun:
        """Execute the pipeline end-to-end."""
        step_results: List[PipelineStep] = []
        data: List[Dict[str, Any]] = []
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
                        ps.output_record_count = len(data)
                    elif step_def["type"] == "TRANSFORM":
                        ps.input_record_count = len(data)
                        data = step_def["func"](data)
                        ps.output_record_count = len(data)
                    elif step_def["type"] == "SINK":
                        ps.input_record_count = len(data)
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

    @property
    def run_history(self) -> List[PipelineRun]:
        """Return all past pipeline runs."""
        return list(self._runs)


class MedFlowOrchestrator:
    """Manages multiple MedFlow clinical data pipelines."""

    def __init__(self) -> None:
        self._pipelines: Dict[str, MedFlowPipeline] = {}

    def create_pipeline(self, name: str) -> MedFlowPipeline:
        """Create and register a new pipeline."""
        pipeline = MedFlowPipeline(name)
        self._pipelines[name] = pipeline
        return pipeline

    def get_pipeline(self, name: str) -> Optional[MedFlowPipeline]:
        """Get a pipeline by name."""
        return self._pipelines.get(name)

    def list_pipelines(self) -> List[str]:
        """List all pipeline names."""
        return list(self._pipelines.keys())


medflow_orchestrator = MedFlowOrchestrator()

# Backward-compatible aliases
LakeflowPipeline = MedFlowPipeline
LakeflowOrchestrator = MedFlowOrchestrator
lakeflow_orchestrator = medflow_orchestrator
