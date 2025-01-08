This is an interview problem I generated from ChatGPT. I wrote a rough solution for it, and then had it generate a visualization which ended up being pretty cool!

![screenshot]("screenshot.png")

---

# 1. Interview Question: Multi-Level Cache

## Scenario

- You are designing a **two-level cache** (L1 and L2) for a backend system.
- The user of this library does not directly access the underlying caches. Instead, they call a method called `get_or_fetch`, which will:
    1. Check if the requested key exists in L1.
    2. If it is not in L1, check L2.
    3. If it is neither in L1 nor L2, call a user-provided function `fetch_func(key)` that simulates fetching data from a slow resource (e.g., a database).
    4. After fetching data from the slow resource, store it into L2 and then into L1.
- **Both caches have limited capacity.** For simplicity, each cache must evict its **Least Recently Used** (LRU) entry when it is full and a new entry is added.

## Requirements

1. **Two data stores**:
    - **L1** cache with capacity `capacity_l1`.
    - **L2** cache with capacity `capacity_l2`.
2. **LRU Eviction** in both caches:
    - If the user tries to put a new key-value pair in an already-full cache, evict the least recently used key from that cache.
    - Accessing or updating a key should mark it as “most recently used.”
3. **Interface**:
    
    ```python
    class DataResult:
        def __init__(self, found: bool, data: any):
            self.found = found
            self.data = data
    
    class MultiLevelCache:
        def __init__(self, capacity_l1: int, capacity_l2: int):
            """
            Initializes L1 and L2 caches with the given capacities.
            """
            pass
    
        def get_or_fetch(self, key: str, fetch_func: callable) -> DataResult:
            """
            1) If the key is in L1, return it.
            2) Else if the key is in L2, 'promote' it to L1 (inserting into L1 as the most recently used)
               and return it.
            3) Otherwise, call fetch_func(key) to get the data.
               - If fetch_func indicates the data was found, store into L2 first, then promote it into L1.
               - Return that data with found=True.
               - If fetch_func indicates the data was not found, return found=False.
            """
            pass
    
        def put(self, key: str, value: any):
            """
            Put a new key-value pair into L1. 
            If L1 is at capacity, evict the LRU from L1.
            """
            pass
    
        def stats(self) -> dict:
            """
            Return any relevant stats or state (like current items in L1 and L2) 
            so the user can debug what's in the caches.
            Example:
            {
              "l1_keys": [...],
              "l2_keys": [...]
            }
            """
            pass
    ```
    
4. **Behavior**:
    - Access order must maintain recency for LRU eviction.
    - If an item is in L2 but not in L1, and we call `get_or_fetch(key)`, we want to **“promote”** it to L1, meaning we insert it into L1 as the most recently used.
    - If L1 is full, we evict its LRU item.
    - If we have to “bring in” a new item to L2 (after fetching from DB), and L2 is full, we also evict the LRU from L2.

## Clarifications to think about

- How do we mark items as “most recently used” in Python or your chosen language? (Hint: Often an `OrderedDict`, a linked list with a HashMap, or a similar structure is used for LRU logic.)
- How do we handle the case where `fetch_func(key)` fails to find data? For instance, it might return `None` or throw an exception. We can standardize it by returning a “found” boolean.
- How do we handle concurrency? (For a simpler interview, you can ignore concurrency, but be prepared to talk about thread-safety if asked.)

---

# 2. Example Usage

Below is a snippet that shows how the user might interact with your `MultiLevelCache` once it’s implemented:

```python
def mock_db_fetch_func(key: str):
    # Simulate a slow database fetch. 
    # Return (found=True, data) if key is recognized, else (found=False, None)
    db_data = {
        "user:1": {"name": "Alice"},
        "user:2": {"name": "Bob"}
    }
    if key in db_data:
        return True, db_data[key]
    return False, None

# Create a multi-level cache with capacities for L1=2, L2=3
ml_cache = MultiLevelCache(2, 3)

# Attempt to fetch user:1 (not in L1 or L2 initially)
result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
print(result.found, result.data) 
# Expect True, {'name': 'Alice'} 
# (It should have fetched from the DB and stored into L2 and L1.)

# Cache stats
print(ml_cache.stats())  
# L1 should contain ["user:1"]; L2 should contain ["user:1"] as well.

# Put a key manually into L1
ml_cache.put("hello", "world")
print(ml_cache.stats())
# L1 should have ["user:1", "hello"] in some LRU order.
```
