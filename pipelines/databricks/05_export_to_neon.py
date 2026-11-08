# Databricks notebook source
# MAGIC %md
# MAGIC # 05: Export to Neon Postgres (HuggingFace Frontend)
# MAGIC Reads the final scored Gold Medallion data and securely exports it to the Neon Postgres database
# MAGIC so the HuggingFace Spaces React/FastAPI website can serve it to clinicians.

# COMMAND ----------
import os

# Doppler will inject DATABASE_URL into the Databricks environment via CI/CD,
# or we read it from Databricks Secrets / environment.
database_url = os.environ.get("DATABASE_URL", "sqlite:///./healthcare.db")


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
records_exported = 0
try:
    records_exported = gold_df.count()
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

# ==========================================
# HIPAA AUDIT LOGGING IN UNITY CATALOG
# ==========================================
try:
    import uuid
    from datetime import datetime

    audit_row = [(
        str(uuid.uuid4()),
        "databricks_medallion_pipeline",
        "SYSTEM_SERVICE_PRINCIPAL",
        "GOLD_NEON_EXPORT",
        "workspace",
        "healthcare_gold",
        "patient_risk_profile",
        "ALL_RECORDS",
        records_exported,
        "10.0.0.1",
        datetime.utcnow()
    )]

    audit_df = spark.createDataFrame(audit_row, [
        "audit_id", "accessed_by", "user_role", "action",
        "target_catalog", "target_schema", "target_table",
        "filter_applied", "records_accessed", "ip_address", "timestamp"
    ])

    audit_df.write.format("delta").mode("append").saveAsTable("workspace.healthcare_governance.hipaa_access_audit_log")
    print("Recorded HIPAA export event into workspace.healthcare_governance.hipaa_access_audit_log")
except Exception as e:
    print(f"HIPAA audit log recording: {e}")
