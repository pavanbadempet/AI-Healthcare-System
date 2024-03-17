
import os
import sys
import time
import socket
import logging
import subprocess
import threading
import requests
from pathlib import Path

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("PreDeploy")

ROOT_DIR = Path(__file__).parent.parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"

def check_dependencies():
    logger.info("[CHECK] Checking Dependencies...")
    try:
        import joblib
        import fastapi
        import uvicorn
        logger.info("   [OK] Critical packages (joblib, fastapi, uvicorn) found.")
    except ImportError as e:
        logger.error(f"   [FAIL] Missing dependency: {e}")
        return False
    return True

def check_models():
    logger.info("[CHECK] Checking AI Models...")
    models = ["diabetes_model.pkl", "heart_disease_model.pkl"]
    missing = []
    for m in models:
        p = BACKEND_DIR / m
        if not p.exists():
            missing.append(m)
        else:
            size_mb = p.stat().st_size / (1024 * 1024)
            logger.info(f"   [OK] {m} found ({size_mb:.2f} MB)")
    
    if missing:
        logger.error(f"   [FAIL] Missing models: {missing}")
        return False
    return True

def check_app_imports():
    logger.info("[CHECK] Checking App Imports (Static Smoke Test)...")
    sys.path.append(str(ROOT_DIR))
    try:
        from backend import main
        from backend import prediction
        logger.info("   [OK] Backend modules imported successfully.")
        return True
    except ImportError as e:
        logger.error(f"   [FAIL] Import Error: {e}")
        return False
    except Exception as e:
        logger.error(f"   [FAIL] Unexpected Error during import: {e}")
        return False

def run_checks():
    print("="*40)
    print("=== AIO HEALTHCARE PRE-DEPLOY CHECK ===")
    print("="*40)
    
    checks = [
        check_dependencies,
        check_models,
        check_app_imports
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
            print("\n[X] One or more checks failed. Fix issues before pushing.")
            break # Stop on first failure
            
    if all_passed:
        print("\n[V] ALL SYSTEM CHECKS PASSED. Ready for Deployment!")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_checks()
