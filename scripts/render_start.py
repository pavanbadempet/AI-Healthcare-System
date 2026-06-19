import sys
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.getenv("PORT", "10000"))
LOG_FILE = "startup.log"

print(f"Starting wrapper script on port {PORT}...")

# Start uvicorn and redirect stdout/stderr to LOG_FILE
log_handle = open(LOG_FILE, "w", buffering=1)
process = subprocess.Popen(
    ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", str(PORT)],
    stdout=log_handle,
    stderr=log_handle
)

# Wait 15 seconds to see if it crashes (give it time to connect/initialize)
time.sleep(15)

# Check if the process is still running
status = process.poll()
if status is not None:
    # Process has exited (crashed!)
    print(f"Uvicorn crashed with exit code {status}. Serving crash logs...")
    log_handle.close()
    
    # Read the logs
    with open(LOG_FILE, "r") as f:
        crash_logs = f.read()
        
    class CrashHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Uvicorn crashed with exit code {status}.\n\nLogs:\n{crash_logs}".encode())
            
    server = HTTPServer(("0.0.0.0", PORT), CrashHandler)
    server.serve_forever()
else:
    print("Uvicorn started successfully and is still running. Streaming logs to stdout...")
    log_handle.close()
    
    # Just print the log file to stdout and then wait
    with open(LOG_FILE, "r") as f:
        print(f.read())
        
    # Wait for the process to finish
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
