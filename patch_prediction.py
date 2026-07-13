import re

filepath = "backend/prediction.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add _run_model_prediction helper
helper_code = """
def _run_model_prediction(model_name: str, input_list: list):
    \"\"\"Run prediction using pickle if available, otherwise ONNX.\"\"\"
    from . import model_service as ms
    import numpy as np
    entry = ms._entries.get(model_name)
    if not entry:
        raise ValueError(f"Model {model_name} not found")

    if entry.model is not None:
        raw_pred = entry.model.predict([input_list])
        raw = ms._normalize_prediction(raw_pred)
        confidence, risk_level = ms._extract_confidence(entry.model, [input_list])
        proba = entry.model.predict_proba([input_list])[0]
        return raw, confidence, risk_level, proba
    elif entry.onnx_session is not None or entry.is_voting:
        input_array = np.array([input_list], dtype=np.float32)
        raw, prob = ms._predict_onnx_probs(entry, input_array)
        confidence, risk_level = ms._classify_confidence(prob)
        return raw, confidence, risk_level, prob[0]
    else:
        raise ValueError(f"No usable model for {model_name}")

"""

if "_run_model_prediction" not in content:
    # Insert after def initialize_models
    init_match = re.search(r"def initialize_models\(\):[\s\S]*?\n\n", content)
    if init_match:
        content = content[:init_match.end()] + helper_code + content[init_match.end():]

# Fix the availability checks
patterns = {
    "kidney": r"    if _pred\.kidney_model is None:\n\s+raise HTTPException\(status_code=503, detail=\"Kidney Model not trained/loaded\.\"\)",
    "lungs": r"    if _pred\.lungs_model is None:\n\s+raise HTTPException\(status_code=503, detail=\"Lung Model not trained/loaded\.\"\)",
    "diabetes": r"    if _pred\.diabetes_model is None:\n\s+raise HTTPException\(status_code=503, detail=\"Diabetes Model not available\"\)",
    "heart": r"    if _pred\.heart_model is None:\n\s+raise HTTPException\(status_code=503, detail=\"Heart Model not available\"\)",
    "liver": r"    if _pred\.liver_model is None or _pred\.liver_scaler is None:\n\s+raise HTTPException\(status_code=503, detail=\"Liver Model or Scaler not available\"\)"
}

replacements = {
    "kidney": "    if not model_service.is_available(\"kidney\"):\n        raise HTTPException(status_code=503, detail=\"Kidney Model not trained/loaded.\")",
    "lungs": "    if not model_service.is_available(\"lungs\"):\n        raise HTTPException(status_code=503, detail=\"Lung Model not trained/loaded.\")",
    "diabetes": "    if not model_service.is_available(\"diabetes\"):\n        raise HTTPException(status_code=503, detail=\"Diabetes Model not available\")",
    "heart": "    if not model_service.is_available(\"heart\"):\n        raise HTTPException(status_code=503, detail=\"Heart Model not available\")",
    "liver": "    if not model_service.is_available(\"liver\"):\n        raise HTTPException(status_code=503, detail=\"Liver Model or Scaler not available\")"
}

for key, pattern in patterns.items():
    content = re.sub(pattern, replacements[key], content)

# Fix imputer loading: it needs the entry directly if model is None
imputer_pattern = r"def _get_imputer_and_conformal\(model_name: str, current_model_obj: Any\):\n[\s\S]*?return None, None"
new_imputer = """def _get_imputer_and_conformal(model_name: str, current_model_obj: Any):
    \"\"\"
    Helper to retrieve the MICE imputer and conformal prediction threshold
    associated with the given model name, maintaining compatibility with tests.
    \"\"\"
    entry = model_service._entries.get(model_name)
    if entry:
        return entry.imputer, entry.conformal_q
    return None, None"""
content = re.sub(imputer_pattern, new_imputer, content)

# Fix prediction logic for each model
prediction_patterns = [
    # Kidney
    (r"        raw_pred = _pred\.kidney_model\.predict\(\[imputed_list\]\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.kidney_model, \[imputed_list\]\)",
     r"        raw, confidence, risk_level, proba = _run_model_prediction(\"kidney\", imputed_list)"),
    (r"        try:\n            proba = _pred\.kidney_model\.predict_proba\(\[imputed_list\]\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Kidney: %s\", e\)",
     r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Kidney: %s\", e)"),

    # Lungs
    (r"        raw_pred = _pred\.lungs_model\.predict\(\[imputed_list\]\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.lungs_model, \[imputed_list\]\)",
     r"        raw, confidence, risk_level, proba = _run_model_prediction(\"lungs\", imputed_list)"),
    (r"        try:\n            proba = _pred\.lungs_model\.predict_proba\(\[imputed_list\]\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Lungs: %s\", e\)",
     r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Lungs: %s\", e)"),

    # Diabetes
    (r"        raw_pred = _pred\.diabetes_model\.predict\(\[imputed_list\]\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.diabetes_model, \[imputed_list\]\)",
     r"        raw, confidence, risk_level, proba = _run_model_prediction(\"diabetes\", imputed_list)"),
    (r"        try:\n            proba = _pred\.diabetes_model\.predict_proba\(\[imputed_list\]\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Diabetes: %s\", e\)",
     r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Diabetes: %s\", e)"),

    # Heart
    (r"        raw_pred = _pred\.heart_model\.predict\(\[imputed_list\]\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.heart_model, \[imputed_list\]\)",
     r"        raw, confidence, risk_level, proba = _run_model_prediction(\"heart\", imputed_list)"),
    (r"        try:\n            proba = _pred\.heart_model\.predict_proba\(\[imputed_list\]\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Heart: %s\", e\)",
     r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Heart: %s\", e)"),

    # Liver
    (r"        raw_pred = _pred\.liver_model\.predict\(\[imputed_list\]\)\n        raw = _normalize_prediction\(raw_pred\)\n        confidence, risk_level = _extract_confidence\(_pred\.liver_model, \[imputed_list\]\)",
     r"        raw, confidence, risk_level, proba = _run_model_prediction(\"liver\", imputed_list)"),
    (r"        try:\n            proba = _pred\.liver_model\.predict_proba\(\[imputed_list\]\)\[0\]\n            proba_pos = float\(proba\[1\]\) if len\(proba\) > 1 else float\(proba\[0\]\)\n        except Exception as e:\n            logger\.warning\(\"Predict proba failed for Liver: %s\", e\)",
     r"        try:\n            proba_pos = float(proba[1]) if len(proba) > 1 else float(proba[0])\n        except Exception as e:\n            logger.warning(\"Predict proba failed for Liver: %s\", e)")
]

for pat, repl in prediction_patterns:
    content = re.sub(pat, repl, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("Patching complete.")
