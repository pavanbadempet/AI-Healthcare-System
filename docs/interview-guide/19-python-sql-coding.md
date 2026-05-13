# 19 — Python & SQL Coding Round

> Data Engineer interviews ALWAYS have a coding round. Here are the patterns they ask.

---

## PYTHON CODING PATTERNS

### Pattern 1: File Processing (Very Common for DE)

**Q: Read a CSV, find duplicates, write clean data to Parquet.**
```python
import pandas as pd

def process_file(input_path: str, output_path: str) -> dict:
    df = pd.read_csv(input_path)
    
    # Find duplicates
    dupes = df[df.duplicated(subset=["id"], keep=False)]
    print(f"Found {len(dupes)} duplicate rows")
    
    # Remove duplicates (keep last)
    clean = df.drop_duplicates(subset=["id"], keep="last")
    
    # Write to Parquet
    clean.to_parquet(output_path, index=False)
    
    return {
        "input_rows": len(df),
        "duplicates_removed": len(df) - len(clean),
        "output_rows": len(clean)
    }
```

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
# → {"a.b": 1, "a.c.d": 2}
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

---

## SQL CODING PATTERNS

### Pattern 1: Window Functions (Most Asked)

**Q: Find the second highest salary per department.**
```sql
WITH ranked AS (
    SELECT 
        department_id,
        employee_name,
        salary,
        DENSE_RANK() OVER (
            PARTITION BY department_id 
            ORDER BY salary DESC
        ) AS rank
    FROM employees
)
SELECT department_id, employee_name, salary
FROM ranked
WHERE rank = 2;
```

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

---

## SPARK CODING PATTERNS

### Q: Read Parquet, join, aggregate, write.
```python
from pyspark.sql import SparkSession, functions as F, Window

spark = SparkSession.builder.appName("ETL").getOrCreate()

# Read
trades = spark.read.parquet("s3://data/trades/")
instruments = spark.read.parquet("s3://data/instruments/")

# Join (broadcast small dimension)
joined = trades.join(
    F.broadcast(instruments), 
    trades.instrument_id == instruments.id
)

# Window function
window = Window.partitionBy("instrument_id").orderBy("trade_date")
result = joined.withColumn(
    "running_pnl", F.sum("amount").over(window)
).withColumn(
    "rank", F.row_number().over(window)
)

# Write partitioned
result.write.partitionBy("trade_date").mode("overwrite").parquet("s3://output/")
```
