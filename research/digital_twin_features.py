"""
Digital Twin Trajectory Feature Generator for Research Experiments.

Takes a clinical cohort dataframe and generates 17 novel features from the
ClinicalDigitalTwinEngine's 10-year multi-organ ODE simulation:

  4 organ baseline scores (CV, Renal, Metabolic, Hepatic)
  4 year-10 untreated projections
  4 year-10 treated projections
  4 trajectory slopes (annual rate of decline without intervention)
  1 overall QALY gain

These features encode mechanistic physiological knowledge that standard
ML models cannot learn from cross-sectional EHR data alone.

Usage:
    python research/digital_twin_features.py --input research/data/mimic_cohort.parquet
    python research/digital_twin_features.py --input research/data/mimic_cohort.parquet --output research/data/mimic_cohort_with_dt.parquet
"""

import argparse
import logging
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.clinical_digital_twin import ClinicalDigitalTwinEngine
from backend.schemas.peak_healthcare import DigitalTwinSimulationRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DigitalTwinFeatures")


# Default clinical values for missing data
DEFAULTS = {
    "bmi": 25.0,
    "systolic_bp": 120.0,
    "fasting_glucose": 95.0,
    "glucose": 95.0,
    "egfr": 90.0,
    "ldl_cholesterol": 100.0,
    "ldl": 100.0,
    "hba1c": 5.6,
}

ORGAN_SYSTEMS = ["cardiovascular", "renal", "metabolic", "hepatic"]


def _map_smoking(row: pd.Series) -> str:
    """Map various smoking representations to digital twin input."""
    val = str(row.get("smoking_status", "never")).lower().strip()
    if val in ("current", "active", "1", "yes"):
        return "current"
    if val in ("former", "ex", "past"):
        return "former"
    return "never"


def _map_diagnoses(row: pd.Series) -> list:
    """Extract active diagnoses from binary flags."""
    diag = []
    flag_map = {
        "has_chf": "Congestive Heart Failure",
        "has_diabetes": "Type 2 Diabetes",
        "has_copd": "COPD",
        "has_ckd": "Chronic Kidney Disease",
        "has_afib": "Atrial Fibrillation",
        "has_hypertension": "Hypertension",
        "has_cad": "Coronary Artery Disease",
    }
    for col, name in flag_map.items():
        if row.get(col, 0) == 1:
            diag.append(name)
    return diag


def _map_interventions(row: pd.Series) -> list:
    """Determine standard-of-care interventions based on diagnoses."""
    interventions = []
    if row.get("has_diabetes", 0) == 1:
        interventions.append("SGLT2i (Empagliflozin 10mg)")
        interventions.append("GLP-1 RA (Semaglutide 0.5mg)")
    if row.get("has_cad", 0) == 1 or row.get("has_hypertension", 0) == 1:
        interventions.append("Atorvastatin 40mg")
    if row.get("has_ckd", 0) == 1:
        interventions.append("SGLT2i (Dapagliflozin 10mg)")
    if not interventions:
        interventions.append("Lifestyle Mediterranean Diet")
    return interventions


def generate_dt_features_for_row(row: pd.Series) -> dict:
    """Run the digital twin engine for a single patient row and extract features."""
    # Build request from available columns
    req = DigitalTwinSimulationRequest(
        patient_id=str(row.get("patient_id", row.get("subject_id", "UNK"))),
        age=int(row.get("age", 60)),
        gender=str(row.get("gender", "Male")),
        bmi=float(row.get("bmi", DEFAULTS["bmi"])),
        systolic_bp=float(row.get("systolic_bp", DEFAULTS["systolic_bp"])),
        fasting_glucose=float(row.get("fasting_glucose", row.get("glucose", DEFAULTS["fasting_glucose"]))),
        egfr=float(row.get("egfr", DEFAULTS["egfr"])),
        ldl_cholesterol=float(row.get("ldl_cholesterol", row.get("ldl", DEFAULTS["ldl_cholesterol"]))),
        hba1c=float(row.get("hba1c", DEFAULTS["hba1c"])),
        smoking_status=_map_smoking(row),
        active_diagnoses=_map_diagnoses(row),
        proposed_interventions=_map_interventions(row),
    )

    resp = ClinicalDigitalTwinEngine.simulate_10_year_trajectory(req)

    features = {}
    for organ in ORGAN_SYSTEMS:
        traj = getattr(resp, organ)

        # Baseline score
        features[f"dt_{organ}_baseline"] = traj.baseline_health_score

        # Year-10 projections
        features[f"dt_{organ}_yr10_untreated"] = traj.projected_score_without_intervention[-1]
        features[f"dt_{organ}_yr10_treated"] = traj.projected_score_with_intervention[-1]

        # Trajectory slope (annual decline rate without intervention)
        untreated = traj.projected_score_without_intervention
        if len(untreated) >= 2:
            slope = (untreated[-1] - traj.baseline_health_score) / len(untreated)
        else:
            slope = 0.0
        features[f"dt_{organ}_slope"] = round(slope, 4)

    # Overall QALY gain
    features["dt_qaly_gain"] = resp.overall_longevity_gain_years

    return features


def generate_digital_twin_features(df: pd.DataFrame) -> pd.DataFrame:
    """Generate digital twin features for an entire cohort dataframe."""
    logger.info(f"Generating digital twin features for {len(df)} patients...")

    dt_records = []
    for idx, row in df.iterrows():
        try:
            feats = generate_dt_features_for_row(row)
        except Exception as e:
            logger.warning(f"Patient {idx}: DT simulation failed ({e}), using defaults")
            feats = {f"dt_{o}_{s}": 0.0 for o in ORGAN_SYSTEMS
                     for s in ["baseline", "yr10_untreated", "yr10_treated", "slope"]}
            feats["dt_qaly_gain"] = 0.0
        dt_records.append(feats)

        if (idx + 1) % 500 == 0:
            logger.info(f"  Processed {idx + 1}/{len(df)} patients")

    dt_df = pd.DataFrame(dt_records)
    result = pd.concat([df.reset_index(drop=True), dt_df], axis=1)

    # Log feature statistics
    dt_cols = [c for c in result.columns if c.startswith("dt_")]
    logger.info(f"Generated {len(dt_cols)} digital twin features:")
    for col in dt_cols:
        logger.info(f"  {col}: mean={result[col].mean():.2f}, std={result[col].std():.2f}")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Digital Twin Trajectory Features")
    parser.add_argument("--input", type=str, required=True, help="Input cohort parquet path")
    parser.add_argument("--output", type=str, default=None, help="Output parquet path")
    args = parser.parse_args()

    df = pd.read_parquet(args.input)
    logger.info(f"Loaded cohort: {len(df)} rows, {len(df.columns)} columns")

    result = generate_digital_twin_features(df)

    output_path = args.output or args.input.replace(".parquet", "_with_dt.parquet")
    result.to_parquet(output_path, index=False)
    logger.info(f"Saved to {output_path} ({len(result)} rows, {len(result.columns)} columns)")


if __name__ == "__main__":
    main()
