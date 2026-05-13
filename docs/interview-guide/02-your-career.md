# 17 â€” Data Engineer Interview Guide (Your Primary Role)

> **Your positioning**: Data Engineer with 2+ years at TCS (Nomura Capital, Nissan), who ALSO builds AI systems.
> This file reframes EVERYTHING through the Data Engineering lens that matches your resume.

---

## YOUR CAREER NARRATIVE (Memorize This)

### 30-Second Pitch:
> "I'm a Data Engineer with 2+ years at TCS, where I've built large-scale Spark ETL pipelines for Nomura Capital â€” processing capital markets data (trades, risk, valuations) â€” and architected serverless batch pipelines for Nissan using AWS Lambda and Step Functions. I've optimized Spark execution time by 30% through broadcast joins and partition pruning, and led the migration from YARN to Kubernetes. On the AI side, I've built two full-stack projects: a healthcare prediction system with XGBoost on 253K CDC records, and a recommendation platform with FAISS vector search and Delta Lake pipelines on 1M+ movie records. I combine strong data engineering fundamentals with practical AI/ML skills."

### Why This Narrative Works:
1. **Leads with professional experience** (TCS, Nomura, Nissan)
2. **Shows Spark depth** (the #1 DE skill)
3. **Shows cloud skills** (AWS, K8s)
4. **AI as differentiator** (not everyone has this)
5. **Numbers** (2 years, 30%, 253K, 1M+)

---

## SECTION 1: TCS / NOMURA CAPITAL QUESTIONS

### Q: Describe your work at Nomura Capital.

> "I engineered and maintained large-scale Spark ETL pipelines for capital markets datasets at Nomura. The data included trade feeds, reference data, risk feeds, and valuation feeds. I used Spark SQL with complex analytical queries â€” multi-way joins between fact and dimension tables, window functions for running calculations, and aggregations for downstream risk analytics and reporting."

### Q: How did you achieve the 30% execution time improvement?

> I analyzed Spark execution metrics and applied 5 optimization techniques:
>
> 1. **Broadcast joins**: Small reference/dimension tables (<100MB) were broadcast to all executors instead of shuffled. This eliminated expensive shuffle operations for fact-dimension joins.
>    ```sql
>    -- Before: shuffle join (slow)
>    SELECT * FROM trades t JOIN ref_data r ON t.instrument_id = r.id
>    
>    -- After: broadcast join (fast)
>    SELECT /*+ BROADCAST(r) */ * FROM trades t JOIN ref_data r ON t.instrument_id = r.id
>    ```
>
> 2. **Partition pruning**: Data was partitioned by trade_date. Queries that filter by date now skip irrelevant partitions entirely.
>    ```python
>    df = spark.read.parquet("s3://data/trades/").filter(F.col("trade_date") >= "2024-01-01")
>    # Spark reads only January+ partitions, not the entire dataset
>    ```
>
> 3. **Predicate pushdown**: Filters pushed down to the Parquet reader level â€” only relevant row groups are scanned.
>
> 4. **Intermediate Parquets**: Instead of one massive transformation, I broke the DAG into stages and persisted intermediate results as Parquet. This prevents recomputation on failure and allows checkpoint-resume.
>
> 5. **Optimized star schema joins**: Fact tables joined to dimensions in the correct order (smallest dimension first) to minimize shuffle size.

### Q: Explain the YARN to Kubernetes migration.

> We migrated Spark workloads from Hadoop YARN (on-prem cluster) to Kubernetes:
>
> **Why?** YARN was tied to HDFS. K8s gives us container orchestration, auto-scaling, and cloud-portable workloads.
>
> **Challenges:**
> - **Storage**: HDFS â†’ MinIO (S3-compatible). Had to update all Spark read/write paths from `hdfs://` to `s3a://`
> - **Spark connectors**: Needed `spark-hadoop-aws` JAR and correct `fs.s3a.*` configurations
> - **Resource management**: YARN's memory/CPU allocation â†’ K8s resource requests/limits
> - **Dynamic allocation**: YARN's dynamic executor allocation â†’ K8s pod autoscaling
>
> **Result**: Same Spark jobs, portable between on-prem MinIO and cloud S3.

### Q: How does AutoSys orchestration work?

> AutoSys is an enterprise job scheduler (like Airflow but for large enterprises). I used it to:
> - Define **dependency chains**: Job B starts only after Job A completes successfully
> - Handle **reruns**: Failed jobs can be re-triggered without re-running the entire chain
> - **Recovery logic**: On failure, send alert â†’ retry 3x â†’ escalate to on-call
> - **Scheduling**: Daily batch windows with SLA monitoring
>
> This reduced manual intervention by 25% â€” operators no longer needed to manually trigger dependent jobs.

### Q: Describe the Nissan project.

> Architected daily batch pipelines using **AWS Lambda** and **Step Functions**:
>
> ```
> S3 Upload â†’ Lambda (validate schema) â†’ Step Function (orchestrate)
>     â†’ Lambda (transform) â†’ Lambda (quality checks) â†’ Snowflake
> ```
>
> **Key features:**
> - **Idempotent re-runs**: Each run checks if data already exists for that date. Re-running won't create duplicates.
> - **Schema validation**: Incoming files validated against expected schema before processing
> - **Data quality checks**: Null counts, range checks, referential integrity
> - **Incremental processing**: Only process new/changed records, not the full dataset
> - **Streamlit interface**: Built for business users to trigger ad-hoc file ingestion and re-runs without touching code
>
> **Result**: Reduced manual effort by 60%, improved pipeline reliability via CloudWatch monitoring.

### Q: How did you implement idempotent re-runs?

> ```python
> def process_batch(date: str, data: DataFrame):
>     # Check if this date's data already exists
>     existing = snowflake.query(f"SELECT COUNT(*) FROM target WHERE batch_date = '{date}'")
>     
>     if existing > 0:
>         # DELETE existing data for this date (idempotent)
>         snowflake.execute(f"DELETE FROM target WHERE batch_date = '{date}'")
>     
>     # INSERT fresh data
>     data.write.mode("append").save("snowflake://target")
> ```
> This means running the same batch twice produces the same result â€” no duplicates, no data corruption.

---

## SECTION 2: SPARK DEEP-DIVE QUESTIONS

### Q: Explain Spark's execution model.

```
Driver Program
    â†“
Creates SparkContext
    â†“
Submits job DAG
    â†“
DAG Scheduler â†’ Stages (shuffle boundaries)
    â†“
Task Scheduler â†’ Tasks (per partition)
    â†“
Executor 1: [Task1, Task2, ...]
Executor 2: [Task3, Task4, ...]
Executor N: [TaskM, ...]
```

**Key concepts:**
- **Driver**: Orchestrates the job, builds DAG, collects results
- **Executor**: Worker process that runs tasks and caches data
- **Stage**: Set of tasks that can run without shuffle
- **Shuffle**: Data redistribution across executors (expensive)
- **Partition**: Unit of parallelism â€” each partition = one task

### Q: What causes a shuffle and how do you avoid it?

**Causes:** `groupBy`, `join`, `repartition`, `distinct`, `orderBy`

**Avoidance techniques:**
1. **Broadcast join** â€” Small table broadcast to all executors, no shuffle
2. **Partition-aligned joins** â€” Both tables partitioned by join key
3. **map-side aggregation** â€” `reduceByKey` instead of `groupByKey`
4. **Bucket joins** â€” Pre-bucket tables by join key during write

### Q: Difference between `repartition()` and `coalesce()`?

| | `repartition(n)` | `coalesce(n)` |
|---|---|---|
| Shuffle | Full shuffle | No shuffle (narrow dependency) |
| Can increase partitions? | Yes | No (only decrease) |
| Use when | Need specific number/hash | Reducing partitions after filter |
| Performance | Slower (shuffle) | Faster (no shuffle) |

### Q: Explain window functions with a real example.

```sql
-- Running total of trades per instrument
SELECT 
    trade_date,
    instrument_id,
    trade_amount,
    SUM(trade_amount) OVER (
        PARTITION BY instrument_id 
        ORDER BY trade_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total,
    ROW_NUMBER() OVER (
        PARTITION BY instrument_id 
        ORDER BY trade_date DESC
    ) AS recency_rank
FROM trades;
```

### Q: What is predicate pushdown?

> When Spark reads Parquet files, it pushes WHERE clause filters down to the file reader level. Parquet stores min/max statistics per row group. If a row group's max value is less than the filter value, the entire group is skipped without reading.
>
> ```python
> # Spark reads only row groups where trade_date >= 2024-01-01
> df = spark.read.parquet("trades.parquet").filter(F.col("trade_date") >= "2024-01-01")
> ```

### Q: How do you handle data skew?

> Data skew = one partition has much more data than others â†’ one executor takes much longer.
>
> **Detection**: Spark UI â†’ Stages tab â†’ check task duration variance
>
> **Solutions:**
> 1. **Salting**: Add random prefix to skewed key, join on salted key, then remove
> 2. **Broadcast join**: If one side is small enough
> 3. **Adaptive Query Execution (AQE)**: `spark.sql.adaptive.enabled=true` â€” Spark auto-coalesces small partitions
> 4. **Custom partitioning**: Repartition by a more evenly distributed column

---

## SECTION 3: SQL DEEP-DIVE

### Q: Write a query to find the top 3 trades per instrument by amount.

```sql
WITH ranked AS (
    SELECT 
        instrument_id,
        trade_amount,
        trade_date,
        ROW_NUMBER() OVER (
            PARTITION BY instrument_id 
            ORDER BY trade_amount DESC
        ) AS rn
    FROM trades
)
SELECT * FROM ranked WHERE rn <= 3;
```

### Q: Explain the difference between star schema and snowflake schema.

| | Star Schema | Snowflake Schema |
|---|---|---|
| Dimensions | Denormalized (flat) | Normalized (sub-dimensions) |
| Joins | Fewer (fact + dims) | More (fact + dim + sub-dim) |
| Storage | More (redundancy) | Less |
| Query speed | Faster | Slower (more joins) |
| Use case | Analytics/reporting | Storage-optimized |

**At Nomura**: We used star schema with trade facts joined to instrument, counterparty, and date dimensions.

### Q: What are CTEs and why use them?

```sql
WITH daily_totals AS (
    SELECT trade_date, SUM(amount) AS total
    FROM trades
    GROUP BY trade_date
),
running AS (
    SELECT trade_date, total,
           SUM(total) OVER (ORDER BY trade_date) AS cumulative
    FROM daily_totals
)
SELECT * FROM running;
```

CTEs make complex queries readable, reusable, and debuggable â€” you can test each CTE independently.

---

## SECTION 4: AWS / CLOUD QUESTIONS

### Q: Explain the AWS Lambda + Step Functions architecture.

```
S3 Event Trigger
    â†“
Lambda: validate_schema()
    â†“ (success)
Step Function orchestrates:
    â”œâ”€â”€ Lambda: transform_data()
    â”œâ”€â”€ Lambda: quality_checks()
    â”œâ”€â”€ Lambda: load_to_snowflake()
    â””â”€â”€ On failure â†’ SNS â†’ CloudWatch Alert
```

**Why Lambda?** Serverless, pay-per-execution, auto-scales. Perfect for batch ETL that runs once daily.

**Why Step Functions?** Visual workflow orchestration with retry policies, error handling, and parallel execution.

### Q: How did CloudWatch monitoring reduce MTTR by 30%?

> MTTR = Mean Time To Resolution.
>
> **Before**: Pipelines failed silently. Engineers discovered failures the next morning when reports were missing. Debugging required SSH into servers and grep through logs.
>
> **After**: 
> - CloudWatch metrics on Lambda execution: duration, errors, throttles
> - CloudWatch alarms trigger SNS notifications (email/Slack)
> - Custom metrics for data freshness and quality
> - Dashboard showing pipeline health at a glance
>
> Engineers now get alerted within minutes of failure, with error context attached.

---

## SECTION 5: HOW PROJECTS DEMONSTRATE DE SKILLS

### Q: How does the Healthcare project show data engineering?

| DE Skill | Healthcare Implementation |
|---|---|
| **ETL pipeline** | CSV â†’ Parquet â†’ Feature engineering â†’ Model training |
| **Data quality** | Pydantic schema validation on every API request |
| **Data processing** | 253K records, column mapping, age bucketing |
| **Batch processing** | Train scripts process full dataset in batch |
| **Storage** | Parquet for training data, SQLite/PostgreSQL for app data |
| **Monitoring** | 7-layer middleware with logging and error tracking |
| **Idempotency** | Model retraining produces same results (random_state=42) |

### Q: How does the Movie project show data engineering?

| DE Skill | Nova Implementation |
|---|---|
| **Delta Lake** | Bronze â†’ Silver â†’ Gold medallion architecture |
| **PySpark ETL** | Full pipeline with schema contracts and ACID writes |
| **Data quality** | Quarantine bad records, quality scoring, metadata completeness |
| **SCD Type 2** | Track dimension history (movie metadata changes over time) |
| **Streaming** | Kafka â†’ Spark Structured Streaming for behavior events |
| **Incremental** | Embedding jobs only for new/changed content |
| **Multi-tenant** | tenant_id, catalog_id â€” same pipeline serves multiple customers |
| **Artifact management** | Model versioning via HuggingFace + promotion gates |

---

## SECTION 6: THE "AI ERA" POSITIONING

### Q: "Why should we hire a Data Engineer who does AI?"

> "In the AI era, every company is building ML pipelines. The bottleneck isn't the model â€” it's the data. You need someone who can:
> 1. Build the ETL that feeds training data
> 2. Ensure data quality (garbage in = garbage out)
> 3. Serve model artifacts efficiently
> 4. Monitor data drift and model performance
> 5. Scale pipelines from prototype to production
>
> I've done all of this â€” Spark ETL for Nomura's capital markets, Delta Lake pipelines for recommendations, and ML serving with FastAPI. I'm not just a modeler who can't deploy, or an engineer who can't understand the ML. I bridge both."

### Q: "What's the difference between a Data Engineer and an ML Engineer?"

| | Data Engineer | ML Engineer | You (Both) |
|---|---|---|---|
| Focus | Pipeline reliability, data quality | Model accuracy, training | Both |
| Tools | Spark, SQL, Airflow, Kafka | PyTorch, XGBoost, scikit-learn | Both |
| Output | Clean, curated datasets | Trained models | Both |
| Concern | Uptime, latency, cost | Accuracy, drift, bias | Both |
| Missing skill | Usually can't train models | Usually can't build pipelines | Neither |

### Q: "Where do you see yourself in 3-5 years?"

> "I see myself as a **Senior Data/AI Engineer** or **ML Platform Engineer** â€” the person who builds the infrastructure that powers AI at scale. Think: the team that builds Spark pipelines to feed training data, serves model artifacts, and monitors production ML systems. At companies like Google, this role is called 'ML Infrastructure Engineer.' I want to be the bridge between data engineering and machine learning."

---

## SECTION 7: NUMBERS TO MEMORIZE

| Metric | Source | Value |
|---|---|---|
| Years of experience | TCS | 2+ years |
| Spark optimization | Nomura | 30% execution time improvement |
| Manual effort reduction | Nissan | 60% reduction |
| MTTR improvement | CloudWatch | 30% reduction |
| Manual intervention | AutoSys | 25% reduction |
| Healthcare training records | BRFSS CDC | 253,680 |
| Movie records | TMDB/Kaggle | 1M+ |
| Healthcare ML accuracy | Real-world validation | 77% (48 records) |
| Healthcare unit tests | pytest | 141 passing |
| Total API endpoints | Both projects | 45+ |
| Technologies used | Resume | 20+ |


---

# 18 â€” Resume Line-by-Line Defense

> For EVERY single bullet point on your resume, here's the detailed answer when they ask "Tell me more about this."

---

## PROFESSIONAL SUMMARY

**Resume says**: "Data Engineer with 2+ years of experience building scalable ETL/ELT data pipelines using Python, SQL, and Spark across AWS and on-prem environments."

**If asked "What do you mean by scalable?"**
> "Scalable means the pipeline can handle 10x data without rewriting code. For example, at Nomura, our Spark jobs processed daily trade feeds that could range from 100K to 5M records depending on market activity. The pipeline handled both without changes because Spark's partitioning and dynamic allocation scaled the compute automatically. I also used partition pruning so queries on specific dates don't scan the entire dataset."

**If asked "ETL vs ELT â€” what's the difference and which do you use?"**
> - **ETL** (Extract, Transform, Load): Transform data BEFORE loading into target. Used at Nomura â€” Spark transforms trade data, then writes to destination.
> - **ELT** (Extract, Load, Transform): Load raw data first, transform inside the target (e.g., Snowflake). Used at Nissan â€” raw files loaded to Snowflake, then SQL transforms inside Snowflake.
> - I've done BOTH. ETL when the transformation is complex (multi-way joins, window functions). ELT when the target has powerful compute (Snowflake).

**If asked "What on-prem vs cloud experience?"**
> - **On-prem**: Nomura â€” YARN cluster with HDFS, later migrated to Kubernetes + MinIO
> - **Cloud**: Nissan â€” AWS Lambda, Step Functions, S3, CloudWatch, Snowflake

---

## EXPERIENCE â€” NOMURA CAPITAL

### Bullet 1: "Engineered and maintained large-scale Spark ETL pipelines using Spark SQL..."

**If asked "How large-scale? Give me numbers."**
> "The capital markets datasets included daily trade feeds (hundreds of thousands of records per day), reference data tables (instrument master, counterparty master â€” millions of rows), risk feeds, and valuation feeds. We processed these through multi-way joins â€” a typical pipeline would join trade facts to 4-5 dimension tables (instrument, counterparty, book, date, currency) using star schema patterns."

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
> - `ROW_NUMBER()` â€” Deduplication (keep latest record per key)
> - `LAG/LEAD` â€” Day-over-day comparisons
> - `SUM/AVG OVER` â€” Running totals, moving averages
> - `RANK/DENSE_RANK` â€” Top-N per group (top 5 trades per instrument)
> - `FIRST_VALUE/LAST_VALUE` â€” First/last trade per day

---

### Bullet 2: "Analyzed Spark execution metrics to improve execution time by 30%..."

**If asked "Walk me through the debugging process."**
> 1. **Spark UI â†’ SQL tab**: Identified slow stages with high shuffle read/write
> 2. **Execution plan**: `EXPLAIN EXTENDED` showed hash joins where broadcast was possible
> 3. **Stage timeline**: One stage was 10x slower than others â€” classic skew
> 4. **GC metrics**: Executors were spending 20% time in garbage collection â€” too much data in memory
>
> **Fixes applied:**
> - Broadcast joins for dimension tables < 100MB â†’ eliminated shuffle
> - Partition pruning via `trade_date` column â†’ skipped 90% of data
> - Predicate pushdown to Parquet reader â†’ fewer row groups scanned
> - Intermediate Parquet checkpoints â†’ prevented recomputation
> - `spark.sql.adaptive.enabled=true` â†’ auto-coalesce small partitions

**If asked "How do you measure 30%?"**
> "Compared wall-clock execution time of the same pipeline on the same data before and after optimizations. A job that took 45 minutes consistently ran in 31 minutes after â€” a 31% improvement."

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
> 3. **Resource management**: YARN's memory model (on-heap + off-heap) â†’ K8s resource requests/limits. Had to tune:
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

## EXPERIENCE â€” TCS iON INTERNSHIP

**If asked "What model did you build?"**
> "An ensemble attrition prediction model â€” combining Random Forest, Gradient Boosting, and Logistic Regression with a voting classifier. Achieved 86% accuracy on validation data. The FastAPI service I built exposed it as a REST endpoint for HR teams to check attrition risk per employee."

---

## PROJECTS SECTION

### Healthcare: "Built automated ETL pipelines processing 250k+ records..."

**If asked "What's the ETL pipeline?"**
> 1. **Extract**: Download BRFSS 2015 CDC CSV from Kaggle
> 2. **Transform**: 
>    - Rename columns (HighBP â†’ hypertension, HighChol â†’ high_chol)
>    - Convert age to buckets (18-24 â†’ 1, 25-29 â†’ 2, ...)
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
>    - Delta Lake: Bronze â†’ Silver â†’ Gold
> 3. **Load**: 
>    - SBERT embeddings â†’ FAISS vector index
>    - Parquet serving artifacts
>    - Publish to HuggingFace for deployment

---

## EDUCATION

**If asked about the PM Scholarship:**
> "The Prime Minister's Scholarship is a merit-based scholarship awarded by the Government of India. I received it for all 4 years of my B.Tech (2019-2023) based on academic performance."

**If asked "What's your minor in AI/ML?"**
> "My B.Tech was Computer Science with a minor specialization in AI/ML. I took additional courses in Machine Learning, Deep Learning, NLP, and Data Mining â€” which gave me the theoretical foundation for the ML work in my projects."

---

## SKILLS SECTION

**If asked "Rate yourself on each skill 1-10":**

| Skill | Rating | Justification |
|---|---|---|
| Python | 8/10 | Daily use for 2+ years, ETL + API + ML |
| SQL | 8/10 | Complex analytical queries, window functions, CTEs |
| Spark/PySpark | 7/10 | Daily at Nomura, optimized 30%, YARNâ†’K8s migration |
| Scala | 5/10 | Can read/modify, not primary language |
| Java | 5/10 | Academic, basic proficiency |
| AWS | 7/10 | Lambda, Step Functions, S3, CloudWatch, Glue |
| Docker | 7/10 | Containerized apps, Docker Compose |
| FastAPI | 8/10 | Built 2 production APIs from scratch |
| Git | 8/10 | Daily use, branching, PRs |
| Snowflake | 6/10 | Data loading, SQL queries, schema design |

