"""Model and dataset cards for local clinical prediction models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data" / "processed"


@dataclass(frozen=True)
class DatasetCard:
    id: str
    name: str
    source: str
    local_artifact: str
    task: str
    intended_use: str
    known_limitations: tuple[str, ...]
    contains_production_patient_data: bool = False

    def to_dict(self) -> dict[str, Any]:
        path = ROOT_DIR / self.local_artifact
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "local_artifact": self.local_artifact,
            "local_artifact_exists": path.exists(),
            "artifact_size_bytes": path.stat().st_size if path.exists() else 0,
            "task": self.task,
            "intended_use": self.intended_use,
            "known_limitations": list(self.known_limitations),
            "contains_production_patient_data": self.contains_production_patient_data,
        }


@dataclass(frozen=True)
class ModelCard:
    id: str
    name: str
    endpoint: str
    artifact: str
    model_family: str
    dataset_card_id: str
    clinical_use_category: str
    intended_use: str
    target_users: tuple[str, ...]
    feature_count: int
    output: str
    limitations: tuple[str, ...]
    human_review_required: bool = True
    medical_disclaimer_required: bool = True
    post_deployment_monitoring_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        path = ROOT_DIR / self.artifact
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": self.endpoint,
            "artifact": self.artifact,
            "artifact_exists": path.exists(),
            "artifact_size_bytes": path.stat().st_size if path.exists() else 0,
            "model_family": self.model_family,
            "dataset_card_id": self.dataset_card_id,
            "clinical_use_category": self.clinical_use_category,
            "intended_use": self.intended_use,
            "target_users": list(self.target_users),
            "feature_count": self.feature_count,
            "output": self.output,
            "limitations": list(self.limitations),
            "human_review_required": self.human_review_required,
            "medical_disclaimer_required": self.medical_disclaimer_required,
            "post_deployment_monitoring_required": self.post_deployment_monitoring_required,
        }


DATASET_CARDS: tuple[DatasetCard, ...] = (
    DatasetCard(
        id="brfss_2015_diabetes",
        name="BRFSS 2015 diabetes screening dataset",
        source="CDC BRFSS public-use survey-derived dataset",
        local_artifact="data/processed/diabetes.parquet",
        task="diabetes risk screening",
        intended_use="Training and local validation for non-diagnostic diabetes risk screening.",
        known_limitations=(
            "Survey-derived features are not a substitute for laboratory diagnosis.",
            "Local calibration should be reviewed before clinical deployment.",
        ),
    ),
    DatasetCard(
        id="cleveland_uci_heart",
        name="Cleveland UCI heart disease dataset",
        source="UCI public clinical research dataset",
        local_artifact="data/processed/heart.parquet",
        task="heart disease screening",
        intended_use="Training and local validation for clinician-reviewed cardiac risk screening.",
        known_limitations=(
            "Small historical dataset with limited demographic representativeness.",
            "Not suitable for autonomous diagnosis or emergency triage.",
        ),
    ),
    DatasetCard(
        id="ilpd_liver",
        name="Indian Liver Patient Dataset",
        source="UCI public clinical research dataset",
        local_artifact="data/processed/liver.parquet",
        task="liver disease screening",
        intended_use="Training and local validation for clinician-reviewed liver disease screening.",
        known_limitations=(
            "Requires local validation against current lab reference ranges.",
            "Feature distributions may not match all hospital populations.",
        ),
    ),
    DatasetCard(
        id="uci_ckd",
        name="UCI chronic kidney disease dataset",
        source="UCI public clinical research dataset",
        local_artifact="data/processed/kidney.parquet",
        task="kidney disease screening",
        intended_use="Training and local validation for clinician-reviewed kidney risk screening.",
        known_limitations=(
            "Missingness and categorical encoding require careful monitoring.",
            "Not a substitute for nephrology review.",
        ),
    ),
    DatasetCard(
        id="lung_survey",
        name="Lung health survey dataset",
        source="Public lung health survey-derived dataset",
        local_artifact="data/processed/lungs.parquet",
        task="respiratory issue screening",
        intended_use="Training and local validation for clinician-reviewed respiratory risk screening.",
        known_limitations=(
            "Survey-derived symptoms are not diagnostic imaging or pulmonary function tests.",
            "Requires local validation before use in clinical pathways.",
        ),
    ),
)


MODEL_CARDS: tuple[ModelCard, ...] = (
    ModelCard(
        id="diabetes_risk_screening",
        name="Diabetes risk screening model",
        endpoint="/predict/diabetes",
        artifact="backend/diabetes_model.pkl",
        model_family="XGBoost/scikit-learn classifier",
        dataset_card_id="brfss_2015_diabetes",
        clinical_use_category="clinician_review",
        intended_use="AI-assisted screening signal for diabetes risk review.",
        target_users=("patient", "doctor"),
        feature_count=9,
        output="risk label, raw class, confidence, risk level, disclaimer",
        limitations=("Screening only; diagnosis requires qualified clinical assessment.",),
    ),
    ModelCard(
        id="heart_disease_screening",
        name="Heart disease screening model",
        endpoint="/predict/heart",
        artifact="backend/heart_disease_model.pkl",
        model_family="Ensemble/scikit-learn classifier",
        dataset_card_id="cleveland_uci_heart",
        clinical_use_category="clinician_review",
        intended_use="AI-assisted cardiac risk signal for clinician review.",
        target_users=("patient", "doctor"),
        feature_count=13,
        output="risk label, raw class, confidence, risk level, disclaimer",
        limitations=("Not for autonomous diagnosis, emergency triage, or treatment selection.",),
    ),
    ModelCard(
        id="liver_disease_screening",
        name="Liver disease screening model",
        endpoint="/predict/liver",
        artifact="backend/liver_disease_model.pkl",
        model_family="Ensemble/scikit-learn classifier with scaler",
        dataset_card_id="ilpd_liver",
        clinical_use_category="clinician_review",
        intended_use="AI-assisted liver disease screening signal for clinician review.",
        target_users=("patient", "doctor"),
        feature_count=10,
        output="risk label, raw class, confidence, risk level, disclaimer",
        limitations=("Requires laboratory context and clinician interpretation.",),
    ),
    ModelCard(
        id="kidney_disease_screening",
        name="Kidney disease screening model",
        endpoint="/predict/kidney",
        artifact="backend/kidney_model.pkl",
        model_family="scikit-learn classifier with scaler",
        dataset_card_id="uci_ckd",
        clinical_use_category="clinician_review",
        intended_use="AI-assisted chronic kidney disease screening signal for clinician review.",
        target_users=("patient", "doctor"),
        feature_count=24,
        output="risk label, raw class, confidence, risk level, disclaimer",
        limitations=("Not a replacement for renal labs, imaging, or nephrology review.",),
    ),
    ModelCard(
        id="lung_health_screening",
        name="Lung health screening model",
        endpoint="/predict/lungs",
        artifact="backend/lungs_model.pkl",
        model_family="scikit-learn classifier with scaler",
        dataset_card_id="lung_survey",
        clinical_use_category="clinician_review",
        intended_use="AI-assisted respiratory issue screening signal for clinician review.",
        target_users=("patient", "doctor"),
        feature_count=15,
        output="risk label, raw class, confidence, risk level, disclaimer",
        limitations=("Not a substitute for pulmonary exam, imaging, or emergency assessment.",),
    ),
)


def registry_response() -> dict[str, Any]:
    return {
        "source": "backend.model_cards",
        "model_cards": [card.to_dict() for card in MODEL_CARDS],
        "dataset_cards": [card.to_dict() for card in DATASET_CARDS],
        "privacy_note": "Cards describe artifacts and intended use only; no training rows or patient identifiers are returned.",
    }
