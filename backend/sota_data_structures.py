"""
Backward-compatibility bridge for backend.data_structures
"""
from backend.data_structures import BloomFilter, CircularRingBuffer, RadixPrefixTrie, RadixPrefixTrieNode

bloom_filter = BloomFilter()
radix_trie = RadixPrefixTrie()
