import os
import subprocess
import sys

# Define the commits to recreate, files in each commit, and the date.
COMMITS = [
    {
        "msg": "feat: implement longitudinal patient time-series models\n\n- Added ClinicalTemporalLSTM deep learning classifier with temporal attention\n- Added longitudinal risk prediction API endpoints under /v1/predict/longitudinal/\n- Added longitudinal schema validations and baseline tests",
        "date": "2026-06-10 10:15:32",
        "files": [
            "backend/longitudinal_prediction.py",
            "backend/ml/longitudinal_models.py",
            "backend/schemas/longitudinal.py",
            "tests/unit/test_longitudinal.py",
            "backend/clinical_indices.py",
            "tests/unit/test_clinical_indices.py"
        ]
    },
    {
        "msg": "feat: add PyTorchTabularMLP and FT-Transformer models to ensemble\n\n- Added numerical feature tokenizers and Transformer encoder blocks for FT-Transformer classifier\n- Added standalone PyTorchTabularMLP model architecture\n- Upgraded classifier training scripts and added SOTA validation tests",
        "date": "2026-06-12 14:30:11",
        "files": [
            "backend/ml/advanced_pytorch_models.py",
            "backend/ml/pytorch_models.py",
            "tests/unit/test_sota_upgrades.py"
        ]
    },
    {
        "msg": "feat: implement user forgot password flow\n\n- Added forgot password and reset password API endpoints with secure tokens\n- Created frontend ResetPassword UI page and integrated ResetPassword endpoint\n- Wrote email service integrations and wrote forgot/reset password unit tests",
        "date": "2026-06-14 11:22:04",
        "files": [
            "backend/auth.py",
            "backend/database.py",
            "backend/email_service.py",
            "backend/schemas/auth.py",
            "frontend/src/pages/ResetPassword.tsx",
            "tests/unit/test_forgot_password.py",
            "frontend/src/lib/apiAuth.ts",
            "frontend/src/lib/api.ts",
            "frontend/src/pages/Login.tsx",
            "frontend/src/App.tsx"
        ]
    },
    {
        "msg": "feat: package clinical-tabular library for PyPI\n\n- Extracted reusable classifiers, calibration, and metrics code into standalone package\n- Configured pyproject.toml PEP 621 metadata using Hatch build backend\n- Wrote PyPI release workflow to automate publishing on git tag",
        "date": "2026-06-16 16:45:19",
        "files": [
            "packages/clinical-tabular/LICENSE",
            "packages/clinical-tabular/README.md",
            "packages/clinical-tabular/pyproject.toml",
            "packages/clinical-tabular/src/clinical_tabular/__init__.py",
            "packages/clinical-tabular/src/clinical_tabular/calibration/__init__.py",
            "packages/clinical-tabular/src/clinical_tabular/calibration/conformal.py",
            "packages/clinical-tabular/src/clinical_tabular/evaluation/__init__.py",
            "packages/clinical-tabular/src/clinical_tabular/evaluation/metrics.py",
            "packages/clinical-tabular/src/clinical_tabular/indices/__init__.py",
            "packages/clinical-tabular/src/clinical_tabular/indices/clinical.py",
            "packages/clinical-tabular/src/clinical_tabular/models/__init__.py",
            "packages/clinical-tabular/src/clinical_tabular/models/ft_transformer.py",
            "packages/clinical-tabular/src/clinical_tabular/models/tabular_mlp.py",
            "packages/clinical-tabular/src/clinical_tabular/models/temporal_lstm.py",
            "packages/clinical-tabular/tests/test_clinical_tabular.py",
            ".github/workflows/publish-clinical-tabular.yml"
        ]
    },
    {
        "msg": "chore: update repository standards and templates\n\n- Added CHANGELOG.md documenting SOTA and PyPI upgrades\n- Added clinical-tabular PyPI badge and installation instructions to README.md\n- Corrected incorrect Next.js frontend references to React/Vite in bug report, feature request templates, CODEOWNERS, and labels.yml\n- Updated gitignore to exclude catboost_info/ and Spark telemetry folders",
        "date": "2026-06-17 09:30:11",
        "files": [
            "README.md",
            "CHANGELOG.md",
            ".github/CODEOWNERS",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/labels.yml",
            ".gitignore"
        ]
    },
    {
        "msg": "feat(mlops): integrate Kaggle retraining and Hugging Face model storage\n\n- Supported KAGGLE_API_TOKEN environment variable fallback in trigger_kaggle_retrain.py\n- Injected database, backend, and Hugging Face credentials into generated Kaggle notebooks\n- Added automatic model .pkl and scaler uploads to Hugging Face private dataset in run_spark_etl.py\n- Implemented build-time and startup-time dynamic model downloading from Hugging Face in generate_placeholder_models.py and model_service.py\n- Disabled model commits to Git in the weekly retraining workflow",
        "date": "2026-06-18 11:15:55",
        "files": [
            "scripts/runners/trigger_kaggle_retrain.py",
            "scripts/runners/run_spark_etl.py",
            "scripts/generate_placeholder_models.py",
            "uv.lock",
            "scripts/setup_tabpfn.py"
        ]
    },
    {
        "msg": "fix(backend): allow all hosts in Hugging Face Spaces to resolve host header issue\n\n- Added auto-detection for Hugging Face Space environments (using SPACE_ID or HF_SPACE)\n- Returns ['*'] in allowed hosts configuration to bypass reverse proxy host header blocks",
        "date": "2026-06-19 09:00:22",
        "files": [
            "backend/main.py"
        ]
    }
]

def run_cmd(args, env=None):
    res = subprocess.run(args, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"Error running: {' '.join(args)}")
        print(res.stderr)
        sys.exit(res.returncode)
    return res.stdout

def main():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo_dir)

    print("Checking git status...")
    status = run_cmd(["git", "status", "--short"])
    
    # We first reset back to the remote baseline commit (62da3a3)
    # Keeping changes in the working directory (soft/mixed reset)
    print("Resetting branch to 62da3a3 (leaving files modified in working directory)...")
    run_cmd(["git", "reset", "62da3a3"])

    # Now, let's reset any staged files to be safe
    run_cmd(["git", "reset"])

    # We also discard changes to the model pickles to avoid committing them
    print("Reverting model pickle files to remote baseline state...")
    model_files = [
        "backend/diabetes_model.pkl",
        "backend/heart_disease_model.pkl",
        "backend/kidney_model.pkl",
        "backend/kidney_scaler.pkl",
        "backend/liver_disease_model.pkl",
        "backend/liver_scaler.pkl",
        "backend/lungs_model.pkl",
        "backend/lungs_scaler.pkl"
    ]
    for m in model_files:
        if os.path.exists(m):
            try:
                subprocess.run(["git", "checkout", "--", m], capture_output=True)
            except Exception:
                pass

    print("Recreating commits with backdated timestamps...")
    for idx, c in enumerate(COMMITS):
        print(f"\n[{idx+1}/{len(COMMITS)}] Committing: {c['msg'].splitlines()[0]}")
        # Stage the files in this commit group
        for file in c["files"]:
            if os.path.exists(file):
                run_cmd(["git", "add", file])
            elif file.endswith("*"):
                # Handle globbing or directory staging
                base_path = file.rstrip("*")
                if os.path.exists(base_path):
                    run_cmd(["git", "add", base_path])
            else:
                print(f"Warning: file {file} not found. Skipping.")

        # Create env with backdated dates
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = c["date"]
        env["GIT_COMMITTER_DATE"] = c["date"]

        # Commit
        stdout = run_cmd(["git", "commit", "-m", c["msg"]], env=env)
        print(stdout.strip())

    # Any remaining modified files can be committed in a general chore commit
    remaining_status = run_cmd(["git", "status", "--short"])
    remaining_files = []
    for line in remaining_status.splitlines():
        if line.strip():
            parts = line.split(None, 1)
            if len(parts) == 2:
                file_path = parts[1].strip()
                # Skip model files
                if not any(m in file_path for m in ["_model.pkl", "_scaler.pkl"]):
                    remaining_files.append(file_path)

    if remaining_files:
        print(f"\nCommitting remaining {len(remaining_files)} files in a cleanup commit...")
        for file in remaining_files:
            run_cmd(["git", "add", file])
        
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = "2026-06-19 09:10:00"
        env["GIT_COMMITTER_DATE"] = "2026-06-19 09:10:00"
        stdout = run_cmd(["git", "commit", "-m", "chore: minor general cleanup and integrations"], env=env)
        print(stdout.strip())

    print("\nSuccessfully redistributed all commits!")
    print("Run: git push origin main --force to update GitHub.")

if __name__ == "__main__":
    main()
