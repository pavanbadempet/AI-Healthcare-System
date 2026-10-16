import os
import shutil
import subprocess
import time

def run():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), f'hf_deploy_{int(time.time())}')

    print(f"Deploying to Hugging Face Spaces from {repo_root}...")
    print(f"Staging deployment in {temp_dir}...")

    # Copy files excluding git, cache, node_modules
    shutil.copytree(
        repo_root,
        temp_dir,
        ignore=shutil.ignore_patterns(
            '.git', '.github', '.gitlab', 'node_modules', '__pycache__',
            'dist', 'build', '.gradle', 'target', '.pytest_cache', 'htmlcov'
        )
    )

    # Remove all binary files that Hugging Face blocks in Git
    print("Stripping binary assets to satisfy Hugging Face pre-receive hook...")
    binary_extensions = (
        '.png', '.gif', '.jpg', '.jpeg', '.webp', '.ico',
        '.db', '.sqlite', '.sqlite3', '.parquet', '.csv',
        '.pkl', '.onnx', '.joblib', '.wasm', '.log', '.bin', '.tar', '.gz'
    )
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            if f.lower().endswith(binary_extensions) or f in {'pytest_failures.txt', 'test_output.txt', 'kaggle_run_logs.txt'}:
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass

    # Ensure Dockerfile.hf is the active Dockerfile
    dockerfile_hf = os.path.join(temp_dir, 'Dockerfile.hf')
    if os.path.exists(dockerfile_hf):
        shutil.copy(dockerfile_hf, os.path.join(temp_dir, 'Dockerfile'))

    # Add Hugging Face Space metadata frontmatter to README.md
    readme_path = os.path.join(temp_dir, 'README.md')
    hf_metadata = """---
title: AIO Health Backend
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

"""
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as rf:
            content = rf.read()
        if not content.startswith('---'):
            with open(readme_path, 'w', encoding='utf-8') as wf:
                wf.write(hf_metadata + content)

    # Initialize Git repository and push
    print("Initializing deployment git commit...")
    subprocess.run("git init", shell=True, cwd=temp_dir, check=True)
    subprocess.run("git checkout -b main", shell=True, cwd=temp_dir, check=True)
    subprocess.run('git config user.email "pavan9b@gmail.com"', shell=True, cwd=temp_dir, check=True)
    subprocess.run('git config user.name "Pavan Badempet"', shell=True, cwd=temp_dir, check=True)
    subprocess.run("git add .", shell=True, cwd=temp_dir, check=True)
    subprocess.run('git commit -m "deploy: update dual-stack gateway with Neon DB and Doppler secrets"', shell=True, cwd=temp_dir, check=True)

    print("Pushing to Hugging Face remote...")
    res = subprocess.run(
        "git push --force https://huggingface.co/spaces/pavanbadempet/aio-health-backend.git main:main",
        shell=True,
        cwd=temp_dir,
        capture_output=True,
        text=True
    )

    if res.returncode == 0:
        print("[SUCCESS] Successfully deployed to Hugging Face Spaces!")
        print(res.stdout)
    else:
        print(f"[ERROR] Deployment failed:\n{res.stderr}")
        raise RuntimeError(res.stderr)

    # Cleanup temp dir
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

if __name__ == '__main__':
    run()
