"""
Unit tests for SOTA Data Structures Engine (backend/sota_data_structures.py).
"""

import pytest
from backend.sota_data_structures import BloomFilter, CircularRingBuffer, RadixPrefixTrie


def test_bloom_filter_membership():
    bf = BloomFilter(capacity=1000, error_rate=0.01)
    bf.add("patient_1001")
    bf.add("revoked_jwt_xyz")

    assert bf.contains("patient_1001") is True
    assert bf.contains("revoked_jwt_xyz") is True
    assert bf.contains("non_existent_id_999") is False


def test_circular_ring_buffer():
    rb = CircularRingBuffer(capacity=3)
    rb.push(120)
    rb.push(125)
    rb.push(130)

    assert rb.get_latest() == [120, 125, 130]

    # Overwrite oldest (120) with 135
    rb.push(135)
    assert rb.get_latest() == [125, 130, 135]

    popped = rb.pop()
    assert popped == 125
    assert rb.get_latest() == [130, 135]


def test_radix_prefix_trie():
    trie = RadixPrefixTrie()
    trie.insert("E11.9", {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"})
    trie.insert("E11.65", {"code": "E11.65", "description": "Type 2 diabetes mellitus with hyperglycemia"})
    trie.insert("I10", {"code": "I10", "description": "Essential hypertension"})

    matches = trie.search_prefix("E11", max_results=5)
    assert len(matches) == 2
    codes = [m["code"] for m in matches]
    assert "E11.9" in codes
    assert "E11.65" in codes
    assert "I10" not in codes
