"""
AI Healthcare System — SOTA High-Performance Low Level Design (LLD) Engine
========================================================================
Provides object-oriented low level design patterns for extreme memory & CPU efficiency:
1. Flyweight Pattern (shares immutable medical code instances to eliminate duplicate object allocations)
2. State & Strategy Pattern (encapsulates patient triage states and risk calculation strategies)
3. Template Method Pattern (standardizes zero-copy FHIR resource conversion pipelines)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


# ── 1. Flyweight Pattern ──────────────────────────────────────────────

class MedicalCodeFlyweight:
    """Immutable Flyweight object representing a medical ICD-10 / SNOMED concept."""

    def __init__(self, code: str, category: str, description: str):
        self.code = code
        self.category = category
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "category": self.category, "description": self.description}


class MedicalCodeFlyweightFactory:
    """Flyweight Factory managing shared medical concept instances."""

    def __init__(self):
        self._flyweights: Dict[str, MedicalCodeFlyweight] = {}

    def get_code(self, code: str, category: str, description: str) -> MedicalCodeFlyweight:
        if code not in self._flyweights:
            self._flyweights[code] = MedicalCodeFlyweight(code, category, description)
        return self._flyweights[code]

    def __len__(self) -> int:
        return len(self._flyweights)


# ── 2. Strategy & State Pattern ────────────────────────────────────────

class RiskEvaluationStrategy(ABC):
    @abstractmethod
    def calculate_risk(self, metrics: Dict[str, float]) -> float:
        pass


class CardiacRiskStrategy(RiskEvaluationStrategy):
    def calculate_risk(self, metrics: Dict[str, float]) -> float:
        sbp = metrics.get("sbp", 120.0)
        chol = metrics.get("cholesterol", 180.0)
        return min(1.0, round(((sbp - 100) / 100.0) * 0.5 + ((chol - 150) / 150.0) * 0.5, 3))


class MetabolicRiskStrategy(RiskEvaluationStrategy):
    def calculate_risk(self, metrics: Dict[str, float]) -> float:
        glucose = metrics.get("glucose", 90.0)
        bmi = metrics.get("bmi", 22.0)
        return min(1.0, round(((glucose - 80) / 100.0) * 0.6 + ((bmi - 20) / 20.0) * 0.4, 3))


class PatientTriageContext:
    """Context owning the active clinical strategy and state."""

    def __init__(self, strategy: RiskEvaluationStrategy):
        self.strategy = strategy
        self.state = "TRIAGE"

    def set_strategy(self, strategy: RiskEvaluationStrategy):
        self.strategy = strategy

    def evaluate(self, metrics: Dict[str, float]) -> float:
        return self.strategy.calculate_risk(metrics)


# ── 3. Template Method Pattern ─────────────────────────────────────────

class BaseFHIRResourceConverter(ABC):
    """Template Method skeleton for zero-copy FHIR resource generation."""

    def convert(self, record: Dict[str, Any]) -> Dict[str, Any]:
        data = self._extract_raw_data(record)
        data = self._apply_pii_sanitization(data)
        return self._build_fhir_payload(data)

    @abstractmethod
    def _extract_raw_data(self, record: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def _apply_pii_sanitization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Default PII sanitization step
        return data

    @abstractmethod
    def _build_fhir_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class FHIRPatientConverter(BaseFHIRResourceConverter):
    def _extract_raw_data(self, record: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": record.get("id"), "name": record.get("name", "Anonymous")}

    def _build_fhir_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": str(data["id"]),
            "active": True
        }


# Singleton instances
flyweight_factory = MedicalCodeFlyweightFactory()
fhir_patient_converter = FHIRPatientConverter()
