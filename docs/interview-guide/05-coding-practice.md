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
# â†' {"a.b": 1, "a.c.d": 2}
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


---


> DE interviews test lighter DSA than SDE roles, but you MUST know these patterns.

---

## THE 10 PATTERNS THEY ASK

### 1. Hash Maps / Dictionaries (Most Common)

**Q: Find two numbers in an array that sum to a target.**
```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value â†' index
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
        key = ''.join(sorted(word))  # "eat" â†' "aet"
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

**Q: Climbing stairs â€" how many ways to reach step n?**
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
- Single loop â†' O(n)
- Nested loops â†' O(n^2)
- Binary search / divide â†' O(log n)
- Sort then search â†' O(n log n)
- Hash map lookup â†' O(1) average
- Spark shuffle â†' O(n) data transfer across network

---

## PYTHON-SPECIFIC KNOWLEDGE

### Q: List vs Tuple vs Set vs Dict â€" when to use each?

| Type | Mutable | Ordered | Duplicates | Lookup | Use Case |
|---|---|---|---|---|---|
| list | Yes | Yes | Yes | O(n) | Ordered collection |
| tuple | No | Yes | Yes | O(n) | Immutable sequence, dict keys |
| set | Yes | No | No | O(1) | Membership testing, dedup |
| dict | Yes | Yes* | Keys: No | O(1) | Key-value mapping |

### Q: What is a generator and why use it?

```python
# Regular function â€" loads ALL data into memory
def read_all(path):
    return open(path).readlines()  # 10GB file â†' 10GB RAM!

# Generator â€" yields one line at a time
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line  # Only 1 line in memory at a time

# Usage â€" memory efficient
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

# process_data(df) â†' "process_data took 3.45s"
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
# Bad â€" catches everything, hides bugs:
try:
    process()
except:
    pass

# Good â€" specific exceptions, logging:
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

