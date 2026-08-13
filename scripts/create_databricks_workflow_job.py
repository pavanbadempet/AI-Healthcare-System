import os
import requests

DATABRICKS_INSTANCE = "https://dbc-3f46f628-dd14.cloud.databricks.com"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
}

def get_user_email():
    me_url = f"{DATABRICKS_INSTANCE}/api/2.0/preview/scim/v2/Me"
    me_response = requests.get(me_url, headers=HEADERS)
    if me_response.status_code == 200:
        return me_response.json().get("userName")
    return None

def create_medallion_job(user_email):
    url = f"{DATABRICKS_INSTANCE}/api/2.1/jobs/create"
    
    # We define a 3-task pipeline executing on a shared Serverless Job cluster for cost efficiency
    GIT_URL = "https://github.com/pavanbadempet/AI-Healthcare-System"
    
    payload = {
        "name": "⭐ AI Healthcare Medallion Pipeline (Bronze -> Silver -> Gold)",
        "git_source": {
            "git_url": GIT_URL,
            "git_provider": "gitHub",
            "git_branch": "main"
        },
        "schedule": {
            "quartz_cron_expression": "0 0 * * * ?", # Runs hourly
            "timezone_id": "UTC",
            "pause_status": "PAUSED" # Keep paused by default so it doesn't run up bills instantly
        },
        "tasks": [
            {
                "task_key": "step_01_bronze_ingest",
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/01_bronze_ingest",
                    "source": "GIT"
                }
            },
            {
                "task_key": "step_02_silver_cleaning",
                "depends_on": [{"task_key": "step_01_bronze_ingest"}],
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/02_silver_cleaning",
                    "source": "GIT"
                }
            },
            {
                "task_key": "step_03_gold_aggregations",
                "depends_on": [{"task_key": "step_02_silver_cleaning"}],
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/03_gold_aggregations",
                    "source": "GIT"
                }
            },
            {
                "task_key": "step_04_gpu_risk_scoring",
                "depends_on": [{"task_key": "step_03_gold_aggregations"}],
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/04_gpu_risk_scoring",
                    "source": "GIT"
                }
            },
            {
                "task_key": "step_05_export_to_neon",
                "depends_on": [{"task_key": "step_04_gpu_risk_scoring"}],
                "notebook_task": {
                    "notebook_path": "databricks_notebooks/05_export_to_neon",
                    "source": "GIT"
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            job_id = response.json().get("job_id")
            print(f"[SUCCESS] Created Databricks Workflow Job ID: {job_id}")
            print(f"You can view your job here: {DATABRICKS_INSTANCE}/#job/{job_id}")
            
            # Optional: trigger a run now
            run_res = requests.post(f"{DATABRICKS_INSTANCE}/api/2.1/jobs/run-now", headers=HEADERS, json={"job_id": job_id})
            if run_res.status_code == 200:
                print(f"[SUCCESS] Triggered initial pipeline run! Run ID: {run_res.json().get('run_id')}")
        else:
            print(f"[ERROR] Failed to create job: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] SSL/Network error creating job: {e}")

if __name__ == "__main__":
    email = get_user_email()
    if not email:
        print("[ERROR] Could not fetch Databricks user email. Check token and network.")
    else:
        print(f"Creating Workflow Job mapped to notebooks in /Workspace/Users/{email}/AI_Healthcare_Medallion/")
        create_medallion_job(email)
