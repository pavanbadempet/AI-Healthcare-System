# Chapter 2 - Your Career: Resume, TCS Experience and Career Positioning

> **Your positioning**: Data Engineer with 2+ years at TCS (Nomura Capital, Nissan), who ALSO builds AI systems.
> This file reframes EVERYTHING through the Data Engineering lens that matches your resume.

---

## YOUR CAREER NARRATIVE (Memorize This)

### 30-Second Pitch:
> "I'm a Data Engineer with 2+ years at TCS, where I built enterprise-scale data platforms for two major clients. At Nomura Capital, I engineered Spark ETL pipelines processing 200M+ daily trade events across equities, fixed income, and derivatives -- designing the star schema, implementing data quality reconciliation, and leading the YARN-to-Kubernetes migration that cut infrastructure costs by 30%. At Nissan, I architected a serverless data platform using AWS Lambda, Step Functions, and Snowflake that processed 50+ daily data feeds with a 99.7% success rate and 6 AM SLA. On the AI side, I've built two full-stack projects: a healthcare prediction system with XGBoost achieving clinical-grade accuracy on 253K CDC records, and a movie recommendation engine with FAISS vector search, Delta Lake Medallion architecture, and Kafka streaming on 1M+ records. I combine production data engineering with practical AI/ML."

### Why This Narrative Works:
1. **Leads with professional experience** (TCS, Nomura, Nissan)
2. **Shows Spark depth** (the #1 DE skill)
3. **Shows cloud skills** (AWS, K8s)
4. **AI as differentiator** (not everyone has this)
5. **Numbers** (2 years, 30%, 253K, 1M+)

---

## SECTION 1: TCS / NOMURA CAPITAL QUESTIONS

### Q: Describe your work at Nomura Capital.

> "I engineered and maintained enterprise-scale Spark ETL pipelines processing 200M+ daily trade events for Nomura's capital markets division. The data covered equities, fixed income, and derivatives -- trade feeds, reference data, risk feeds, and valuation feeds from 8+ upstream trading systems. I designed a star schema with fct_trades at the center and 8 dimension tables (instruments, desks, counterparties, exchanges, currencies, dates, traders, strategies). I used Spark SQL with complex analytical queries -- multi-way joins between fact and dimension tables, window functions for running P&L calculations, and aggregations for downstream risk analytics and regulatory reporting (MiFID II, SOX). I also implemented a data quality framework with automated reconciliation between source trading systems and the warehouse -- row count checks, duplicate trade ID detection, and cross-system balance validation."

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
> 3. **Predicate pushdown**: Filters pushed down to the Parquet reader level " only relevant row groups are scanned.
>
> 4. **Intermediate Parquets**: Instead of one massive transformation, I broke the DAG into stages and persisted intermediate results as Parquet. This prevents recomputation on failure and allows checkpoint-resume.
>
> 5. **Optimized star schema joins**: Fact tables joined to dimensions in the correct order (smallest dimension first) to minimize shuffle size.

### Q: Explain the YARN to Kubernetes migration.

> We migrated Spark workloads from Hadoop YARN (on-prem cluster) to Kubernetes:
>
> **Why?** YARN was tied to HDFS with fixed cluster sizes. K8s gives us container orchestration, auto-scaling, storage-agnostic workloads, and cloud portability.
>
> **Challenges:**
> - **Storage**: HDFS → MinIO (S3-compatible). Updated all Spark read/write paths from `hdfs://` to `s3a://` and configured S3A connectors
> - **Spark connectors**: Added `spark-hadoop-aws` JAR with correct `fs.s3a.*` configurations for MinIO endpoints
> - **Resource management**: Translated YARN's memory/CPU allocation → K8s resource requests/limits. Set executor memory to 8GB with 4 cores per pod
> - **Dynamic allocation**: YARN's dynamic executor allocation → K8s pod autoscaling with HPA (Horizontal Pod Autoscaler)
> - **Validation**: Ran parallel pipelines (YARN + K8s) for 2 weeks. Compared outputs for 100% of tables -- validated within 0.01% variance
>
> **Result**: Same Spark jobs, portable between on-prem MinIO and cloud S3. 30% cost reduction from better resource utilization (K8s packs workloads more efficiently than YARN's static allocation). Zero downtime during cutover.

### Q: How does AutoSys orchestration work?

> AutoSys is an enterprise job scheduler (like Airflow but for large enterprises). I used it to:
> - Define **dependency chains**: Job B starts only after Job A completes successfully
> - Handle **reruns**: Failed jobs can be re-triggered without re-running the entire chain
> - **Recovery logic**: On failure, send alert ' retry 3x ' escalate to on-call
> - **Scheduling**: Daily batch windows with SLA monitoring
>
> This reduced manual intervention by 25% " operators no longer needed to manually trigger dependent jobs.

> Architected a production-grade serverless data platform processing **50+ daily data feeds** from manufacturing, supply chain, sales, and dealer network systems:
>
> ```
> [Source Systems] → [S3 Landing Zone] → [Lambda (validate + transform)]
>     → [Step Functions (orchestrate 7-step pipeline)]
>     → [S3 Processed Zone (Parquet, partitioned by date)]
>     → [Snowflake (raw/clean/mart schemas)] → [Tableau dashboards]
> ```
>
> **Key features:**
> - **Idempotent re-runs**: Each run checks if data already exists for that date. Re-running won't create duplicates.
> - **Schema validation**: Incoming files validated against expected schema. Caught 12 upstream breaking changes before they hit production.
> - **Data quality checks**: Row count validation (within 2 std dev of 30-day average), null rate monitoring, range checks, referential integrity
> - **Incremental processing**: Only process new/changed records, not the full dataset
> - **Dead letter queue**: Failed records routed to separate S3 path for manual review instead of blocking the pipeline
> - **Multi-environment**: Dev/staging/prod Snowflake databases with identical schemas. Lambda deployed via CodePipeline CI/CD
> - **Cost optimization**: Snowflake auto-suspend after 5 min, S3 lifecycle (Standard → IA → Glacier), Lambda right-sized memory
> - **Monitoring**: CloudWatch dashboards + PagerDuty alerts for SLA-threatening delays
>
> **Result**: 99.7% pipeline success rate, 6 AM SLA never missed in 6 months, ~40% cost reduction vs previous always-on EC2 approach, 15+ concurrent analysts served without degradation.

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
> This means running the same batch twice produces the same result " no duplicates, no data corruption.

---

## SECTION 2: SPARK DEEP-DIVE QUESTIONS

### Q: Explain Spark's execution model.

```
Driver Program
    "
Creates SparkContext
    "
Submits job DAG
    "
DAG Scheduler ' Stages (shuffle boundaries)
    "
Task Scheduler ' Tasks (per partition)
    "
Executor 1: [Task1, Task2, ...]
Executor 2: [Task3, Task4, ...]
Executor N: [TaskM, ...]
```

**Key concepts:**
- **Driver**: Orchestrates the job, builds DAG, collects results
- **Executor**: Worker process that runs tasks and caches data
- **Stage**: Set of tasks that can run without shuffle
- **Shuffle**: Data redistribution across executors (expensive)
- **Partition**: Unit of parallelism " each partition = one task

### Q: What causes a shuffle and how do you avoid it?

**Causes:** `groupBy`, `join`, `repartition`, `distinct`, `orderBy`

**Avoidance techniques:**
1. **Broadcast join** " Small table broadcast to all executors, no shuffle
2. **Partition-aligned joins** " Both tables partitioned by join key
3. **map-side aggregation** " `reduceByKey` instead of `groupByKey`
4. **Bucket joins** " Pre-bucket tables by join key during write

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

> Data skew = one partition has much more data than others ' one executor takes much longer.
>
> **Detection**: Spark UI ' Stages tab ' check task duration variance
>
> **Solutions:**
> 1. **Salting**: Add random prefix to skewed key, join on salted key, then remove
> 2. **Broadcast join**: If one side is small enough
> 3. **Adaptive Query Execution (AQE)**: `spark.sql.adaptive.enabled=true` " Spark auto-coalesces small partitions
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

CTEs make complex queries readable, reusable, and debuggable " you can test each CTE independently.

---

## SECTION 4: AWS / CLOUD QUESTIONS

### Q: Explain the AWS Lambda + Step Functions architecture.

```
S3 Event Trigger
    "
Lambda: validate_schema()
    " (success)
Step Function orchestrates:
    """ Lambda: transform_data()
    """ Lambda: quality_checks()
    """ Lambda: load_to_snowflake()
    """" On failure ' SNS ' CloudWatch Alert
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
| **ETL pipeline** | CSV ' Parquet ' Feature engineering ' Model training |
| **Data quality** | Pydantic schema validation on every API request |
| **Data processing** | 253K records, column mapping, age bucketing |
| **Batch processing** | Train scripts process full dataset in batch |
| **Storage** | Parquet for training data, SQLite/PostgreSQL for app data |
| **Monitoring** | 7-layer middleware with logging and error tracking |
| **Idempotency** | Model retraining produces same results (random_state=42) |

### Q: How does the Movie project show data engineering?

| DE Skill | Nova Implementation |
|---|---|
| **Delta Lake** | Bronze ' Silver ' Gold medallion architecture |
| **PySpark ETL** | Full pipeline with schema contracts and ACID writes |
| **Data quality** | Quarantine bad records, quality scoring, metadata completeness |
| **SCD Type 2** | Track dimension history (movie metadata changes over time) |
| **Streaming** | Kafka ' Spark Structured Streaming for behavior events |
| **Incremental** | Embedding jobs only for new/changed content |
| **Multi-tenant** | tenant_id, catalog_id " same pipeline serves multiple customers |
| **Artifact management** | Model versioning via HuggingFace + promotion gates |

---

## SECTION 6: THE "AI ERA" POSITIONING

### Q: "Why should we hire a Data Engineer who does AI?"

> "In the AI era, every company is building ML pipelines. The bottleneck isn't the model " it's the data. You need someone who can:
> 1. Build the ETL that feeds training data
> 2. Ensure data quality (garbage in = garbage out)
> 3. Serve model artifacts efficiently
> 4. Monitor data drift and model performance
> 5. Scale pipelines from prototype to production
>
> I've done all of this " Spark ETL for Nomura's capital markets, Delta Lake pipelines for recommendations, and ML serving with FastAPI. I'm not just a modeler who can't deploy, or an engineer who can't understand the ML. I bridge both."

### Q: "What's the difference between a Data Engineer and an ML Engineer?"

| | Data Engineer | ML Engineer | You (Both) |
|---|---|---|---|
| Focus | Pipeline reliability, data quality | Model accuracy, training | Both |
| Tools | Spark, SQL, Airflow, Kafka | PyTorch, XGBoost, scikit-learn | Both |
| Output | Clean, curated datasets | Trained models | Both |
| Concern | Uptime, latency, cost | Accuracy, drift, bias | Both |
| Missing skill | Usually can't train models | Usually can't build pipelines | Neither |

### Q: "Where do you see yourself in 3-5 years?"

> "I see myself as a **Senior Data/AI Engineer** or **ML Platform Engineer** " the person who builds the infrastructure that powers AI at scale. Think: the team that builds Spark pipelines to feed training data, serves model artifacts, and monitors production ML systems. At companies like Google, this role is called 'ML Infrastructure Engineer.' I want to be the bridge between data engineering and machine learning."

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


> For EVERY single bullet point on your resume, here's the detailed answer when they ask "Tell me more about this."

---

## PROFESSIONAL SUMMARY

**Resume says**: "Data Engineer with 2+ years of experience building scalable ETL/ELT data pipelines using Python, SQL, and Spark across AWS and on-prem environments."

**If asked "What do you mean by scalable?"**
> "Scalable means the pipeline can handle 10x data without rewriting code. For example, at Nomura, our Spark jobs processed daily trade feeds that could range from 100K to 5M records depending on market activity. The pipeline handled both without changes because Spark's partitioning and dynamic allocation scaled the compute automatically. I also used partition pruning so queries on specific dates don't scan the entire dataset."

**If asked "ETL vs ELT " what's the difference and which do you use?"**
> - **ETL** (Extract, Transform, Load): Transform data BEFORE loading into target. Used at Nomura " Spark transforms trade data, then writes to destination.
> - **ELT** (Extract, Load, Transform): Load raw data first, transform inside the target (e.g., Snowflake). Used at Nissan " raw files loaded to Snowflake, then SQL transforms inside Snowflake.
> - I've done BOTH. ETL when the transformation is complex (multi-way joins, window functions). ELT when the target has powerful compute (Snowflake).

**If asked "What on-prem vs cloud experience?"**
> - **On-prem**: Nomura " YARN cluster with HDFS, later migrated to Kubernetes + MinIO
> - **Cloud**: Nissan " AWS Lambda, Step Functions, S3, CloudWatch, Snowflake

---

## EXPERIENCE " NOMURA CAPITAL

### Bullet 1: "Engineered and maintained large-scale Spark ETL pipelines using Spark SQL..."

**If asked "How large-scale? Give me numbers."**
> "The capital markets datasets included daily trade feeds (hundreds of thousands of records per day), reference data tables (instrument master, counterparty master " millions of rows), risk feeds, and valuation feeds. We processed these through multi-way joins " a typical pipeline would join trade facts to 4-5 dimension tables (instrument, counterparty, book, date, currency) using star schema patterns."

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
> - `ROW_NUMBER()` " Deduplication (keep latest record per key)
> - `LAG/LEAD` " Day-over-day comparisons
> - `SUM/AVG OVER` " Running totals, moving averages
> - `RANK/DENSE_RANK` " Top-N per group (top 5 trades per instrument)
> - `FIRST_VALUE/LAST_VALUE` " First/last trade per day

---

### Bullet 2: "Analyzed Spark execution metrics to improve execution time by 30%..."

**If asked "Walk me through the debugging process."**
> 1. **Spark UI ' SQL tab**: Identified slow stages with high shuffle read/write
> 2. **Execution plan**: `EXPLAIN EXTENDED` showed hash joins where broadcast was possible
> 3. **Stage timeline**: One stage was 10x slower than others " classic skew
> 4. **GC metrics**: Executors were spending 20% time in garbage collection " too much data in memory
>
> **Fixes applied:**
> - Broadcast joins for dimension tables < 100MB ' eliminated shuffle
> - Partition pruning via `trade_date` column ' skipped 90% of data
> - Predicate pushdown to Parquet reader ' fewer row groups scanned
> - Intermediate Parquet checkpoints ' prevented recomputation
> - `spark.sql.adaptive.enabled=true` ' auto-coalesce small partitions

**If asked "How do you measure 30%?"**
> "Compared wall-clock execution time of the same pipeline on the same data before and after optimizations. A job that took 45 minutes consistently ran in 31 minutes after " a 31% improvement."

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
> 3. **Resource management**: YARN's memory model (on-heap + off-heap) ' K8s resource requests/limits. Had to tune:
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

## EXPERIENCE " TCS iON INTERNSHIP

**If asked "What model did you build?"**
> "An ensemble attrition prediction model " combining Random Forest, Gradient Boosting, and Logistic Regression with a voting classifier. Achieved 86% accuracy on validation data. The FastAPI service I built exposed it as a REST endpoint for HR teams to check attrition risk per employee."

---

## PROJECTS SECTION

### Healthcare: "Built automated ETL pipelines processing 250k+ records..."

**If asked "What's the ETL pipeline?"**
> 1. **Extract**: Download BRFSS 2015 CDC CSV from Kaggle
> 2. **Transform**: 
>    - Rename columns (HighBP ' hypertension, HighChol ' high_chol)
>    - Convert age to buckets (18-24 ' 1, 25-29 ' 2, ...)
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
>    - Delta Lake: Bronze ' Silver ' Gold
> 3. **Load**: 
>    - SBERT embeddings ' FAISS vector index
>    - Parquet serving artifacts
>    - Publish to HuggingFace for deployment

---

## EDUCATION

**If asked about the PM Scholarship:**
> "The Prime Minister's Scholarship is a merit-based scholarship awarded by the Government of India. I received it for all 4 years of my B.Tech (2019-2023) based on academic performance."

**If asked "What's your minor in AI/ML?"**
> "My B.Tech was Computer Science with a minor specialization in AI/ML. I took additional courses in Machine Learning, Deep Learning, NLP, and Data Mining " which gave me the theoretical foundation for the ML work in my projects."

---

## SKILLS SECTION

**If asked "Rate yourself on each skill 1-10":**

| Skill | Rating | Justification |
|---|---|---|
| Python | 8/10 | Daily use for 2+ years, ETL + API + ML |
| SQL | 8/10 | Complex analytical queries, window functions, CTEs |
| Spark/PySpark | 7/10 | Daily at Nomura, optimized 30%, YARN'K8s migration |
| Scala | 5/10 | Can read/modify, not primary language |
| Java | 5/10 | Academic, basic proficiency |
| AWS | 7/10 | Lambda, Step Functions, S3, CloudWatch, Glue |
| Docker | 7/10 | Containerized apps, Docker Compose |
| FastAPI | 8/10 | Built 2 production APIs from scratch |
| Git | 8/10 | Daily use, branching, PRs |
| Snowflake | 6/10 | Data loading, SQL queries, schema design |

