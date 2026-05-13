# 22 — DSA Patterns for Data Engineer Interviews

> DE interviews test lighter DSA than SDE roles, but you MUST know these patterns.

---

## THE 10 PATTERNS THEY ASK

### 1. Hash Maps / Dictionaries (Most Common)

**Q: Find two numbers in an array that sum to a target.**
```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value → index
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
        key = ''.join(sorted(word))  # "eat" → "aet"
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

**Q: Climbing stairs — how many ways to reach step n?**
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
- Single loop → O(n)
- Nested loops → O(n^2)
- Binary search / divide → O(log n)
- Sort then search → O(n log n)
- Hash map lookup → O(1) average
- Spark shuffle → O(n) data transfer across network

---

## PYTHON-SPECIFIC KNOWLEDGE

### Q: List vs Tuple vs Set vs Dict — when to use each?

| Type | Mutable | Ordered | Duplicates | Lookup | Use Case |
|---|---|---|---|---|---|
| list | Yes | Yes | Yes | O(n) | Ordered collection |
| tuple | No | Yes | Yes | O(n) | Immutable sequence, dict keys |
| set | Yes | No | No | O(1) | Membership testing, dedup |
| dict | Yes | Yes* | Keys: No | O(1) | Key-value mapping |

### Q: What is a generator and why use it?

```python
# Regular function — loads ALL data into memory
def read_all(path):
    return open(path).readlines()  # 10GB file → 10GB RAM!

# Generator — yields one line at a time
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line  # Only 1 line in memory at a time

# Usage — memory efficient
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

# process_data(df) → "process_data took 3.45s"
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
# Bad — catches everything, hides bugs:
try:
    process()
except:
    pass

# Good — specific exceptions, logging:
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
