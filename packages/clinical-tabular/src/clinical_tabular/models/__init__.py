"""Model classes for clinical tabular prediction.

All three models require PyTorch.  When ``torch`` is not installed the names
are still importable but resolve to ``None`` so that downstream code can
gate on availability without crashing at import time.
"""

try:
    from clinical_tabular.models.ft_transformer import FTTransformerClassifier
except ImportError:
    FTTransformerClassifier = None  # type: ignore[assignment,misc]

try:
    from clinical_tabular.models.temporal_lstm import ClinicalTemporalLSTM
except ImportError:
    ClinicalTemporalLSTM = None  # type: ignore[assignment,misc]

try:
    from clinical_tabular.models.tabular_mlp import PyTorchTabularMLP
except ImportError:
    PyTorchTabularMLP = None  # type: ignore[assignment,misc]

__all__ = [
    "FTTransformerClassifier",
    "ClinicalTemporalLSTM",
    "PyTorchTabularMLP",
]
