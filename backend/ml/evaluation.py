"""
Shared evaluation module for AI Healthcare clinical prediction models.

Computes AUC-ROC, precision/recall/F1, confusion matrix, and feature
importance for any sklearn-compatible classifier.  Writes results to a
JSON artifact that the ``/admin/model-cards`` endpoint and
``docs/MODEL_CARDS.md`` can reference.

Usage from a training script::

    from backend.ml.evaluation import evaluate_and_save
    evaluate_and_save(model, X_test, y_test, feature_names, "diabetes")

The JSON artifact is written to ``backend/ml/eval_<model_name>.json``.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_EVAL_DIR = os.path.dirname(os.path.abspath(__file__))


def evaluate_model(
    model,
    X_test: pd.DataFrame | np.ndarray,
    y_test: pd.Series | np.ndarray,
    feature_names: list[str],
    model_name: str,
) -> dict[str, Any]:
    """Run a comprehensive evaluation suite on a trained classifier.

    Parameters
    ----------
    model:
        A fitted sklearn-compatible classifier with ``predict`` and
        ``predict_proba`` methods.
    X_test:
        Test features.
    y_test:
        True labels.
    feature_names:
        Column names matching ``X_test`` columns.
    model_name:
        Short identifier (e.g. ``"diabetes"``, ``"heart"``).

    Returns
    -------
    dict
        Evaluation results containing accuracy, AUC-ROC, classification
        report, confusion matrix, and feature importances.
    """
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
        roc_auc_score,
    )

    y_pred = model.predict(X_test)

    # --- Core metrics ---
    acc = float(accuracy_score(y_test, y_pred))

    # AUC-ROC (handle binary and multiclass)
    auc_roc = None
    try:
        y_proba = model.predict_proba(X_test)
        n_classes = y_proba.shape[1]
        if n_classes == 2:
            auc_roc = float(roc_auc_score(y_test, y_proba[:, 1]))
        else:
            auc_roc = float(
                roc_auc_score(y_test, y_proba, multi_class="ovr", average="weighted")
            )
    except Exception as exc:
        logger.warning("AUC-ROC computation failed for %s: %s", model_name, exc)

    # --- Classification report (precision, recall, F1 per class) ---
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # --- Confusion matrix ---
    cm = confusion_matrix(y_test, y_pred).tolist()

    # --- Sensitivity / Specificity (binary only) ---
    sensitivity = None
    specificity = None
    if len(cm) == 2:
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        sensitivity = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    # --- Feature importance ---
    importances: dict[str, float] = {}
    if hasattr(model, "feature_importances_"):
        raw_imp = model.feature_importances_
        for i, name in enumerate(feature_names):
            if i < len(raw_imp):
                importances[name] = round(float(raw_imp[i]), 4)

    # --- Dataset statistics ---
    n_test = int(len(y_test))
    y_arr = np.asarray(y_test)
    class_distribution = {}
    for label in sorted(np.unique(y_arr)):
        class_distribution[str(int(label))] = int((y_arr == label).sum())

    results: dict[str, Any] = {
        "model_name": model_name,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "test_set_size": n_test,
        "class_distribution": class_distribution,
        "accuracy": round(acc, 4),
        "auc_roc": round(auc_roc, 4) if auc_roc is not None else None,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "classification_report": {
            k: v
            for k, v in report_dict.items()
            if k not in ("accuracy",)  # avoid duplication
        },
        "confusion_matrix": cm,
        "feature_importances": importances,
        "n_features": len(feature_names),
        "feature_names": feature_names,
    }

    return results


def evaluate_and_save(
    model,
    X_test: pd.DataFrame | np.ndarray,
    y_test: pd.Series | np.ndarray,
    feature_names: list[str],
    model_name: str,
) -> dict[str, Any]:
    """Evaluate the model and persist results to a JSON artifact.

    Calls :func:`evaluate_model` and writes the result dict to
    ``backend/ml/eval_<model_name>.json``.

    Returns the evaluation dict.
    """
    results = evaluate_model(model, X_test, y_test, feature_names, model_name)

    # Print human-readable summary
    _print_summary(results)

    # Write JSON artifact
    out_path = os.path.join(_EVAL_DIR, f"eval_{model_name}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"Evaluation artifact saved to {out_path}")

    return results


def _print_summary(results: dict[str, Any]) -> None:
    """Print a concise human-readable evaluation summary."""
    name = results["model_name"]
    print(f"\n{'='*60}")
    print(f"  Evaluation Results: {name.upper()}")
    print(f"{'='*60}")
    print(f"  Test Set Size   : {results['test_set_size']}")
    print(f"  Class Dist.     : {results['class_distribution']}")
    print(f"  Accuracy        : {results['accuracy']:.4f}")
    if results["auc_roc"] is not None:
        print(f"  AUC-ROC         : {results['auc_roc']:.4f}")
    if results["sensitivity"] is not None:
        print(f"  Sensitivity     : {results['sensitivity']:.4f}")
        print(f"  Specificity     : {results['specificity']:.4f}")
    print("\n  Confusion Matrix:")
    for row in results["confusion_matrix"]:
        print(f"    {row}")
    if results["feature_importances"]:
        print("\n  Top-5 Features:")
        sorted_feats = sorted(
            results["feature_importances"].items(), key=lambda x: x[1], reverse=True
        )
        for feat, imp in sorted_feats[:5]:
            print(f"    {feat:30s} {imp:.4f}")
    print(f"{'='*60}\n")
