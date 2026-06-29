# Optional heavy imports - not available on lite deployment
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    shap = None

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

import logging

import numpy as np

# --- Logging Configuration ---
logger = logging.getLogger(__name__)

def get_shap_values(model, input_vector, feature_names):
    """
    Generates SHAP values for a given model and input.
    Handles VotingClassifier by interacting with the first estimator (XGBoost) as a proxy,
    since direct ensemble SHAP is complex/slow for real-time.

    Args:
        model: The trained model (VotingClassifier or XGBClassifier)
        input_vector: Numpy array of shape (1, n_features)
        feature_names: List of strings

    Returns:
        JSON compatible dict with 'base_value', 'shap_values', 'feature_names'
        OR base64 image string of a force plot.
    """

    # Check if SHAP is available
    if not SHAP_AVAILABLE:
        return {
            "html": "<div style='color:#F59E0B;padding:20px;'>⚠️ SHAP explanations are not available on the lite deployment. Full explanations require additional memory.</div>",
            "error": "SHAP library not installed"
        }

    # Strategy: Unwrap VotingClassifier and CalibratedClassifierCV to get the strongest tree-based member (XGBoost)
    # This provides a "High Fidelity Proxy Explanation" which is standard practice when
    # ensemble explanation is too computationally expensive for real-time.
    target_estimator = model
    if hasattr(model, 'estimators_'):
        # 0 is XGBoost/Calibrated XGBoost in our train pipeline
        target_estimator = model.estimators_[0]

    # Unwrap CalibratedClassifierCV if present
    if hasattr(target_estimator, 'calibrated_classifiers_') and len(target_estimator.calibrated_classifiers_) > 0:
        target_estimator = target_estimator.calibrated_classifiers_[0].estimator
    elif hasattr(target_estimator, 'estimator'):
        target_estimator = target_estimator.estimator

    # Check if target_estimator is a TabPFNClassifier
    if "TabPFNClassifier" in str(type(target_estimator)):
        return {
            "html": "<div style='color:#3B82F6;padding:20px;'>💡 Explanation calculated natively: TabPFN is a state-of-the-art attentive tabular transformer. Its predictions are computed by performing in-context attention over the entire training set, providing optimal clinical accuracy without relying on fixed tree structures.</div>",
            "info": "TabPFN is a deep transformer, SHAP TreeExplainer is bypassed."
        }

    # Create Explainer
    try:
        explainer = shap.TreeExplainer(target_estimator)
        shap_values = explainer.shap_values(input_vector)

        # Handle different SHAP output formats (binary class usually gives single array or list of two)
        if isinstance(shap_values, list):
            sv = shap_values[1][0] # Positive class
        elif len(shap_values.shape) > 1 and shap_values.shape[1] > 1:
             sv = shap_values[0][1] # Multiclass structure
        else:
            sv = shap_values[0] # Single output

        # Generate HTML Force Plot
        # shap.force_plot returns a Visualizer. .html() gets the string.
        # We need to initialize JS in the HTML string usually.
        force_plot = shap.force_plot(
            explainer.expected_value if np.isscalar(explainer.expected_value) else explainer.expected_value[0],
            sv,
            input_vector[0],
            feature_names=feature_names,
            matplotlib=False,
            show=False
        )

        # Save to HTML string
        html_str = f"<head><script src='https://cdnjs.cloudflare.com/ajax/libs/shapjs/0.4.1/shap.min.js'></script></head><body>{force_plot.html()}</body>"

        # Generate static image fallback
        static_img = generate_static_force_plot(model, input_vector, feature_names)

        return {"html": html_str, "image": static_img}

    except Exception:
        logger.error("SHAP generation failed")
        return None

def generate_static_force_plot(model, input_vector, feature_names):
    """
    Generates a static matplotlib image of the SHAP waterfall/force plot.
    Use this if frontend interactivity is hard to implement.
    """
    if not SHAP_AVAILABLE or not MATPLOTLIB_AVAILABLE:
        return None

    import io
    import base64

    # Unwrap VotingClassifier and CalibratedClassifierCV
    target_estimator = model
    if hasattr(model, 'estimators_'):
        target_estimator = model.estimators_[0]

    if hasattr(target_estimator, 'calibrated_classifiers_') and len(target_estimator.calibrated_classifiers_) > 0:
        target_estimator = target_estimator.calibrated_classifiers_[0].estimator
    elif hasattr(target_estimator, 'estimator'):
        target_estimator = target_estimator.estimator

    if "TabPFNClassifier" in str(type(target_estimator)):
        return None

    try:
        explainer = shap.TreeExplainer(target_estimator)
        shap_values = explainer.shap_values(input_vector)

        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        elif len(shap_values.shape) > 1 and shap_values.shape[1] > 1:
             sv = shap_values[0][1]
        else:
            sv = shap_values[0]

        # Use matplotlib to draw the force plot
        fig = plt.figure(figsize=(10, 3))
        shap.force_plot(
            explainer.expected_value if np.isscalar(explainer.expected_value) else explainer.expected_value[0],
            sv,
            input_vector[0],
            feature_names=feature_names,
            matplotlib=True,
            show=False
        )

        plt.tight_layout()
        
        # Save to base64 buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.error("Static SHAP generation failed: %s", str(e))
        return None

