# Chapter 5 - Coding Practice: Python, SQL, DSA and PySpark

> Data Engineer interviews ALWAYS have a coding round. Here are the patterns they ask.

---

## PYTHON CODING PATTERNS

### Pattern 1: File Processing (Very Common for DE)

**Q: Read a CSV, find duplicates, write clean data to Parquet.**

**What the interviewer is testing**: Can you handle real-world data tasks? Do you think about data quality? Do you know Parquet vs CSV?

**How to think about it (say this out loud):**
> "First, I'd read the file. Then identify duplicates - I need to know: what makes a row a duplicate? Same ID? Same all columns? Let me ask... OK, same ID. I'll keep the last occurrence. Then write clean data to Parquet for better compression and query speed."

```python
import pandas as pd

def process_file(input_path: str, output_path: str) -> dict:
    # Step 1: Read raw data
    df = pd.read_csv(input_path)
    
    # Step 2: Find duplicates based on "id" column
    # keep=False marks ALL duplicate rows (not just the extra ones)
    dupes = df[df.duplicated(subset=["id"], keep=False)]
    print(f"Found {len(dupes)} duplicate rows")
    
    # Step 3: Remove duplicates, keep the LAST occurrence
    # Why "last"? In incremental data, the latest record is most up-to-date
    clean = df.drop_duplicates(subset=["id"], keep="last")
    
    # Step 4: Write to Parquet (columnar, compressed, typed)
    clean.to_parquet(output_path, index=False)
    
    # Step 5: Return summary for logging/monitoring
    return {
        "input_rows": len(df),
        "duplicates_removed": len(df) - len(clean),
        "output_rows": len(clean)
    }
```

**Edge cases to mention:**
- What if the CSV is too large for memory? Use `pd.read_csv(path, chunksize=10000)` to process in chunks
- What if there are encoding issues? `pd.read_csv(path, encoding='utf-8')` or `encoding='latin-1'`
- What if "id" column doesn't exist? Add validation: `assert "id" in df.columns`
- What if ALL rows are duplicates? The function still works - returns 1 row per unique ID

**Follow-up they might ask:**
- "Why Parquet over CSV?" - Columnar storage, 5-10x compression, embedded types, column pruning
- "How would you handle this at scale (100GB)?" - Use PySpark instead of Pandas
- "What if duplicates span across multiple daily files?" - Use a window function or merge with existing data

### Pattern 2: Data Validation

**Q: Write a function that validates a DataFrame against a schema.**
```python
def validate_schema(df: pd.DataFrame, expected: dict) -> list[str]:
    """
    expected = {"id": "int64", "name": "object", "amount": "float64"}
    Returns list of errors (empty = valid)
    """
    errors = []
    
    # Check missing columns
    for col in expected:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
    
    # Check extra columns
    for col in df.columns:
        if col not in expected:
            errors.append(f"Unexpected column: {col}")
    
    # Check types
    for col, dtype in expected.items():
        if col in df.columns and str(df[col].dtype) != dtype:
            errors.append(f"Column {col}: expected {dtype}, got {df[col].dtype}")
    
    # Check nulls in required fields
    for col in ["id", "name"]:
        if col in df.columns and df[col].isnull().any():
            null_count = df[col].isnull().sum()
            errors.append(f"Column {col}: {null_count} null values")
    
    return errors
```

### Pattern 3: Dictionary/Hash Map Problems

**Q: Group transactions by customer and find total spend.**
```python
from collections import defaultdict

def total_spend_by_customer(transactions: list[dict]) -> dict:
    """
    Input: [{"customer_id": 1, "amount": 50}, {"customer_id": 1, "amount": 30}, ...]
    Output: {1: 80, 2: ...}
    """
    totals = defaultdict(float)
    for txn in transactions:
        totals[txn["customer_id"]] += txn["amount"]
    return dict(totals)
```

**Q: Find the first non-repeating character in a string.**
```python
from collections import Counter

def first_unique_char(s: str) -> str:
    counts = Counter(s)
    for char in s:
        if counts[char] == 1:
            return char
    return ""
```

### Pattern 4: Two Pointers / Sliding Window

**Q: Find the maximum sum of a subarray of size k.**
```python
def max_sum_subarray(arr: list[int], k: int) -> int:
    if len(arr) < k:
        return 0
    
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]  # Slide window
        max_sum = max(max_sum, window_sum)
    
    return max_sum
```

### Pattern 5: JSON/API Data Processing

**Q: Flatten nested JSON into a flat dictionary.**
```python
def flatten_json(nested: dict, prefix: str = "") -> dict:
    flat = {}
    for key, value in nested.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_json(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flat.update(flatten_json(item, f"{full_key}[{i}]"))
                else:
                    flat[f"{full_key}[{i}]"] = item
        else:
            flat[full_key] = value
    return flat

# Example:
# flatten_json({"a": {"b": 1, "c": {"d": 2}}})
# ' {"a.b": 1, "a.c.d": 2}
```

### Pattern 6: Batch Processing Simulation

**Q: Process records in batches of N.**
```python
def process_in_batches(records: list, batch_size: int = 1000):
    """Process large datasets in memory-efficient batches."""
    total = len(records)
    processed = 0
    
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        
        # Process batch
        results = transform_batch(batch)
        load_batch(results)
        
        processed += len(batch)
        print(f"Progress: {processed}/{total} ({processed/total*100:.1f}%)")
    
    return processed
```

### Pattern 7: Generator for Large File Processing (Memory-Efficient)

**Q: "Process a 50GB log file without running out of memory."**

**Why generators:** A generator yields one item at a time instead of loading everything into memory. Essential for DE when dealing with files that don't fit in RAM.

```python
def read_large_file(file_path: str, chunk_size: int = 8192):
    """Read a large file line by line without loading into memory."""
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

def process_log_file(file_path: str) -> dict:
    """Process a massive log file with constant memory usage."""
    stats = {"total": 0, "errors": 0, "warnings": 0}

    for line in read_large_file(file_path):
        stats["total"] += 1
        if "ERROR" in line:
            stats["errors"] += 1
        elif "WARN" in line:
            stats["warnings"] += 1

    return stats

# Memory usage: ~1 line at a time, regardless of file size
# 50GB file? Still uses ~1KB of memory
```

**Follow-up:** "What's the difference between a generator and a list?"
> "A list stores all items in memory at once. A generator computes items lazily -- only when asked. For 1M records: list uses ~800MB, generator uses ~1KB. In DE, we use generators for ETL pipelines where data flows through transformations without materializing intermediate results."

### Pattern 8: Retry with Exponential Backoff (Production Pattern)

**Q: "Write a retry decorator for flaky API calls."**

```python
import time
import functools

def retry(max_attempts=3, backoff_factor=2, exceptions=(Exception,)):
    """Decorator that retries a function with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise  # Final attempt failed, propagate error
                    wait = backoff_factor ** attempt  # 2, 4, 8 seconds
                    print(f"Attempt {attempt} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        return wrapper
    return decorator

# Usage:
@retry(max_attempts=3, backoff_factor=2, exceptions=(ConnectionError, TimeoutError))
def fetch_data_from_api(url: str) -> dict:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()
```

**Why this matters:** Every production pipeline has flaky dependencies (APIs, databases, S3). This pattern is in YOUR Healthcare project (middleware retry logic).

### Pattern 9: ETL Pipeline Class (What They Want to See)

**Q: "Write a simple ETL pipeline framework."**

```python
from abc import ABC, abstractmethod
from datetime import datetime

class ETLPipeline(ABC):
    """Base class for ETL pipelines. Subclass and implement extract/transform/load."""

    def __init__(self, pipeline_name: str):
        self.name = pipeline_name
        self.metrics = {"start": None, "end": None, "rows_in": 0, "rows_out": 0}

    def run(self, execution_date: str) -> dict:
        """Execute the full ETL pipeline."""
        self.metrics["start"] = datetime.now()

        try:
            # Extract
            raw_data = self.extract(execution_date)
            self.metrics["rows_in"] = len(raw_data)

            # Transform
            clean_data = self.transform(raw_data)

            # Load
            self.load(clean_data, execution_date)
            self.metrics["rows_out"] = len(clean_data)

            self.metrics["end"] = datetime.now()
            self.metrics["status"] = "SUCCESS"
        except Exception as e:
            self.metrics["status"] = "FAILED"
            self.metrics["error"] = str(e)
            raise

        return self.metrics

    @abstractmethod
    def extract(self, execution_date: str) -> list: ...

    @abstractmethod
    def transform(self, raw_data: list) -> list: ...

    @abstractmethod
    def load(self, clean_data: list, execution_date: str) -> None: ...


# Concrete implementation:
class TradePipeline(ETLPipeline):
    def extract(self, execution_date):
        return read_from_s3(f"trades/{execution_date}/")

    def transform(self, raw_data):
        return [r for r in raw_data if r["amount"] > 0 and r["trade_id"] is not None]

    def load(self, clean_data, execution_date):
        write_to_snowflake(clean_data, table="fct_trades", partition=execution_date)
```

**Why this impresses:** Shows OOP, separation of concerns, error handling, metrics collection, and production thinking.

### Pattern 10: Concurrent API Calls (Common DE Task)

**Q: "Fetch data from 100 API endpoints efficiently."**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def fetch_all_endpoints(urls: list[str], max_workers: int = 10) -> list[dict]:
    """Fetch data from multiple URLs concurrently."""
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(requests.get, url): url for url in urls}

        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                response = future.result(timeout=30)
                results.append({"url": url, "data": response.json()})
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

    print(f"Success: {len(results)}, Errors: {len(errors)}")
    return results

# Sequential: 100 APIs x 2 sec each = 200 seconds
# Concurrent (10 workers): 100 APIs / 10 workers x 2 sec = 20 seconds
```

### Pattern 11: Date Range Generation (Every DE Needs This)

```python
from datetime import datetime, timedelta

def generate_date_range(start: str, end: str) -> list[str]:
    """Generate list of dates between start and end (inclusive)."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")

    dates = []
    current = start_dt
    while current <= end_dt:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates

# Used for: backfills, partition generation, date-based processing
# generate_date_range("2024-01-01", "2024-01-05")
# -> ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
```

### Pattern 12: Data Profiling (First Thing You Do with New Data)

```python
def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Profile a DataFrame: types, nulls, unique values, sample values."""
    profile = pd.DataFrame({
        "dtype": df.dtypes,
        "non_null": df.count(),
        "null_pct": (df.isnull().sum() / len(df) * 100).round(1),
        "unique": df.nunique(),
        "unique_pct": (df.nunique() / len(df) * 100).round(1),
        "sample": df.iloc[0] if len(df) > 0 else None,
    })
    return profile

# Use this FIRST when you encounter new data. Shows you think about
# data quality BEFORE writing transformations.
```

### Pattern 13: Log Parsing with Regex (Common in DE Coding Rounds)

```python
import re
from collections import Counter

def parse_access_log(log_path: str) -> dict:
    """Parse web server access log and compute statistics."""
    # Apache log format: 127.0.0.1 - - [10/Oct/2024:13:55:36] "GET /api/health HTTP/1.1" 200 2326
    pattern = r'(\d+\.\d+\.\d+\.\d+) .+ "(\w+) (.+) HTTP/.+" (\d+) (\d+)'

    stats = {
        "total_requests": 0,
        "status_codes": Counter(),
        "top_endpoints": Counter(),
        "error_ips": Counter(),
    }

    for line in read_large_file(log_path):
        match = re.match(pattern, line)
        if match:
            ip, method, path, status, size = match.groups()
            stats["total_requests"] += 1
            stats["status_codes"][status] += 1
            stats["top_endpoints"][path] += 1
            if status.startswith("5"):
                stats["error_ips"][ip] += 1

    return stats
```

---

## SQL CODING PATTERNS


### Pattern 1: Window Functions (Most Asked - know this COLD)

**What is a window function?** A function that performs a calculation ACROSS a set of rows related to the current row - WITHOUT collapsing rows like GROUP BY does.

```sql
-- GROUP BY collapses rows (10 rows become 3):
SELECT department, AVG(salary) FROM employees GROUP BY department;
-- Returns: Engineering: 95K, Sales: 75K, HR: 65K  (3 rows)

-- Window function KEEPS all rows (10 rows stay 10):
SELECT name, department, salary,
       AVG(salary) OVER (PARTITION BY department) AS dept_avg
FROM employees;
-- Returns all 10 employees, each with their department's average
```

**The syntax:**
```sql
FUNCTION() OVER (
    PARTITION BY column    -- Like GROUP BY, but keeps rows
    ORDER BY column        -- Order within each partition
    ROWS BETWEEN ...       -- Optional: define the window frame
)
```

**Q: Find the second highest salary per department.**

**How to think about it:** "I need to rank salaries within each department, then pick rank 2. I'll use DENSE_RANK because if two people tie for #1, I still want a #2."

```sql
WITH ranked AS (
    SELECT 
        department_id,
        employee_name,
        salary,
        DENSE_RANK() OVER (
            PARTITION BY department_id   -- Rank within each department
            ORDER BY salary DESC         -- Highest salary = rank 1
        ) AS rank
    FROM employees
)
SELECT department_id, employee_name, salary
FROM ranked
WHERE rank = 2;
```

**Why DENSE_RANK not ROW_NUMBER or RANK?**
```
Salaries: 100K, 100K, 90K, 80K

ROW_NUMBER:  1, 2, 3, 4    -- 100K gets ranks 1 AND 2 (arbitrary)
RANK:        1, 1, 3, 4    -- Skips rank 2 entirely!
DENSE_RANK:  1, 1, 2, 3    -- 90K gets rank 2 (what we want)
```

**Follow-up:** "What if no one has the second highest?" - The query returns empty. Use LEFT JOIN or COALESCE to handle.

**Q: Running total of sales per month.**
```sql
SELECT 
    month,
    sales,
    SUM(sales) OVER (ORDER BY month) AS running_total,
    AVG(sales) OVER (
        ORDER BY month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3m
FROM monthly_sales;
```

### Pattern 2: Self-Joins

**Q: Find employees who earn more than their manager.**
```sql
SELECT e.name AS employee, e.salary, m.name AS manager, m.salary AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

### Pattern 3: GROUP BY with HAVING

**Q: Find customers who placed more than 5 orders in the last month.**
```sql
SELECT customer_id, COUNT(*) AS order_count
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY customer_id
HAVING COUNT(*) > 5
ORDER BY order_count DESC;
```

### Pattern 4: Subqueries

**Q: Find products that have never been ordered.**
```sql
SELECT p.product_name
FROM products p
WHERE p.id NOT IN (
    SELECT DISTINCT product_id FROM order_items
);

-- Better performance with LEFT JOIN:
SELECT p.product_name
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE oi.product_id IS NULL;
```

### Pattern 5: Date Operations

**Q: Find the gap between consecutive orders per customer.**
```sql
SELECT 
    customer_id,
    order_date,
    LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS prev_order,
    order_date - LAG(order_date) OVER (
        PARTITION BY customer_id ORDER BY order_date
    ) AS days_between_orders
FROM orders;
```

### Pattern 6: CASE WHEN

**Q: Categorize customers by total spend.**
```sql
SELECT 
    customer_id,
    SUM(amount) AS total_spend,
    CASE 
        WHEN SUM(amount) >= 10000 THEN 'Platinum'
        WHEN SUM(amount) >= 5000 THEN 'Gold'
        WHEN SUM(amount) >= 1000 THEN 'Silver'
        ELSE 'Bronze'
    END AS tier
FROM transactions
GROUP BY customer_id;
```

### Pattern 7: Pivot/Unpivot

**Q: Pivot monthly sales into columns.**
```sql
SELECT 
    product_id,
    SUM(CASE WHEN month = 1 THEN amount ELSE 0 END) AS jan,
    SUM(CASE WHEN month = 2 THEN amount ELSE 0 END) AS feb,
    SUM(CASE WHEN month = 3 THEN amount ELSE 0 END) AS mar
FROM sales
GROUP BY product_id;
```

### Pattern 8: Consecutive Days / Streaks (Very Common in DE)

**Q: Find users who logged in for 3+ consecutive days.**

**Why this is asked:** Tests your understanding of window functions AND date arithmetic. This pattern appears in user engagement, uptime monitoring, and SLA tracking.

```sql
WITH login_with_groups AS (
    SELECT
        user_id,
        login_date,
        -- Subtract row_number from login_date
        -- Consecutive dates produce the SAME group value
        login_date - INTERVAL '1 day' * ROW_NUMBER() OVER (
            PARTITION BY user_id ORDER BY login_date
        ) AS grp
    FROM user_logins
)
SELECT
    user_id,
    MIN(login_date) AS streak_start,
    MAX(login_date) AS streak_end,
    COUNT(*) AS streak_length
FROM login_with_groups
GROUP BY user_id, grp
HAVING COUNT(*) >= 3
ORDER BY streak_length DESC;
```

**How the trick works:**
```
login_date:    Jan 1, Jan 2, Jan 3, Jan 5, Jan 6
row_number:       1,     2,     3,     4,     5
date - row_num: Dec 31, Dec 31, Dec 31, Jan 1, Jan 1
                ^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^
                Same group = streak!    Same group = streak!
```

### Pattern 9: Gaps and Islands

**Q: Find periods where a sensor was offline (gaps in time-series data).**

```sql
WITH status_changes AS (
    SELECT
        sensor_id,
        timestamp,
        status,
        LAG(status) OVER (PARTITION BY sensor_id ORDER BY timestamp) AS prev_status,
        LAG(timestamp) OVER (PARTITION BY sensor_id ORDER BY timestamp) AS prev_time
    FROM sensor_readings
)
SELECT
    sensor_id,
    prev_time AS offline_start,
    timestamp AS back_online,
    timestamp - prev_time AS downtime_duration
FROM status_changes
WHERE status = 'online' AND prev_status = 'offline';
```

**Why this matters for DE:** Monitoring pipeline SLAs, detecting data gaps, finding missing partitions in data lakes.

### Pattern 10: Deduplication with ROW_NUMBER (The #1 DE SQL Pattern)

**Q: Remove duplicate records, keeping the most recent one per key.**

```sql
-- Method 1: DELETE duplicates (for tables you can modify)
DELETE FROM raw_events
WHERE id IN (
    SELECT id FROM (
        SELECT
            id,
            ROW_NUMBER() OVER (
                PARTITION BY event_id
                ORDER BY event_timestamp DESC
            ) AS rn
        FROM raw_events
    ) ranked
    WHERE rn > 1    -- Delete everything except the latest
);

-- Method 2: SELECT deduplicated (for read-only queries)
WITH deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY event_id
            ORDER BY event_timestamp DESC
        ) AS rn
    FROM raw_events
)
SELECT * FROM deduplicated WHERE rn = 1;
```

**This is the SQL equivalent of your PySpark dedup pattern from Chapter 5's PySpark section.** Same logic, different syntax.

### Pattern 11: Recursive CTEs (Know the Concept)

**Q: Given an employee hierarchy, find all reports under a given manager.**

```sql
WITH RECURSIVE org_chart AS (
    -- Base case: the manager themselves
    SELECT id, name, manager_id, 0 AS level
    FROM employees
    WHERE id = 100    -- Starting manager

    UNION ALL

    -- Recursive case: find their direct reports, then THEIR reports, etc.
    SELECT e.id, e.name, e.manager_id, oc.level + 1
    FROM employees e
    JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT * FROM org_chart ORDER BY level, name;
```

**When this comes up:** Org charts, category trees (parent/child products), bill of materials, file system hierarchies.

### Pattern 12: MERGE / UPSERT (Critical for DE)

**Q: Write a SQL MERGE that updates existing records and inserts new ones.**

```sql
-- Snowflake/Delta Lake MERGE syntax
MERGE INTO dim_instruments AS target
USING staging_instruments AS source
ON target.instrument_id = source.instrument_id

WHEN MATCHED AND source.updated_at > target.updated_at THEN
    UPDATE SET
        target.instrument_name = source.instrument_name,
        target.asset_class = source.asset_class,
        target.updated_at = source.updated_at

WHEN NOT MATCHED THEN
    INSERT (instrument_id, instrument_name, asset_class, created_at, updated_at)
    VALUES (source.instrument_id, source.instrument_name, source.asset_class,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

**Why this matters:** This is how you implement idempotent data loading. Running the same MERGE twice won't create duplicates. This is the SQL version of your Delta Lake PySpark MERGE pattern.

### Pattern 13: Percentile / Median

**Q: Find the median salary per department.**

```sql
-- Snowflake / PostgreSQL
SELECT
    department_id,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) AS p25_salary,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) AS p75_salary,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) -
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) AS iqr
FROM employees
GROUP BY department_id;
```

**IQR (Interquartile Range)** = P75 - P25. Used in data quality checks to detect outliers. Values outside P25 - 1.5*IQR or P75 + 1.5*IQR are potential outliers.

### Pattern 14: Retention / Cohort Analysis

**Q: Calculate Day-7 retention rate by signup cohort.**

```sql
WITH first_login AS (
    -- Get each user's first login date (their cohort)
    SELECT user_id, MIN(login_date) AS cohort_date
    FROM user_logins
    GROUP BY user_id
),
retention AS (
    SELECT
        f.cohort_date,
        COUNT(DISTINCT f.user_id) AS cohort_size,
        COUNT(DISTINCT CASE
            WHEN l.login_date = f.cohort_date + INTERVAL '7 days'
            THEN l.user_id
        END) AS retained_day7
    FROM first_login f
    LEFT JOIN user_logins l ON f.user_id = l.user_id
    GROUP BY f.cohort_date
)
SELECT
    cohort_date,
    cohort_size,
    retained_day7,
    ROUND(100.0 * retained_day7 / cohort_size, 1) AS retention_pct
FROM retention
ORDER BY cohort_date;
```

**Why this matters:** Product analytics, subscription metrics, and customer churn analysis. Shows you can think beyond ETL into business impact.

---


## PYSPARK CODING PATTERNS (Critical for DE Interviews)

**Why this matters:** Data Engineer interviews at companies using Spark will test you on PySpark. These are the exact patterns from your Nomura and Nova work.

### Pattern 1: Read, Join, Aggregate, Write (The bread and butter)

**What the interviewer is testing:** Can you write a basic ETL pipeline in Spark?

```python
from pyspark.sql import SparkSession, functions as F, Window

spark = SparkSession.builder.appName("ETL").getOrCreate()

# Step 1: Read from source (Parquet is columnar, fast)
trades = spark.read.parquet("s3://data/trades/")
instruments = spark.read.parquet("s3://data/instruments/")

# Step 2: Join -- broadcast the SMALL table (instruments ~10K rows)
# broadcast() tells Spark to send the small table to every executor
# instead of shuffling the large table. This avoids expensive data movement.
joined = trades.join(
    F.broadcast(instruments),        # Small table -> sent to all executors
    trades.instrument_id == instruments.id
)
# Without broadcast: Spark shuffles BOTH tables across the network (slow)
# With broadcast: Only instruments (10K rows) is sent, trades stays put

# Step 3: Window function -- running P&L per instrument
window = Window.partitionBy("instrument_id").orderBy("trade_date")
result = joined.withColumn(
    "running_pnl", F.sum("amount").over(window)
).withColumn(
    "trade_rank", F.row_number().over(window)
)

# Step 4: Write partitioned by date (enables partition pruning on reads)
result.write.partitionBy("trade_date").mode("overwrite").parquet("s3://output/")
```

**Follow-up: "What is partition pruning?"**
> When you write `WHERE trade_date = '2024-01-15'`, Spark only reads the `trade_date=2024-01-15/` folder -- skipping ALL other dates. On a year of daily data, this reads 1/365th of the data. That's the 30% optimization I achieved at Nomura.

### Pattern 2: Deduplication with Window Functions

**Q: Remove duplicate records, keeping the most recent one per key.**

```python
from pyspark.sql import Window
from pyspark.sql import functions as F

def deduplicate(df, key_col, timestamp_col):
    """
    Keep only the latest record per key.
    This is how you handle late-arriving data or replayed events.
    """
    window = Window.partitionBy(key_col).orderBy(F.col(timestamp_col).desc())

    return (
        df
        .withColumn("row_num", F.row_number().over(window))
        .filter(F.col("row_num") == 1)    # Keep only the latest
        .drop("row_num")                   # Clean up helper column
    )

# Usage:
clean_df = deduplicate(raw_events, "event_id", "event_timestamp")
```

**Why this pattern matters:** In streaming/batch pipelines, the same event can arrive multiple times (retries, Kafka replay). Dedup is essential for idempotent pipelines.

### Pattern 3: Delta Lake Upsert (Merge)

**Q: Write a PySpark job that upserts new data into an existing Delta table.**

```python
from delta.tables import DeltaTable

def upsert_movies(spark, new_data_path, target_path):
    """
    MERGE = UPDATE existing rows + INSERT new rows in one atomic operation.
    This is how Nova's Silver layer handles catalog updates.
    """
    # Read new batch
    new_df = spark.read.parquet(new_data_path)

    # Load existing Delta table
    target = DeltaTable.forPath(spark, target_path)

    # Merge: match on movie_id
    target.alias("existing").merge(
        new_df.alias("new"),
        "existing.movie_id = new.movie_id"
    ).whenMatchedUpdate(
        # If movie exists: update its metadata
        set={
            "title": "new.title",
            "rating": "new.rating",
            "updated_at": F.current_timestamp()
        }
    ).whenNotMatchedInsert(
        # If movie is new: insert it
        values={
            "movie_id": "new.movie_id",
            "title": "new.title",
            "rating": "new.rating",
            "created_at": F.current_timestamp(),
            "updated_at": F.current_timestamp()
        }
    ).execute()

# This is ATOMIC -- if it fails midway, no partial writes.
# This is what makes Delta Lake better than raw Parquet.
```

**Follow-up: "What if you need to track history?"** -- Use SCD Type 2: instead of `whenMatchedUpdate`, insert a new row with `is_current=true` and mark the old row as `is_current=false`.

### Pattern 4: Data Quality Checks in PySpark

**Q: Write quality validation for a pipeline.**

```python
def validate_dataframe(df, table_name):
    """
    Run quality checks before writing. Fail early, fail loud.
    This is the Silver layer validation from Nova.
    """
    checks = []

    # Check 1: Not empty
    count = df.count()
    checks.append(("row_count > 0", count > 0, count))

    # Check 2: No null primary keys
    null_keys = df.filter(F.col("id").isNull()).count()
    checks.append(("no_null_keys", null_keys == 0, null_keys))

    # Check 3: No duplicate primary keys
    distinct_count = df.select("id").distinct().count()
    checks.append(("no_duplicate_keys", distinct_count == count, count - distinct_count))

    # Check 4: Values in expected range
    bad_ratings = df.filter((F.col("rating") < 0) | (F.col("rating") > 10)).count()
    checks.append(("rating_in_range", bad_ratings == 0, bad_ratings))

    # Report
    for name, passed, value in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {value}")

    failed = [c for c in checks if not c[1]]
    if failed:
        raise ValueError(f"Quality gate FAILED for {table_name}: {[c[0] for c in failed]}")

    return df
```

### Pattern 5: Performance Optimization (The Interview Question)

**Q: "Your Spark job takes 45 minutes. How do you optimize it?"**

```python
# BEFORE (slow):
df1 = spark.read.parquet("s3://big_table/")      # 100GB
df2 = spark.read.parquet("s3://small_table/")     # 50MB

result = df1.join(df2, "key")                      # Shuffle join (BAD for small table)
result = result.filter(col("date") == "2024-01-15") # Filter AFTER join (BAD)
result.write.parquet("s3://output/")               # No partitioning (BAD for reads)

# AFTER (fast - what you did at Nomura):

# Fix 1: Filter BEFORE join (predicate pushdown)
df1 = spark.read.parquet("s3://big_table/").filter(col("date") == "2024-01-15")
# Now we only join 1 day of data instead of all history

# Fix 2: Broadcast join for small table
result = df1.join(F.broadcast(df2), "key")
# Small table sent to all executors. No shuffle of the big table.

# Fix 3: Repartition before expensive operations
result = result.repartition(200, "key")    # Even distribution
# Prevents data skew (one partition with 90% of data)

# Fix 4: Cache intermediate results used multiple times
result.cache()    # Keep in memory for reuse

# Fix 5: Write with partitioning for downstream queries
result.write.partitionBy("date").mode("overwrite").parquet("s3://output/")

# Result: 45 min -> 31 min (30% improvement)
# The biggest wins: predicate pushdown + broadcast join
```

**The 5 Spark optimization levers to mention in interviews:**
1. **Predicate pushdown** -- filter before join, not after
2. **Broadcast join** -- send small table to executors instead of shuffling
3. **Partition pruning** -- read only the partitions you need
4. **Repartitioning** -- fix data skew by redistributing evenly
5. **Caching** -- avoid recomputing intermediate DataFrames

---



> DE interviews test lighter DSA than SDE roles, but you MUST know these patterns.

---

## THE 10 PATTERNS THEY ASK

### 1. Hash Maps / Dictionaries (Most Common)

**Q: Find two numbers in an array that sum to a target.**
```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value ' index
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Time: O(n), Space: O(n)
```

**Q: Find the most frequent element.**
```python
from collections import Counter

def most_frequent(arr: list) -> any:
    return Counter(arr).most_common(1)[0][0]
```

**Q: Group anagrams together.**
```python
from collections import defaultdict

def group_anagrams(words: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for word in words:
        key = ''.join(sorted(word))  # "eat" ' "aet"
        groups[key].append(word)
    return list(groups.values())

# Input: ["eat", "tea", "tan", "ate", "nat", "bat"]
# Output: [["eat","tea","ate"], ["tan","nat"], ["bat"]]
```

---

### 2. Sorting

**Q: Sort a list of (name, age) tuples by age, then name.**
```python
people = [("Bob", 30), ("Alice", 25), ("Charlie", 25)]
sorted_people = sorted(people, key=lambda x: (x[1], x[0]))
# [("Alice", 25), ("Charlie", 25), ("Bob", 30)]
```

**Q: Merge two sorted arrays.**
```python
def merge_sorted(a: list, b: list) -> list:
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i]); i += 1
        else:
            result.append(b[j]); j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result
# Time: O(n+m)
```

---

### 3. Strings

**Q: Check if a string is a palindrome (ignore non-alphanumeric).**
```python
def is_palindrome(s: str) -> bool:
    clean = ''.join(c.lower() for c in s if c.isalnum())
    return clean == clean[::-1]
```

**Q: Longest common prefix.**
```python
def longest_prefix(strs: list[str]) -> str:
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix
```

---

### 4. Arrays / Lists

**Q: Remove duplicates from a sorted array in-place.**
```python
def remove_duplicates(nums: list[int]) -> int:
    if not nums:
        return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[read - 1]:
            nums[write] = nums[read]
            write += 1
    return write  # New length
```

**Q: Rotate an array by k positions.**
```python
def rotate(nums: list[int], k: int) -> list[int]:
    k = k % len(nums)
    return nums[-k:] + nums[:-k]
```

**Q: Find missing number in 1..n.**
```python
def missing_number(nums: list[int]) -> int:
    n = len(nums)
    expected = n * (n + 1) // 2
    return expected - sum(nums)
# Time: O(n), Space: O(1)
```

---

### 5. Stacks / Queues

**Q: Validate balanced parentheses.**
```python
def is_valid(s: str) -> bool:
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')]}':
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
    return len(stack) == 0
```

**Q: Implement a queue using two stacks.**
```python
class MyQueue:
    def __init__(self):
        self.push_stack = []
        self.pop_stack = []
    
    def push(self, x):
        self.push_stack.append(x)
    
    def pop(self):
        if not self.pop_stack:
            while self.push_stack:
                self.pop_stack.append(self.push_stack.pop())
        return self.pop_stack.pop()
```

---

### 6. Linked Lists (Less Common for DE)

**Q: Reverse a linked list.**
```python
def reverse_list(head):
    prev = None
    current = head
    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node
    return prev
```

**Q: Detect a cycle.**
```python
def has_cycle(head) -> bool:
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

---

### 7. Trees (Know the Basics)

**Q: Inorder traversal.**
```python
def inorder(root) -> list:
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)
```

**Q: Max depth of binary tree.**
```python
def max_depth(root) -> int:
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

---

### 8. Graphs (BFS/DFS)

**Q: Find if a path exists between two nodes.**
```python
from collections import deque

def has_path(graph: dict, start: int, end: int) -> bool:
    visited = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == end:
            return True
        visited.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return False
```

---

### 9. Binary Search

**Q: Find insertion position.**
```python
def search_insert(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return lo
# Time: O(log n)
```

---

### 10. Dynamic Programming (Rare for DE, but know basics)

**Q: Climbing stairs " how many ways to reach step n?**
```python
def climb_stairs(n: int) -> int:
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
```

---

## BIG-O CHEAT SHEET

| Notation | Name | Example |
|---|---|---|
| O(1) | Constant | Dictionary lookup |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Single loop through array |
| O(n log n) | Linearithmic | Sorting (merge sort, timsort) |
| O(n^2) | Quadratic | Nested loops |
| O(2^n) | Exponential | Recursive subsets |

**When they ask "What's the time complexity?":**
- Single loop ' O(n)
- Nested loops ' O(n^2)
- Binary search / divide ' O(log n)
- Sort then search ' O(n log n)
- Hash map lookup ' O(1) average
- Spark shuffle ' O(n) data transfer across network

---

## PYTHON-SPECIFIC KNOWLEDGE

### Q: List vs Tuple vs Set vs Dict " when to use each?

| Type | Mutable | Ordered | Duplicates | Lookup | Use Case |
|---|---|---|---|---|---|
| list | Yes | Yes | Yes | O(n) | Ordered collection |
| tuple | No | Yes | Yes | O(n) | Immutable sequence, dict keys |
| set | Yes | No | No | O(1) | Membership testing, dedup |
| dict | Yes | Yes* | Keys: No | O(1) | Key-value mapping |

### Q: What is a generator and why use it?

```python
# Regular function " loads ALL data into memory
def read_all(path):
    return open(path).readlines()  # 10GB file ' 10GB RAM!

# Generator " yields one line at a time
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line  # Only 1 line in memory at a time

# Usage " memory efficient
for line in read_lines("huge_file.csv"):
    process(line)
```

**In DE**: Essential for processing files larger than RAM.

### Q: What are decorators?

```python
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@timer
def process_data(df):
    # ... expensive operation
    return df.transform(...)

# process_data(df) ' "process_data took 3.45s"
```

### Q: What is `__init__`, `__str__`, `__repr__`?

```python
class Pipeline:
    def __init__(self, name, source):     # Constructor
        self.name = name
        self.source = source
    
    def __str__(self):                     # Human-readable
        return f"Pipeline: {self.name}"
    
    def __repr__(self):                    # Debug representation
        return f"Pipeline(name='{self.name}', source='{self.source}')"
```

### Q: Exception handling best practices?

```python
# Bad " catches everything, hides bugs:
try:
    process()
except:
    pass

# Good " specific exceptions, logging:
try:
    df = spark.read.parquet(path)
except FileNotFoundError:
    logger.error(f"Source file not found: {path}")
    raise
except AnalysisException as e:
    logger.error(f"Schema error: {e}")
    send_alert(f"Pipeline failed: schema mismatch at {path}")
    raise
```

