# 23 — Tool & Technology Comparisons

> Interviewers LOVE asking "Why X over Y?" Here's every comparison you need.

---

## DATABASES

### Snowflake vs Redshift vs BigQuery vs Databricks SQL

| | Snowflake | Redshift | BigQuery | Databricks SQL |
|---|---|---|---|---|
| Cloud | Multi-cloud | AWS only | GCP only | Multi-cloud |
| Architecture | Separated compute/storage | Shared-nothing cluster | Serverless | Lakehouse (Delta) |
| Scaling | Auto, per-query | Manual cluster resize | Auto | Auto |
| Cost model | Per-second compute | Per-hour cluster | Per-query scan | Per-DBU |
| Concurrency | Excellent (virtual warehouses) | Limited (cluster-bound) | Excellent | Good |
| Semi-structured | VARIANT column (JSON) | Limited | STRUCT/ARRAY | Good |
| My experience | **Nissan project** | Aware | Aware | Aware |

**When asked "Why did you use Snowflake at Nissan?"**
> "Snowflake separated compute from storage — we could scale down warehouses at night (saving cost) and scale up during batch windows. Its COPY INTO command made S3 → Snowflake loading simple. The VARIANT type handled our semi-structured data without pre-flattening."

---

### PostgreSQL vs MySQL vs MongoDB

| | PostgreSQL | MySQL | MongoDB |
|---|---|---|---|
| Type | Relational | Relational | Document (NoSQL) |
| ACID | Full | Full | Configurable |
| JSON support | JSONB (excellent) | Basic | Native |
| Scalability | Vertical (+read replicas) | Vertical | Horizontal (sharding) |
| Use case | Complex queries, analytics | Web apps, simple CRUD | Flexible schema, high write |
| My usage | Healthcare (production DB) | Aware | Aware |

---

## DATA PROCESSING

### Spark vs Pandas vs Polars vs Dask

| | Spark | Pandas | Polars | Dask |
|---|---|---|---|---|
| Scale | TB+ (distributed) | GB (single machine) | GB+ (single, fast) | TB (distributed) |
| Language | Python/Scala/SQL | Python | Python/Rust | Python |
| Execution | Lazy (DAG) | Eager | Lazy | Lazy |
| Memory | Cluster-distributed | In-memory | In-memory (efficient) | Out-of-core |
| Use case | Production ETL | Prototyping, small data | Medium data, speed | Pandas-like distributed |
| My usage | **Nomura (daily)** | **Both projects** | Aware | Aware |

**When asked "When do you use Spark vs Pandas?"**
> "Pandas for anything under ~5GB that fits in RAM — fast prototyping, data exploration, simple transforms. Spark for anything bigger, anything that needs to scale, or anything that runs in production with reliability requirements. At Nomura, all production ETL was Spark. For local data exploration and testing, I used Pandas."

---

### Spark RDD vs DataFrame vs Dataset

| | RDD | DataFrame | Dataset |
|---|---|---|---|
| Type safety | Compile-time (Scala) | Runtime | Compile-time (Scala) |
| Optimization | No Catalyst | Catalyst + Tungsten | Catalyst + Tungsten |
| API | Functional (map/filter) | SQL-like | Typed SQL-like |
| Performance | Slowest | Fast | Fast |
| My usage | Rarely | **Daily at Nomura** | Aware (Scala) |

> "I use DataFrames exclusively. RDDs are lower-level and miss Catalyst optimizations. Datasets are Scala-only. DataFrames give the best balance of performance, readability, and Spark SQL integration."

---

## ORCHESTRATION

### Airflow vs Prefect vs Dagster vs Step Functions

| | Airflow | Prefect | Dagster | Step Functions |
|---|---|---|---|---|
| Language | Python | Python | Python | JSON/YAML |
| Hosting | Self or MWAA | Cloud | Cloud/self | AWS managed |
| DAG definition | Python decorators | Python decorators | Python + assets | State machine JSON |
| UI | Good | Modern | Excellent | AWS Console |
| Strengths | Mature, huge community | Modern, easy to use | Asset-oriented | Serverless, no infra |
| Weaknesses | Complex setup | Newer | Steeper learning curve | AWS only |
| My experience | Project knowledge | Aware | Aware | **Nissan (daily)** |

---

## STREAMING

### Kafka vs RabbitMQ vs AWS SQS vs AWS Kinesis

| | Kafka | RabbitMQ | SQS | Kinesis |
|---|---|---|---|---|
| Model | Log (pull) | Queue (push) | Queue (pull) | Stream (pull) |
| Ordering | Per-partition | FIFO queue | FIFO option | Per-shard |
| Retention | Days-weeks | Until consumed | 14 days max | 7 days default |
| Throughput | 1M+ msg/sec | 10K msg/sec | Unlimited | 1MB/sec/shard |
| Replay | Yes (offset) | No | No | Yes (iterator) |
| Use case | Event streaming, CDC | Task queues | Decoupling services | Real-time analytics |
| My experience | **Nova project** | Aware | Aware | Aware |

---

## STORAGE

### S3 vs HDFS vs MinIO vs GCS

| | S3 | HDFS | MinIO | GCS |
|---|---|---|---|---|
| Type | Object store | Distributed FS | Object store | Object store |
| Cloud | AWS | On-prem | On-prem/cloud | GCP |
| Cost | Pay per GB + request | Hardware cost | Free (self-hosted) | Pay per GB |
| Scalability | Unlimited | Cluster-limited | Hardware-limited | Unlimited |
| POSIX | No | Yes | No | No |
| S3 compatible | Yes (native) | No | Yes | Via interop |
| My experience | **Nissan** | **Nomura (before)** | **Nomura (after)** | Healthcare |

---

## DATA FORMATS

### Delta Lake vs Apache Iceberg vs Apache Hudi

| | Delta Lake | Iceberg | Hudi |
|---|---|---|---|
| Developed by | Databricks | Netflix → Apache | Uber → Apache |
| Storage | Parquet + JSON log | Parquet + metadata | Parquet + timeline |
| ACID | Yes | Yes | Yes |
| Time travel | Yes (version history) | Yes (snapshots) | Yes (timeline) |
| Schema evolution | Yes | Excellent | Yes |
| Merge/Upsert | MERGE INTO | MERGE INTO | Upsert natively |
| Community | Large (Databricks) | Growing fast | Smaller |
| My experience | **Nova project** | Aware | Aware |

**When asked "Why Delta Lake?"**
> "Delta Lake adds ACID transactions to Parquet — I can do MERGE operations, time travel, and Change Data Feed. In Nova, I use Delta for the medallion architecture: Bronze (raw ingest with ACID), Silver (validated with MERGE), Gold (curated with SCD Type 2). The transaction log prevents corrupt partial writes."

---

## CONTAINERIZATION

### Docker vs Kubernetes vs Docker Compose

| | Docker | Docker Compose | Kubernetes |
|---|---|---|---|
| What | Single container runtime | Multi-container on one host | Container orchestration at scale |
| Scale | 1 container | Multiple containers, 1 machine | Multiple containers, many machines |
| Networking | Port mapping | Virtual network | Service discovery, load balancing |
| Use case | Development, single service | Local dev, small apps | Production, auto-scaling |
| My experience | **Both projects** | **Nova** | **Nomura (Spark on K8s)** |

---

## QUICK DECISION MATRIX

**When asked "What would you choose for X?"**

| Scenario | Choose | Why |
|---|---|---|
| ETL on 100GB daily | **Spark** | Distributed, handles scale |
| ETL on 1GB daily | **Pandas/Python** | Simpler, no cluster needed |
| Real-time events | **Kafka** | High throughput, replay |
| Task queue | **SQS/RabbitMQ** | Simpler, managed |
| Orchestration (AWS) | **Step Functions** | Serverless, visual |
| Orchestration (general) | **Airflow** | Flexible, community |
| Data warehouse | **Snowflake** | Multi-cloud, auto-scale |
| Lakehouse | **Delta Lake** | ACID + Parquet + Spark |
| ML model serving | **FastAPI** | Async, fast, auto-docs |
| Password storage | **bcrypt** | One-way, salted, industry standard |
| API auth | **JWT** | Stateless, scalable |
| Vector search | **FAISS** | Sub-ms, battle-tested |
