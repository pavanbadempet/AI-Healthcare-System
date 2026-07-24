"""
Unit tests for SOTA Dimensional Modeling Engine (backend/sota_dimensional_modeling.py).
"""

from backend.sota_dimensional_modeling import (
    DimFacility,
    DimPatient,
    FactPatientEncounter,
    SOTADimensionalModelingEngine,
)


def test_dimensional_star_schema_kpi():
    engine = SOTADimensionalModelingEngine()

    dim_p = DimPatient(patient_dim_key=101, patient_id="PAT_01", age_group="45-54", gender="F")
    dim_f = DimFacility(facility_dim_key=501, facility_name="General Hospital", region="North")

    fact1 = FactPatientEncounter(
        encounter_fact_key=10001,
        patient_dim_key=dim_p.patient_dim_key,
        facility_dim_key=dim_f.facility_dim_key,
        length_of_stay_hours=48.0,
        total_cost_usd=1200.0,
        readmission_risk_score=0.15
    )

    engine.register_encounter_fact(fact1)
    kpis = engine.calculate_facility_kpis(501)

    assert kpis["facility_dim_key"] == 501
    assert kpis["total_encounters"] == 1
    assert kpis["avg_stay_hours"] == 48.0
    assert kpis["avg_cost_usd"] == 1200.0
