"""
AI Healthcare System — Unified Data Intelligence Platform.

Consolidates all clinical data analytics, feature engineering, lineage tracking,
and real-time streaming into a single composable intelligence layer:

1. Clinical Feature Store — versioned feature vectors for ML model training
2. Data Lineage Tracker — end-to-end provenance graph for every data transformation
3. Real-Time Streaming Analytics Engine — sliding-window vitals anomaly detection
4. Data Quality Gate — automated validation rules enforcing schema & range contracts
5. Unified Query Fabric — single API surface across all clinical data domains
"""

import time
import uuid
import statistics
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =====================================================================
# 1. Clinical Feature Store
# =====================================================================

class FeatureVector(BaseModel):
    """A single versioned feature vector for a patient."""
    feature_id: str = Field(default_factory=lambda: f"FV-{uuid.uuid4().hex[:8]}")
    patient_id: str
    feature_name: str
    value: float
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClinicalFeatureStore:
    """
    Versioned feature store for clinical ML pipelines.

    Stores pre-computed feature vectors (e.g. rolling heart-rate mean,
    lab-trend slope) that models consume at training and inference time.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[FeatureVector]] = {}

    def upsert_feature(
        self,
        patient_id: str,
        feature_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeatureVector:
        """Insert or version-bump a feature vector."""
        key = f"{patient_id}:{feature_name}"
        existing = self._store.get(key, [])
        new_version = (existing[-1].version + 1) if existing else 1
        fv = FeatureVector(
            patient_id=patient_id,
            feature_name=feature_name,
            value=value,
            version=new_version,
            metadata=metadata or {},
        )
        existing.append(fv)
        self._store[key] = existing
        return fv

    def get_latest(self, patient_id: str, feature_name: str) -> Optional[FeatureVector]:
        """Retrieve the latest version of a feature."""
        key = f"{patient_id}:{feature_name}"
        versions = self._store.get(key)
        return versions[-1] if versions else None

    def get_patient_features(self, patient_id: str) -> List[FeatureVector]:
        """Retrieve all latest features for a patient."""
        results: List[FeatureVector] = []
        for key, versions in self._store.items():
            if key.startswith(f"{patient_id}:"):
                results.append(versions[-1])
        return results

    @property
    def total_features(self) -> int:
        """Return total number of unique feature keys."""
        return len(self._store)


# =====================================================================
# 2. Data Lineage Tracker
# =====================================================================

class LineageNode(BaseModel):
    """A single node in the data lineage graph."""
    node_id: str = Field(default_factory=lambda: f"LN-{uuid.uuid4().hex[:6]}")
    name: str
    node_type: str  # "SOURCE", "TRANSFORM", "SINK"
    upstream_ids: List[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataLineageTracker:
    """
    Tracks end-to-end provenance of every data transformation.

    Builds a directed acyclic graph (DAG) of data flow from raw ingestion
    through feature engineering to model prediction output.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, LineageNode] = {}

    def register_node(
        self,
        name: str,
        node_type: str,
        upstream_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LineageNode:
        """Register a new lineage node."""
        node = LineageNode(
            name=name,
            node_type=node_type,
            upstream_ids=upstream_ids or [],
            metadata=metadata or {},
        )
        self._nodes[node.node_id] = node
        return node

    def get_upstream_chain(self, node_id: str) -> List[LineageNode]:
        """Trace the full upstream provenance chain for a node."""
        chain: List[LineageNode] = []
        visited = set()

        def _walk(nid: str) -> None:
            if nid in visited or nid not in self._nodes:
                return
            visited.add(nid)
            node = self._nodes[nid]
            chain.append(node)
            for uid in node.upstream_ids:
                _walk(uid)

        _walk(node_id)
        return chain

    @property
    def node_count(self) -> int:
        """Return total lineage nodes."""
        return len(self._nodes)


# =====================================================================
# 3. Real-Time Streaming Analytics Engine
# =====================================================================

class VitalsAnomaly(BaseModel):
    """Detected anomaly in a patient vitals stream."""
    patient_id: str
    metric_name: str
    current_value: float
    window_mean: float
    window_std: float
    z_score: float
    is_anomaly: bool
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"


class StreamingAnalyticsEngine:
    """
    Sliding-window anomaly detection over streaming patient vitals.

    Maintains per-patient, per-metric circular buffers and flags readings
    whose z-score exceeds configurable thresholds.
    """

    def __init__(self, window_size: int = 20, z_threshold: float = 2.0) -> None:
        self.window_size = window_size
        self.z_threshold = z_threshold
        self._buffers: Dict[str, List[float]] = {}

    def ingest(self, patient_id: str, metric_name: str, value: float) -> VitalsAnomaly:
        """Ingest a single vitals reading and return anomaly assessment."""
        key = f"{patient_id}:{metric_name}"
        buf = self._buffers.get(key, [])
        buf.append(value)
        if len(buf) > self.window_size:
            buf = buf[-self.window_size:]
        self._buffers[key] = buf

        if len(buf) < 3:
            return VitalsAnomaly(
                patient_id=patient_id,
                metric_name=metric_name,
                current_value=value,
                window_mean=value,
                window_std=0.0,
                z_score=0.0,
                is_anomaly=False,
                severity="LOW",
            )

        mean = statistics.mean(buf)
        std = statistics.stdev(buf)
        z = abs((value - mean) / std) if std > 0 else 0.0

        is_anomaly = z > self.z_threshold
        if z > 4.0:
            severity = "CRITICAL"
        elif z > 3.0:
            severity = "HIGH"
        elif z > self.z_threshold:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return VitalsAnomaly(
            patient_id=patient_id,
            metric_name=metric_name,
            current_value=value,
            window_mean=round(mean, 2),
            window_std=round(std, 2),
            z_score=round(z, 2),
            is_anomaly=is_anomaly,
            severity=severity,
        )


# =====================================================================
# 4. Data Quality Gate
# =====================================================================

class QualityRuleResult(BaseModel):
    """Result of a single data quality rule evaluation."""
    rule_name: str
    passed: bool
    message: str


class DataQualityGate:
    """
    Automated data quality enforcement with pluggable validation rules.

    Each rule is a callable that receives a record dict and returns
    a QualityRuleResult. All rules must pass for the record to proceed.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, Any] = {}

    def add_rule(self, name: str, validator: Any) -> None:
        """Register a named validation rule."""
        self._rules[name] = validator

    def validate(self, record: Dict[str, Any]) -> List[QualityRuleResult]:
        """Run all rules against a record."""
        results: List[QualityRuleResult] = []
        for name, validator in self._rules.items():
            try:
                passed = validator(record)
                results.append(QualityRuleResult(
                    rule_name=name,
                    passed=bool(passed),
                    message="OK" if passed else f"Rule '{name}' failed.",
                ))
            except Exception as exc:
                results.append(QualityRuleResult(
                    rule_name=name, passed=False, message=str(exc),
                ))
        return results

    def gate_passes(self, record: Dict[str, Any]) -> bool:
        """Return True only if every rule passes."""
        return all(r.passed for r in self.validate(record))


# =====================================================================
# 5. Unified Query Fabric
# =====================================================================

class QueryResult(BaseModel):
    """Result of a unified query."""
    domain: str
    records: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float


class UnifiedQueryFabric:
    """
    Single API surface that federates queries across all clinical data domains.

    Registered domain handlers are invoked transparently so callers never
    need to know the underlying storage technology.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Any] = {}

    def register_domain(self, domain: str, handler: Any) -> None:
        """Register a query handler for a clinical data domain."""
        self._handlers[domain] = handler

    def query(self, domain: str, **kwargs: Any) -> QueryResult:
        """Execute a federated query against a registered domain."""
        start = time.time()
        handler = self._handlers.get(domain)
        if handler is None:
            return QueryResult(domain=domain, records=[], total_count=0, query_time_ms=0.0)

        records = handler(**kwargs)
        elapsed = (time.time() - start) * 1000
        return QueryResult(
            domain=domain,
            records=records if isinstance(records, list) else [records],
            total_count=len(records) if isinstance(records, list) else 1,
            query_time_ms=round(elapsed, 3),
        )

    @property
    def domain_count(self) -> int:
        """Return number of registered domains."""
        return len(self._handlers)


# =====================================================================
# Global singletons
# =====================================================================
clinical_feature_store = ClinicalFeatureStore()
data_lineage_tracker = DataLineageTracker()
streaming_analytics_engine = StreamingAnalyticsEngine()
data_quality_gate = DataQualityGate()
unified_query_fabric = UnifiedQueryFabric()

# Pre-register standard quality rules
data_quality_gate.add_rule(
    "patient_id_present",
    lambda r: bool(r.get("patient_id")),
)
data_quality_gate.add_rule(
    "heart_rate_range",
    lambda r: 20 < r.get("heart_rate", 70) < 300,
)
