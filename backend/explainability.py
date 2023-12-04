import shap
import json
import numpy as np
import pickle
import matplotlib.pyplot as plt
import io
import base64

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
    
    # Strategy: Unwrap VotingClassifier to get the strongest tree-based member (XGBoost)
    # This provides a "High Fidelity Proxy Explanation" which is standard practice when
    # ensemble explanation is too computationally expensive for real-time.
    target_estimator = model
    if hasattr(model, 'estimators_'):
        # 0 is XGBoost in our train_ensemble.py pipeline
        target_estimator = model.estimators_[0]
        
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
        
        return {"html": html_str}

    except Exception as e:
        print(f"SHAP Generation Error: {e}")
        return None

def generate_static_force_plot(model, input_vector, feature_names):
    """
    Generates a static matplotlib image of the SHAP waterfall/force plot.
    Use this if frontend interactivity is hard to implement.
    """
    # ... implementation can be added if frontend pure JS fails
    pass
