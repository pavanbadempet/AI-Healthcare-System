# 12 — Quick Reference Cheat Sheet

## One-Line Definitions

| Term | Definition |
|---|---|
| **FastAPI** | Async Python web framework with automatic docs and Pydantic validation |
| **Next.js** | React framework with server-side rendering, file-based routing, Turbopack |
| **XGBoost** | Gradient-boosted decision tree algorithm — best for tabular data |
| **SVM** | Support Vector Machine — finds optimal boundary, good for small datasets |
| **Random Forest** | Ensemble of decision trees — reduces overfitting via bagging |
| **JWT** | JSON Web Token — stateless auth token (header.payload.signature) |
| **bcrypt** | One-way password hashing with salt — industry standard |
| **OAuth2** | Authentication framework — we use Password grant + Bearer tokens |
| **CORS** | Cross-Origin Resource Sharing — controls which domains call your API |
| **SSE** | Server-Sent Events — server pushes data to client over HTTP |
| **WebSocket** | Full-duplex bidirectional communication — more complex than SSE |
| **RAG** | Retrieval-Augmented Generation — inject relevant docs into AI prompts |
| **Pydantic** | Data validation library using Python type hints |
| **SQLAlchemy** | Python ORM — maps classes to database tables |
| **Zustand** | Lightweight React state management (alternative to Redux) |
| **Framer Motion** | React animation library for smooth transitions |
| **scale_pos_weight** | XGBoost parameter — weights minority class to handle imbalance |
| **predict_proba** | Returns class probabilities instead of binary 0/1 |
| **StandardScaler** | Normalizes features to mean=0, std=1 (required for SVM) |
| **Parquet** | Columnar file format — 10x faster reads than CSV |
| **Uvicorn** | ASGI server that runs FastAPI applications |
| **ASGI** | Async Server Gateway Interface — Python's async web standard |
| **Middleware** | Code that runs between request and response (auth, logging, etc.) |
| **Dependency Injection** | FastAPI auto-provides function args (db sessions, auth) |
| **Lifespan** | FastAPI startup/shutdown hook for loading models |
| **ORM** | Object-Relational Mapping — write Python, not SQL |
| **HIPAA** | US law governing health data privacy and security |
| **PII** | Personally Identifiable Information — names, DOBs, health data |
| **Sensitivity** | True positive rate — % of sick patients correctly identified |
| **Specificity** | True negative rate — % of healthy patients correctly identified |

---

## Key Numbers to Remember

| Metric | Value |
|---|---|
| Total datasets | 5 |
| Largest dataset | 253,680 records (BRFSS) |
| Total training records | ~538K |
| Frontend routes | 21 |
| Backend modules | 40+ |
| Unit tests | 141 |
| Integration checks | 28 |
| Real-world validation | 48 records, 77% accuracy |
| Model total size | ~1.6 MB |
| API response time | ~9ms per prediction |
| Middleware layers | 7 |
| Class imbalance ratio | Up to 9.6:1 (heart) |

---

## Architecture Summary (30-second version)

```
Next.js Frontend (21 routes, Zustand auth, Framer Motion animations)
        ↕ HTTP + SSE
FastAPI Backend (7 middleware layers, JWT auth, Pydantic validation)
        ↕
3 services:
  1. ML Prediction (5 XGBoost/SVM models → confidence + risk + disclaimer)
  2. AI Chat (RAG + Gemini → SSE streaming)
  3. Data (SQLAlchemy + SQLite/PostgreSQL)
```

---

## When Asked "Why X over Y?"

| Question | Answer Template |
|---|---|
| Why Next.js over React? | App Router layouts, SSR, file routing, Turbopack |
| Why FastAPI over Flask? | Async, auto-docs, Pydantic, 10x faster |
| Why FastAPI over Django? | Django too heavy for REST API — don't need admin/templates |
| Why XGBoost over neural nets? | Tabular data, handles imbalance, fast training |
| Why SVM over XGBoost (kidney/lungs)? | Small datasets — SVM generalizes better |
| Why JWT over sessions? | Stateless, scalable, no server-side storage |
| Why SSE over WebSocket? | Unidirectional streaming, simpler, auto-reconnect |
| Why Zustand over Redux? | Less boilerplate, sufficient for auth state |
| Why SQLite over PostgreSQL? | Zero-config dev, switch via env var for prod |
| Why CSS vars over Tailwind config? | Runtime theme control, works with animations |
| Why pickle over ONNX? | Simpler, Python-only deployment, small models |
| Why monolith over microservices? | Single app is simpler at this scale |

---

## Common Follow-up Answers

**"What's your biggest achievement?"**
→ Fixing class imbalance: one parameter (`scale_pos_weight=6.16`) took disease detection from 0% to ~60%.

**"What's your biggest failure?"**
→ Initially shipped with 86.7% accuracy thinking it was great, only to discover it detected zero diseases. Taught me that accuracy alone is meaningless.

**"How do you handle deadlines?"**
→ I prioritize: get core prediction working first, then add auth, then frontend polish, then tests. Each phase is independently deployable.

**"How do you learn new technologies?"**
→ I build. This project forced me to learn FastAPI, Next.js App Router, XGBoost tuning, SSE streaming, and RAG — all by implementing them in a real system.
