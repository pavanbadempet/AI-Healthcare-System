# 17 — Data Engineer Interview Guide (Your Primary Role)

> **Your positioning**: Data Engineer with 2+ years at TCS (Nomura Capital, Nissan), who ALSO builds AI systems.
> This file reframes EVERYTHING through the Data Engineering lens that matches your resume.

---

## YOUR CAREER NARRATIVE (Memorize This)

### 30-Second Pitch:
> "I'm a Data Engineer with 2+ years at TCS, where I've built large-scale Spark ETL pipelines for Nomura Capital — processing capital markets data (trades, risk, valuations) — and architected serverless batch pipelines for Nissan using AWS Lambda and Step Functions. I've optimized Spark execution time by 30% through broadcast joins and partition pruning, and led the migration from YARN to Kubernetes. On the AI side, I've built two full-stack projects: a healthcare prediction system with XGBoost on 253K CDC records, and a recommendation platform with FAISS vector search and Delta Lake pipelines on 1M+ movie records. I combine strong data engineering fundamentals with practical AI/ML skills."

### Why This Narrative Works:
1. **Leads with professional experience** (TCS, Nomura, Nissan)
2. **Shows Spark depth** (the #1 DE skill)
3. **Shows cloud skills** (AWS, K8s)
4. **AI as differentiator** (not everyone has this)
5. **Numbers** (2 years, 30%, 253K, 1M+)

---

## SECTION 1: TCS / NOMURA CAPITAL QUESTIONS

### Q: Describe your work at Nomura Capital.

> "I engineered and maintained large-scale Spark ETL pipelines for capital markets datasets at Nomura. The data included trade feeds, reference data, risk feeds, and valuation feeds. I used Spark SQL with complex analytical queries — multi-way joins between fact and dimension tables, window functions for running calculations, and aggregations for downstream risk analytics and reporting."

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
> 3. **Predicate pushdown**: Filters pushed down to the Parquet reader level — only relevant row groups are scanned.
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
> - **Storage**: HDFS → MinIO (S3-compatible). Had to update all Spark read/write paths from `hdfs://` to `s3a://`
> - **Spark connectors**: Needed `spark-hadoop-aws` JAR and correct `fs.s3a.*` configurations
> - **Resource management**: YARN's memory/CPU allocation → K8s resource requests/limits
> - **Dynamic allocation**: YARN's dynamic executor allocation → K8s pod autoscaling
>
> **Result**: Same Spark jobs, portable between on-prem MinIO and cloud S3.

### Q: How does AutoSys orchestration work?

> AutoSys is an enterprise job scheduler (like Airflow but for large enterprises). I used it to:
> - Define **dependency chains**: Job B starts only after Job A completes successfully
> - Handle **reruns**: Failed jobs can be re-triggered without re-running the entire chain
> - **Recovery logic**: On failure, send alert → retry 3x → escalate to on-call
> - **Scheduling**: Daily batch windows with SLA monitoring
>
> This reduced manual intervention by 25% — operators no longer needed to manually trigger dependent jobs.

### Q: Describe the Nissan project.

> Architected daily batch pipelines using **AWS Lambda** and **Step Functions**:
>
> ```
> S3 Upload → Lambda (validate schema) → Step Function (orchestrate)
>     → Lambda (transform) → Lambda (quality checks) → Snowflake
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
> This means running the same batch twice produces the same result — no duplicates, no data corruption.

---

## SECTION 2: SPARK DEEP-DIVE QUESTIONS

### Q: Explain Spark's execution model.

```
Driver Program
    ↓
Creates SparkContext
    ↓
Submits job DAG
    ↓
DAG Scheduler → Stages (shuffle boundaries)
    ↓
Task Scheduler → Tasks (per partition)
    ↓
Executor 1: [Task1, Task2, ...]
Executor 2: [Task3, Task4, ...]
Executor N: [TaskM, ...]
```

**Key concepts:**
- **Driver**: Orchestrates the job, builds DAG, collects results
- **Executor**: Worker process that runs tasks and caches data
- **Stage**: Set of tasks that can run without shuffle
- **Shuffle**: Data redistribution across executors (expensive)
- **Partition**: Unit of parallelism — each partition = one task

### Q: What causes a shuffle and how do you avoid it?

**Causes:** `groupBy`, `join`, `repartition`, `distinct`, `orderBy`

**Avoidance techniques:**
1. **Broadcast join** — Small table broadcast to all executors, no shuffle
2. **Partition-aligned joins** — Both tables partitioned by join key
3. **map-side aggregation** — `reduceByKey` instead of `groupByKey`
4. **Bucket joins** — Pre-bucket tables by join key during write

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

> Data skew = one partition has much more data than others → one executor takes much longer.
>
> **Detection**: Spark UI → Stages tab → check task duration variance
>
> **Solutions:**
> 1. **Salting**: Add random prefix to skewed key, join on salted key, then remove
> 2. **Broadcast join**: If one side is small enough
> 3. **Adaptive Query Execution (AQE)**: `spark.sql.adaptive.enabled=true` — Spark auto-coalesces small partitions
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

CTEs make complex queries readable, reusable, and debuggable — you can test each CTE independently.

---

## SECTION 4: AWS / CLOUD QUESTIONS

### Q: Explain the AWS Lambda + Step Functions architecture.

```
S3 Event Trigger
    ↓
Lambda: validate_schema()
    ↓ (success)
Step Function orchestrates:
    ├── Lambda: transform_data()
    ├── Lambda: quality_checks()
    ├── Lambda: load_to_snowflake()
    └── On failure → SNS → CloudWatch Alert
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
| **ETL pipeline** | CSV → Parquet → Feature engineering → Model training |
| **Data quality** | Pydantic schema validation on every API request |
| **Data processing** | 253K records, column mapping, age bucketing |
| **Batch processing** | Train scripts process full dataset in batch |
| **Storage** | Parquet for training data, SQLite/PostgreSQL for app data |
| **Monitoring** | 7-layer middleware with logging and error tracking |
| **Idempotency** | Model retraining produces same results (random_state=42) |

### Q: How does the Movie project show data engineering?

| DE Skill | Nova Implementation |
|---|---|
| **Delta Lake** | Bronze → Silver → Gold medallion architecture |
| **PySpark ETL** | Full pipeline with schema contracts and ACID writes |
| **Data quality** | Quarantine bad records, quality scoring, metadata completeness |
| **SCD Type 2** | Track dimension history (movie metadata changes over time) |
| **Streaming** | Kafka → Spark Structured Streaming for behavior events |
| **Incremental** | Embedding jobs only for new/changed content |
| **Multi-tenant** | tenant_id, catalog_id — same pipeline serves multiple customers |
| **Artifact management** | Model versioning via HuggingFace + promotion gates |

---

## SECTION 6: THE "AI ERA" POSITIONING

### Q: "Why should we hire a Data Engineer who does AI?"

> "In the AI era, every company is building ML pipelines. The bottleneck isn't the model — it's the data. You need someone who can:
> 1. Build the ETL that feeds training data
> 2. Ensure data quality (garbage in = garbage out)
> 3. Serve model artifacts efficiently
> 4. Monitor data drift and model performance
> 5. Scale pipelines from prototype to production
>
> I've done all of this — Spark ETL for Nomura's capital markets, Delta Lake pipelines for recommendations, and ML serving with FastAPI. I'm not just a modeler who can't deploy, or an engineer who can't understand the ML. I bridge both."

### Q: "What's the difference between a Data Engineer and an ML Engineer?"

| | Data Engineer | ML Engineer | You (Both) |
|---|---|---|---|
| Focus | Pipeline reliability, data quality | Model accuracy, training | Both |
| Tools | Spark, SQL, Airflow, Kafka | PyTorch, XGBoost, scikit-learn | Both |
| Output | Clean, curated datasets | Trained models | Both |
| Concern | Uptime, latency, cost | Accuracy, drift, bias | Both |
| Missing skill | Usually can't train models | Usually can't build pipelines | Neither |

### Q: "Where do you see yourself in 3-5 years?"

> "I see myself as a **Senior Data/AI Engineer** or **ML Platform Engineer** — the person who builds the infrastructure that powers AI at scale. Think: the team that builds Spark pipelines to feed training data, serves model artifacts, and monitors production ML systems. At companies like Google, this role is called 'ML Infrastructure Engineer.' I want to be the bridge between data engineering and machine learning."

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
