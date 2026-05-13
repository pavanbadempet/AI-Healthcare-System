# Chapter 4 - Nova Recommendation Platform and Both Projects Compared

> **Two projects. One narrative. Maximum impact.**
> This file shows how to present BOTH projects together as a cohesive portfolio.

---

## Your Two Projects at a Glance

| | AI Healthcare System | Nova: Recommendation Platform |
|---|---|---|
| **Domain** | Healthcare / Clinical ML | Media / Content Discovery |
| **Frontend** | Next.js 16 (App Router, Zustand) | Vite + React + Streamlit Console |
| **Backend** | FastAPI (Python) | FastAPI (Python) |
| **ML** | XGBoost, SVM (classification) | FAISS, SBERT, TF-IDF, Learned Ranker (similarity/ranking) |
| **AI** | Google Gemini + RAG chatbot | OpenRouter LLM + Semantic Twins |
| **Data** | Parquet + SQLite/PostgreSQL | Delta Lake Medallion (Bronzeâ†'Silverâ†'Gold) |
| **Streaming** | SSE for chat | Kafka + Spark Structured Streaming |
| **Pipeline** | Train scripts â†' .pkl models | PySpark ETL â†' Delta â†' FAISS artifacts |
| **Scale** | 253K patient records | 50K+ movies, tenant-aware multi-catalog |
| **Testing** | 141 unit + 28 integration | Final verification suite + artifact health |
| **Deployment** | Render + Vercel | Docker Compose + HuggingFace + Render |
| **Key Technique** | Class imbalance (scale_pos_weight) | Hybrid retrieval (sparse + dense + rerank) |

---

## The Portfolio Narrative (2 Minutes)

> "I built two production-grade AI systems that show different sides of ML engineering.
>
> **Project 1 â€" AI Healthcare System** is a clinical screening tool. It predicts 5 diseases using XGBoost and SVM trained on 253K real CDC records. The key challenge was class imbalance â€" 86% of data is healthy, so I used scale_pos_weight to ensure the model actually catches at-risk patients. Each prediction returns confidence scores and medical disclaimers. It has a Next.js frontend, FastAPI backend with 7 middleware layers, JWT auth, and a RAG-powered AI chatbot.
>
> **Project 2 â€" Nova** is a B2B recommendation intelligence platform. It ingests content catalogs through a PySpark Delta Lake pipeline (Bronze â†' Silver â†' Gold), builds SBERT embeddings and FAISS vector indexes for sub-millisecond similarity search, and serves hybrid AI recommendations that blend sparse recall, dense vectors, cross-encoder reranking, and user behavior signals. It supports multi-tenant catalogs with API keys, Kafka event streaming, and a learned ranking model that trains from implicit feedback.
>
> Together, they demonstrate classification, ranking, NLP, data engineering, and production system design."

---

## How to Answer "Which Project Are You Most Proud Of?"

**Pick Healthcare for:** Clinical impact, class imbalance, ethical AI, HIPAA awareness
**Pick Nova for:** System design depth, data engineering, recommendation algorithms, scalability

**Best answer:** "Both solve different problems. Healthcare shows I can handle medical ML where false negatives are costly. Nova shows I can build enterprise data pipelines and ranking systems. Together they cover classification, ranking, NLP, streaming, and production infra."

---

## Side-by-Side Technical Comparisons

### Q: Compare the ML approaches.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Task** | Binary classification (sick/healthy) | Ranking + similarity (find best matches) |
| **Algorithm** | XGBoost (tabular), SVM (small datasets) | FAISS (vector search), TF-IDF + BM25 (sparse), SBERT (dense), Learned Ranker |
| **Training data** | Labeled (0=healthy, 1=disease) | Implicit feedback (views, clicks, ratings) |
| **Output** | Probability (0-100%) â†' risk level | Similarity scores â†' ranked list |
| **Key challenge** | Class imbalance (86% majority class) | Cold start (new items, no behavior data) |
| **Solution** | scale_pos_weight in XGBoost | Hybrid retrieval (sparse catches cold-start items) |
| **Evaluation** | Accuracy + sensitivity + real-world validation | Coverage, diversity, genre consistency, vector health |

### Q: Compare the data pipelines.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Source** | Static CSV/Parquet from CDC/Kaggle | Customer catalog CSV â†' PySpark batch |
| **Storage** | Single Parquet files | Delta Lake Medallion (Bronzeâ†'Silverâ†'Gold) |
| **Schema** | Fixed (9-24 features per model) | SCD Type 2 dimensions with history |
| **Quality** | Basic validation in training scripts | Quarantine bad records, quality scoring, metadata completeness |
| **Refresh** | Retrain manually | Daily GitHub Actions + Kaggle pipeline |
| **Streaming** | None (batch only) | Kafka â†' Spark Structured Streaming for events |

### Q: Compare the serving architectures.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Model loading** | pickle .pkl at startup | FAISS index + SBERT embeddings (memory-mapped) |
| **Inference time** | ~9ms per prediction | ~5ms per FAISS query |
| **Memory mgmt** | Models in RAM (~1.6MB) | numpy mmap_mode='r' (reads from disk, not RAM) |
| **Hot reload** | Restart server | POST /artifacts/reload (zero downtime) |
| **Multi-model** | 5 independent models | Hybrid: sparse + dense + cross-encoder + ranker |

---

## Questions That Bridge Both Projects

### Q: "How do you handle model serving differently in each project?"

> **Healthcare**: Models are small (200KB each), so I load them into RAM at startup via pickle. Prediction takes ~9ms â€" pure in-memory inference. If a model is corrupted, that endpoint returns 503 but others still work.
>
> **Nova**: The FAISS index and embedding matrix are large (could be hundreds of MB). I use numpy's `mmap_mode='r'` which memory-maps the file â€" data stays on disk and is paged into RAM on demand. This lets Nova run on free-tier Render (512MB RAM) with a 50K movie catalog. Nova also has a hot reload endpoint (`/v1/artifacts/reload`) that downloads new artifacts from HuggingFace and swaps the recommender instance without downtime.

### Q: "How do you evaluate model quality differently?"

> **Healthcare**: Standard ML metrics â€" accuracy, sensitivity, specificity. Plus real-world validation: I tested 48 actual patient records through the live API and got 77% match with ground truth. The key insight: accuracy alone is misleading with class imbalance. 86.7% accuracy with 0% disease detection is useless.
>
> **Nova**: Recommendation quality is harder to measure â€" there's no single "correct" answer. I use label-free metrics:
> - **Coverage**: What % of the catalog is recommendable?
> - **Diversity**: Are recommendations varied or repetitive?
> - **Genre consistency**: Do similar items share genres?
> - **Vector health**: Are FAISS rows aligned with the serving catalog?
> - **Promotion gate**: New ranker must beat baseline metrics before deployment.

### Q: "How do you handle the cold start problem?"

> **Healthcare**: Not applicable â€" every prediction is independent. User provides their health metrics, model predicts immediately. No user history needed.
>
> **Nova**: Cold start is the #1 challenge. New movies have no behavior data (views, clicks, ratings). My solution is **hybrid retrieval**:
> 1. **Sparse recall** (TF-IDF) â€" works purely on text (title, overview, genres). New items with metadata are immediately searchable.
> 2. **Dense recall** (SBERT â†' FAISS) â€" semantic similarity. Even obscure movies get meaningful embeddings from their descriptions.
> 3. **Quality scoring** â€" weak metadata is scored, not deleted. Low-popularity items stay in the catalog with quality flags.
> This ensures that even a brand-new movie with just a title and description is immediately discoverable.

### Q: "How does your data engineering differ between projects?"

> **Healthcare**: Simple pipeline â€" CSV â†' Parquet â†' train â†' pickle model. No streaming, no versioning, no multi-tenant concerns. It's a batch pipeline for model training.
>
> **Nova**: Full Delta Lake medallion architecture:
> - **Bronze**: Raw CSV snapshots ingested by PySpark
> - **Silver**: Validated records (schema checks, null handling). Bad records go to a quarantine table, not silently dropped.
> - **Gold**: Feature-enriched views with SCD Type 2 history (track how metadata changes over time)
> - **Streaming**: Kafka ingests product events (views, clicks, ratings) â†' Spark Structured Streaming â†' Gold Delta fact tables
> - **ACID guarantees**: Delta Lake provides transactional writes, time travel, and Change Data Feed

---

## Project-Specific Deep Questions

### Nova: "Explain the hybrid retrieval pipeline."

```
User Query: "sci-fi movies like Interstellar"
                    â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 1. SPARSE RECALL (TF-IDF)â"‚  Fast, handles cold-start
    â"‚    Cosine similarity      â"‚  Returns 200 candidates
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 2. DENSE RECALL (SBERT)  â"‚  Semantic understanding
    â"‚    FAISS vector search    â"‚  "space exploration" â‰ˆ "interstellar"
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 3. SCORE FUSION          â"‚  Combine sparse + dense scores
    â"‚    Quality + popularity   â"‚  Weight by metadata completeness
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 4. CROSS-ENCODER RERANK  â"‚  Precise relevance scoring
    â"‚    (optional, slow)       â"‚  Compares query-candidate pairs
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 5. MMR DIVERSITY         â"‚  Avoid showing 5 identical movies
    â"‚    Î»=0.72 diversity       â"‚  Balance relevance + diversity
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
    â"‚ 6. BEHAVIOR BOOST        â"‚  Trending signal from events
    â"‚    Recency-weighted       â"‚  Half-life decay: 14 days
    â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                â†"
         Top 10 Results
```

### Nova: "Explain the Delta Lake medallion model."

```
Bronze (Raw)         â†'  Silver (Validated)      â†'  Gold (Curated)
â"â"â"â"â"â"â"â"â"â"â"â"         â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"      â"â"â"â"â"â"â"â"â"â"â"â"â"â"â"
Raw CSV snapshots       Schema validation          Content features
No transforms          Null handling               SCD Type 2 history
Append-only            Quarantine bad records      Embedding job tracking
                       Type casting                Pipeline run metadata
                                                   Behavior aggregates
```

### Nova: "What is SCD Type 2 and why?"

SCD = Slowly Changing Dimension. Movie metadata changes over time (new ratings, updated descriptions). Instead of overwriting, SCD Type 2 keeps history:

```sql
| movie_id | title     | rating | valid_from | valid_to   | is_current |
|----------|-----------|--------|------------|------------|------------|
| 123      | Inception | 8.5    | 2024-01-01 | 2024-06-15 | false      |
| 123      | Inception | 8.8    | 2024-06-15 | NULL       | true       |
```

This enables time travel queries: "What was our catalog state on March 1st?"

### Nova: "How does the learned ranker work?"

```python
# scripts/train_ranker.py
# 1. Collect implicit feedback from events
events = load_events()  # views, clicks, ratings

# 2. Build features: content quality + behavior signal
features = [
    movie.content_quality_score,
    movie.vote_average,
    movie.popularity,
    event_count,
    avg_rating,
    click_count
]

# 3. Train gradient-boosted ranker
ranker = GradientBoostingRegressor()
ranker.fit(features, labels)

# 4. Promotion gate: must beat baseline
if new_metrics > baseline_metrics:
    deploy(ranker)  # Promote to production
else:
    reject(ranker)  # Keep current model
```

---

## Combined Numbers for Maximum Impact

| Metric | Healthcare | Nova | Combined |
|---|---|---|---|
| Training records | 538K | 50K+ movies | 588K+ |
| ML models | 5 (classification) | 4 (retrieval/ranking) | 9 |
| API endpoints | 20+ | 25+ | 45+ |
| Frontend routes | 21 | Streamlit + Vite | 25+ |
| Tests | 141 + 28 = 169 | Verification suites | 180+ |
| Backend modules | 40+ | 20+ | 60+ |
| Technologies | 12+ | 15+ | 20+ unique |

---

## The Killer Closing Statement

> "Across both projects I've worked with classification (XGBoost, SVM), ranking (FAISS, learned rankers), NLP (SBERT embeddings, RAG), data engineering (Delta Lake, Kafka streaming), and production infrastructure (FastAPI, Docker, CI/CD). Healthcare taught me that the right metric matters more than the best algorithm. Nova taught me that production ML is 90% data engineering and 10% model training. Together, they represent a complete ML engineering skill set â€" from research to production."
