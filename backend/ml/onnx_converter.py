import logging
import os
import pickle
from typing import Any

logger = logging.getLogger(__name__)

def convert_to_onnx(model_path: str, output_path: str, initial_types: list = None) -> bool:
    """
    Convert a pickled model/scaler to ONNX format.
    Supports: scikit-learn, XGBoost, LightGBM, CatBoost.
    """
    if not os.path.exists(model_path):
        logger.error("Model path %s does not exist", model_path)
        return False

    try:
        with open(model_path, "rb") as f:
            obj = pickle.load(f)
    except Exception as e:
        logger.error("Failed to load pickle file %s: %s", model_path, e)
        return False

    # Extract model from dictionary if wrapped
    model = obj["model"] if isinstance(obj, dict) and "model" in obj else obj

    try:
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError as e:
        logger.error("ONNX conversion packages are not installed: %s", e)
        return False

    # Determine estimator type and convert
    model_classname = model.__class__.__name__
    logger.info("Converting %s (class: %s) to ONNX", model_path, model_classname)

    if initial_types is None:
        # Default assumption: FloatTensorType of shape [None, n_features]
        # We will deduce number of features if possible
        n_features = 9 # fallback default
        if hasattr(model, "n_features_in_"):
            n_features = model.n_features_in_
        elif hasattr(model, "n_features_"):
            n_features = model.n_features_
        elif hasattr(model, "feature_names_in_"):
            n_features = len(model.feature_names_in_)
        elif model_classname == "XGBClassifier" or model_classname == "XGBRegressor":
            n_features = getattr(model, "n_features_in_", 9)
        elif "CatBoost" in model_classname:
            n_features = len(model.feature_names_) if model.feature_names_ else 9

        if "XGB" in model_classname or "LGBM" in model_classname:
            from onnxmltools.convert.common.data_types import FloatTensorType as ToolFloatTensorType
            initial_types = [("float_input", ToolFloatTensorType([None, n_features]))]
        else:
            initial_types = [("float_input", FloatTensorType([None, n_features]))]

    try:
        if "VotingClassifier" in model_classname:
            # For VotingClassifier, we export each sub-estimator individually
            logger.info("Encountered VotingClassifier. Exporting sub-estimators individually.")
            sub_estimators = model.estimators_
            base_dir = os.path.dirname(output_path)
            base_name = os.path.basename(output_path).replace(".onnx", "")
            for name, est in zip(model.estimators_names_, sub_estimators):
                sub_output = os.path.join(base_dir, f"{base_name}_{name}.onnx")

                # Make sure to use the right FloatTensorType type for the sub-estimator
                est_classname = est.__class__.__name__
                if "XGB" in est_classname or "LGBM" in est_classname:
                    from onnxmltools.convert.common.data_types import FloatTensorType as ToolFloatTensorType
                    sub_initial_types = [("float_input", ToolFloatTensorType(initial_types[0][1].shape))]
                else:
                    from skl2onnx.common.data_types import FloatTensorType as SklFloatTensorType
                    sub_initial_types = [("float_input", SklFloatTensorType(initial_types[0][1].shape))]

                success = save_single_estimator(est, sub_output, sub_initial_types)
                if not success:
                    return False
            # Also save metadata indicating it's a voting classifier
            meta_path = output_path.replace(".onnx", ".meta.json")
            import json
            with open(meta_path, "w") as f_meta:
                json.dump({
                    "type": "VotingClassifier",
                    "estimators": model.estimators_names_,
                    "weights": list(model.weights) if model.weights is not None else None
                }, f_meta)
            return True
        else:
            return save_single_estimator(model, output_path, initial_types)

    except Exception as e:
        logger.error("Failed to convert %s to ONNX: %s", model_path, e)
        return False

def save_single_estimator(model: Any, output_path: str, initial_types: list) -> bool:
    import onnx
    import onnxmltools
    from skl2onnx import convert_sklearn

    model_classname = model.__class__.__name__

    if "XGB" in model_classname:
        try:
            model.get_booster().feature_names = None
        except Exception as ex:
            logger.warning("Failed to clear feature_names on XGBoost booster: %s", ex)
        onnx_model = onnxmltools.convert_xgboost(model, initial_types=initial_types, target_opset=15)
    elif "LGBM" in model_classname:
        onnx_model = onnxmltools.convert_lightgbm(model, initial_types=initial_types, target_opset=15)
    elif "CatBoost" in model_classname:
        model.save_model(output_path, format="onnx")
        logger.info("Exported CatBoost model directly to %s", output_path)
        return True
    else:
        # Scikit-learn models/scalers/imputers
        onnx_model = convert_sklearn(model, initial_types=initial_types, target_opset=15)

    if onnx_model:
        onnx.save_model(onnx_model, output_path)
        logger.info("Successfully saved ONNX model to %s", output_path)
        return True

    return False
