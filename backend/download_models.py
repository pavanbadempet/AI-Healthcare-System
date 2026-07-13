import logging
import os

from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Repository containing the pre-trained model files
REPO_ID = "pavanbadempet/ai-healthcare-models"

# List of all files we need to download from the Hugging Face Model Registry
MODEL_FILES = [
    "diabetes_model.onnx",
    "diabetes_model.pkl",
    "heart_disease_model.onnx",
    "heart_disease_model.pkl",
    "kidney_model.onnx",
    "kidney_model.pkl",
    "kidney_scaler.onnx",
    "kidney_scaler.pkl",
    "liver_disease_model.onnx",
    "liver_disease_model.pkl",
    "liver_scaler.onnx",
    "liver_scaler.pkl",
    "lungs_model.onnx",
    "lungs_model.pkl",
    "lungs_scaler.onnx",
    "lungs_scaler.pkl"
]

def download_all_models():
    """Download all required model weights from Hugging Face Hub."""
    dest_dir = os.path.dirname(os.path.abspath(__file__))
    token = os.environ.get("HF_TOKEN")

    print(f"Starting model downloads from Hugging Face Model Registry: {REPO_ID}...")
    for filename in MODEL_FILES:
        target_path = os.path.join(dest_dir, filename)

        # Skip download if the file is already present
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print(f"Model file already exists locally: {filename} (skipped)")
            continue

        print(f"Downloading {filename}...")
        try:
            downloaded_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=dest_dir,
                token=token
            )
            print(f"Successfully downloaded {filename} to {downloaded_path}")
        except Exception as e:
            print(f"Error downloading {filename} from Hugging Face Hub: {str(e)}")
            # Write a small placeholder or raise warning
            if not os.path.exists(target_path):
                # Ensure a placeholder exists so model initialization doesn't crash entirely
                with open(target_path, "w") as f:
                    f.write("")

if __name__ == "__main__":
    download_all_models()
