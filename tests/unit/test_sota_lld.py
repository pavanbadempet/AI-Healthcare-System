"""
Unit tests for SOTA Low Level Design (backend/sota_lld.py).
"""

import pytest
from backend.sota_lld import (
    MedicalCodeFlyweightFactory,
    CardiacRiskStrategy,
    MetabolicRiskStrategy,
    PatientTriageContext,
    FHIRPatientConverter,
)


def test_flyweight_factory():
    factory = MedicalCodeFlyweightFactory()
    code1 = factory.get_code("E11.9", "Endocrine", "Type 2 Diabetes")
    code2 = factory.get_code("E11.9", "Endocrine", "Type 2 Diabetes")

    assert code1 is code2  # Same flyweight instance in memory
    assert len(factory) == 1


def test_strategy_pattern():
    cardiac = CardiacRiskStrategy()
    metabolic = MetabolicRiskStrategy()

    ctx = PatientTriageContext(cardiac)
    cardiac_risk = ctx.evaluate({"sbp": 140.0, "cholesterol": 220.0})
    assert cardiac_risk > 0.0

    ctx.set_strategy(metabolic)
    metabolic_risk = ctx.evaluate({"glucose": 130.0, "bmi": 28.0})
    assert metabolic_risk > 0.0


def test_template_method_converter():
    converter = FHIRPatientConverter()
    fhir_res = converter.convert({"id": "PAT123", "name": "John Doe"})

    assert fhir_res["resourceType"] == "Patient"
    assert fhir_res["id"] == "PAT123"
    assert fhir_res["active"] is True
