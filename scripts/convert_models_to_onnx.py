import os
import sys
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.onnx_converter import convert_to_onnx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    
    models = {
        "diabetes": (os.path.join(backend_dir, "diabetes_model.pkl"), os.path.join(backend_dir, "diabetes_model.onnx")),
        "heart": (os.path.join(backend_dir, "heart_disease_model.pkl"), os.path.join(backend_dir, "heart_disease_model.onnx")),
        "liver_model": (os.path.join(backend_dir, "liver_disease_model.pkl"), os.path.join(backend_dir, "liver_disease_model.onnx")),
        "liver_scaler": (os.path.join(backend_dir, "liver_scaler.pkl"), os.path.join(backend_dir, "liver_scaler.onnx")),
        "kidney_model": (os.path.join(backend_dir, "kidney_model.pkl"), os.path.join(backend_dir, "kidney_model.onnx")),
        "kidney_scaler": (os.path.join(backend_dir, "kidney_scaler.pkl"), os.path.join(backend_dir, "kidney_scaler.onnx")),
        "lungs_model": (os.path.join(backend_dir, "lungs_model.pkl"), os.path.join(backend_dir, "lungs_model.onnx")),
        "lungs_scaler": (os.path.join(backend_dir, "lungs_scaler.pkl"), os.path.join(backend_dir, "lungs_scaler.onnx")),
    }
    
    success_count = 0
    for name, (pkl_path, onnx_path) in models.items():
        logger.info("Converting %s...", name)
        if not os.path.exists(pkl_path):
            logger.warning("Pickle file %s not found. Skipping.", pkl_path)
            continue
            
        success = convert_to_onnx(pkl_path, onnx_path)
        if success:
            success_count += 1
            logger.info("Successfully converted %s to %s", name, onnx_path)
        else:
            logger.error("Failed to convert %s", name)
            
    logger.info("Model conversion complete. Successfully converted %d of %d models.", success_count, len(models))

if __name__ == "__main__":
    main()
