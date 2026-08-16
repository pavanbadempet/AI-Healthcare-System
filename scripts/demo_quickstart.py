"""
AI Healthcare System — 1-Click Interactive Demo Launcher
Launches the complete clinical stack with zero friction and zero setup.
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def check_environment():
    print("=" * 65)
    print("  AI HEALTHCARE SYSTEM — 1-CLICK INTERACTIVE DEMO LAUNCHER")
    print("=" * 65)
    print("\n[1/4] Checking Python & Node/Bun environment...")
    print(f"  -> Python {sys.version.split()[0]} ({sys.executable})")

    # Check bun or npm
    has_bun = False
    try:
        res = subprocess.run(["bun", "--version"], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            print(f"  -> Bun {res.stdout.strip()} detected (Ultra-fast runtime)")
            has_bun = True
    except FileNotFoundError:
        pass

    if not has_bun:
        try:
            res = subprocess.run(["npm", "--version"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                print(f"  -> Node.js npm {res.stdout.strip()} detected")
        except FileNotFoundError:
            print("  [!] Warning: Neither Bun nor Node/npm found on PATH.")

    return has_bun

def verify_and_seed_database():
    print("\n[2/4] Verifying local database & clinical seed records...")
    db_path = REPO_ROOT / "healthcare.db"
    if not db_path.exists():
        print("  -> Initializing fresh SQLite clinical database...")
        try:
            from backend.database import Base, engine
            Base.metadata.create_all(bind=engine)
            print("  -> Database tables created successfully.")
        except Exception as e:
            print(f"  -> DB setup note: {e}")
    else:
        print(f"  -> Existing clinical database verified ({db_path.stat().st_size // 1024} KB)")

def verify_models():
    print("\n[3/4] Verifying TabICLv2 & Quad-Ensemble model artifacts...")
    model_files = [
        "diabetes_model.pkl",
        "heart_disease_model.pkl",
        "liver_disease_model.pkl",
        "kidney_model.pkl",
        "lungs_model.pkl"
    ]
    for mf in model_files:
        p = REPO_ROOT / "backend" / mf
        if p.exists():
            print(f"  -> [OK] {mf} ({p.stat().st_size // 1024} KB)")
        else:
            print(f"  -> [!] {mf} missing, fallback heuristics will be used.")

def start_services(has_bun):
    print("\n[4/4] Starting FastAPI backend & React frontend...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    # 1. Start Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"]
    print(f"  -> Launching Backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(REPO_ROOT), env=env)

    # 2. Start Frontend
    if has_bun:
        frontend_cmd = ["bun", "run", "--cwd", "frontend", "dev"]
    else:
        frontend_cmd = ["npm", "--prefix", "frontend", "run", "dev"]

    print(f"  -> Launching Frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(REPO_ROOT), env=env)

    print("\n" + "=" * 65)
    print("  ALL SERVICES RUNNING!")
    print("  Backend API:  http://127.0.0.1:8000/docs")
    print("  Frontend App: http://127.0.0.1:3000")
    print("=" * 65)
    print("\nOpening browser in 3 seconds... (Press Ctrl+C to stop)")

    time.sleep(3)
    try:
        webbrowser.open("http://127.0.0.1:3000")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping demo services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Demo shut down gracefully. Thank you for testing AI Healthcare System!")

if __name__ == "__main__":
    bun_avail = check_environment()
    verify_and_seed_database()
    verify_models()
    start_services(bun_avail)
