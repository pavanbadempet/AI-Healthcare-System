# Research Experiments — AI Healthcare System

## Overview

This directory contains reproducible experiment code for two research papers:

1. **Paper A (SoftwareX)**: System architecture benchmarks → `../scripts/benchmark_system.py`
2. **Paper B (ML4H/CHIL)**: Digital Twin + TabPFN readmission prediction → this directory

## Prerequisites

### PhysioNet MIMIC-IV Access
1. Create account at https://physionet.org
2. Complete CITI "Data or Specimens Only Research" training
3. Sign the MIMIC-IV Data Use Agreement
4. Download MIMIC-IV v2.2+ and place CSVs in `pipelines/research/data/mimic-iv/`

### Python Environment
```bash
pip install pandas numpy scikit-learn xgboost matplotlib tabpfn scipy
```

## Reproducing Paper B Results

```bash
# Step 1: Build cohort from MIMIC-IV (requires data access)
python pipelines/research/mimic_iv_etl.py --mimic-dir pipelines/research/data/mimic-iv --output pipelines/research/data/mimic_cohort.parquet

# Step 2: Generate digital twin trajectory features
python pipelines/research/digital_twin_features.py --input pipelines/research/data/mimic_cohort.parquet --output pipelines/research/data/mimic_cohort_with_dt.parquet

# Step 3: Run full experiment (5-fold CV + 1000 bootstrap iterations)
python pipelines/research/experiment_runner.py --data pipelines/research/data/mimic_cohort_with_dt.parquet --folds 5 --bootstrap 1000

# Step 4: Generate LaTeX tables and figures
python pipelines/research/generate_paper_figures.py --results pipelines/research/results/experiment_results.json --output pipelines/research/figures/

# Dry-run with synthetic data (no MIMIC-IV access needed)
python pipelines/research/experiment_runner.py --synthetic --folds 2 --bootstrap 100
```

## Ethics Statement
All experiments use the publicly available MIMIC-IV dataset under PhysioNet
Credentialed Health Data License 1.5.0. No identifiable patient data is stored
in this repository. IRB exemption applies per PhysioNet's institutional review.
