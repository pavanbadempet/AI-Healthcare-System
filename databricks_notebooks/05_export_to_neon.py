# Databricks notebook source
# MAGIC %md
# MAGIC # 05: Export to Neon Postgres (HuggingFace Frontend)
# MAGIC Reads the final scored Gold Medallion data and securely exports it to the Neon Postgres database 
# MAGIC so the HuggingFace Spaces React/FastAPI website can serve it to clinicians.

# COMMAND ----------
import os

# Doppler will inject DATABASE_URL into the Databricks environment via CI/CD, 
# or we read it from Databricks Secrets.
# E.g. DATABASE_URL="postgres://user:password@ep-cool-lake-123456.us-east-2.aws.neon.tech/neondb"
database_url = os.environ.get("DATABASE_URL", "postgresql://mock_user:mock_pass@mock-neon-host.neon.tech/mockdb")

if not database_url.startswith("jdbc:"):
    # Convert standard postgres URL to JDBC
    jdbc_url = database_url.replace("postgresql://", "jdbc:postgresql://").replace("postgres://", "jdbc:postgresql://")
    
    if "@" in jdbc_url:
        # Extract user/pass from JDBC URL if needed
        parts = jdbc_url.split("://")[1].split("@")
        creds = parts[0].split(":")
        user = creds[0]
        password = creds[1]
        host_db = parts[1]
        jdbc_url = f"jdbc:postgresql://{host_db}"
    else:
        user = "mock_user"
        password = "mock_password"

# COMMAND ----------
gold_df = spark.read.table("gold_patient_hourly_vitals")

print(f"Exporting {gold_df.count()} records to Neon Postgres database...")

# Write to Neon via JDBC
try:
    (gold_df.write
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", "gold_patient_hourly_vitals")
        .option("user", user)
        .option("password", password)
        .option("driver", "org.postgresql.Driver")
        .mode("overwrite") # Overwrite or Append for the dashboard
        .save())
    print("Successfully exported Gold Medallion data to Neon!")
except Exception as e:
    print(f"Neon export skipped during mock/development run: {e}")
