"""
Unit tests for SOTA Algorithms Engine (backend/sota_algorithms.py).
"""

import pytest
from backend.sota_algorithms import HyperLogLogCounter, MinHashDeduplicator, ConsistentHashRing


def test_hyperloglog_counter():
    hll = HyperLogLogCounter(precision=8)
    for i in range(100):
        hll.add(f"patient_{i}")
    cnt = hll.count()
    # Expect count within reasonable estimation bound
    assert 80 <= cnt <= 120


def test_minhash_deduplicator():
    dedup = MinHashDeduplicator(num_hashes=16)
    doc1 = "Patient diagnosed with type 2 diabetes mellitus and hypertension."
    doc2 = "Patient diagnosed with type 2 diabetes mellitus and severe hypertension."
    doc3 = "Unrelated medical notes about orthopedic knee surgery."

    sig1 = dedup.compute_signature(doc1)
    sig2 = dedup.compute_signature(doc2)
    sig3 = dedup.compute_signature(doc3)

    sim_1_2 = dedup.jaccard_similarity(sig1, sig2)
    sim_1_3 = dedup.jaccard_similarity(sig1, sig3)

    assert sim_1_2 > sim_1_3
    assert sim_1_2 >= 0.5


def test_consistent_hash_ring():
    ring = ConsistentHashRing(virtual_nodes=10)
    ring.add_node("node1")
    ring.add_node("node2")

    target = ring.get_node("patient_record_99")
    assert target in ["node1", "node2"]
