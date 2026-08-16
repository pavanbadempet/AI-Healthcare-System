import os

import requests

url = "https://dbc-3f46f628-dd14.cloud.databricks.com/api/2.1/jobs/update"
token = os.environ.get("DATABRICKS_TOKEN")
h = {"Authorization": f"Bearer {token}"}
p = {
    "job_id": 96157132607052,
    "new_settings": {
        "schedule": {
            "quartz_cron_expression": "0 0 0 * * ?",
            "timezone_id": "UTC",
            "pause_status": "PAUSED"
        }
    }
}
r = requests.post(url, headers=h, json=p)
print(r.status_code, r.text)
