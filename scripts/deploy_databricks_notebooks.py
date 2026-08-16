import base64
import os

import requests

DATABRICKS_INSTANCE = "https://dbc-3f46f628-dd14.cloud.databricks.com"
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
}

NOTEBOOK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "databricks_notebooks")

def get_user_email():
    me_url = f"{DATABRICKS_INSTANCE}/api/2.0/preview/scim/v2/Me"
    me_response = requests.get(me_url, headers=HEADERS)
    if me_response.status_code == 200:
        return me_response.json().get("userName")
    return None

def upload_notebook(local_path, user_email):
    url = f"{DATABRICKS_INSTANCE}/api/2.0/workspace/import"

    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()

    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    filename = os.path.basename(local_path).replace(".py", "")
    databricks_path = f"/Workspace/Users/{user_email}/AI_Healthcare_Medallion/{filename}"

    payload = {
        "path": databricks_path,
        "format": "SOURCE",
        "language": "PYTHON",
        "content": content_b64,
        "overwrite": True
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            print(f"[SUCCESS] Deployed {filename} to {databricks_path}")
        else:
            print(f"[ERROR] Failed to deploy {filename}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] SSL/Network error deploying {filename}: {e}")

if __name__ == "__main__":
    email = get_user_email()
    if not email:
        print("[ERROR] Could not fetch Databricks user email. Check token and network.")
    else:
        folder_path = f"/Workspace/Users/{email}/AI_Healthcare_Medallion"
        print(f"Deploying Medallion Notebooks to {folder_path}/")

        # Create folder
        requests.post(f"{DATABRICKS_INSTANCE}/api/2.0/workspace/mkdirs", headers=HEADERS, json={"path": folder_path})

        # Ensure the directory exists by uploading files into it
        for file in sorted(os.listdir(NOTEBOOK_DIR)):
            if file.endswith(".py"):
                upload_notebook(os.path.join(NOTEBOOK_DIR, file), email)
