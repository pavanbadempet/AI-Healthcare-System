"""Model evaluation utilities for sklearn-compatible clinical classifiers.

Computes AUC-ROC, precision / recall / F1, confusion matrix, sensitivity,
specificity, and feature importance for any classifier that exposes
``predict`` and ``predict_proba``.

Functions
---------
evaluate_model
    Run a comprehensive evaluation suite and return a results dict.
print_summary
    Print a concise human-readable evaluation summary to stdout.
save_evaluation
    Persist an evaluation results dict to a JSON file.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)


def evaluate_model(
    model: Any,
    X_test: Any,
    y_test: Any,
    feature_names: List[str],
    model_name: str,
) -> Dict[str, Any]:
    """Run a comprehensive evaluation suite on a trained classifier.

    Parameters
    ----------
    model :
        A fitted sklearn-compatible classifier with ``predict`` and
        ``predict_proba`` methods.
    X_test :
        Test features (``pandas.DataFrame`` or ``numpy.ndarray``).
    y_test :
        True labels (``pandas.Series`` or ``numpy.ndarray``).
    feature_names :
        Column names matching ``X_test`` columns.
    model_name :
        Short identifier (e.g. ``"diabetes"``, ``"heart"``).

    Returns
    -------
    dict
        Evaluation results containing accuracy, AUC-ROC, classification
        report, confusion matrix, and feature importances.
    """
    import pandas as pd  # noqa: F811 – deferred import
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
    auc_roc: Optional[float] = None
    try:
        y_proba = model.predict_proba(X_test)
        n_classes = y_proba.shape[1]
        if n_classes == 2:
            auc_roc = float(roc_auc_score(y_test, y_proba[:, 1]))
        else:
            auc_roc = float(
                roc_auc_score(
                    y_test, y_proba, multi_class="ovr", average="weighted"
                )
            )
    except Exception as exc:
        logger.warning("AUC-ROC computation failed for %s: %s", model_name, exc)

    # --- Classification report (precision, recall, F1 per class) ---
    report_dict = classification_report(
        y_test, y_pred, output_dict=True, zero_division=0
    )

    # --- Confusion matrix ---
    cm = confusion_matrix(y_test, y_pred).tolist()

    # --- Sensitivity / Specificity (binary only) ---
    sensitivity: Optional[float] = None
    specificity: Optional[float] = None
    if len(cm) == 2:
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        sensitivity = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

    # --- Feature importance ---
    importances: Dict[str, float] = {}
    if hasattr(model, "feature_importances_"):
        raw_imp = model.feature_importances_
        for i, name in enumerate(feature_names):
            if i < len(raw_imp):
                importances[name] = round(float(raw_imp[i]), 4)

    # --- Dataset statistics ---
    n_test = int(len(y_test))
    y_arr = np.asarray(y_test)
    class_distribution: Dict[str, int] = {}
    for label in sorted(np.unique(y_arr)):
        class_distribution[str(int(label))] = int((y_arr == label).sum())

    results: Dict[str, Any] = {
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


def print_summary(results: Dict[str, Any]) -> None:
    """Print a concise human-readable evaluation summary.

    Parameters
    ----------
    results :
        Evaluation dict as returned by :func:`evaluate_model`.
    """
    name = results["model_name"]
    print(f"\n{'=' * 60}")
    print(f"  Evaluation Results: {name.upper()}")
    print(f"{'=' * 60}")
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
            results["feature_importances"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for feat, imp in sorted_feats[:5]:
            print(f"    {feat:30s} {imp:.4f}")
    print(f"{'=' * 60}\n")


def save_evaluation(
    results: Dict[str, Any],
    output_path: str,
) -> None:
    """Persist evaluation results to a JSON file.

    Parameters
    ----------
    results :
        Evaluation dict as returned by :func:`evaluate_model`.
    output_path :
        Absolute or relative path for the output JSON file.
    """
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    logger.info("Evaluation artifact saved to %s", output_path)
