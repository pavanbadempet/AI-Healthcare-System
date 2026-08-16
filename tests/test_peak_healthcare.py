"""
Comprehensive Test Suite for Peak Healthcare Intelligence:
- Clinical Digital Twin (10-Year Multi-Organ Trajectory Simulation)
- Precision Pharmacogenomics (CPIC Drug-Gene Prescribing Engine)
- Autonomous Multi-Specialist Clinical Consensus Council
- Peak Healthcare FastAPI Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.agents.clinical_consensus_council import clinical_council
from backend.clinical_digital_twin import digital_twin_engine
from backend.main import app
from backend.precision_pharmacogenomics import pharmacogenomics_engine
from backend.schemas.peak_healthcare import (
    ClinicalCouncilDeliberationRequest,
    DigitalTwinSimulationRequest,
    PharmacogenomicEvaluationRequest,
    PharmacogenomicProfile,
)


@pytest.fixture
def sample_twin_request():
    return DigitalTwinSimulationRequest(
        patient_id="TWIN-PAT-101",
        age=55.0,
        gender="male",
        bmi=32.0,
        systolic_bp=148.0,
        fasting_glucose=145.0,
        egfr=72.0,
        ldl_cholesterol=140.0,
        hba1c=7.8,
        smoking_status="former",
        proposed_interventions=[
            "SGLT2 inhibitor (Empagliflozin 10mg)",
            "GLP-1 RA (Semaglutide 0.5mg)",
            "High-Intensity Statin (Atorvastatin 40mg)",
            "Mediterranean Diet & Zone 2 Exercise Protocol"
        ]
    )


@pytest.fixture
def sample_pgx_request():
    return PharmacogenomicEvaluationRequest(
        patient_id="PGX-PAT-202",
        proposed_medications=["Clopidogrel 75mg", "Simvastatin 40mg", "Codeine 30mg", "Abacavir 300mg"],
        genomic_profile=PharmacogenomicProfile(
            patient_id="PGX-PAT-202",
            cyp2c19_phenotype="Poor Metabolizer (*2/*2)",
            slco1b1_genotype="Decreased Function (*5/*5)",
            cyp2d6_phenotype="Ultra-Rapid Metabolizer (*1/*1xN)",
            hla_b5701_status="Positive"
        )
    )


@pytest.fixture
def sample_council_request():
    return ClinicalCouncilDeliberationRequest(
        patient_id="COUNCIL-PAT-303",
        clinical_summary="62-year-old female presenting with worsening exertional dyspnea, microalbuminuria, and suboptimal glycemic control.",
        primary_symptoms=["exertional dyspnea", "substernal chest pressure", "bilateral lower extremity edema"],
        vitals_summary={"systolic_bp": 152, "diastolic_bp": 92, "heart_rate": 86, "spo2": 96},
        lab_results={"fasting_glucose": 160, "hba1c": 8.4, "egfr": 54, "uacr": 180},
        current_medications=["Metformin 1000mg BID", "Lisinopril 20mg", "Losartan 50mg"]
    )


def test_digital_twin_trajectory_simulation(sample_twin_request):
    """Verifies that the Digital Twin engine projects 10-year multi-organ trajectories."""
    resp = digital_twin_engine.simulate_10_year_trajectory(sample_twin_request)

    assert resp.patient_id == "TWIN-PAT-101"
    assert resp.simulation_horizon_years == 10
    assert resp.overall_longevity_gain_years > 0.0

    for organ_name in ["cardiovascular", "renal", "metabolic", "hepatic"]:
        organ_traj = getattr(resp, organ_name)
        assert organ_traj.organ == organ_name
        assert len(organ_traj.projected_score_without_intervention) == 10
        assert len(organ_traj.projected_score_with_intervention) == 10
        # Intervention trajectory must maintain higher score than non-intervention
        assert organ_traj.projected_score_with_intervention[-1] > organ_traj.projected_score_without_intervention[-1]
        assert organ_traj.relative_risk_reduction > 0.0


def test_precision_pharmacogenomics_cpic_evaluation(sample_pgx_request):
    """Verifies CPIC Level A detection for critical gene-drug metabolic interactions."""
    resp = pharmacogenomics_engine.evaluate(sample_pgx_request)

    assert resp.patient_id == "PGX-PAT-202"
    assert resp.total_drugs_analyzed == 4
    assert resp.has_critical_contraindications is True

    clopidogrel_rep = next(r for r in resp.evaluations if "clopidogrel" in r.drug_name.lower())
    assert "CYP2C19" in clopidogrel_rep.relevant_gene
    assert "AVOID CLOPIDOGREL" in clopidogrel_rep.recommended_dosage_adjustment

    simvastatin_rep = next(r for r in resp.evaluations if "simvastatin" in r.drug_name.lower())
    assert "SLCO1B1" in simvastatin_rep.relevant_gene
    assert "RHABDOMYOLYSIS" in simvastatin_rep.recommended_dosage_adjustment

    abacavir_rep = next(r for r in resp.evaluations if "abacavir" in r.drug_name.lower())
    assert "HLA-B*5701" in abacavir_rep.relevant_gene
    assert "ABSOLUTELY CONTRAINDICATED" in abacavir_rep.recommended_dosage_adjustment


def test_clinical_consensus_council_deliberation(sample_council_request):
    """Verifies multi-agent swarm deliberation across 5 medical specialties and safety synthesis."""
    resp = clinical_council.deliberate_and_synthesize(sample_council_request)

    assert resp.patient_id == "COUNCIL-PAT-303"
    assert len(resp.specialist_opinions) == 5
    assert resp.consensus_confidence > 0.85
    assert len(resp.unified_care_plan) > 0

    # Check that dual RAS blockade flag was caught by pharmacist
    assert any("Concurrent ACEI and ARB" in alert for alert in resp.critical_safety_alerts)


def test_peak_healthcare_fastapi_endpoints(sample_twin_request, sample_pgx_request, sample_council_request):
    """Verifies HTTP REST API endpoints for all peak healthcare capabilities."""
    client = TestClient(app)

    # 1. Digital twin simulation endpoint
    res_twin = client.post("/v1/digital-twin/simulate", json=sample_twin_request.model_dump())
    assert res_twin.status_code == 200
    data_twin = res_twin.json()
    assert "cardiovascular" in data_twin
    assert data_twin["overall_longevity_gain_years"] > 0

    # 2. Pharmacogenomics evaluation endpoint
    res_pgx = client.post("/v1/pharmacogenomics/evaluate", json=sample_pgx_request.model_dump())
    assert res_pgx.status_code == 200
    data_pgx = res_pgx.json()
    assert data_pgx["has_critical_contraindications"] is True
    assert len(data_pgx["evaluations"]) == 4

    # 3. Clinical council deliberation endpoint
    res_council = client.post("/v1/clinical-council/deliberate", json=sample_council_request.model_dump())
    assert res_council.status_code == 200
    data_council = res_council.json()
    assert len(data_council["specialist_opinions"]) == 5
    assert len(data_council["critical_safety_alerts"]) > 0
