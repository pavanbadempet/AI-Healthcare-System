import requests
import os
url = "https://dbc-3f46f628-dd14.cloud.databricks.com/api/2.1/jobs/runs/get-output?run_id=472696313200554"
token = os.environ.get("DATABRICKS_TOKEN")
h = {"Authorization": f"Bearer {token}"}
r = requests.get(url, headers=h)
data = r.json()
print("OUTPUT KEYS:", data.keys())
if "error" in data:
    print("ERROR:", data["error"])
if "metadata" in data:
    print("METADATA:", data["metadata"])
if "error_trace" in data:
    print("ERROR TRACE:")
    print(data["error_trace"])
