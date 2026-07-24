from backend.ml.patient_phenotyping import ClinicalPhenotypingEngine, run_patient_phenotyping_pipeline


def test_clinical_phenotyping_engine():
    engine = ClinicalPhenotypingEngine()
    res = engine.Discover_patient_phenotypes()
    assert res.stability_pass is True
    assert res.num_clusters == 3
    assert res.cluster_stability_ari >= 0.85


def test_run_patient_phenotyping_pipeline_helper():
    info = run_patient_phenotyping_pipeline()
    assert info["stability_pass"] is True
    assert "Phenotype_1_Cardiometabolic_High_Risk" in info["cluster_distribution"]
