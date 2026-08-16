"""
Backward-compatibility bridge for backend.data_structures algorithms
"""
from backend.data_structures import ConsistentHashRing, HyperLogLogCounter, MinHashDeduplicator

hll_counter = HyperLogLogCounter()
minhash_dedup = MinHashDeduplicator()
hash_ring = ConsistentHashRing()
