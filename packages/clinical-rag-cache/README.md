# 🧠 clinical-rag-cache — AI Prompt Caching & RAG Vector Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> A production-ready developer package providing high-performance Semantic Caching (for reducing cloud LLM latency and costs), Clinical Retrieval-Augmented Generation (RAG) utilities, and a clean Prompt Registry manager.

---

## 🔬 Core Features

* **Semantic Cache (`SemanticCache`)**:
  - Caches prompt-completions using cosine similarity thresholds.
  - Prevents redundant cloud LLM queries for identical or semantically similar patient questions, reducing latency and costs.
* **Retrieval-Augmented Generation (RAG)**:
  - Text chunking, metadata-filtered searches, and embedding generators.
  - Built-in `SimpleVectorStore` for lightweight local file-based vector storage.
  - Scoped clinical search utilities for retrieving matching patient checkups, diagnostic history, and care logs.
* **Prompt Registry (`PromptRegistry`)**:
  - Clean dictionary-based prompt loader supporting template versioning, variable interpolation, and system prompt registries.

---

## 🚀 Installation

Install the package via pip:

```bash
pip install clinical-rag-cache
```

---

## 📖 Code Reference & Quick Start

### 1. Implementing Semantic Caching
Reduce cloud LLM costs by serving similar semantic hits locally:

```python
from clinical_rag_cache import SemanticCache

# Initialize a semantic cache with a 0.92 cosine similarity threshold
cache = SemanticCache(
    similarity_threshold=0.92,
    cache_filepath="models/semantic_cache.json"
)

user_query = "What are the common lifestyle adjustments for early-stage hypertension?"

# Check cache for a semantic hit
cached_response = cache.get(user_query)
if cached_response:
    print(f"Served from Cache: {cached_response}")
else:
    # Fetch from cloud LLM
    response = "Maintain a low-sodium diet, exercise 30m daily..."
    cache.set(user_query, response)
```

### 2. Clinical RAG Vector Operations
Index, store, and query clinical document snippets:

```python
from clinical_rag_cache import SimpleVectorStore, RetrievedChunk

# Initialize local JSON-based vector store
vector_store = SimpleVectorStore(filepath="models/vector_store.json")

# Ingest patient interaction text
vector_store.add_document(
    doc_id="doc-123",
    text="Patient logs Joint Pain and minor fatigue after morning exercise.",
    metadata={"patient_id": 99, "type": "symptom_log"}
)

# Search with metadata constraints
results = vector_store.search(
    query="Joint pain",
    limit=2,
    filter_dict={"patient_id": 99}
)

for chunk in results:
    print(f"Similarity Score: {chunk.score:.4f} | Text: {chunk.text}")
```

### 3. Prompt Registry Template Loader
Decouple prompts from endpoint logic and manage prompt templates in a single catalog:

```python
from clinical_rag_cache import get_prompt, register_prompt

# Load system prompt template
system_template = get_prompt("chat_system")

# Interpolate patient context variables
final_system_prompt = system_template.format(
    patient_profile="Jane Doe, Female, Age: 36",
    available_reports="eGFR: 92 mL/min (Normal)"
)
```
