import requests
import os
url = "https://dbc-3f46f628-dd14.cloud.databricks.com/api/2.1/jobs/runs/export?run_id=800186599180777"
token = os.environ.get("DATABRICKS_TOKEN")
h = {"Authorization": f"Bearer {token}"}
r = requests.get(url, headers=h)
print(r.json().get("views", [{}])[0].get("content", "No content"))
