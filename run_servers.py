import os
import shutil
import subprocess
import sys
import threading
import time


def log_stream(proc, prefix):
    try:
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            print(f"{prefix} {line.strip()}")
    except Exception:
        pass

def run():
    print("=" * 60)
    print("  AI Healthcare System - Concurrent Services Runner")
    print("=" * 60)
    print("[INFO] Starting all services concurrently...")

    is_prod = (
        os.getenv("ENV", "").strip().lower() in {"production", "prod"}
        or os.getenv("ENVIRONMENT", "").strip().lower() in {"production", "prod"}
        or "--prod" in sys.argv
        or "-p" in sys.argv
    )

    # Start Backend
    if is_prod:
        print("[INFO] Production Mode Detected: Starting Pure Rust Gateway on http://127.0.0.1:8000 ...")
        rust_binary = os.path.join(
            "rust_gateway", "target", "release", "rust_gateway.exe" if os.name == "nt" else "rust_gateway"
        )
        if os.path.exists(rust_binary):
            backend_cmd = [rust_binary]
        else:
            backend_cmd = ["cargo", "run", "--release", "--manifest-path", "rust_gateway/Cargo.toml", "--bin", "rust_gateway"]
    else:
        print("[INFO] Development Mode: Starting Backend (FastAPI / Dev Spec) on http://127.0.0.1:8000 ...")
        backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]

    backend_proc = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        errors="ignore"
    )

    # Start Frontend
    print("[INFO] Starting Frontend (Bun + Vite) on http://127.0.0.1:3000 ...")
    if shutil.which("bun"):
        frontend_runner = "bun.cmd" if os.name == "nt" else "bun"
    else:
        frontend_runner = "npm.cmd" if os.name == "nt" else "npm"

    frontend_cmd = [frontend_runner, "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=os.path.join(os.getcwd(), "frontend"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        errors="ignore"
    )

    # Spawn threads to read output streams in real-time
    t1 = threading.Thread(target=log_stream, args=(backend_proc, "\033[96m[Backend]\033[0m"))
    t2 = threading.Thread(target=log_stream, args=(frontend_proc, "\033[92m[Frontend]\033[0m"))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()

    print("[OK] Services initiated. Press Ctrl+C to terminate both servers.")
    print("-" * 60)

    try:
        while True:
            # Check if either process died unexpectedly
            if backend_proc.poll() is not None:
                print(f"\n[FATAL] Backend exited unexpectedly with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"\n[FATAL] Frontend exited unexpectedly with code {frontend_proc.returncode}")
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Termination requested. Stopping services...")
    finally:
        # Graceful shutdown
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            print("[WARN] Force killing processes that did not exit in time...")
            backend_proc.kill()
            frontend_proc.kill()
        print("[OK] Both services stopped successfully.")

if __name__ == "__main__":
    run()
