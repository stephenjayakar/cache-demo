from collections import namedtuple


# Basic test helper
def p(exp, act, msg=""):
    print(f"{msg} expected: {exp} actual: {act}")


# This is probably what we return from the cache class
class DataResult:
    def __init__(self, found: bool, data: any):
        self.found = found
        self.data = data


class DequeNode:
    def __init__(self, val):
        # While this is called `value`, this is actually the key in
        # the way we're using it as we need this data structure to
        # link back to the actual store for removal
        self.val = val
        self.prev = None
        self.nxt = None


class Deque:
    def __init__(self):
        self.head = None
        self.tail = None

    def _possibly_reset_pointers(self):
        if self.head is None or self.tail is None:
            self.head = None
            self.tail = None

    # All of the following operations are O(1)
    # append returns the pointer to be stored in a higher data structure
    # for O(1) removes
    def append(self, val):
        node = DequeNode(val)
        if self.head is None and self.tail is None:
            self.head = node
            self.tail = node
        else:
            self.tail.nxt = node
            node.prev = self.tail
            self.tail = self.tail.nxt
        return node

    def pop_left(self):
        if self.head is None:
            return None
        else:
            node = self.head
            self.head = self.head.nxt
            self._possibly_reset_pointers()
            return node

    def remove_node(self, node):
        if self.head is None or self.tail is None:
            raise Exception("invalid passed node")
        prev = node.prev
        nxt = node.nxt
        if prev is not None:
            prev.nxt = nxt
        if nxt is not None:
            nxt.prev = prev
        if self.head == node:
            self.head = nxt
        if self.tail == node:
            self.tail = prev
        self._possibly_reset_pointers()

    def debug_print(self):
        vals = []
        pointer = self.head
        while pointer is not None:
            vals.append(str(pointer.val))
            pointer = pointer.nxt
        return ", ".join(vals)


# We're storing the lru_node reference to support O(1) deletions inside the queue
CacheEntry = namedtuple("CacheEntry", ["value", "lru_node"])
CacheEntry.__repr__ = lambda x: str(x.value)


class Cache:
    def __init__(self, capacity):
        self.store = {}
        self.capacity = capacity
        self.lru_deque = Deque()

    def get(self, key):
        if key in self.store:
            cache_entry = self.store[key]
            node, value = cache_entry.lru_node, cache_entry.value
            # Delete & readd the node to put it on the MRU
            new_node = self._remove_and_readd_node(node)
            self.store[key] = CacheEntry(value, new_node)
            return DataResult(True, value)
        else:
            return DataResult(False, None)

    def _size(self):
        return len(self.store.keys())

    def _remove_and_readd_node(self, node):
        value = node.val
        self.lru_deque.remove_node(node)
        new_node = self.lru_deque.append(value)
        return new_node

    def put(self, key, value):
        # Update case
        if key in self.store:
            cache_entry = self.store[key]
            new_node = self._remove_and_readd_node(cache_entry.lru_node)
            self.store[key] = CacheEntry(value, new_node)
            return
        # New insertion case
        node = self.lru_deque.append(key)
        self.store[key] = CacheEntry(value, node)
        # This should behave if capacity is 1. Obviously not if 0
        if self._size() > self.capacity:
            node = self.lru_deque.pop_left()
            if node is None:
                raise Exception("lru data structure is not in line with cache")
            key = node.val
            del self.store[key]

    def _debug_print(self):
        return str(self.store)


class MultiLevelCache:
    def __init__(self, capacity_l1: int, capacity_l2: int):
        """
        Initializes L1 and L2 caches with the given capacities.
        """
        self.l1 = Cache(capacity_l1)
        self.l2 = Cache(capacity_l2)

    def get_or_fetch(self, key: str, fetch_func: callable) -> DataResult:
        """
        1) If the key is in L1, return it.
        2) Else if the key is in L2, 'promote' it to L1 (inserting into L1 as the most recently used)
           and return it.
        3) Otherwise, call fetch_func(key) to get the data.
           - If fetch_func indicates the data was found, store into L2 first, then promote it into L1.
           - Return that data with found=True.
           - If fetch_func indicates the data was not found, return found=False.

        SJ: If it's in L1 but not L2, I'm not sure if I also add it to L2. Will not for now
        * `fetch_func` returns found, data
        """
        # L1
        data_result = self.l1.get(key)
        if data_result.found:
            return data_result
        # L2
        data_result = self.l2.get(key)
        if data_result.found:
            self.l1.put(key, data_result.data)
            return data_result
        # miss
        found, data = fetch_func(key)
        if not found:
            return DataResult(False, None)
        else:
            self.l2.put(key, data)
            self.l1.put(key, data)
            return DataResult(True, data)

    def put(self, key: str, value: any):
        """
        Put a new key-value pair into L1.
        If L1 is at capacity, evict the LRU from L1.
        """
        self.l1.put(key, value)

    # This should be ordered so we can compare
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
        return {
            "l1_keys": self.l1.lru_deque.debug_print(),
            "l2_keys": self.l2.lru_deque.debug_print(),
        }


if __name__ == "__main__":
    print("deque test")
    deque = Deque()
    deque.append(1)
    deque.append(2)
    node = deque.append(3)
    deque.append(4)
    deque.append(5)
    p("1 2 3 4 5", deque.debug_print())
    deque.pop_left()
    p("2 3 4 5", deque.debug_print())
    deque.remove_node(node)
    deque.append(3)
    p("2 4 5 3", deque.debug_print())
    deque.pop_left()
    deque.pop_left()
    deque.pop_left()
    deque.pop_left()
    deque.append(5)
    deque.append(6)
    p("5 6", deque.debug_print())

    # Cache tests
    print("cache tests")
    # Update test
    print("update test")
    c = Cache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    p("three entries", c._debug_print())
    c.put(4, 4)
    p("1 removed", c._debug_print())
    c.put(2, 4)
    p("2 changed", c._debug_print())
    c.put(5, 5)
    p("3 removed", c._debug_print())

    # Get test
    print("\nget test")
    c = Cache(3)
    c.put(1, 1)
    c.put(2, 2)
    c.put(3, 3)
    p("three entries", c._debug_print())
    c.get(1)
    c.put(4, 4)
    p("2 removed", c._debug_print())

    # multilevel cache tests
    # things to test
    # 1. basic removal with `put` in l1
    # 2. fetching things that fill l2, but then l1 is blown up
    # 3. ...and then eventually l2 starts replacing
    # 4. data isn't found in DB - what happens?
    # 5. value is "promoted" and then not removed in both caches somehow
    print("basic multilevel test")

    def mock_db_fetch_func(key: str):
        # Simulate a slow database fetch.
        # Return (found=True, data) if key is recognized, else (found=False, None)
        db_data = {
            "user:1": {"name": "Alice"},
            "user:2": {"name": "Bob"},
            "user:3": {"name": "Stephen"},
            "user:4": {"name": "David"},
        }
        if key in db_data:
            return True, db_data[key]
        return False, None

    # Create a multi-level cache with capacities for L1=2, L2=3
    ml_cache = MultiLevelCache(2, 3)

    result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
    p("alice found", result.data)

    p("both caches should have", ml_cache.stats())

    ml_cache.put("hello", "world")
    p("hello should now be in l1. there should be order", ml_cache.stats())
    ml_cache.put("I am", "stephen")
    p("new entry in l1, first removed", ml_cache.stats())

    print("test 2 + 3: filling up l1, then l2")
    ml_cache = MultiLevelCache(2, 3)
    result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:2", mock_db_fetch_func)
    p("both caches should have", ml_cache.stats())
    result = ml_cache.get_or_fetch("user:3", mock_db_fetch_func)
    p("l1 removed user 1", ml_cache.stats())
    result = ml_cache.get_or_fetch("user:4", mock_db_fetch_func)
    p("l1 removed user 1, l2 removed user 1", ml_cache.stats())

    print("test 5: value promotion")
    ml_cache = MultiLevelCache(2, 3)
    result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:2", mock_db_fetch_func)
    p("both caches should have", ml_cache.stats())
    result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
    p("user 2 promoted in l1", ml_cache.stats())
    result = ml_cache.get_or_fetch("user:3", mock_db_fetch_func)
    p("user 1 removed in l1, user 3 in both", ml_cache.stats())
    result = ml_cache.get_or_fetch("user:2", mock_db_fetch_func)
    p("l1 removed 1 added 2, l2 promoted 2", ml_cache.stats())

    print("test 4: value not found")
    ml_cache = MultiLevelCache(2, 3)
    result = ml_cache.get_or_fetch("user:1", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:2", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:100", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:100", mock_db_fetch_func)
    result = ml_cache.get_or_fetch("user:100", mock_db_fetch_func)
    p("user 1 and 2 in both caches", ml_cache.stats())
