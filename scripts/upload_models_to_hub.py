import os
import sys
from huggingface_hub import HfApi

# Ensure repository root is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Target model repository on Hugging Face Model Hub
REPO_ID = "pavanbadempet/ai-healthcare-models"

# List of files to upload
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

def upload_models():
    """Create the model registry and upload local weights to Hugging Face Model Hub."""
    api = HfApi()
    
    # Read Hugging Face token from environment
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Error: HF_TOKEN environment variable not set.")
        print("Please set it in your environment: $env:HF_TOKEN=\"your_write_token\"")
        return
        
    print(f"Creating Hugging Face model repository: {REPO_ID} (if it doesn't exist)...")
    try:
        api.create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True, token=token)
        print("Model repository is ready.")
    except Exception as e:
        print(f"Note: {str(e)}")
        
    # Locate the backend directory where local models are stored
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
    
    print("\nStarting upload of local weights to registry...")
    uploaded_count = 0
    for filename in MODEL_FILES:
        filepath = os.path.join(backend_dir, filename)
        if os.path.exists(filepath):
            print(f"Uploading {filename} to Hub...")
            try:
                api.upload_file(
                    path_or_fileobj=filepath,
                    path_in_repo=filename,
                    repo_id=REPO_ID,
                    repo_type="model",
                    token=token
                )
                print(f" -> {filename} uploaded successfully!")
                uploaded_count += 1
            except Exception as e:
                print(f" -> Failed to upload {filename}: {str(e)}")
        else:
            print(f" -> Skipping {filename} (not found locally in backend/)")
            
    print(f"\nCompleted. Uploaded {uploaded_count} model files to {REPO_ID}.")

if __name__ == "__main__":
    upload_models()
