import os
import queue
import logging
import threading
from datetime import datetime, timezone
import requests

class AxiomHandler(logging.Handler):
    """
    Thread-safe asynchronous log handler for Axiom.co ingestion API.
    Batches logs in a background thread and streams them to prevent blocking the web app.
    """
    def __init__(self, token: str, dataset: str):
        super().__init__()
        self.token = token
        self.dataset = dataset
        self.url = f"https://api.axiom.co/v1/datasets/{dataset}/ingest"
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Start background worker thread
        self.worker = threading.Thread(target=self._worker_loop, daemon=True, name="AxiomLoggerThread")
        self.worker.start()

    def emit(self, record):
        try:
            # Format time as ISO-8601 UTC string
            dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
            log_entry = {
                "_time": dt.isoformat(),
                "message": self.format(record),
                "level": record.levelname,
                "logger": record.name,
                "module": record.module,
                "line": record.lineno,
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            self.queue.put(log_entry)
        except Exception:
            self.handleError(record)

    def _worker_loop(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        while not self.stop_event.is_set():
            batch = []
            try:
                # Retrieve all currently queued logs up to a batch size of 50
                while len(batch) < 50:
                    # Timeout of 2.0s ensures frequent flushes
                    item = self.queue.get(timeout=2.0)
                    batch.append(item)
                    self.queue.task_done()
            except queue.Empty:
                pass
            
            if batch:
                try:
                    # Send logs using synchronous requests inside background daemon thread
                    response = requests.post(self.url, json=batch, headers=headers, timeout=5.0)
                    if response.status_code not in (200, 201):
                        print(f"[AxiomLogger Warning] Failed ingestion (status {response.status_code}): {response.text}", flush=True)
                except Exception as e:
                    print(f"[AxiomLogger Error] Connection failed: {e}", flush=True)


def setup_axiom_logging():
    """Dynamically integrates Axiom logging handler if configuration variables exist in the environment."""
    token = os.environ.get("AXIOM_TOKEN")
    dataset = os.environ.get("AXIOM_DATASET")
    
    if token and dataset:
        try:
            axiom_handler = AxiomHandler(token=token, dataset=dataset)
            # Use basic formatting
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            axiom_handler.setFormatter(formatter)
            axiom_handler.setLevel(logging.INFO)
            
            # Attach to the root logger so it captures logs from all backend modules
            root_logger = logging.getLogger()
            root_logger.addHandler(axiom_handler)
            logging.getLogger(__name__).info("Successfully registered Axiom logging handler.")
        except Exception as e:
            print(f"[AxiomLogger Setup Error] {e}", flush=True)
