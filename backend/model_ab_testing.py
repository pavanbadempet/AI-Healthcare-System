"""
Model A/B Testing & Canary Deployments Service
=============================================
Manages routing, telemetry, and outcome recording for live A/B tests,
canary releases, and shadow model configurations.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .cache_service import cache

logger = logging.getLogger(__name__)

@dataclass
class ABTestConfig:
    experiment_id: str
    model_a_name: str
    model_b_name: str
    traffic_split: float  # 0.0 to 1.0 (portion directed to B)
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, stopped, paused
    strategy: str = "canary"  # canary, shadow, blue_green

@dataclass
class ExperimentOutcome:
    experiment_id: str
    model_version: str
    prediction: Any
    actual_outcome: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class ModelABTestManager:
    """Thread-safe singleton managing ML model A/B testing configurations,
    routing decisions, and outcome tracking.
    """
    _instance: Optional[ModelABTestManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> ModelABTestManager:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._init_manager()
                cls._instance = inst
            return cls._instance

    def _init_manager(self) -> None:
        self._lock = threading.Lock()
        self._experiments: Dict[str, ABTestConfig] = {}
        self._outcomes: Dict[str, List[ExperimentOutcome]] = {}
        self._load_from_persistence()

    def _load_from_persistence(self) -> None:
        """Loads experiment configs from cache/Redis if available."""
        try:
            cached_data = cache.get("ab_testing_configs")
            if cached_data:
                configs = json.loads(cached_data)
                for exp_id, exp_dict in configs.items():
                    exp_dict["start_time"] = datetime.fromisoformat(exp_dict["start_time"])
                    if exp_dict.get("end_time"):
                        exp_dict["end_time"] = datetime.fromisoformat(exp_dict["end_time"])
                    self._experiments[exp_id] = ABTestConfig(**exp_dict)

            cached_outcomes = cache.get("ab_testing_outcomes")
            if cached_outcomes:
                outcomes_raw = json.loads(cached_outcomes)
                for exp_id, list_out in outcomes_raw.items():
                    self._outcomes[exp_id] = [
                        ExperimentOutcome(
                            experiment_id=o["experiment_id"],
                            model_version=o["model_version"],
                            prediction=o["prediction"],
                            actual_outcome=o["actual_outcome"],
                            timestamp=datetime.fromisoformat(o["timestamp"])
                        )
                        for o in list_out
                    ]
        except Exception as e:
            logger.warning("Failed to load A/B test manager state: %s", e)

    def _persist(self) -> None:
        """Persists current experiment state to Redis/cache."""
        try:
            exp_serialized = {
                k: {**asdict(v), "start_time": v.start_time.isoformat(),
                    "end_time": v.end_time.isoformat() if v.end_time else None}
                for k, v in self._experiments.items()
            }
            cache.set("ab_testing_configs", json.dumps(exp_serialized))

            outcomes_serialized = {
                k: [
                    {
                        "experiment_id": o.experiment_id,
                        "model_version": o.model_version,
                        "prediction": o.prediction,
                        "actual_outcome": o.actual_outcome,
                        "timestamp": o.timestamp.isoformat()
                    }
                    for o in v
                ]
                for k, v in self._outcomes.items()
            }
            cache.set("ab_testing_outcomes", json.dumps(outcomes_serialized))
        except Exception as e:
            logger.warning("Failed to persist A/B test state: %s", e)

    def create_experiment(self, config: ABTestConfig) -> None:
        """Registers a new experiment configuration."""
        with self._lock:
            self._experiments[config.experiment_id] = config
            if config.experiment_id not in self._outcomes:
                self._outcomes[config.experiment_id] = []
            self._persist()
            logger.info("A/B test experiment %s created.", config.experiment_id)

    def stop_experiment(self, experiment_id: str) -> None:
        """Stops an active experiment."""
        with self._lock:
            if experiment_id in self._experiments:
                self._experiments[experiment_id].status = "stopped"
                self._experiments[experiment_id].end_time = datetime.now(timezone.utc)
                self._persist()
                logger.info("A/B test experiment %s stopped.", experiment_id)

    def route_prediction(self, patient_data: Dict[str, Any], experiment_id: str) -> str:
        """Routes a prediction request for a given patient to either Model A or Model B.

        Uses a deterministic hash of user/patient identifier to ensure sticky routing.
        """
        with self._lock:
            config = self._experiments.get(experiment_id)
            if not config or config.status != "active":
                return "model_a"  # Fallback to control group / default model A

            # Deterministic split on identifier (patient_id, email, username, etc.)
            patient_id = str(patient_data.get("patient_id", patient_data.get("id", "anonymous")))
            hash_val = int(hashlib.md5(patient_id.encode("utf-8")).hexdigest(), 16)
            bucket = (hash_val % 100) / 100.0

            if config.strategy == "shadow":
                # Shadow runs both, returns model A's name as the serving decision
                return config.model_a_name

            if bucket < config.traffic_split:
                return config.model_b_name
            else:
                return config.model_a_name

    def record_outcome(self, experiment_id: str, model_version: str, prediction: Any, actual_outcome: Any) -> None:
        """Logs the actual outcome of an A/B routed prediction for downstream analysis."""
        with self._lock:
            if experiment_id not in self._outcomes:
                self._outcomes[experiment_id] = []
            self._outcomes[experiment_id].append(
                ExperimentOutcome(
                    experiment_id=experiment_id,
                    model_version=model_version,
                    prediction=prediction,
                    actual_outcome=actual_outcome
                )
            )
            self._persist()

    def get_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """Calculates performance comparison metrics for models under test."""
        with self._lock:
            config = self._experiments.get(experiment_id)
            outcomes = self._outcomes.get(experiment_id, [])

            if not config:
                return {"error": f"Experiment {experiment_id} not found"}

            results: Dict[str, Dict[str, Any]] = {
                config.model_a_name: {"correct": 0, "total": 0, "accuracy": 0.0},
                config.model_b_name: {"correct": 0, "total": 0, "accuracy": 0.0}
            }

            for outcome in outcomes:
                ver = outcome.model_version
                if ver not in results:
                    results[ver] = {"correct": 0, "total": 0, "accuracy": 0.0}

                results[ver]["total"] += 1
                try:
                    # Generic equivalence check for prediction & outcome
                    if str(outcome.prediction).lower() == str(outcome.actual_outcome).lower():
                        results[ver]["correct"] += 1
                except Exception:
                    pass

            for ver in results:
                if results[ver]["total"] > 0:
                    results[ver]["accuracy"] = results[ver]["correct"] / results[ver]["total"]

            return {
                "experiment_id": experiment_id,
                "strategy": config.strategy,
                "status": config.status,
                "metrics": results
            }

# Global instance
ab_test_manager = ModelABTestManager()
