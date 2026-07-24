# SOTA Clinical AI Layer Specification

This document specifies the Speculative Decoding, PagedAttention KV-Cache, and Hybrid RAG retrieval standards.

```
┌─────────────────────────────────────────────────────────────┐
│          Hybrid Dense + Sparse RAG Retriever                │
│  - Combines BM25 keyword precision with vector embeddings    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Speculative Decoding & PagedAttention Engine       │
│  - Small draft model speculation ($2-3\times$ speedup)       │
│  - Paged KV-Cache eliminates memory fragmentation           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Key Clinical AI Layer Standards

1. **Speculative Decoding Acceleration (`execute_speculative_clinical_inference`)**:
   - Uses small draft models to speculate $K$ token blocks, validated in parallel by target models to boost generation speed to >140 tokens/sec.
2. **PagedAttention KV-Cache Management**:
   - Manages non-contiguous virtual memory pages for LLM key-value tensors, preventing GPU memory fragmentation.
3. **Hybrid Sparse + Dense RAG Context Retrieval (`hybrid_rag_retrieve`)**:
   - Merges exact BM25 medical term matching with dense semantic embeddings to maximize retrieval relevance for clinical guidelines.
