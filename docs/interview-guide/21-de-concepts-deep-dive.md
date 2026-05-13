# 21 — Data Engineering Concepts Deep-Dive

> Every concept a DE interviewer expects you to know, with clear explanations and examples.

---

## DATA PIPELINE FUNDAMENTALS

### Q: What is idempotency and why does it matter?

**Idempotent** = Running the same operation multiple times produces the same result.

```python
# NOT idempotent — appends duplicates:
df.write.mode("append").parquet("output/")
# Run twice → 2x data!

# Idempotent — safe to re-run:
df.write.mode("overwrite").parquet("output/partition_date=2024-06-15/")
# Run twice → same result

# Even better — DELETE + INSERT pattern:
DELETE FROM target WHERE batch_date = '2024-06-15';
INSERT INTO target SELECT * FROM staging WHERE batch_date = '2024-06-15';
# Run twice → same result
```

**Why it matters**: Pipelines WILL fail. When you re-run them, you must not create duplicates. At Nissan, every pipeline I built was idempotent.

---

### Q: What is a data lake vs data warehouse vs data lakehouse?

| | Data Lake | Data Warehouse | Data Lakehouse |
|---|---|---|---|
| Storage | Raw files (S3, HDFS) | Structured tables | Files + table metadata |
| Format | Any (CSV, JSON, Parquet) | Columnar (proprietary) | Parquet + Delta/Iceberg |
| Schema | Schema-on-read | Schema-on-write | Both |
| ACID | No | Yes | Yes (via Delta Lake) |
| Query speed | Slow (full scan) | Fast (indexed) | Fast (partition pruning) |
| Cost | Cheap (just storage) | Expensive (compute + storage) | Medium |
| Example | S3 bucket of CSVs | Snowflake, Redshift | Delta Lake, Apache Iceberg |
| In my work | Healthcare raw data | Nissan → Snowflake | Nova → Delta Lake |

---

### Q: What is the medallion architecture (Bronze/Silver/Gold)?

I implemented this in Nova:

```
BRONZE (Raw)          SILVER (Validated)      GOLD (Curated)
────────────          ──────────────────      ──────────────
Raw CSV ingestion     Schema validation       Business metrics
No transforms        Null handling            Feature engineering
Append-only           Deduplication           SCD Type 2 history
Full fidelity         Type casting             Aggregates
Source timestamps     Quarantine bad rows      Ready for ML/reporting
```

**Why 3 layers?**
- Bronze = "we never lose raw data"
- Silver = "data is clean and trustworthy"  
- Gold = "data is ready for business use"

If something breaks in Gold, you rebuild from Silver. If Silver is wrong, you rebuild from Bronze. You NEVER re-extract from source.

---

### Q: What is SCD Type 2?

**Slowly Changing Dimension Type 2** — Track history of dimension changes.

```sql
-- Without SCD: We lose history
UPDATE movies SET rating = 8.8 WHERE id = 123;
-- Old rating (8.5) is gone forever!

-- With SCD Type 2: We keep history
INSERT INTO dim_movies VALUES (123, 'Inception', 8.8, '2024-06-15', NULL, true);
UPDATE dim_movies SET valid_to = '2024-06-15', is_current = false 
    WHERE id = 123 AND is_current = true;

-- Now we can query: "What was the rating on January 1st?"
SELECT rating FROM dim_movies 
WHERE id = 123 AND '2024-01-01' BETWEEN valid_from AND COALESCE(valid_to, '9999-12-31');
-- Returns: 8.5 (the old value)
```

I used SCD Type 2 in Nova's `gold.dim_movie_scd` table to track how movie metadata changes over time.

---

### Q: What is Change Data Capture (CDC)?

CDC captures only the CHANGES (inserts, updates, deletes) from a source system instead of full snapshots.

**Methods:**
1. **Log-based**: Read database transaction log (WAL in PostgreSQL, binlog in MySQL)
2. **Timestamp-based**: Query `WHERE modified_at > last_run` (what I used at Nissan)
3. **Trigger-based**: Database triggers write changes to a staging table
4. **Delta Lake CDF**: Delta Lake's Change Data Feed tracks row-level changes automatically

**My usage**: 
- Nissan: Timestamp-based incremental processing
- Nova: Delta Lake Change Data Feed for tracking catalog changes

---

## DISTRIBUTED SYSTEMS CONCEPTS

### Q: What is the CAP theorem?

**C**onsistency — Every read returns the latest write
**A**vailability — Every request gets a response
**P**artition tolerance — System works despite network failures

**You can only have 2 of 3:**

| System | Choice | Trade-off |
|---|---|---|
| PostgreSQL | CP | Consistent, but single node = not always available |
| Cassandra | AP | Always available, but reads might be stale |
| MongoDB | CP (default) | Consistent reads, but writes pause during elections |

**In my projects:**
- Healthcare (SQLite/PostgreSQL): CP — consistency matters for patient data
- Nova (Delta Lake): CP — ACID writes ensure data integrity

---

### Q: What is eventual consistency?

> "If no new updates are made, eventually all reads will return the same value."

Example: After writing to S3, a read might return the old file for a few seconds. Eventually it sees the new file.

**Where I deal with this:**
- S3 has strong read-after-write consistency (since 2020)
- FAISS index reload: Old index serves until new one is fully loaded
- Behavior features in Nova: Refreshed every 60 seconds (TTL-based)

---

### Q: What is sharding?

Splitting a database across multiple servers by a key:

```
Shard 1: customer_id 1-1000
Shard 2: customer_id 1001-2000
Shard 3: customer_id 2001-3000
```

**Spark's equivalent**: Partitioning. Data is split across executors by partition key.

**Snowflake's equivalent**: Micro-partitions. Data is automatically clustered and pruned.

---

## FILE FORMAT KNOWLEDGE

### Q: Compare CSV, JSON, Parquet, Avro, ORC.

| Format | Type | Schema | Compression | Query Speed | Use Case |
|---|---|---|---|---|---|
| CSV | Row | No | None | Slow | Raw data exchange |
| JSON | Row | Self-describing | None | Slow | APIs, config |
| Parquet | Column | Embedded | Snappy/Gzip | Fast | Analytics, ML |
| Avro | Row | Embedded | Snappy | Medium | Streaming, Kafka |
| ORC | Column | Embedded | Zlib | Fast | Hive ecosystem |
| Delta | Column | Managed | Snappy | Fast | Lakehouse (ACID) |

**Why Parquet?**
- Column-oriented = only read columns you need
- Built-in compression = 10x smaller than CSV
- Row group statistics = predicate pushdown skips irrelevant data
- Schema evolution = add columns without breaking reads

**My usage**: 
- Healthcare: Training data stored as Parquet
- Nova: Delta Lake (which uses Parquet underneath + transaction log)

---

### Q: What is columnar vs row-based storage?

```
ROW-BASED (CSV, MySQL):              COLUMNAR (Parquet, Snowflake):
┌──────┬──────┬──────┐              ┌──────┬──────┬──────┐
│  id  │ name │ age  │              │ id   │ id   │ id   │
│  1   │ John │  25  │              │  1   │  2   │  3   │
│  2   │ Jane │  30  │              ├──────┼──────┼──────┤
│  3   │ Bob  │  35  │              │ name │ name │ name │
└──────┴──────┴──────┘              │ John │ Jane │ Bob  │
                                    ├──────┼──────┼──────┤
Row: reads ALL columns              │ age  │ age  │ age  │
Good for: SELECT * WHERE id=1       │  25  │  30  │  35  │
                                    └──────┴──────┴──────┘
                                    
                                    Column: reads only needed columns
                                    Good for: SELECT AVG(age) FROM table
```

---

## DATA QUALITY CONCEPTS

### Q: What are the dimensions of data quality?

| Dimension | Meaning | How I Check |
|---|---|---|
| **Completeness** | No missing values | `df.isnull().mean()` |
| **Accuracy** | Values are correct | Range checks, referential integrity |
| **Consistency** | Same data across systems | Cross-system checksums |
| **Timeliness** | Data arrives on time | Pipeline SLA monitoring (CloudWatch) |
| **Uniqueness** | No duplicates | `df.duplicated().sum()` |
| **Validity** | Values match expected format | Schema validation, regex checks |

---

### Q: What is data lineage?

Tracking WHERE data came from and HOW it was transformed:

```
BRFSS_2015.csv (CDC source)
    ↓ Extract
data/raw/diabetes.csv
    ↓ Column rename (HighBP → hypertension)
data/processed/diabetes.parquet
    ↓ Train/test split, class balancing
diabetes_model.pkl
    ↓ predict_proba()
API response: {"prediction": "High Risk", "confidence": 94.2}
```

In Nova, the `pipeline_manifest.json` tracks:
- Run ID, run date
- Source file checksums
- Row counts at each stage
- Quality metrics
- Serving contract (expected vs actual artifact sizes)

---

## STREAMING CONCEPTS

### Q: What is the difference between batch and streaming?

| | Batch | Streaming |
|---|---|---|
| Latency | Minutes to hours | Seconds to minutes |
| Processing | Bounded dataset | Unbounded stream |
| State | Stateless (each run independent) | Stateful (maintain windows) |
| Tools | Spark (batch), Airflow | Kafka, Spark Structured Streaming, Flink |
| Cost | Cheaper | More expensive |
| Use case | Daily reports, model training | Real-time alerts, live dashboards |

**My usage:**
- Batch: Healthcare model training, Nova catalog ETL
- Streaming: Nova behavior events (Kafka → Spark Structured Streaming → Delta)

### Q: What is Kafka and how does it work?

```
Producer → Topic (partitioned) → Consumer Group
```

- **Producer**: Sends messages (events) to a topic
- **Topic**: Ordered log of messages, split into partitions
- **Partition**: Unit of parallelism. Messages within a partition are ordered.
- **Consumer Group**: Multiple consumers reading from different partitions in parallel
- **Offset**: Position in the partition. Consumer tracks where it left off.

**In Nova:**
```
Frontend (click/view event) → Kafka topic: nova.content_events → 
    Spark Structured Streaming → gold.fact_content_event (Delta table)
```

### Q: What is exactly-once semantics?

Three delivery guarantees:
- **At-most-once**: Fire and forget. Messages might be lost.
- **At-least-once**: Retry until confirmed. Messages might be duplicated.
- **Exactly-once**: Each message processed exactly once. No loss, no duplication.

**How to achieve exactly-once:**
- Kafka: Idempotent producers + transactional consumers
- Spark Structured Streaming: Checkpointing + WAL
- Application level: Idempotent writes (what I do — safe to re-process)

---

## ORCHESTRATION

### Q: Compare Airflow, AutoSys, Step Functions, Prefect.

| | Airflow | AutoSys | Step Functions | Prefect |
|---|---|---|---|---|
| Type | Open-source | Enterprise | Serverless | Open-source |
| DAG definition | Python | JIL files | JSON/YAML | Python |
| Hosting | Self-managed/Cloud | Vendor-managed | AWS-managed | Cloud |
| Cost | Free (+ infra) | Expensive license | Per-execution | Free tier |
| Strengths | Flexible, extensible | Enterprise compliance | Serverless, visual | Modern Python API |
| Weaknesses | Complex setup | Old UI, limited | AWS-only | Newer, smaller community |
| My experience | Project knowledge | Nomura (daily) | Nissan (daily) | Aware |
