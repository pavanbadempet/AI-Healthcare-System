"""Conformal prediction utilities for calibrated uncertainty quantification.

This module provides a minimal, dependency-light toolkit for split-conformal
inference on binary classifiers.  It covers three stages of the workflow:

1. **Calibration** – compute nonconformity-score thresholds from a held-out
   calibration set (``compute_conformal_threshold``,
   ``class_conditional_thresholds``).
2. **Prediction** – generate prediction sets at a target significance level
   given a new observation's predicted probability
   (``conformal_prediction_set``).
3. **Triage** – translate the prediction set into human-readable clinical
   action guidance (``get_triage_recommendation``).

The implementation follows the *split-conformal* approach of Vovk et al.
(2005) with the finite-sample correction ``(1 - α)(1 + 1/n)`` for the
quantile level.
"""

from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Union


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


def compute_conformal_threshold(
    y_true: np.ndarray,
    proba_positive: np.ndarray,
    alpha: float = 0.05,
) -> float:
    """Compute the marginal conformal prediction threshold from a calibration set.

    Uses the nonconformity score ``s = 1 − p(true class)``: for positive
    labels the score is ``1 − p₁`` and for negative labels it is ``p₁``
    (equivalently ``1 − p₀``).

    Parameters
    ----------
    y_true : array-like of {0, 1}
        True binary labels from the calibration set.
    proba_positive : array-like of float
        Predicted probability of the *positive* class (class 1).
    alpha : float, default 0.05
        Target miscoverage rate.  The resulting threshold guarantees
        ``1 − α`` marginal coverage on exchangeable test data.

    Returns
    -------
    float
        The ``(1 − α)``-quantile of the nonconformity scores (with
        finite-sample correction).
    """
    y_true = np.asarray(y_true)
    proba_positive = np.asarray(proba_positive)

    scores = np.where(y_true == 1, 1.0 - proba_positive, proba_positive)

    n = len(scores)
    q_level = min(1.0, (1.0 - alpha) * (1 + 1 / n))
    threshold = float(np.quantile(scores, q_level))
    return threshold


def class_conditional_thresholds(
    y_true: np.ndarray,
    proba_positive: np.ndarray,
    alpha: float = 0.05,
) -> Dict[int, float]:
    """Compute per-class conformal thresholds for class-conditional coverage.

    Instead of a single threshold, this computes separate thresholds for
    the positive and negative classes so that the coverage guarantee holds
    *within* each class.

    Parameters
    ----------
    y_true : array-like of {0, 1}
        True binary labels from the calibration set.
    proba_positive : array-like of float
        Predicted probability of the positive class.
    alpha : float, default 0.05
        Target miscoverage rate per class.

    Returns
    -------
    dict[int, float]
        Mapping ``{0: threshold_neg, 1: threshold_pos}``.  Falls back to
        ``0.5`` for any class with zero calibration samples.
    """
    y_true = np.asarray(y_true)
    proba_positive = np.asarray(proba_positive)

    thresholds: Dict[int, float] = {}
    for cls in [0, 1]:
        mask = y_true == cls
        if mask.sum() == 0:
            thresholds[cls] = 0.5
            continue
        if cls == 1:
            scores = 1.0 - proba_positive[mask]
        else:
            scores = proba_positive[mask]
        n = len(scores)
        q_level = min(1.0, (1.0 - alpha) * (1 + 1 / n))
        thresholds[cls] = float(np.quantile(scores, q_level))
    return thresholds


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def conformal_prediction_set(
    proba_positive: float,
    conformal_q: Union[float, Dict[int, float]],
) -> Dict[str, Any]:
    """Generate a conformal prediction set at 95 % confidence.

    Supports both marginal (single ``float`` threshold) and
    class-conditional (``dict`` of per-class thresholds) modes.

    Parameters
    ----------
    proba_positive : float
        Predicted probability of the positive class for a single
        observation.
    conformal_q : float or dict[int, float]
        Conformal threshold(s) computed by
        :func:`compute_conformal_threshold` or
        :func:`class_conditional_thresholds`.

    Returns
    -------
    dict
        ``conformal_prediction_set`` – list of class labels included in
        the prediction set, ``significance_level`` – the α used (0.05),
        ``uncertainty_status`` – one of *Low Uncertainty*,
        *High Uncertainty (Ambiguous Case)*, or
        *High Uncertainty (Out-of-Distribution Case)*.
    """
    p0 = 1.0 - proba_positive
    p1 = proba_positive

    prediction_set: List[int] = []
    if isinstance(conformal_q, dict):
        q0 = conformal_q.get(0, conformal_q.get("0", 0.0))
        q1 = conformal_q.get(1, conformal_q.get("1", 0.0))
        if p0 >= 1.0 - q0:
            prediction_set.append(0)
        if p1 >= 1.0 - q1:
            prediction_set.append(1)
    else:
        threshold = 1.0 - (conformal_q or 0.0)
        if p0 >= threshold:
            prediction_set.append(0)
        if p1 >= threshold:
            prediction_set.append(1)

    if len(prediction_set) == 1:
        uncertainty_status = "Low Uncertainty"
    elif len(prediction_set) > 1:
        uncertainty_status = "High Uncertainty (Ambiguous Case)"
    else:
        uncertainty_status = "High Uncertainty (Out-of-Distribution Case)"

    return {
        "conformal_prediction_set": prediction_set,
        "significance_level": 0.05,
        "uncertainty_status": uncertainty_status,
    }


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------


def get_triage_recommendation(
    prediction_val: int, conformal_set: List[int]
) -> str:
    """Translate conformal prediction sets into actionable clinical triage guidance.

    Parameters
    ----------
    prediction_val : int
        The raw binary prediction (0 or 1).
    conformal_set : list[int]
        The conformal prediction set as returned by
        :func:`conformal_prediction_set`.

    Returns
    -------
    str
        A human-readable triage recommendation string.
    """
    if conformal_set == [1]:
        return (
            "Urgent Action: Patient exhibits strong canonical markers. "
            "Initiate standard treatment protocols."
        )
    elif conformal_set == [0]:
        return (
            "Routine Monitoring: Patient is within normal parameters. "
            "Re-evaluate at next routine visit."
        )
    elif len(conformal_set) > 1:
        return (
            "Clinical Triage: Borderline case. "
            "Schedule a follow-up test or refer to a specialist."
        )
    else:
        return (
            "Secondary Review: Patient presents with unusual clinical "
            "features not well-represented in training. "
            "Perform manual chart review."
        )
