# Interview Mastery Curriculum -- Study Order

> **7 files. 599 KB. 10,600+ lines. Everything you need.**
> Close any other interview files -- this is the ONLY folder that matters.

---

## THE 4-PHASE STUDY PLAN

### Phase 1: Build the Foundation (4 hours)
| Priority | Chapter | What you learn | Time |
|---|---|---|---|
| 1 | [01-foundations.md](01-foundations.md) | Every concept from zero: ML, Spark, SQL, Cloud (AWS/Azure), Snowflake, On-Prem, Platform Wars, Project Defenses (Parts 1-32) | 150 min |
| 2 | [02-your-career.md](02-your-career.md) | TCS/Nomura/Nissan defense, resume line-by-line, Spark deep-dive, 30-sec pitch | 90 min |

### Phase 2: Master Your Projects (4 hours)
| Priority | Chapter | What you learn | Time |
|---|---|---|---|
| 3 | [03-healthcare-project.md](03-healthcare-project.md) | Complete Healthcare: ML pipeline, backend, frontend, security, testing | 150 min |
| 4 | [04-nova-project.md](04-nova-project.md) | Complete Nova: FAISS, SBERT, Delta Lake, Kafka, hybrid retrieval | 90 min |

### Phase 3: Practice Coding (3 hours)
| Priority | Chapter | What you learn | Time |
|---|---|---|---|
| 5 | [05-coding-practice.md](05-coding-practice.md) | Python + SQL + 5 PySpark patterns + 10 DSA patterns with thinking process | 180 min |

### Phase 4: Win the Interview (2 hours)
| Priority | Chapter | What you learn | Time |
|---|---|---|---|
| 6 | [06-interview-mastery.md](06-interview-mastery.md) | 5 golden rules, scenarios, tradeoffs, salary, body language, scorecard | 120 min |

**Total: ~13 hours for complete preparation.**

---

## WHAT'S IN 01-FOUNDATIONS.MD (32 Parts)

| Part | Topic |
|---|---|
| 1-8 | Core DE Concepts (Spark, SQL, ETL, Data Modeling, etc.) |
| 9-15 | Cloud Platforms (AWS, Azure, On-Prem) |
| 16-20 | Tools Deep-Dives (Snowflake, Databricks, Kafka, Delta Lake) |
| 21-27 | Trade-offs, Data Governance, Performance |
| 28 | **Platform Wars** (Why X not Y -- every major comparison) |
| 29 | **Project Justifications** (Nissan 24 Q&As, Nomura 21 Q&As, Healthcare 19 Q&As, Nova 13 Q&As) |
| 30 | **8 STAR Behavioral Stories** (mapped to your real projects) |
| 31 | **15 Gotcha/Trap Questions** (with safe answers) |
| 32 | **10 Questions to Ask the Interviewer** |

---

## QUICK TOPIC LOOKUP

| If they ask about... | Go to |
|---|---|
| XGBoost, class imbalance, SHAP, model monitoring | Ch 1 (Part 29: Healthcare Q10-Q19) + Ch 3 |
| Spark optimization, broadcast joins, partitioning | Ch 2 (Nomura work) + Ch 1 (Part 29: Nomura Q15) |
| FAISS, SBERT, vector search, cold-start problem | Ch 1 (Part 29: Nova Q10-Q13) + Ch 4 |
| Delta Lake, medallion, Bronze/Silver/Gold | Ch 4 (Nova) + Ch 5 (PySpark merge pattern) |
| FastAPI, middleware, JWT, bcrypt, API security | Ch 1 (Part 29: Healthcare Q19) + Ch 3 |
| Next.js, Zustand, SSE streaming | Ch 3 (Healthcare frontend) |
| SQL window functions, CTEs, joins | Ch 2 (Nomura SQL) + Ch 5 (SQL patterns) |
| AWS Lambda, Step Functions, S3, EventBridge, SNS | Ch 1 (Part 29: Nissan Q13-Q24) + Ch 2 |
| Snowflake (RBAC, clustering, Snowpipe, multi-warehouse) | Ch 1 (Part 29: Nissan Q16, Q21, Q23) |
| Athena, Glue Catalog | Ch 1 (Part 29: Nissan Q24) |
| YARN to Kubernetes migration | Ch 2 (Nomura bullet 4) + Ch 1 (Part 29: Nomura) |
| AutoSys dependency chains, job scheduling | Ch 1 (Part 29: Nomura Q16) + Ch 2 |
| DRT reconciliation, feed failures, on-call | Ch 1 (Part 29: Nomura Q11-Q17) |
| Month-end processing, cross-region joins | Ch 1 (Part 29: Nomura Q14, Q19) |
| Data governance, lineage, RBAC | Ch 1 (Part 29: Nomura Q20) |
| Spark configs (executor memory, broadcast threshold) | Ch 1 (Part 29: Nomura Q15) |
| Schema evolution, upstream changes | Ch 1 (Part 29: Nissan Q22) |
| Data quality, testing, validation | Ch 3 (Healthcare testing) + Ch 5 |
| Kafka ordering, event streaming | Ch 1 (Part 29: Nova Q13) + Ch 4 |
| Star schema, fact/dimension tables | Ch 1 (Kimball section) + Ch 2 |
| "Tell me about yourself" / 30-sec pitch | Ch 2 (pitch) + Ch 6 (HR section) |
| Salary negotiation | Ch 6 (salary scripts) |
| "Why leave TCS?" | Ch 1 (Part 31: Gotcha Q5) |
| Production failure at 2 AM | Ch 1 (Part 30: STAR Story 1) + Ch 6 |
| "Rate yourself on Spark" | Ch 1 (Part 31: Gotcha Q3) |
| "Biggest weakness" | Ch 1 (Part 31: Gotcha Q2) |
| "Why hire you over 5-year exp?" | Ch 1 (Part 31: Gotcha Q6) |
| System design (vague requirement) | Ch 1 (Part 31: Gotcha Q10) + Ch 6 |
| Questions to ask THEM | Ch 1 (Part 32) |
| Two Sum, binary search, DSA | Ch 5 (10 patterns) |
| Resume bullet defense | Ch 2 (every bullet explained) |
| NCFA, NFPS, NSC (Nomura regions) | Ch 1 (Part 29: Nomura) + Ch 2 |
| DRT, SFT, PRISM, CA (Nomura feeds) | Ch 1 (Part 29: Nomura fact tables) |

---

## FILE SIZES

```
01-foundations.md        272 KB  3,890 lines  (The Textbook: 35 Parts)
02-your-career.md         29 KB    522 lines  (Career Defense)
03-healthcare-project.md 134 KB  3,109 lines  (Healthcare Deep-Dive)
04-nova-project.md        22 KB    342 lines  (Nova Deep-Dive)
05-coding-practice.md     41 KB  1,102 lines  (Code Drills)
06-interview-mastery.md   95 KB  1,562 lines  (Interview Strategy + Live Rounds)
----------------------------------------------
TOTAL                    599 KB  10,600+ lines
```

### Ch6 Now Includes:
- **8 Live SQL Problems** (using YOUR Nomura schema)
- **5 Live PySpark Problems** (broadcast joins, Delta MERGE, SCD Type 2)
- **3 Data Modeling Problems** (e-commerce, ride-sharing, YOUR Nomura schema)
- **6 Advanced SQL Patterns** (recursive CTE, MERGE, LAG/LEAD, GROUPING SETS, gap detection, sessionization)
- **Full Mock Interview Transcript** (30-minute conversation flow)
- **Interview Day Timeline** (T-60 to post-interview checklist)

**This is your ONE source of truth. No other interview files exist.**
