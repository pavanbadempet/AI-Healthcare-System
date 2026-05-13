# 18 — Resume Line-by-Line Defense

> For EVERY single bullet point on your resume, here's the detailed answer when they ask "Tell me more about this."

---

## PROFESSIONAL SUMMARY

**Resume says**: "Data Engineer with 2+ years of experience building scalable ETL/ELT data pipelines using Python, SQL, and Spark across AWS and on-prem environments."

**If asked "What do you mean by scalable?"**
> "Scalable means the pipeline can handle 10x data without rewriting code. For example, at Nomura, our Spark jobs processed daily trade feeds that could range from 100K to 5M records depending on market activity. The pipeline handled both without changes because Spark's partitioning and dynamic allocation scaled the compute automatically. I also used partition pruning so queries on specific dates don't scan the entire dataset."

**If asked "ETL vs ELT — what's the difference and which do you use?"**
> - **ETL** (Extract, Transform, Load): Transform data BEFORE loading into target. Used at Nomura — Spark transforms trade data, then writes to destination.
> - **ELT** (Extract, Load, Transform): Load raw data first, transform inside the target (e.g., Snowflake). Used at Nissan — raw files loaded to Snowflake, then SQL transforms inside Snowflake.
> - I've done BOTH. ETL when the transformation is complex (multi-way joins, window functions). ELT when the target has powerful compute (Snowflake).

**If asked "What on-prem vs cloud experience?"**
> - **On-prem**: Nomura — YARN cluster with HDFS, later migrated to Kubernetes + MinIO
> - **Cloud**: Nissan — AWS Lambda, Step Functions, S3, CloudWatch, Snowflake

---

## EXPERIENCE — NOMURA CAPITAL

### Bullet 1: "Engineered and maintained large-scale Spark ETL pipelines using Spark SQL..."

**If asked "How large-scale? Give me numbers."**
> "The capital markets datasets included daily trade feeds (hundreds of thousands of records per day), reference data tables (instrument master, counterparty master — millions of rows), risk feeds, and valuation feeds. We processed these through multi-way joins — a typical pipeline would join trade facts to 4-5 dimension tables (instrument, counterparty, book, date, currency) using star schema patterns."

**If asked "What kind of SQL queries?"**
```sql
-- Example: Daily P&L calculation with window functions
SELECT 
    t.trade_date,
    t.instrument_id,
    i.instrument_name,
    t.trade_amount,
    SUM(t.trade_amount) OVER (
        PARTITION BY t.instrument_id 
        ORDER BY t.trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_pnl,
    LAG(t.trade_amount) OVER (
        PARTITION BY t.instrument_id 
        ORDER BY t.trade_date
    ) AS prev_day_amount,
    t.trade_amount - LAG(t.trade_amount) OVER (
        PARTITION BY t.instrument_id 
        ORDER BY t.trade_date
    ) AS day_over_day_change
FROM trades t
JOIN instruments i ON t.instrument_id = i.id
JOIN counterparties c ON t.counterparty_id = c.id
WHERE t.trade_date >= '2024-01-01'
```

**If asked "What window functions did you use?"**
> - `ROW_NUMBER()` — Deduplication (keep latest record per key)
> - `LAG/LEAD` — Day-over-day comparisons
> - `SUM/AVG OVER` — Running totals, moving averages
> - `RANK/DENSE_RANK` — Top-N per group (top 5 trades per instrument)
> - `FIRST_VALUE/LAST_VALUE` — First/last trade per day

---

### Bullet 2: "Analyzed Spark execution metrics to improve execution time by 30%..."

**If asked "Walk me through the debugging process."**
> 1. **Spark UI → SQL tab**: Identified slow stages with high shuffle read/write
> 2. **Execution plan**: `EXPLAIN EXTENDED` showed hash joins where broadcast was possible
> 3. **Stage timeline**: One stage was 10x slower than others — classic skew
> 4. **GC metrics**: Executors were spending 20% time in garbage collection — too much data in memory
>
> **Fixes applied:**
> - Broadcast joins for dimension tables < 100MB → eliminated shuffle
> - Partition pruning via `trade_date` column → skipped 90% of data
> - Predicate pushdown to Parquet reader → fewer row groups scanned
> - Intermediate Parquet checkpoints → prevented recomputation
> - `spark.sql.adaptive.enabled=true` → auto-coalesce small partitions

**If asked "How do you measure 30%?"**
> "Compared wall-clock execution time of the same pipeline on the same data before and after optimizations. A job that took 45 minutes consistently ran in 31 minutes after — a 31% improvement."

---

### Bullet 3: "Orchestrated Spark workflows using AutoSys..."

**If asked "How is AutoSys different from Airflow?"**

| | AutoSys | Airflow |
|---|---|---|
| Type | Enterprise job scheduler | Open-source workflow orchestrator |
| Used by | Banks, large enterprises | Tech companies, startups |
| DAG definition | JIL (Job Information Language) | Python |
| Monitoring | AutoSys console | Airflow web UI |
| Strengths | Proven in finance, compliance-ready | Flexible, extensible, free |

> "AutoSys is the standard at banks like Nomura because it has enterprise support, audit trails, and compliance features that Airflow doesn't have out of the box. But conceptually they solve the same problem: defining job dependencies, scheduling, retries, and alerting."

---

### Bullet 4: "Executed migration of Spark workloads from YARN to Kubernetes..."

**If asked "What specific issues did you face?"**

> 1. **Spark connector JAR hell**: YARN had Hadoop JARs pre-installed. K8s needed explicit `spark-hadoop-aws` and `hadoop-aws` JARs in the Docker image.
>
> 2. **S3A configuration**: MinIO uses S3-compatible API but needs:
>    ```
>    spark.hadoop.fs.s3a.endpoint=http://minio:9000
>    spark.hadoop.fs.s3a.access.key=XXXX
>    spark.hadoop.fs.s3a.secret.key=XXXX
>    spark.hadoop.fs.s3a.path.style.access=true  # Required for MinIO
>    ```
>
> 3. **Resource management**: YARN's memory model (on-heap + off-heap) → K8s resource requests/limits. Had to tune:
>    ```
>    spark.kubernetes.executor.request.cores=2
>    spark.kubernetes.executor.limit.cores=4
>    spark.executor.memory=4g
>    ```
>
> 4. **Dynamic allocation**: YARN natively supports dynamic executor allocation. K8s needs `spark.dynamicAllocation.enabled=true` with `spark.dynamicAllocation.shuffleTracking.enabled=true`.

---

### Bullet 5 (Nissan): "Architected daily batch pipelines using AWS Lambda and Step Functions..."

**If asked "Why Lambda instead of EC2 or ECS?"**
> - **Lambda**: Serverless, zero infrastructure management, pay-per-invocation. Perfect for batch ETL that runs once daily for a few minutes. Cost: ~$0.50/month vs $30+/month for EC2.
> - **When NOT to use Lambda**: Long-running jobs (>15 min timeout), jobs needing >10GB RAM, or persistent compute.

**If asked "How does Step Functions orchestrate?"**
```json
{
  "StartAt": "ValidateSchema",
  "States": {
    "ValidateSchema": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:validate_schema",
      "Next": "TransformData",
      "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3}]
    },
    "TransformData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:transform",
      "Next": "QualityChecks"
    },
    "QualityChecks": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:quality_check",
      "Next": "LoadToSnowflake",
      "Catch": [{"ErrorEquals": ["QualityError"], "Next": "AlertAndFail"}]
    },
    "LoadToSnowflake": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:load",
      "End": true
    },
    "AlertAndFail": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:send_alert",
      "End": true
    }
  }
}
```

---

### Bullet 6: "Implemented schema validation, data quality checks, and incremental batch processing..."

**If asked "What quality checks exactly?"**
```python
def quality_checks(df: pd.DataFrame) -> dict:
    checks = {
        "row_count": len(df),
        "null_pct": df.isnull().mean().to_dict(),       # Null % per column
        "duplicate_count": df.duplicated().sum(),         # Exact duplicates
        "schema_match": set(df.columns) == EXPECTED_COLS,# Column names match
        "range_checks": {
            "amount": df["amount"].between(0, 1e9).all(),  # No negative/extreme
            "date": pd.to_datetime(df["date"]).notna().all(), # Valid dates
        },
        "referential_integrity": df["instrument_id"].isin(valid_instruments).all()
    }
    
    # Fail if critical checks fail
    if checks["null_pct"]["instrument_id"] > 0.01:  # >1% null IDs = fail
        raise QualityError("Too many null instrument IDs")
    
    return checks
```

**If asked "What's incremental processing?"**
> "Instead of processing ALL historical data every day, I only process new/changed records:
> ```python
> # Get the last processed timestamp
> last_run = get_last_watermark()  # e.g., '2024-06-14 23:00:00'
> 
> # Query only new records
> new_data = source.query(f"WHERE modified_at > '{last_run}'")
> 
> # Process only the delta
> transform_and_load(new_data)
> 
> # Update watermark
> set_watermark(datetime.now())
> ```
> This reduced processing time from 2 hours (full) to 10 minutes (incremental)."

---

## EXPERIENCE — TCS iON INTERNSHIP

**If asked "What model did you build?"**
> "An ensemble attrition prediction model — combining Random Forest, Gradient Boosting, and Logistic Regression with a voting classifier. Achieved 86% accuracy on validation data. The FastAPI service I built exposed it as a REST endpoint for HR teams to check attrition risk per employee."

---

## PROJECTS SECTION

### Healthcare: "Built automated ETL pipelines processing 250k+ records..."

**If asked "What's the ETL pipeline?"**
> 1. **Extract**: Download BRFSS 2015 CDC CSV from Kaggle
> 2. **Transform**: 
>    - Rename columns (HighBP → hypertension, HighChol → high_chol)
>    - Convert age to buckets (18-24 → 1, 25-29 → 2, ...)
>    - Handle class imbalance (scale_pos_weight=6.16)
>    - Train/test split (80/20)
> 3. **Load**: Train XGBoost model, save as .pkl file, load at API startup

### Movie Rec: "Built end-to-end recommendation pipeline processing 1M+ movie records..."

**If asked "What's the pipeline?"**
> 1. **Extract**: TMDB/Kaggle movie dataset (1M+ records)
> 2. **Transform** (PySpark): 
>    - Schema validation and null handling
>    - Feature engineering (content_quality_score, metadata_completeness)
>    - Quarantine bad records
>    - Delta Lake: Bronze → Silver → Gold
> 3. **Load**: 
>    - SBERT embeddings → FAISS vector index
>    - Parquet serving artifacts
>    - Publish to HuggingFace for deployment

---

## EDUCATION

**If asked about the PM Scholarship:**
> "The Prime Minister's Scholarship is a merit-based scholarship awarded by the Government of India. I received it for all 4 years of my B.Tech (2019-2023) based on academic performance."

**If asked "What's your minor in AI/ML?"**
> "My B.Tech was Computer Science with a minor specialization in AI/ML. I took additional courses in Machine Learning, Deep Learning, NLP, and Data Mining — which gave me the theoretical foundation for the ML work in my projects."

---

## SKILLS SECTION

**If asked "Rate yourself on each skill 1-10":**

| Skill | Rating | Justification |
|---|---|---|
| Python | 8/10 | Daily use for 2+ years, ETL + API + ML |
| SQL | 8/10 | Complex analytical queries, window functions, CTEs |
| Spark/PySpark | 7/10 | Daily at Nomura, optimized 30%, YARN→K8s migration |
| Scala | 5/10 | Can read/modify, not primary language |
| Java | 5/10 | Academic, basic proficiency |
| AWS | 7/10 | Lambda, Step Functions, S3, CloudWatch, Glue |
| Docker | 7/10 | Containerized apps, Docker Compose |
| FastAPI | 8/10 | Built 2 production APIs from scratch |
| Git | 8/10 | Daily use, branching, PRs |
| Snowflake | 6/10 | Data loading, SQL queries, schema design |
