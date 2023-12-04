import subprocess
import time
import sys
import os
import threading

def stream_reader(pipe, prefix):
    for line in iter(pipe.readline, b''):
        print(f"[{prefix}] {line.decode().strip()}", flush=True)

def start_services():
    print("Cleaning ports manually done...")
    # subprocess.run('taskkill /F /IM python.exe /T', shell=True, stderr=subprocess.DEVNULL)
    
    print("=== STARTING BACKEND ===")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    threading.Thread(target=stream_reader, args=(backend.stdout, "BACKEND_OUT"), daemon=True).start()
    threading.Thread(target=stream_reader, args=(backend.stderr, "BACKEND_ERR"), daemon=True).start()
    
    time.sleep(10)
    if backend.poll() is not None:
        print("BACKEND DEAD.")
        return

    print("=== STARTING FRONTEND ===")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    threading.Thread(target=stream_reader, args=(frontend.stdout, "FRONTEND_OUT"), daemon=True).start()
    threading.Thread(target=stream_reader, args=(frontend.stderr, "FRONTEND_ERR"), daemon=True).start()

    time.sleep(15)
    
    print("FINISHED. Terminating...")
    backend.terminate()
    frontend.terminate()

if __name__ == "__main__":
    start_services()
