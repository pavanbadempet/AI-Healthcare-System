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
    # try:
    #    subprocess.run('taskkill /F /IM python.exe /T', shell=True, stderr=subprocess.DEVNULL)
    # except: pass
    
    print("=== STARTING BACKEND ===")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    threading.Thread(target=stream_reader, args=(backend.stdout, "BACKEND_OUT"), daemon=True).start()
    threading.Thread(target=stream_reader, args=(backend.stderr, "BACKEND_ERR"), daemon=True).start()
    
    time.sleep(15) 
    
    print("=== STARTING NICEGUI FRONTEND (8080) ===")
    frontend = subprocess.Popen(
        [sys.executable, "main_nicegui.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    threading.Thread(target=stream_reader, args=(frontend.stdout, "FRONTEND_OUT"), daemon=True).start()
    threading.Thread(target=stream_reader, args=(frontend.stderr, "FRONTEND_ERR"), daemon=True).start()

    time.sleep(5)
    
    print("SYSTEM READY FOR TEST.")
    time.sleep(300)
    
    backend.terminate()
    frontend.terminate()

if __name__ == "__main__":
    start_services()
