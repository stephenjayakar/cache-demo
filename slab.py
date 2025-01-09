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

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    key: Any
    value: Any
    prev: int | None
    nxt: int | None


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
        if key not in self.key_to_index:
            new_cache_entry = CacheEntry(key, value, self.tail, None)
            # Case 1: Evict LRU case
            if self.size == self.capacity:
                index = self.head
                lru_cache_entry = self.slab[index]
                # 1. Update the head to move on to the evicted next
                #    Also have to rewire it to not have a prev
                new_head_entry = self.slab[lru_cache_entry.nxt]
                new_head_entry.prev = None
                self.head = lru_cache_entry.nxt
                # 2. Put in the new entry at the tail
                #    + have the previous tail point to it
                self.slab[index] = new_cache_entry
                self.slab[self.tail].nxt = index
                del self.key_to_index[lru_cache_entry.key]
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
                    prev_tail_cache_entry.nxt = index
                self.size += 1
            # We're always going to be putting it as the new tail
            self.tail = index
            self.key_to_index[key] = index
        else:
            # Edit case: Upgrade to MRU
            index = self.key_to_index[key]
            cache_entry = self._promote_to_mru(index)
            # Actually update the value
            cache_entry.value = value

    def _promote_to_mru(self, index):
        cache_entry = self.slab[index]

        # 1. Update cache prev and cache nxt to point at each other
        prev_index = cache_entry.prev
        nxt_index = cache_entry.nxt
        if prev_index is not None:
            prev_cache_entry = self.slab[prev_index]
            prev_cache_entry.nxt = nxt_index
        if nxt_index is not None:
            nxt_cache_entry = self.slab[nxt_index]
            nxt_cache_entry.prev = prev_index

        # 2. Actually update the cache entry first for the modified value
        # * We already know it will be the new tail
        cache_entry.prev = self.tail
        cache_entry.nxt = None

        # 3. Possibly update the tail, and possibly the head
        if index != self.tail:
            prev_tail = self.slab[self.tail]
            # Have the tail point at the new tail
            prev_tail.nxt = index
            self.tail = index
        # Update the head ONLY if the promoted elem was the previous
        # head, and if there's > 1 value.
        if index == self.head and nxt_index is not None:
            self.head = nxt_index
        return cache_entry

    def debug_str(self):
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
    cache.put("d", 4)
    cache.put("e", 5)
    p("c:2, d:4, e:5", cache.debug_str())
    cache.get("c")
    p("d:4, e:5, c:2", cache.debug_str())
