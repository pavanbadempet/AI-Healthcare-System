import os
import requests

DATABRICKS_INSTANCE = "https://dbc-3f46f628-dd14.cloud.databricks.com"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
}

def run_debug():
    url = f"{DATABRICKS_INSTANCE}/api/2.1/jobs/runs/submit"
    
    payload = {
        "run_name": "Debug Volumes",
        "git_source": {
            "git_url": "https://github.com/pavanbadempet/AI-Healthcare-System",
            "git_provider": "gitHub",
            "git_branch": "main"
        },
        "tasks": [
            {
                "task_key": "debug",
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/debug",
                    "source": "GIT"
                }
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        run_id = response.json().get("run_id")
        print(f"Triggered run: {run_id}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    run_debug()
