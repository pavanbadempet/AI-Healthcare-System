"""clinical-tabular — tabular & temporal deep learning models for clinical decision support.

Provides production-ready classifiers (FT-Transformer, Temporal LSTM, Tabular MLP)
with sklearn-compatible APIs, clinical risk indices, conformal calibration utilities,
and model evaluation helpers.
"""

__version__ = "0.1.0"

from clinical_tabular.models import (
    FTTransformerClassifier,
    ClinicalTemporalLSTM,
    PyTorchTabularMLP,
)

__all__ = [
    "__version__",
    "FTTransformerClassifier",
    "ClinicalTemporalLSTM",
    "PyTorchTabularMLP",
]
