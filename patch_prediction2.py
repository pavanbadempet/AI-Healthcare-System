import re
import os

filepath = "backend/prediction.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Update _run_model_prediction helper to accept X
helper_code = """
def _run_model_prediction_scaled(model_name: str, input_list: list, X=None):
    \"\"\"Run prediction using pickle if available, otherwise ONNX. Supports scaled input.\"\"\"
    from . import model_service as ms
    import numpy as np
    entry = ms._entries.get(model_name)
    if not entry:
        raise ValueError(f"Model {model_name} not found")
        
    predict_input = X if X is not None else [input_list]
        
    if entry.model is not None:
        raw_pred = entry.model.predict(predict_input)
        raw = ms._normalize_prediction(raw_pred)
        confidence, risk_level = ms._extract_confidence(entry.model, predict_input)
        proba = entry.model.predict_proba(predict_input)[0]
        return raw, confidence, risk_level, proba
    elif entry.onnx_session is not None or entry.is_voting:
        # ONNX uses unscaled input if scaler_onnx_session exists in model_service
        # Actually model_service predict_kidney passes input_list to scaler if needed
        # Let's check how model_service handles it:
        input_array = np.array([input_list], dtype=np.float32)
        if entry.scaler_needed and entry.scaler_onnx_session is not None:
            input_array = entry.scaler_onnx_session.run(None, {entry.scaler_onnx_session.get_inputs()[0].name: input_array})[0]
        elif entry.scaler_needed and entry.scaler is not None:
            input_array = entry.scaler.transform(input_array).astype(np.float32)
        
        raw, prob = ms._predict_onnx_probs(entry, input_array)
        confidence, risk_level = ms._classify_confidence(prob)
        return raw, confidence, risk_level, prob[0]
    else:
        raise ValueError(f"No usable model for {model_name}")
"""

# Replace the old helper
content = re.sub(
    r"def _run_model_prediction\(model_name: str, input_list: list\):[\s\S]*?raise ValueError\(f\"No usable model for \{model_name\}\"\)\n\n",
    helper_code,
    content
)

# Kidney
content = re.sub(
    r"        raw_pred = _pred\.kidney_model\.predict\(X\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.kidney_model, X\)",
    r"        raw, confidence, risk_level, proba = _run_model_prediction_scaled(\"kidney\", imputed_list, X)",
    content
)
content = re.sub(
    r"        try:\n            proba = _pred\.kidney_model\.predict_proba\(X\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Kidney: %s\", e\)",
    r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Kidney: %s\", e)",
    content
)

# Lungs
content = re.sub(
    r"        raw_pred = _pred\.lungs_model\.predict\(X\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.lungs_model, X\)",
    r"        raw, confidence, risk_level, proba = _run_model_prediction_scaled(\"lungs\", imputed_list, X)",
    content
)
content = re.sub(
    r"        try:\n            proba = _pred\.lungs_model\.predict_proba\(X\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Lungs: %s\", e\)",
    r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Lungs: %s\", e)",
    content
)

# Liver
content = re.sub(
    r"        raw_pred = _pred\.liver_model\.predict\(X\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.liver_model, X\)",
    r"        raw, confidence, risk_level, proba = _run_model_prediction_scaled(\"liver\", imputed_list, X)",
    content
)
content = re.sub(
    r"        try:\n            proba = _pred\.liver_model\.predict_proba\(X\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Liver: %s\", e\)",
    r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Liver: %s\", e)",
    content
)

# Also rename the calls for Diabetes and Heart to _run_model_prediction_scaled
content = content.replace("_run_model_prediction(\"diabetes\", imputed_list)", "_run_model_prediction_scaled(\"diabetes\", imputed_list)")
content = content.replace("_run_model_prediction(\"heart\", imputed_list)", "_run_model_prediction_scaled(\"heart\", imputed_list)")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Patching scaled models complete.")
