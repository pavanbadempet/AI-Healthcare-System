# Real-Time Telemetry Streaming Guide

This guide explains the architecture and operational steps for running the real-time patient telemetry streaming pipeline inside the AI Healthcare System.

---

## Architecture Overview

The real-time telemetry pipeline is designed to ingest patient vital observations (heart rate, blood pressure, oxygen saturation, temperature, respiratory rate), apply machine learning classification models to evaluate risk, and commit critical alerts directly to the database.

It uses a **unified, native PySpark Structured Streaming** design with `.foreachBatch()`. This executes database ingestion, rolling average calculations, and ML model inference directly in memory on each micro-batch on the Spark driver. This eliminates legacy file-system serialization, making it fully portable across on-prem, cloud (Databricks, AWS EMR/Glue), and serverless environments (Kaggle, Hugging Face, GitHub Actions).

```
+-------------------------------------------------------+
|              Vital Signs Telemetry Simulator          |
|      (scripts/runners/simulate_vitals_stream.py)      |
+--------------------------+----------------------------+
                           |
                           v  (JSON files or Kafka Stream)
+--------------------------+----------------------------+
|         Spark Structured Streaming vital pipeline     |
|      (scripts/runners/run_telemetry_streaming.py)     |
+--------------------------+----------------------------+
                           |  (native foreachBatch direct DB commit + ML)
                           v
+--------------------------+----------------------------+
|                Neon PostgreSQL / SQLite               |
|      (Tables: vital_observations, monitoring_signals) |
+--------------------------+----------------------------+
                           |
                           v  (WebSocket broadcast /telemetry/stream)
+--------------------------+----------------------------+
|                 FastAPI Application Server            |
|                  (backend/telemetry.py)               |
+--------------------------+----------------------------+
                           |
                           v  (Pushes real-time alerts count)
+--------------------------+----------------------------+
|                Frontend Operations Cockpit            |
|               (React Operations dashboard UI)         |
+-------------------------------------------------------+
```

---

## Setup & Prerequisites

Before running the streaming pipeline, ensure PySpark is installed in your local Python environment:

```bash
pip install pyspark
```

If you plan to run using Apache Kafka as the ingestion layer, you must also install `kafka-python` and make sure a Kafka broker is running at `localhost:9092`:

```bash
pip install kafka-python
```

### Windows Local Development

Running PySpark Structured Streaming locally on Windows requires the Hadoop native binaries (`winutils.exe` and `hadoop.dll`) to prevent `java.lang.UnsatisfiedLinkError` and other file access warnings.

We have included a pre-configured, self-contained Hadoop bundle in this repository under the `.hadoop/` directory.

The telemetry scripts (`run_telemetry_streaming.py` and E2E verification scripts) will **automatically detect and load** these binaries dynamically at runtime on Windows, so you do not need to configure global system or user environment variables.

If you need to set it globally or debug manual configurations:
1. Ensure `.hadoop/bin/winutils.exe` and `.hadoop/bin/hadoop.dll` exist in the project root.
2. Set the `HADOOP_HOME` environment variable to point to the `.hadoop` directory.
3. Append `%HADOOP_HOME%\bin` to your system `PATH`.

---

## How to Run the Telemetry Pipeline

To run the pipeline locally using file-based streaming (the default mode, which does not require a Kafka installation):

### Step 1: Start the Vital Signs Simulator
The simulator generates vital signs observations for patients in the database, introducing random clinical anomalies (such as drop in SpO2, spike in heart rate/BP) with a configurable rate.

```bash
python scripts/runners/simulate_vitals_stream.py --interval 5.0 --anomaly-rate 0.10
```

*This will write real-time JSON observation files to the `data/telemetry_stream/` directory.*

### Step 2: Start the Spark Structured Streaming Pipeline
The Spark streaming engine monitors the stream directory (or Kafka stream), processes each micro-batch in-memory using `foreachBatch`, applies pre-trained ML models, and commits conformed observations and critical alerts (`MonitoringSignals`) directly to the database (dynamically computing 2-minute rolling averages).

```bash
python scripts/runners/run_telemetry_streaming.py --processing-time "5 seconds"
```

### Step 3: Run the Backend & Watch the Dashboard
Start the FastAPI backend server:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Start the React frontend application:
```bash
npm --prefix frontend run dev
```

Navigate to the **Operations Cockpit** in the web dashboard. The WebSocket stream (`/telemetry/stream`) will continuously query the database and update the live Census capacity, department loads, and the count of **Open Monitoring Signals** in real-time as the Spark streaming pipeline inserts critical risk alerts.

---

## Running with Apache Kafka

If you have a Kafka broker running at `localhost:9092` and want to stream vitals through a message queue instead of a directory:

1. **Start the Simulator in Kafka Mode**:
   ```bash
   python scripts/runners/simulate_vitals_stream.py --kafka --kafka-servers "localhost:9092" --kafka-topic "hospital.vitals_stream"
   ```

2. **Start the Spark Pipeline in Kafka Ingestion Mode**:
   ```bash
   python scripts/runners/run_telemetry_streaming.py --kafka --kafka-servers "localhost:9092" --kafka-topic "hospital.vitals_stream"
   ```

---

## Directory Management

When running in file-based streaming mode, the simulator creates files continuously. To prevent consuming all disk space, the simulator automatically purges telemetry JSON files older than **5 minutes** every 10 iterations.
You can configure this limit using the `--cleanup-minutes` parameter.
