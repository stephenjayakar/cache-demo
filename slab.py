"""
Previous file: multi-level-cache.py

In this file, we're going to attempt to use the `slab` abstraction. So we're going to have a class

LRUCache:
  key -> index
  slab[index] = metadata for key

Metadata:
  value,
  prev
  nxt

Instead of multiple datastructures, where we had a hashmap & a linked list separately, we're going to store everything contiguously.

This can support all operations but conceptually is harder to understand. It also makes "upgrading to MRU" much more complicated.
"""

from collections import namedtuple

CacheEntry = namedtuple("CacheEntry", ("value", "prev", "nxt"))


class LRUCache:
    def __init__(self, capacity):
        # While this isn't exactly an malloc(sizeof(CacheEntry)), I
        # didn't see the point of overoptimizing here as regardless
        # it's going to be a jump in Python
        self.slab = [None] * capacity
        self.capacity = capacity
        self.key_to_index = {}
        self.head = None
        self.tail = None
        self.size = 0

    def get(self, key):
        if key in self.key_to_index:
            index = self.key_to_index[key]
            self._promote_to_mru(index)
            return self.slab[index].value
        else:
            return None

    def put(self, key, value):
        """
        `put` behavior changes when at capacity
        1. when not at capacity: you add it to the free space
        2. when at capacity: you replace the LRU

        in both examples, you make it the tail

        when modifying, it's also different. you modify the value, and
        promote it to MRU
        """
        prev = self.tail
        nxt = None
        new_cache_entry = CacheEntry(value, prev, nxt)
        if key not in self.key_to_index:
            # Case 1: Evict LRU case
            if self.size == self.capacity:
                index = self.head
                lru_cache_entry = self.slab[index]
                # 1. Update the head to move on to the evicted next
                #    Also have to rewire it to not have a prev
                new_head_entry = self.slab[lru_cache_entry.nxt]
                new_head_entry = CacheEntry(
                    new_head_entry.value,
                    None,
                    new_head_entry.nxt,
                )
                self.head = lru_cache_entry.nxt
                self.slab[lru_cache_entry.nxt] = new_head_entry
                # 2. Put in the new entry at the tail
                #    + have the previous tail point to it
                self.slab[index] = new_cache_entry
                self.tail.nxt = index
                self.tail = index
            # Case 2: Slab isn't full yet
            else:
                index = self.size
                self.key_to_index[key] = index
                self.slab[index] = new_cache_entry
                if self.head is None:
                    self.head = index
                # If there was a tail, we want it to point to the new tail
                if self.tail is not None:
                    prev_tail_cache_entry = self.slab[self.tail]
                    self.slab[self.tail] = CacheEntry(
                        prev_tail_cache_entry.value,
                        prev_tail_cache_entry.prev,
                        index,
                    )
                self.tail = index
                self.size += 1
        else:
            # Edit case: Upgrade to MRU
            index = self.key_to_index[key]
            self._promote_to_mru(index)
            # Still have to update the value. Unfortunately a double write, but a better abstraction
            self.slab[index] = new_cache_entry

    def _promote_to_mru(self, index):
        cache_entry = self.slab[index]
        # Actually update the cache entry first for the modified value
        new_cache_entry = CacheEntry(
            cache_entry.value,
            # We already know it will be the new tail
            self.tail,
            None,
        )
        self.slab[index] = new_cache_entry
        # 1. Update cache prev and cache nxt to point at each other
        prev = cache_entry.prev
        nxt = cache_entry.nxt
        if prev is not None:
            old_prev = self.slab[prev]
            new_prev = CacheEntry(
                old_prev.value,
                old_prev.prev,
                nxt,
            )
            self.slab[prev] = new_prev
        if nxt is not None:
            old_nxt = self.slab[nxt]
            new_nxt = CacheEntry(
                old_nxt.value,
                prev,
                old_nxt.nxt,
            )
            self.slab[nxt] = new_nxt
        # 2. Possibly update the tail, and possibly the head
        if index != self.tail:
            prev_tail = self.slab[self.tail]
            # Have the tail point at the new tail
            new_prev_tail = CacheEntry(
                prev_tail.value,
                prev_tail.prev,
                index,
            )
            self.slab[self.tail] = new_prev_tail
            self.tail = index
        if index == self.head:
            self.head = cache_entry.nxt

    def debug_str(self):
        print(self.head, self.slab)
        # Create index to keys so we can print keys
        index_to_keys = {}
        for k in self.key_to_index.keys():
            index_to_keys[self.key_to_index[k]] = k
        values = []
        pointer = self.head
        while pointer is not None:
            cache_entry = self.slab[pointer]
            values.append(f"{index_to_keys[pointer]}:{str(cache_entry.value)}")
            pointer = cache_entry.nxt
        return ", ".join(values)


def p(exp, act):
    print(f" {exp} -- {act}")


if __name__ == "__main__":
    cache = LRUCache(3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    p("a:1, b:2, c:3", cache.debug_str())
    cache.get("b")
    p("a:1, c:3, b:2", cache.debug_str())
    cache.put("c", 2)
    p("a:1, b:2, c:2", cache.debug_str())
