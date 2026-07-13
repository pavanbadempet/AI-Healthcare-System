import os
import shutil
import subprocess


def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {cmd}: {result.stderr}")
        return False
    return True

import time

temp_dir = os.path.join(os.environ['TEMP'], f'hf_sync_{int(time.time())}')

# Copy everything
print("Copying files...")
shutil.copytree('.', temp_dir, ignore=shutil.ignore_patterns('.git', '.github', 'node_modules', '__pycache__', 'dist', 'build', '.gradle'))

print("Cleaning large files...")
for root, dirs, files in os.walk(temp_dir):
    for file in files:
        if file.endswith(('.csv', '.parquet', '.db', '.sqlite3', '.pkl', '.onnx', '.png', '.joblib')) or file == 'kaggle_run_logs.txt' or file.endswith('.log'):
            os.remove(os.path.join(root, file))

# Rename Dockerfile
if os.path.exists(os.path.join(temp_dir, 'Dockerfile.hf')):
    shutil.copy(os.path.join(temp_dir, 'Dockerfile.hf'), os.path.join(temp_dir, 'Dockerfile'))

# Build README.md for HF
hf_readme = """---
title: AIO Health Backend
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

"""
readme_path = os.path.join(temp_dir, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        hf_readme += f.read()

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(hf_readme)

print("Initializing git and pushing...")
run_cmd("git init", cwd=temp_dir)
run_cmd("git checkout -b main", cwd=temp_dir)
run_cmd('git config user.email "bot@example.com"', cwd=temp_dir)
run_cmd('git config user.name "Bot"', cwd=temp_dir)
run_cmd("git add .", cwd=temp_dir)
run_cmd('git commit -m "Force deploy to Hugging Face via Python"', cwd=temp_dir)
# Add remote
run_cmd("git remote add hf https://huggingface.co/spaces/pavanbadempet/aio-health-backend", cwd=temp_dir)
print("Pushing to Hugging Face...")
# We use force push. Note: If the user doesn't have credentials cached, this will fail or prompt.
res = subprocess.run("git push --force hf main:main", shell=True, cwd=temp_dir, capture_output=True, text=True)
if res.returncode == 0:
    print("Successfully pushed to Hugging Face!")
else:
    print(f"Failed to push: {res.stderr}")

