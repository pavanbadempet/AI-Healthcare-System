# Cloud Retraining Guide — 100% Free Cloud Execution

To avoid using any of your local computer's memory or CPU, this pipeline is designed to run **entirely in the cloud** for free. You do not need to install Java, Spark, or run any heavy processes locally.

Here are the three ways to run the retraining pipeline in the cloud:

---

## Option 1: GitHub Actions (Fully Automated)
This is already configured in your repository and runs on GitHub's hosted virtual machines (completely free, up to 2000 minutes/month).

### How to trigger it:
1. Go to your repository on GitHub.
2. Click on the **Actions** tab.
3. In the left sidebar, click on **Weekly PySpark ETL & ML Retraining**.
4. Click the **Run workflow** dropdown on the right side and click the green **Run workflow** button.
5. The job will run completely in the cloud, retrain the models, commit the new weights back to the branch, and redeploy them to your Hugging Face Space.

---

## Option 2: Google Colab (One-Click Interactive)
You can run the entire pipeline interactively in your browser using Google's free cloud resources (up to 12.7 GB RAM and free GPUs).

### Step-by-Step:
1. Open [Google Colab](https://colab.research.google.com/).
2. Create a new notebook.
3. Paste the following code into a code cell, configure your database credentials, and click **Run**:

```python
# 1. Clone the repository
!git clone https://github.com/pavanbadempet/AI-Healthcare-System.git

# 2. Install required dependencies in the Colab container
!pip install pyspark delta-spark xgboost scikit-learn pandas sqlalchemy psycopg2-binary requests

# 3. Set your credentials (replace with your Neon/Supabase Postgres credentials)
import os
os.environ["DATABASE_URL"] = "postgresql://user:password@host:port/dbname"
os.environ["BACKEND_URL"] = "https://pavanbadempet-ai-healthcare-system.hf.space"
os.environ["ADMIN_JWT_TOKEN"] = "your_admin_jwt_token" # (optional, for reloading models on the fly)

# 4. Run the PySpark ETL & Retraining pipeline
!python AI-Healthcare-System/scripts/runners/run_spark_etl.py
```

---

## Option 3: Kaggle Notebooks (High Performance)
Kaggle provides 30 hours of free GPU per week and unlimited CPU kernels with 30 GB of RAM.

### Step-by-Step:
1. Go to [Kaggle](https://www.kaggle.com/) and click **Create** -> **New Notebook**.
2. In the right-hand panel, under **Notebook options**, ensure **Internet** is toggled ON.
3. Paste the same Google Colab code block above into a Kaggle cell and click **Run All**.
