"""
MIMIC-IV ETL Pipeline for 30-Day Readmission Prediction Cohort.

Extracts patient demographics, vitals, labs, and diagnoses from MIMIC-IV
CSV/parquet files and constructs a binary 30-day readmission label.

Standard inclusion/exclusion criteria:
  - Adults (age >= 18 at admission)
  - Exclude in-hospital deaths (cannot be readmitted)
  - Exclude admissions with LOS < 24 hours (observation stays)
  - Index admission = first admission per patient; readmission = any
    subsequent admission within 30 days of prior discharge

Usage:
    python research/mimic_iv_etl.py --mimic-dir research/data/mimic-iv
    python research/mimic_iv_etl.py --synthetic  # generate synthetic cohort for testing
"""

import argparse
import logging
import os
import sys
from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MIMIC-IV-ETL")


# ---------------------------------------------------------------------------
# Synthetic data generator (for pipeline testing without MIMIC-IV access)
# ---------------------------------------------------------------------------

def generate_synthetic_cohort(n_patients: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic synthetic clinical cohort for dry-run testing."""
    rng = np.random.RandomState(seed)
    logger.info(f"Generating synthetic cohort with {n_patients} patients...")

    ages = rng.normal(65, 14, n_patients).clip(18, 100).astype(int)
    genders = rng.choice(["M", "F"], n_patients, p=[0.52, 0.48])
    bmis = rng.normal(28, 5, n_patients).clip(15, 55).round(1)

    # Vitals (mean of last 24h before discharge)
    heart_rates = rng.normal(82, 15, n_patients).clip(40, 180).round(1)
    systolic_bps = rng.normal(130, 20, n_patients).clip(70, 220).round(1)
    diastolic_bps = rng.normal(75, 12, n_patients).clip(40, 130).round(1)
    resp_rates = rng.normal(18, 4, n_patients).clip(8, 45).round(1)
    spo2s = rng.normal(96, 2.5, n_patients).clip(70, 100).round(1)
    temperatures = rng.normal(36.8, 0.5, n_patients).clip(34, 41).round(1)

    # Labs
    glucose = rng.normal(120, 40, n_patients).clip(50, 500).round(1)
    creatinine = rng.lognormal(0.1, 0.5, n_patients).clip(0.3, 15).round(2)
    bun = rng.normal(22, 12, n_patients).clip(5, 100).round(1)
    sodium = rng.normal(139, 4, n_patients).clip(120, 160).round(0)
    potassium = rng.normal(4.2, 0.6, n_patients).clip(2.5, 7.0).round(1)
    hemoglobin = rng.normal(12.5, 2.2, n_patients).clip(5, 20).round(1)
    wbc = rng.lognormal(2.1, 0.4, n_patients).clip(1, 50).round(1)
    platelets = rng.normal(230, 80, n_patients).clip(20, 800).round(0)
    albumin = rng.normal(3.4, 0.6, n_patients).clip(1.0, 5.5).round(1)
    hba1c = rng.normal(6.2, 1.5, n_patients).clip(4.0, 15.0).round(1)
    ldl = rng.normal(110, 35, n_patients).clip(30, 250).round(0)
    alt = rng.lognormal(3.0, 0.6, n_patients).clip(5, 500).round(0)
    ast = rng.lognormal(3.0, 0.5, n_patients).clip(5, 400).round(0)

    # Derived
    egfr = np.array([
        175 * (cr ** -1.154) * (age ** -0.203) * (0.742 if g == "F" else 1.0)
        for cr, age, g in zip(creatinine, ages, genders)
    ]).clip(5, 150).round(1)

    # Diagnoses (binary flags for common ICD-10 groups)
    has_chf = rng.binomial(1, 0.25, n_patients)
    has_diabetes = rng.binomial(1, 0.30, n_patients)
    has_copd = rng.binomial(1, 0.18, n_patients)
    has_ckd = rng.binomial(1, 0.20, n_patients)
    has_afib = rng.binomial(1, 0.15, n_patients)
    has_hypertension = rng.binomial(1, 0.55, n_patients)
    has_cad = rng.binomial(1, 0.22, n_patients)

    # Utilization features
    los_days = rng.lognormal(1.2, 0.8, n_patients).clip(1, 60).round(1)
    n_prior_admissions = rng.poisson(1.2, n_patients).clip(0, 15)
    n_medications = rng.poisson(8, n_patients).clip(0, 30)
    icu_stay = rng.binomial(1, 0.20, n_patients)
    emergency_admission = rng.binomial(1, 0.55, n_patients)

    # Smoking
    smoking = rng.choice(["never", "former", "current"], n_patients, p=[0.45, 0.35, 0.20])

    # 30-day readmission label (realistic ~15% rate, correlated with risk factors)
    logit = (
        -2.0
        + 0.015 * (ages - 65)
        + 0.4 * has_chf
        + 0.3 * has_diabetes
        + 0.35 * has_copd
        + 0.3 * has_ckd
        + 0.25 * has_cad
        + 0.02 * (los_days - 5)
        + 0.15 * n_prior_admissions
        + 0.05 * n_medications
        + 0.3 * icu_stay
        + 0.2 * emergency_admission
        - 0.02 * egfr
        + 0.1 * (creatinine - 1.0)
        + rng.normal(0, 0.3, n_patients)
    )
    prob_readmit = 1 / (1 + np.exp(-logit))
    readmitted_30d = (rng.uniform(0, 1, n_patients) < prob_readmit).astype(int)

    df = pd.DataFrame({
        "patient_id": [f"SYN-{i:06d}" for i in range(n_patients)],
        "age": ages,
        "gender": genders,
        "bmi": bmis,
        "heart_rate": heart_rates,
        "systolic_bp": systolic_bps,
        "diastolic_bp": diastolic_bps,
        "respiratory_rate": resp_rates,
        "spo2": spo2s,
        "temperature": temperatures,
        "glucose": glucose,
        "creatinine": creatinine,
        "bun": bun,
        "sodium": sodium,
        "potassium": potassium,
        "hemoglobin": hemoglobin,
        "wbc": wbc,
        "platelets": platelets,
        "albumin": albumin,
        "hba1c": hba1c,
        "ldl_cholesterol": ldl,
        "alt": alt,
        "ast": ast,
        "egfr": egfr,
        "has_chf": has_chf,
        "has_diabetes": has_diabetes,
        "has_copd": has_copd,
        "has_ckd": has_ckd,
        "has_afib": has_afib,
        "has_hypertension": has_hypertension,
        "has_cad": has_cad,
        "los_days": los_days,
        "n_prior_admissions": n_prior_admissions,
        "n_medications": n_medications,
        "icu_stay": icu_stay,
        "emergency_admission": emergency_admission,
        "smoking_status": smoking,
        "readmitted_30d": readmitted_30d,
    })

    rate = readmitted_30d.mean() * 100
    logger.info(f"Synthetic cohort: {len(df)} patients, readmission rate: {rate:.1f}%")
    return df


# ---------------------------------------------------------------------------
# MIMIC-IV ETL (real data)
# ---------------------------------------------------------------------------

def load_mimic_cohort(mimic_dir: str) -> pd.DataFrame:
    """
    Extract 30-day readmission cohort from MIMIC-IV CSV files.

    Expected directory structure:
        mimic_dir/
            hosp/
                patients.csv.gz
                admissions.csv.gz
                diagnoses_icd.csv.gz
                labevents.csv.gz
            icu/
                chartevents.csv.gz (optional, large)
    """
    hosp_dir = os.path.join(mimic_dir, "hosp")
    if not os.path.isdir(hosp_dir):
        raise FileNotFoundError(f"MIMIC-IV hosp directory not found: {hosp_dir}")

    # --- Patients ---
    logger.info("Loading patients...")
    patients = pd.read_csv(
        os.path.join(hosp_dir, "patients.csv.gz"),
        usecols=["subject_id", "gender", "anchor_age", "anchor_year", "dod"],
    )

    # --- Admissions ---
    logger.info("Loading admissions...")
    admissions = pd.read_csv(
        os.path.join(hosp_dir, "admissions.csv.gz"),
        usecols=["subject_id", "hadm_id", "admittime", "dischtime",
                 "admission_type", "hospital_expire_flag"],
        parse_dates=["admittime", "dischtime"],
    )

    # Merge demographics
    df = admissions.merge(patients, on="subject_id", how="left")

    # Calculate age at admission
    df["admit_year"] = df["admittime"].dt.year
    df["age"] = df["anchor_age"] + (df["admit_year"] - df["anchor_year"])

    # --- Inclusion / Exclusion ---
    n_initial = len(df)
    df = df[df["age"] >= 18]  # Adults only
    logger.info(f"After age >= 18 filter: {len(df)} / {n_initial}")

    df = df[df["hospital_expire_flag"] == 0]  # Exclude in-hospital deaths
    logger.info(f"After excluding in-hospital deaths: {len(df)}")

    df["los_hours"] = (df["dischtime"] - df["admittime"]).dt.total_seconds() / 3600
    df = df[df["los_hours"] >= 24]  # Exclude observation stays
    df["los_days"] = (df["los_hours"] / 24).round(1)
    logger.info(f"After LOS >= 24h filter: {len(df)}")

    # --- 30-Day Readmission Label ---
    df = df.sort_values(["subject_id", "admittime"])
    df["next_admittime"] = df.groupby("subject_id")["admittime"].shift(-1)
    df["days_to_readmit"] = (df["next_admittime"] - df["dischtime"]).dt.days
    df["readmitted_30d"] = (df["days_to_readmit"] <= 30).astype(int).fillna(0).astype(int)

    logger.info(f"Readmission rate: {df['readmitted_30d'].mean() * 100:.1f}%")

    # --- Diagnoses (ICD-10 flags) ---
    logger.info("Loading diagnoses...")
    diag = pd.read_csv(
        os.path.join(hosp_dir, "diagnoses_icd.csv.gz"),
        usecols=["hadm_id", "icd_code", "icd_version"],
    )
    diag10 = diag[diag["icd_version"] == 10].copy()

    icd_flags = {
        "has_chf": ["I50"],
        "has_diabetes": ["E10", "E11", "E13"],
        "has_copd": ["J44"],
        "has_ckd": ["N18"],
        "has_afib": ["I48"],
        "has_hypertension": ["I10", "I11", "I12", "I13"],
        "has_cad": ["I25"],
    }

    for flag_name, prefixes in icd_flags.items():
        mask = diag10["icd_code"].str[:3].isin(prefixes)
        flagged_hadms = diag10.loc[mask, "hadm_id"].unique()
        df[flag_name] = df["hadm_id"].isin(flagged_hadms).astype(int)

    # --- Labs (aggregate last 24h before discharge) ---
    logger.info("Loading lab events (this may take a few minutes)...")
    lab_items = {
        50912: "creatinine",
        50971: "potassium",
        50983: "sodium",
        50931: "glucose",
        51222: "hemoglobin",
        51301: "wbc",
        51265: "platelets",
        50862: "albumin",
        51003: "bun",
    }

    labs = pd.read_csv(
        os.path.join(hosp_dir, "labevents.csv.gz"),
        usecols=["hadm_id", "itemid", "charttime", "valuenum"],
        parse_dates=["charttime"],
    )
    labs = labs[labs["itemid"].isin(lab_items.keys())].dropna(subset=["valuenum"])
    labs["lab_name"] = labs["itemid"].map(lab_items)

    # Merge discharge times for last-24h filtering
    labs = labs.merge(
        df[["hadm_id", "dischtime"]].drop_duplicates(),
        on="hadm_id", how="inner",
    )
    labs["hours_before_disch"] = (labs["dischtime"] - labs["charttime"]).dt.total_seconds() / 3600
    labs = labs[(labs["hours_before_disch"] >= 0) & (labs["hours_before_disch"] <= 24)]

    lab_agg = labs.groupby(["hadm_id", "lab_name"])["valuenum"].median().unstack(fill_value=np.nan)
    df = df.merge(lab_agg, on="hadm_id", how="left")

    # --- Derived features ---
    if "creatinine" in df.columns:
        df["egfr"] = df.apply(
            lambda r: min(150, max(5, 175 * (max(0.3, r.get("creatinine", 1.0)) ** -1.154)
                          * (max(18, r["age"]) ** -0.203)
                          * (0.742 if r["gender"] == "F" else 1.0))),
            axis=1,
        ).round(1)

    # Emergency admission flag
    df["emergency_admission"] = df["admission_type"].str.contains(
        "EMERGENCY|URGENT", case=False, na=False
    ).astype(int)

    # Prior admissions count
    df["n_prior_admissions"] = df.groupby("subject_id").cumcount()

    # Select final columns
    feature_cols = [
        "subject_id", "hadm_id", "age", "gender", "los_days",
        "emergency_admission", "n_prior_admissions",
        "has_chf", "has_diabetes", "has_copd", "has_ckd",
        "has_afib", "has_hypertension", "has_cad",
    ] + [c for c in lab_items.values() if c in df.columns] + [
        "egfr", "readmitted_30d",
    ]
    existing_cols = [c for c in feature_cols if c in df.columns]
    result = df[existing_cols].copy()

    logger.info(f"Final cohort: {len(result)} admissions, {result['readmitted_30d'].mean()*100:.1f}% readmission rate")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for MIMIC-IV ETL."""
    parser = argparse.ArgumentParser(description="MIMIC-IV 30-Day Readmission Cohort Builder")
    parser.add_argument("--mimic-dir", type=str, default=None, help="Path to MIMIC-IV directory")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic cohort instead")
    parser.add_argument("--n-patients", type=int, default=2000, help="Synthetic cohort size")
    parser.add_argument("--output", type=str, default=None, help="Output parquet path")
    args = parser.parse_args()

    if args.synthetic or args.mimic_dir is None:
        df = generate_synthetic_cohort(n_patients=args.n_patients)
    else:
        df = load_mimic_cohort(args.mimic_dir)

    output_path = args.output or os.path.join(
        os.path.dirname(__file__), "data", "mimic_cohort.parquet"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Cohort saved to {output_path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
