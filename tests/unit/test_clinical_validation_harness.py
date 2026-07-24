from backend.ml.clinical_validation_harness import MultiCenterClinicalValidator, evaluate_clinical_readiness


def test_multi_center_clinical_validator_pass():
    validator = MultiCenterClinicalValidator()
    sites = [
        {"sensitivity": 0.95, "specificity": 0.90, "auroc": 0.93, "brier": 0.08, "samples": 2000},
        {"sensitivity": 0.92, "specificity": 0.88, "auroc": 0.91, "brier": 0.09, "samples": 1500},
    ]
    res = validator.validate_model_multicenter("heart_disease", sites)
    assert res.fda_samd_pass is True
    assert res.num_sites_evaluated == 2
    assert res.total_samples == 3500


def test_multi_center_clinical_validator_fail():
    validator = MultiCenterClinicalValidator()
    sites = [
        {"sensitivity": 0.80, "specificity": 0.70, "auroc": 0.75, "brier": 0.25, "samples": 1000},
    ]
    res = validator.validate_model_multicenter("low_accuracy_model", sites)
    assert res.fda_samd_pass is False


def test_evaluate_clinical_readiness_helper():
    info = evaluate_clinical_readiness("diabetes")
    assert info["model_name"] == "diabetes"
    assert info["num_sites"] == 3
    assert info["fda_samd_readiness"] is True
