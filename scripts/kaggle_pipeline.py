import os
import subprocess
import sys
from huggingface_hub import HfApi

# Target repository on Hugging Face Model Hub
REPO_ID = "pavanbadempet/ai-healthcare-models"

# List of files we expect the training to generate and upload
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

def run_command(command, cwd=None):
    """Run a terminal command and stream output."""
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=cwd)
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        print(f"Warning: Command '{command}' exited with code {process.returncode}")

def run_kaggle_pipeline():
    """Clones code, installs deps, trains all models, and pushes weights to HF Hub."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("CRITICAL ERROR: HF_TOKEN environment variable is not set. Cannot authenticate with Hugging Face.")
        sys.exit(1)

    # 1. Clone repository to get all feature mappings and training files
    print("\n--- Step 1: Cloning Repository ---")
    if not os.path.exists("AI-Healthcare-System"):
        run_command("git clone https://github.com/pavanbadempet/AI-Healthcare-System.git")
    else:
        print("Repository folder already exists, skipping clone.")

    repo_dir = os.path.abspath("AI-Healthcare-System")

    # 2. Install required training packages
    print("\n--- Step 2: Installing Dependencies ---")
    run_command("pip install xgboost scikit-learn onnxruntime skl2onnx onnxmltools pandas pyjwt requests huggingface_hub polars deltalake duckdb great-expectations jinja2 markupsafe")

    # 3. Train all 5 classifiers
    print("\n--- Step 3: Running Model Training Scripts ---")
    # Make sure data/processed directories exist
    os.makedirs(os.path.join(repo_dir, "data/processed"), exist_ok=True)
    
    # Run the training scripts in order
    run_command("python scripts/training/train_diabetes.py", cwd=repo_dir)
    run_command("python scripts/training/train_heart.py", cwd=repo_dir)
    run_command("python scripts/training/train_kidney.py", cwd=repo_dir)
    run_command("python scripts/training/train_liver.py", cwd=repo_dir)
    run_command("python scripts/training/train_lungs.py", cwd=repo_dir)

    # 4. Upload all compiled models to Hugging Face Model Registry
    print("\n--- Step 4: Uploading Weights to Hugging Face Model Registry ---")
    api = HfApi()
    
    try:
        api.create_repo(repo_id=REPO_ID, repo_type="model", exist_ok=True, token=token)
        print(f"Created/Verified target repository: {REPO_ID}")
    except Exception as e:
        print(f"Repo setup note: {str(e)}")

    backend_dir = os.path.join(repo_dir, "backend")
    uploaded = 0
    
    for filename in MODEL_FILES:
        filepath = os.path.join(backend_dir, filename)
        if os.path.exists(filepath):
            print(f"Pushing {filename} to Model Hub...")
            try:
                api.upload_file(
                    path_or_fileobj=filepath,
                    path_in_repo=filename,
                    repo_id=REPO_ID,
                    repo_type="model",
                    token=token
                )
                print(f" -> {filename} uploaded successfully!")
                uploaded += 1
            except Exception as e:
                print(f" -> Failed to upload {filename}: {str(e)}")
        else:
            print(f" -> Warning: {filename} was not found after training runs!")

    print(f"\nPipeline finished. Successfully uploaded {uploaded}/{len(MODEL_FILES)} models to Hugging Face Hub.")

if __name__ == "__main__":
    run_kaggle_pipeline()
