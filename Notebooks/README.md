# Experimentation Notebooks
===========================

This directory contains the **Proprietary Research Notebooks** used to design the Advanced Voting Ensemble architectures.

**Note:** These files are for research and explainability. Production training is handled by the automated pipeline in `../pipelines/train_ensemble.py`.

## Contents

-   **Diabetes Notebook.ipynb**: Advanced Voting Ensemble (XGB+RF+GB) for Diabetes prediction.
-   **Heart Disease Notebook.ipynb**: Cardiac Risk Ensemble (LGBM+XGB) for Heart Disease.
-   **Liver Disease Notebook.ipynb**: Hepatic Risk Ensemble with Log-Normalization logic.
-   **Kidney Disease Notebook.ipynb**: Renal Health XGBoost for Chronic Kidney Disease.
-   **Respiratory Health Notebook.ipynb**: Pulmonary Risk Model for Lung Cancer detection.

## Usage

To view or run these notebooks:

1.  Install Jupyter: `pip install jupyterlab`
2.  Launch: `jupyter lab`
3.  Open the desired notebook.

*Warning: Running these notebooks may overwrite the production `.pkl` models in the `../models/` directory.*
