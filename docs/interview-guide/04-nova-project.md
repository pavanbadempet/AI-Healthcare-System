# Chapter 4 - Nova Recommendation Platform and Both Projects Compared

> **Two projects. One narrative. Maximum impact.**
> This chapter covers the Nova project in depth, then compares both projects side-by-side.

---

## Your Two Projects at a Glance

| | AI Healthcare System | Nova: Recommendation Platform |
|---|---|---|
| **Domain** | Healthcare / Clinical ML | Media / Content Discovery |
| **Frontend** | Next.js 16 (App Router, Zustand) | Vite + React + Streamlit Console |
| **Backend** | FastAPI (Python) | FastAPI (Python) |
| **ML** | XGBoost, SVM (classification) | FAISS, SBERT, TF-IDF, Learned Ranker (similarity/ranking) |
| **AI** | Google Gemini + RAG chatbot | OpenRouter LLM + Semantic Twins |
| **Data** | Parquet + SQLite/PostgreSQL | Delta Lake Medallion (Bronze->Silver->Gold) |
| **Streaming** | SSE for chat | Kafka + Spark Structured Streaming |
| **Pipeline** | Train scripts -> .pkl models | PySpark ETL -> Delta -> FAISS artifacts |
| **Scale** | 253K patient records | 50K+ movies, tenant-aware multi-catalog |
| **Testing** | 141 unit + 28 integration | Final verification suite + artifact health |
| **Deployment** | Render + Vercel | Docker Compose + HuggingFace + Render |
| **Key Technique** | Class imbalance (scale_pos_weight) | Hybrid retrieval (sparse + dense + rerank) |

---

## The Portfolio Narrative (2 Minutes)

> "I built two production-grade AI systems that show different sides of ML engineering.
>
> **Project 1 -- AI Healthcare System** is a clinical screening tool. It predicts 5 diseases using XGBoost and SVM trained on 253K real CDC records. The key challenge was class imbalance -- 86% of data is healthy, so I used scale_pos_weight to ensure the model actually catches at-risk patients. Each prediction returns confidence scores and medical disclaimers. It has a Next.js frontend, FastAPI backend with 7 middleware layers, JWT auth, and a RAG-powered AI chatbot.
>
> **Project 2 -- Nova** is a B2B recommendation intelligence platform. It ingests content catalogs through a PySpark Delta Lake pipeline (Bronze -> Silver -> Gold), builds SBERT embeddings and FAISS vector indexes for sub-millisecond similarity search, and serves hybrid AI recommendations that blend sparse recall, dense vectors, cross-encoder reranking, and user behavior signals. It supports multi-tenant catalogs with API keys, Kafka event streaming, and a learned ranking model that trains from implicit feedback.
>
> Together, they demonstrate classification, ranking, NLP, data engineering, and production system design."

---

## How to Answer "Which Project Are You Most Proud Of?"

**Pick Healthcare for:** Clinical impact, class imbalance, ethical AI, HIPAA awareness
**Pick Nova for:** System design depth, data engineering, recommendation algorithms, scalability

**Best answer:** "Both solve different problems. Healthcare shows I can handle medical ML where false negatives are costly. Nova shows I can build enterprise data pipelines and ranking systems. Together they cover classification, ranking, NLP, streaming, and production infra."

---

## NOVA DEEP-DIVE: Every Component Explained

### What is Nova?

Nova is a **B2B recommendation platform** -- think "recommendation-as-a-service." A streaming company (like Netflix or Hotstar) would use Nova's API to get movie recommendations for their users.

**What it does:**
1. Customer uploads their movie catalog (CSV)
2. Nova processes it through a data pipeline (clean, validate, enrich)
3. Nova builds vector embeddings and search indexes
4. Customer's app calls Nova's API: "Give me movies similar to Interstellar"
5. Nova returns ranked recommendations in ~5ms

### What is FAISS? (Explained Simply)

**FAISS** = Facebook AI Similarity Search. It's a library for finding similar things FAST.

**The problem:** You have 50,000 movies. Each movie is represented as a 384-dimension vector (from SBERT). When a user asks "movies like Interstellar," you need to find the 10 most similar vectors. Comparing against all 50K takes too long.

**How FAISS works:**
```
Without FAISS (brute force):
  Compare Interstellar's vector against ALL 50,000 movies
  50,000 comparisons x 384 dimensions = slow
  Time: ~50ms

With FAISS (indexed):
  FAISS partitions vectors into clusters during index build time
  At query time, only search the nearest clusters
  ~500 comparisons instead of 50,000
  Time: ~0.5ms (100x faster)
```

**Analogy:** Instead of checking every book in a library to find similar ones, FAISS first goes to the right SECTION (sci-fi, romance, etc.), then compares only within that section.

**Your code:**
```python
import faiss
import numpy as np

# BUILD: Create index from 50K movie embeddings (done once during pipeline)
embeddings = np.load("movie_embeddings.npy")  # Shape: (50000, 384)
index = faiss.IndexFlatIP(384)                 # Inner product similarity
index.add(embeddings)                          # Add all vectors
faiss.write_index(index, "movies.faiss")       # Save to disk

# SERVE: Query at runtime (done per API call, ~0.5ms)
query_vector = sbert_model.encode("sci-fi movies like Interstellar")
distances, indices = index.search(query_vector.reshape(1, -1), k=10)
# indices = [142, 8901, 3456, ...]  <- IDs of the 10 most similar movies
```

### What is SBERT? (Sentence-BERT)

**SBERT** converts text into a 384-dimensional vector that captures MEANING.

```
"sci-fi movies about space exploration"  ->  [0.23, -0.45, 0.12, ..., 0.87]  (384 numbers)
"interstellar travel and astronauts"     ->  [0.21, -0.42, 0.14, ..., 0.85]  (384 numbers)
"romantic comedy in New York"            ->  [-0.31, 0.67, -0.08, ..., -0.22]  (384 numbers)
```

The first two vectors are CLOSE together (similar meaning). The third is FAR away. FAISS measures this distance.

**Why not just keyword search?** Keywords miss semantic meaning:
- "space exploration" and "interstellar travel" share ZERO keywords but mean the same thing
- SBERT understands they're similar because it was trained on millions of text pairs

### What is TF-IDF? (Sparse Recall)

**TF-IDF** = Term Frequency - Inverse Document Frequency. A simpler, faster text matching approach.

```
TF (Term Frequency):     How often a word appears in THIS document
IDF (Inverse Document):  How rare the word is across ALL documents

"Interstellar" appears in 1 out of 50,000 movies -> high IDF (very specific)
"the" appears in 49,000 out of 50,000 movies -> low IDF (too common, ignored)
```

**Why use BOTH TF-IDF and SBERT?**
- TF-IDF is fast and handles cold-start (works with just text, no training needed)
- SBERT is smarter (understands meaning, not just keywords)
- Together they catch more relevant results than either alone

### What is Hybrid Retrieval? (The Full Pipeline)

```
User Query: "sci-fi movies like Interstellar"
                    |
    +---------------+---------------+
    |                               |
    v                               v
SPARSE RECALL (TF-IDF)         DENSE RECALL (SBERT + FAISS)
  - Keyword matching             - Semantic understanding
  - Fast, simple                 - "space exploration" = "interstellar"
  - Works for new items          - Deeper understanding
  - Returns 200 candidates       - Returns 200 candidates
    |                               |
    +---------------+---------------+
                    |
                    v
            SCORE FUSION
            Combine both lists
            Weight by quality score
            Weight by popularity
            Deduplicate
                    |
                    v
          CROSS-ENCODER RERANK (optional)
          Takes top 50, compares each with query
          Much slower but much more precise
          Like reading the full book vs reading the title
                    |
                    v
            MMR DIVERSITY
            Maximal Marginal Relevance
            lambda=0.72 (72% relevance, 28% diversity)
            Prevents showing 5 identical space movies
                    |
                    v
          BEHAVIOR BOOST
          Boost trending movies (Kafka event signals)
          Half-life decay: 14 days
          A movie trending today gets boosted
          A movie trending 30 days ago gets less boost
                    |
                    v
            TOP 10 RESULTS
```

**Why all these stages?**
- Sparse alone misses semantic matches ("astronaut" != "space traveler")
- Dense alone misses exact keyword matches and cold-start items
- Without diversity, you get 10 versions of the same movie
- Without behavior boost, popular trending content doesn't surface
- Each stage makes the results better at the cost of more latency

### What is the Delta Lake Medallion Architecture?

**Delta Lake** = An open-source storage layer on top of Parquet files that adds ACID transactions, schema enforcement, and time travel. Think of it as "a database for data lakes."

**Medallion** = Three tiers of data quality:

```
BRONZE (Raw)                SILVER (Validated)            GOLD (Curated)
------------------          ----------------------        -------------------
Raw CSV snapshots           Schema-validated records      Feature-enriched views
No transforms applied       Null handling applied         SCD Type 2 history
Append-only ingestion       Bad records quarantined       Embedding job tracking
Preserves source data       Type casting enforced         Behavior aggregates
                            Quality scoring added         Ready for ML serving
```

**Why not just one table?**
- Bronze keeps the original data for auditing and reprocessing
- Silver catches data quality issues before they pollute ML models
- Gold is optimized for serving -- pre-computed features, pre-joined, indexed

**Real example:**
```python
# Bronze: Raw ingestion (PySpark)
raw_df = spark.read.csv("catalog_upload.csv", header=True)
raw_df.write.format("delta").mode("append").save("bronze/movies")

# Silver: Validation
silver_df = (
    spark.read.format("delta").load("bronze/movies")
    .filter(col("title").isNotNull())           # Remove null titles
    .filter(col("release_year") > 1900)         # Remove invalid years
    .withColumn("vote_average", col("vote_average").cast("float"))
    .withColumn("ingested_at", current_timestamp())
)
# Bad records -> quarantine table
bad_records = raw_df.filter(col("title").isNull())
bad_records.write.format("delta").mode("append").save("quarantine/movies")

silver_df.write.format("delta").mode("overwrite").save("silver/movies")

# Gold: Feature enrichment
gold_df = (
    spark.read.format("delta").load("silver/movies")
    .withColumn("content_quality_score", compute_quality(col("overview"), col("genres")))
    .withColumn("popularity_bucket", ntile(10).over(Window.orderBy("popularity")))
)
gold_df.write.format("delta").mode("overwrite").save("gold/movies")
```

### What is SCD Type 2? (Slowly Changing Dimensions)

**The problem:** Movie metadata changes over time. Inception's rating was 8.5 in January, now it's 8.8. If you just overwrite, you lose history.

**SCD Type 2** keeps BOTH the old and new values:

```
| movie_id | title     | rating | valid_from | valid_to   | is_current |
|----------|-----------|--------|------------|------------|------------|
| 123      | Inception | 8.5    | 2024-01-01 | 2024-06-15 | false      |
| 123      | Inception | 8.8    | 2024-06-15 | NULL       | true       |
```

**Why this matters:**
- "What was our catalog state on March 1st?" -- just filter `WHERE valid_from <= '2024-03-01' AND (valid_to > '2024-03-01' OR valid_to IS NULL)`
- Regulatory compliance: prove what data you had at a point in time
- A/B testing: compare recommendations from different catalog versions

**SCD Types comparison:**
| Type | What it does | Example | Tradeoff |
|---|---|---|---|
| Type 0 | Never update | Reference data (country codes) | Simple but stale |
| Type 1 | Overwrite | Fix a typo in a movie title | Simple but loses history |
| Type 2 | Add new row | Rating change: 8.5 -> 8.8 | Keeps history but grows table |
| Type 3 | Add column | `current_rating` + `previous_rating` | Limited history (only 1 previous) |

### What is Kafka? (Event Streaming)

**Kafka** is a distributed message queue for real-time events.

```
In Nova's architecture:

USER ACTIONS                    KAFKA                        PROCESSING
User views movie 123    ->   Topic: "user-events"    ->   Spark Structured Streaming
User clicks movie 456   ->   Topic: "user-events"    ->   reads events in micro-batches
User rates movie 789    ->   Topic: "user-events"    ->   writes to Gold Delta tables
                                                          Updates behavior signals
```

**Why Kafka instead of just writing to the database?**
- **Decoupling:** The app doesn't need to know what processes the events. It just writes to Kafka. Consumers (Spark, analytics, ML training) read independently.
- **Buffering:** If Spark is slow, events queue up in Kafka without losing data. Without Kafka, if the database is slow, events are lost.
- **Replay:** Kafka retains events for a configurable period. You can replay events to rebuild tables or fix bugs.
- **Scale:** Kafka handles millions of events/second. Direct database writes would overwhelm the database.

### How Does the Learned Ranker Work?

**The problem:** Static retrieval (TF-IDF + FAISS) ranks movies by content similarity. But users care about more than similarity -- they want popular, well-reviewed, trending content.

**The solution:** Train a model that learns what makes a recommendation "good" from user behavior.

```python
# scripts/train_ranker.py

# Step 1: Collect implicit feedback from Kafka events
events = load_events()  # views, clicks, ratings from Gold Delta table

# Step 2: Build features for each movie
features = [
    movie.content_quality_score,    # How complete is the metadata? (0-1)
    movie.vote_average,             # TMDB rating (0-10)
    movie.popularity,               # TMDB popularity score
    movie.vote_count,               # Number of votes (proxy for trust)
    event_count,                    # How many times viewed in last 30 days
    avg_user_rating,                # Average user rating from events
    click_through_rate,             # Clicks / impressions
    days_since_release,             # Recency factor
]

# Step 3: Label = user engagement (click or rating as positive)
labels = compute_engagement_score(events)

# Step 4: Train a gradient boosted regressor
from sklearn.ensemble import GradientBoostingRegressor
ranker = GradientBoostingRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1
)
ranker.fit(features, labels)

# Step 5: Promotion gate -- must beat baseline before deployment
new_ndcg = evaluate(ranker, test_set)
baseline_ndcg = evaluate(current_ranker, test_set)

if new_ndcg > baseline_ndcg:
    save_and_deploy(ranker)       # Promote to production
    print(f"New ranker deployed: NDCG {baseline_ndcg:.3f} -> {new_ndcg:.3f}")
else:
    print(f"Rejected: new={new_ndcg:.3f} < baseline={baseline_ndcg:.3f}")
    # Keep current model -- never deploy a regression
```

**What is NDCG?** Normalized Discounted Cumulative Gain. It measures ranking quality:
- Did the BEST items appear at the TOP of the list?
- A perfect ranking = NDCG 1.0. Random ranking = ~0.5.

---

## Side-by-Side Technical Comparisons

### Q: Compare the ML approaches.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Task** | Binary classification (sick/healthy) | Ranking + similarity (find best matches) |
| **Algorithm** | XGBoost (tabular), SVM (small datasets) | FAISS (vector search), TF-IDF + BM25 (sparse), SBERT (dense), Learned Ranker |
| **Training data** | Labeled (0=healthy, 1=disease) | Implicit feedback (views, clicks, ratings) |
| **Output** | Probability (0-100%) -> risk level | Similarity scores -> ranked list |
| **Key challenge** | Class imbalance (86% majority class) | Cold start (new items, no behavior data) |
| **Solution** | scale_pos_weight in XGBoost | Hybrid retrieval (sparse catches cold-start items) |
| **Evaluation** | Accuracy + sensitivity + real-world validation | Coverage, diversity, NDCG, genre consistency |

### Q: Compare the data pipelines.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Source** | Static CSV/Parquet from CDC/Kaggle | Customer catalog CSV -> PySpark batch |
| **Storage** | Single Parquet files | Delta Lake Medallion (Bronze->Silver->Gold) |
| **Schema** | Fixed (9-24 features per model) | SCD Type 2 dimensions with history |
| **Quality** | Basic validation in training scripts | Quarantine bad records, quality scoring, metadata completeness |
| **Refresh** | Retrain manually | Daily GitHub Actions + Kaggle pipeline |
| **Streaming** | None (batch only) | Kafka -> Spark Structured Streaming for events |
| **ACID** | None (file-based) | Delta Lake transactional writes |

### Q: Compare the serving architectures.

| Aspect | Healthcare | Nova |
|---|---|---|
| **Model loading** | pickle .pkl at startup | FAISS index + SBERT embeddings (memory-mapped) |
| **Inference time** | ~9ms per prediction | ~5ms per FAISS query |
| **Memory mgmt** | Models in RAM (~1.6MB) | numpy mmap_mode='r' (reads from disk, not RAM) |
| **Hot reload** | Restart server | POST /artifacts/reload (zero downtime) |
| **Multi-model** | 5 independent models | Hybrid: sparse + dense + cross-encoder + ranker |
| **Multi-tenant** | Single user | API key-based tenant isolation |

---

## Questions That Bridge Both Projects

### Q: "How do you handle model serving differently in each project?"

> **Healthcare**: Models are small (200KB each), so I load them into RAM at startup via pickle. Prediction takes ~9ms -- pure in-memory inference. If a model is corrupted, that endpoint returns 503 but others still work. Simple and effective for small models.
>
> **Nova**: The FAISS index and embedding matrix are larger (could be hundreds of MB for a real catalog). I use numpy's `mmap_mode='r'` which memory-maps the file -- data stays on disk and is paged into RAM on demand by the OS. This lets Nova run on free-tier Render (512MB RAM) with a 50K movie catalog. Nova also has a hot reload endpoint (`/v1/artifacts/reload`) that downloads new artifacts from HuggingFace and swaps the recommender instance without downtime. No server restart needed.

### Q: "How do you evaluate model quality differently?"

> **Healthcare**: Standard ML metrics -- accuracy, sensitivity, specificity. Plus real-world validation: I tested 48 actual patient records through the live API and got 77% match with ground truth. The key insight: accuracy alone is misleading with class imbalance. 86.7% accuracy with 0% disease detection is useless. I optimized for SENSITIVITY (catching sick patients).
>
> **Nova**: Recommendation quality is harder to measure -- there's no single "correct" answer. I use label-free metrics:
> - **Coverage**: What % of the catalog is recommendable? (goal: >80%)
> - **Diversity**: Are recommendations varied or repetitive? (measured by genre spread)
> - **Genre consistency**: Do "similar" items actually share genres?
> - **Vector health**: Are FAISS rows aligned with the serving catalog? (no stale vectors)
> - **NDCG**: Are the best items ranked highest?
> - **Promotion gate**: New ranker must beat baseline metrics before deployment -- no regressions allowed.

### Q: "How do you handle the cold start problem?"

> **Healthcare**: Not applicable -- every prediction is independent. User provides their health metrics, model predicts immediately. No user history needed.
>
> **Nova**: Cold start is the #1 challenge. New movies have no behavior data (views, clicks, ratings). My solution is **hybrid retrieval**:
> 1. **Sparse recall** (TF-IDF) -- works purely on text (title, overview, genres). New items with metadata are immediately searchable. No training data needed.
> 2. **Dense recall** (SBERT -> FAISS) -- semantic similarity. Even obscure movies get meaningful embeddings from their descriptions.
> 3. **Quality scoring** -- weak metadata is scored, not deleted. Low-popularity items stay in the catalog with quality flags.
>
> This ensures that even a brand-new movie with just a title and description is immediately discoverable. The hybrid approach catches it through text matching even before any users interact with it.

### Q: "How does your data engineering differ between projects?"

> **Healthcare**: Simple pipeline -- CSV -> Parquet -> train -> pickle model. No streaming, no versioning, no multi-tenant concerns. It's a batch pipeline for model training. Total pipeline runs in under a minute.
>
> **Nova**: Full enterprise Delta Lake medallion architecture:
> - **Bronze**: Raw CSV snapshots ingested by PySpark. Preserves original data for auditing.
> - **Silver**: Validated records with schema checks, null handling. Bad records go to a quarantine table -- never silently dropped. Every record gets a quality score.
> - **Gold**: Feature-enriched views with SCD Type 2 history. Pre-computed content quality scores. Ready for ML serving.
> - **Streaming**: Kafka ingests user events (views, clicks, ratings) -> Spark Structured Streaming -> Gold Delta fact tables. Events drive the behavior boost and learned ranker training.
> - **ACID guarantees**: Delta Lake provides transactional writes (no partial writes), time travel (query historical snapshots), and Change Data Feed (track what changed).

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

> "Across both projects I've worked with classification (XGBoost, SVM), ranking (FAISS, learned rankers), NLP (SBERT embeddings, RAG), data engineering (Delta Lake, Kafka streaming), and production infrastructure (FastAPI, Docker, CI/CD). Healthcare taught me that the right metric matters more than the best algorithm. Nova taught me that production ML is 90% data engineering and 10% model training. Together, they represent a complete ML engineering skill set -- from research to production."
