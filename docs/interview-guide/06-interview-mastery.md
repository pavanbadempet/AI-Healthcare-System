# Chapter 6 - Interview Mastery: Psychology, Behavioral, HR and Salary

> This file is about HOW to think during the interview â€" not what to say, but how to NEVER go wrong.

---

## THE 5 RULES THAT PREVENT FAILURE

### Rule 1: Never Say "I Don't Know" Empty-Handed

**Wrong**: "I don't know what Apache Flink is."

**Right**: "I haven't worked with Flink directly, but I know it's a stream processing framework similar to Spark Structured Streaming, which I've used in my Nova project for Kafka event ingestion. From what I understand, Flink has lower latency for true event-at-a-time processing, while Spark Structured Streaming works in micro-batches. I'd be excited to learn it."

**Pattern**: "I haven't used X, but I know Y (similar thing I've used), and the difference is Z. I'd be excited to learn it."

This shows: honesty + related knowledge + learning attitude.

---

### Rule 2: Always Mention What You REJECTED and WHY

**Wrong**: "I used XGBoost."

**Right**: "I chose XGBoost over Random Forest and neural networks. Random Forest was close, but XGBoost handles class imbalance natively with scale_pos_weight. Neural networks would overfit on 253K tabular records â€" the Grinsztajn 2022 benchmark showed tree-based models outperform deep learning on tabular data."

Let's unpack every term in that answer so you UNDERSTAND it and can explain further if asked:

- **XGBoost (eXtreme Gradient Boosting)**: An algorithm that trains hundreds of small decision trees one after another. Each new tree focuses on correcting the mistakes of the previous trees. Like a team of weak learners that together become strong. It's the go-to for tabular (spreadsheet-like) data.

- **Random Forest**: Also uses decision trees, but trains them ALL independently in parallel (not sequentially like XGBoost). Each tree votes, majority wins. Simpler but doesn't have a built-in way to handle imbalanced data.

- **Class imbalance**: When one category vastly outnumbers the other. In your diabetes data, 86% of patients are healthy, only 14% are diabetic. The model gets lazy â€" it learns that predicting "healthy" every time gives 86% accuracy. It catches ZERO diabetic patients. 86% accuracy but completely useless.

- **scale_pos_weight=6.16**: Tells XGBoost "missing a diabetic patient is 6.16x worse than a false alarm on a healthy patient." Calculated as: 218,334 healthy / 35,346 diabetic = 6.16. Now the model is FORCED to learn patterns that catch diabetic patients, because missing them costs 6x more during training.

- **Overfit**: When a model memorizes the training data instead of learning real patterns. It scores 99% on training data but fails on new data. Like a student who memorizes exam answers but can't solve new problems. Neural networks with limited data (253K is "limited" for deep learning) tend to overfit on tabular data.

- **Tabular data**: Data in rows and columns â€" like a spreadsheet or SQL table. Your health data is tabular: each row is a patient, each column is a measurement (BMI, age, blood pressure). This is different from images or text, where neural networks excel.

- **Grinsztajn 2022**: A NeurIPS research paper that benchmarked tree-based models (XGBoost, Random Forest) against deep learning on 45 tabular datasets. Result: tree models won on medium-sized tabular data. This is your academic backing for choosing XGBoost.

**Pattern**: "I chose X over Y and Z because [specific technical reason]."

This shows: you evaluated options, you have depth, you make informed decisions.

---

### Rule 3: Always Give NUMBERS

**Wrong**: "I improved the pipeline."

**Right**: "I improved Spark execution time by 30% â€" from 45 minutes to 31 minutes â€" through broadcast joins on dimension tables under 100MB, partition pruning on trade_date, and predicate pushdown to the Parquet reader."

**Pattern**: [What] + [Number] + [How]

Interviewers remember numbers. "30% improvement" sticks in their head during the hiring committee meeting.

---

### Rule 4: Always Discuss FAILURE MODES

**Wrong**: "The prediction API returns the result."

**Right**: "The prediction API returns the result. If the model isn't loaded, it returns 503. If the input is invalid, Pydantic returns 422 with the specific field error. If there's an unexpected exception, the middleware catches it and returns a UUID error ID â€" never a stack trace â€" for debugging without exposing PII."

**Pattern**: "Here's what happens when it works. Here's what happens when it BREAKS."

This shows: production thinking. Junior engineers only think about the happy path.

---

### Rule 5: End Every Answer With a Forward Look

**Wrong**: "That's how I did it."

**Right**: "That's how I did it. If I were to improve this, I'd add SHAP explainability to show which features contributed most to each prediction, and implement model drift monitoring with Evidently AI."

**Pattern**: "Here's what I did. Here's what I'd do NEXT."

This shows: growth mindset, you're always thinking ahead.

---

## TRAPS AND HOW TO AVOID THEM

### Trap 1: "Rate yourself 1-10 on Python"

**The trap**: Say 9 or 10 â†' they'll ask obscure questions to humiliate you. Say 5 â†' you look weak.

**The answer**: "I'd say 7-8. I use Python daily for ETL, API development, and ML. I'm very comfortable with pandas, PySpark, FastAPI, and data processing patterns. I know there's always more to learn â€" for example, I'd like to deepen my knowledge of async patterns and metaclasses."

**Rule**: Never above 8. Always mention what you still want to learn.

---

### Trap 2: "What's your biggest weakness?"

**The trap**: Say a real weakness â†' they worry. Say "I work too hard" â†' they know you're lying.

**The answer**: "I tend to over-engineer solutions initially. In my Healthcare project, I built 7 middleware layers and comprehensive testing when a simpler MVP might have shipped faster. I've learned to ask 'what's the minimum viable solution?' first, then iterate. I now use a 'make it work, make it right, make it fast' approach."

**Rule**: Pick a REAL weakness that shows you're an engineer who cares about quality, then show how you're fixing it.

---

### Trap 3: "Why are you leaving TCS?"

**The trap**: If you criticize TCS â†' red flag. If you sound desperate â†' red flag.

**The answer**: "TCS gave me a strong foundation â€" Spark, SQL, production systems, working with large enterprises like Nomura. I'm now looking for a role where I can (1) work on more modern data stacks, (2) get closer to the AI/ML side of data engineering, and (3) be in an environment that prioritizes engineering growth."

**Rule**: Appreciate current employer + frame the move as growth, not escape.

---

### Trap 4: "Do you have any questions?" (saying "No")

**The trap**: Saying "no" signals disinterest.

**Always ask at least 3:**
1. "What does the data stack look like here?" (shows technical interest)
2. "What's the biggest engineering challenge the team is facing?" (shows you want to solve problems)
3. "How does career growth work for data engineers here?" (shows you're thinking long-term)

**Bonus power questions:**
- "How does your team handle data quality in production?"
- "Is there a culture of code reviews and knowledge sharing?"
- "What does on-call look like for this team?"

---

### Trap 5: "Can you start immediately?"

**The trap**: Saying yes might signal desperation. Being rigid might lose the offer.

**The answer**: "I have a [30-day/60-day] notice period at TCS. I'll work with my manager to see if we can expedite it. I'd like to wrap up my current responsibilities properly â€" that's the same professionalism I'd bring to your team."

---

### Trap 6: "What if the interviewer is wrong about something?"

**The approach**: NEVER say "you're wrong." Instead:

**Wrong**: "No, that's not how Spark works."

**Right**: "That's interesting â€" in my experience with Spark at Nomura, I've seen it work differently. The shuffle happens when... but I could be thinking of a different context. Could you tell me more about the scenario you're describing?"

**Rule**: Disagree by sharing your experience, not by correcting them. Then ask them to elaborate.

---

## BODY LANGUAGE & COMMUNICATION

### Before the Interview
- Sleep well. Seriously. Your brain processes patterns during sleep.
- Have water nearby. Sipping water buys thinking time.
- Have your resume printed in front of you (even for virtual interviews).
- Open your projects in the browser â€" ready to screenshare.

### During the Interview
- **Pause before answering**. 3 seconds of thinking looks confident. Rushing looks nervous.
- **Think out loud** during coding. "I'm thinking about using a hash map here because lookup is O(1)..."
- **Ask clarifying questions** before jumping into coding. "Should I handle edge cases like empty input?"
- **Say "Let me think about this"** â€" it's NEVER a bad thing to say.

### When Stuck
- "I'm not sure about the exact syntax, but the approach would be..."
- "I haven't encountered this specific scenario, but here's how I'd reason through it..."
- "Can I talk through my thought process? I think the key insight is..."

### Virtual Interview Specifics
- Camera ON, good lighting, clean background
- Look at the CAMERA when speaking (not the screen) â€" appears as eye contact
- Mute when not speaking to avoid background noise
- Have a code editor ready (VS Code) for live coding

---

## SALARY NEGOTIATION

### When They Ask "What are your expectations?"

**Never give a number first.** Always try:
> "I'm flexible on compensation. Could you share the range budgeted for this role?"

If they insist:
> "Based on my experience and market research for this role, I'm looking at [current CTC + 40-60%]. But I'm open to discussing based on the complete package â€" role, growth, team, and learning opportunities matter to me."

### After Receiving an Offer

- **Never accept immediately.** "Thank you, I'm very excited about this opportunity. Can I have 2-3 days to review the complete offer?"
- **Negotiate one thing**: If base is fixed, ask about joining bonus, stock, or flexible working.
- **Show enthusiasm**: "I'm genuinely excited about this role. The only thing I'd like to discuss is..."

### Benchmarks (India, 2+ years DE):

| Company Type | Expected Range |
|---|---|
| Service (TCS, Infosys, Wipro) | 4-8 LPA |
| Product (mid-tier) | 10-18 LPA |
| Product (top-tier / unicorn) | 15-30 LPA |
| FAANG / MNC | 25-45 LPA |

---

## THE INTERVIEWER'S HIDDEN SCORECARD

What they're ACTUALLY evaluating:

| What They Ask | What They're Really Checking |
|---|---|
| "Tell me about yourself" | Can you communicate concisely? |
| "Explain your project" | Do you UNDERSTAND what you built, or just copy-pasted? |
| "Why X over Y?" | Do you evaluate trade-offs like a senior engineer? |
| "What if this breaks?" | Do you think about production reliability? |
| "Walk me through the code" | Can you read and explain code fluently? |
| "What would you improve?" | Do you have growth mindset and self-awareness? |
| "Any questions for us?" | Are you genuinely interested in THIS role? |
| Coding problem | Can you think systematically under pressure? |
| Behavioral question | Will you be a good teammate? Handle conflict? Learn? |

---

## PRE-INTERVIEW CHECKLIST

```
[ ] Resume printed / open on screen
[ ] Both projects accessible (GitHub links, running locally if possible)
[ ] Water bottle nearby
[ ] Quiet room, good lighting, camera working
[ ] Read File 00 study order
[ ] Read File 12 quick reference (refresh definitions)
[ ] Practiced 30-second pitch OUT LOUD (not just in your head)
[ ] Prepared 3 questions to ask them
[ ] Salary range decided (with flexibility)
[ ] Know the company's product / what they do
[ ] Confident mindset: "I built two production AI systems. I'm ready."
```


---


> How to present this project to impress at Google, Amazon, Microsoft, Meta, or any top company.

---

## The Golden Rule: NEVER Just Describe â€" Always Show DEPTH

**Bad answer**: "I used XGBoost to predict diabetes."
**FAANG answer**: "I chose XGBoost over neural nets because the dataset is tabular with 253K records and severe class imbalance at 6:1. XGBoost handles this natively with `scale_pos_weight`, and its gradient-boosted trees excel on structured data â€" outperforming deep learning for tabular problems according to the Grinsztajn et al. 2022 benchmark. I validated with 48 real patient records and achieved 77% accuracy."

---

## How to Structure EVERY Answer: STAR+I

| Step | What | Example |
|---|---|---|
| **S** - Situation | Set the context | "The diabetes dataset had 86% healthy, 14% diabetic records" |
| **T** - Task | What needed to be done | "I needed a screening model that actually catches diabetic patients" |
| **A** - Action | What YOU did (technical) | "I added scale_pos_weight=6.16 and switched from accuracy to sensitivity" |
| **R** - Result | Quantify the outcome | "Disease detection went from 0/5 to 4/5 known diabetic patients" |
| **I** - Impact/Insight | What you learned | "This taught me that accuracy alone is meaningless for imbalanced medical data" |

---

## System Design Questions (THE Most Important Round)

### Q: "Design a disease prediction system that handles 1M requests/day"

**Your answer framework:**

#### Step 1: Requirements (2 minutes)
```
Functional:
- Users submit health metrics â†' get prediction + confidence
- Support 5 disease models
- Real-time AI chat
- User auth + records

Non-functional:
- Latency: <100ms per prediction
- Availability: 99.9%
- Throughput: 1M req/day = ~12 req/sec average, ~100 req/sec peak
- Data privacy: HIPAA compliant
```

#### Step 2: High-Level Design (5 minutes)
```
                    â"Œâ"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"€â"
                    â"‚   CDN (Vercel) â"‚
                    â"‚   Frontend     â"‚
                    â""â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                            â"‚
                    â"Œâ"€â"€â"€â"€â"€â"€â"€â-¼â"€â"€â"€â"€â"€â"€â"€â"€â"
                    â"‚ API Gateway    â"‚  Rate limiting, auth
                    â"‚ (Kong/Nginx)   â"‚
                    â""â"€â"€â"€â"€â"€â"€â"€â"¬â"€â"€â"€â"€â"€â"€â"€â"€â"˜
                     â"Œâ"€â"€â"€â"€â"€â"€â"¼â"€â"€â"€â"€â"€â"€â"
                     â"‚      â"‚      â"‚
              â"Œâ"€â"€â"€â"€â"€â"€â-¼â" â"Œâ"€â"€â"€â-¼â"€â"€â" â"Œâ"€â-¼â"€â"€â"€â"€â"€â"
              â"‚Predict â"‚ â"‚Chat  â"‚ â"‚Auth   â"‚
              â"‚Service â"‚ â"‚Serviceâ"‚ â"‚Serviceâ"‚
              â""â"€â"€â"€â"¬â"€â"€â"€â"€â"˜ â""â"€â"€â"¬â"€â"€â"€â"˜ â""â"€â"€â"¬â"€â"€â"€â"€â"˜
                  â"‚         â"‚        â"‚
           â"Œâ"€â"€â"€â"€â"€â"€â-¼â"€â"€â"  â"Œâ"€â"€â"€â-¼â"€â"€â"  â"Œâ"€â"€â-¼â"€â"€â"
           â"‚Model    â"‚  â"‚Geminiâ"‚  â"‚ DB  â"‚
           â"‚Server   â"‚  â"‚ API  â"‚  â"‚(PG) â"‚
           â"‚(TF Serve)â"‚  â""â"€â"€â"€â"€â"€â"€â"˜  â""â"€â"€â"€â"€â"€â"˜
           â""â"€â"€â"€â"€â"€â"€â"€â"€â"€â"˜
```

#### Step 3: Deep Dive (10 minutes)
**Model Serving:**
- "Instead of pickle in RAM, I'd use TensorFlow Serving or Triton Inference Server"
- "Models versioned in S3: `s3://models/diabetes/v3/model.onnx`"
- "A/B testing: 90% traffic to v2, 10% to v3 â€" compare accuracy"
- "Canary deployment: roll out new model to 1% first"

**Caching:**
- "Redis cache for identical predictions â€" same inputs = same output"
- "Cache key: `hash(model_name + sorted(features))` â†' TTL 1 hour"
- "Reduces model inference calls by ~40% for repeat queries"

**Database:**
- "PostgreSQL with read replicas for /records queries"
- "Write-ahead log for prediction audit trail"
- "JSONB column for flexible health data storage"

**Scaling:**
- "Horizontal scaling: 3 API instances behind load balancer"
- "Model server scales independently â€" GPU instances for heavy models"
- "Chat service scales separately (SSE connections are long-lived)"

#### Step 4: Trade-offs (2 minutes)
- "Chose SSE over WebSocket for simplicity â€" sufficient for unidirectional streaming"
- "Chose PostgreSQL over NoSQL â€" structured health data benefits from relational integrity"
- "Chose ONNX over pickle â€" cross-platform, language-agnostic model format"

---

### Q: "How would you ensure this system is reliable?"

```
1. MONITORING
   - Prometheus metrics: request latency, error rate, model inference time
   - Grafana dashboards: real-time health
   - PagerDuty alerts: if p99 latency > 200ms or error rate > 1%

2. CIRCUIT BREAKER
   - If Gemini API fails 5x in 1 minute â†' stop calling, use fallback
   - Pattern: closed â†' open â†' half-open â†' closed

3. GRACEFUL DEGRADATION
   - Gemini down â†' Ollama local LLM â†' static FAQ responses
   - Database down â†' predictions still work (models in RAM)
   - Redis down â†' bypass cache, direct to service

4. HEALTH CHECKS
   - /healthz endpoint: checks DB connection + model loaded
   - Kubernetes liveness probe: restart if unhealthy
   - Readiness probe: don't route traffic until models loaded

5. DATA BACKUP
   - PostgreSQL: daily automated backups
   - Model files: versioned in S3 with 30-day retention
   - User data: encrypted at rest (AES-256)
```

---

## Behavioral Questions (STAR Format)

### Q: "Tell me about a time you faced a difficult technical challenge."

> **S**: I was building an AI healthcare system with a diabetes prediction model trained on 253K CDC records.
> 
> **T**: The model showed 86.7% accuracy during evaluation, which seemed great. But when I tested it with 5 known diabetic patients from the dataset, it detected zero of them.
> 
> **A**: I investigated and found severe class imbalance â€" 86% of records were healthy. The model learned to just predict "healthy" for everything, getting 86% accuracy by default. I researched class balancing techniques and implemented `scale_pos_weight=6.16` in XGBoost, which tells the algorithm that missing a diabetic patient is 6x worse than a false alarm.
> 
> **R**: Disease detection went from 0% to ~60%. Overall accuracy dropped to 71.7%, but the model now actually catches at-risk patients.
> 
> **I**: This taught me that accuracy alone is a misleading metric for imbalanced datasets. In healthcare, sensitivity (catching sick patients) matters more than overall accuracy. I now always check class distribution before evaluating any model.

---

### Q: "Tell me about a time you had to make a trade-off."

> **S**: I needed to choose between higher accuracy (86.7%) and actual disease detection capability for a medical screening tool.
> 
> **T**: The stakeholder value was in catching at-risk patients early, not in having a high accuracy number.
> 
> **A**: I intentionally accepted a 15-point accuracy drop by adding class balancing. I also added confidence scores and risk levels so users understand HOW confident the model is, and medical disclaimers so they know it's a screening tool, not a diagnosis.
> 
> **R**: The system now detects ~60% of positive cases (up from 0%) and every prediction comes with a confidence percentage. The trade-off was explicitly documented.
> 
> **I**: In production ML, optimizing for the right metric is more important than optimizing for a vanity metric. I'd rather ship a 72% accurate model that saves lives than an 87% one that catches no one.

---

### Q: "Tell me about a time you debugged a complex issue."

> **S**: After deploying the heart disease model, it went from detecting 5/5 known cases to 0/5 â€" a complete regression.
> 
> **T**: I needed to find why the same model on the same data was now giving inverted results.
> 
> **A**: I systematically debugged: (1) Checked model file wasn't corrupted â€" it was fine. (2) Checked API endpoint â€" requests were reaching the model. (3) Printed raw features being sent to the model vs. what training expected. Found the bug: the BRFSS dataset has different column names than the Cleveland Heart Disease schema our API uses. The column mapping was wrong â€" BMI was being interpreted as blood pressure.
> 
> **R**: Fixed the column mapping in `train_heart.py`, retrained, and detection went back to 5/5.
> 
> **I**: Feature alignment between training and inference is critical. Even if the model is perfect, sending features in the wrong order or with wrong encoding will produce garbage predictions. I now always have a test that validates feature alignment.

---

## Power Phrases That Impress FAANG Interviewers

| Instead of saying... | Say this... |
|---|---|
| "I used XGBoost" | "I chose XGBoost because it's the state-of-the-art for tabular data with class imbalance" |
| "I added error handling" | "I implemented a 7-layer middleware stack with rate limiting, security headers, and error masking" |
| "I tested it" | "I validated with 3 testing layers: 141 unit tests, 28 integration checks, and 48 real-world patient records" |
| "It's a healthcare app" | "It's a clinical-grade screening system with confidence scoring, risk stratification, and medical disclaimers" |
| "I used React" | "I built a reusable component architecture â€" one PredictionForm component powers all 5 disease pages" |
| "I stored data" | "I used SQLAlchemy ORM with dependency injection for session lifecycle management" |
| "I did authentication" | "I implemented OAuth2 with JWT tokens, bcrypt password hashing, and role-based access control" |
| "I deployed it" | "The system is deployment-ready with Docker support, environment-based configuration, and CI/CD pipeline design" |

---

## Questions YOU Should Ask the Interviewer

These show senior-level thinking:

1. "How does your team handle model versioning and A/B testing in production?"
2. "What's your approach to monitoring ML model drift in production?"
3. "How do you balance feature velocity with technical debt in healthcare compliance?"
4. "What's the biggest challenge your team faces with real-time data pipelines?"
5. "How does your team handle PII/PHI in development and staging environments?"

---

## Red Flags to Avoid

| Don't... | Do... |
|---|---|
| Say "I just followed a tutorial" | Say "I researched multiple approaches and chose X because..." |
| Give one-word answers | Always give context â†' action â†' result |
| Skip trade-offs | Always mention what you considered AND rejected |
| Ignore failure modes | Always discuss what happens when things break |
| Forget security | Always mention auth, PII protection, HIPAA awareness |
| Present without numbers | Always quantify: 253K records, 77% accuracy, 141 tests, 9ms latency |


---


> "What would you do if..." â€" these test your real-world engineering judgment.

---

## SCENARIO 1: Production Pipeline Failure

**Q: "Your Spark ETL pipeline fails at 2 AM. The downstream reporting team needs data by 6 AM. What do you do?"**

> **Minute 0-5**: Check AutoSys/monitoring alerts. Identify WHICH job failed and the error message.
>
> **Minute 5-15**: Check Spark UI or logs.
> - **OutOfMemoryError** â†' Increase executor memory, reduce partition size
> - **FileNotFoundException** â†' Source file not delivered, check with upstream
> - **Data quality failure** â†' Schema change in source data, investigate
> - **Network/infra** â†' Cluster health, K8s pod status
>
> **Minute 15-30**: Apply fix based on root cause.
> - If fixable: Fix and re-run the failed job (idempotent design means safe to re-run)
> - If source data issue: Contact upstream team, run with previous day's data + alert
> - If infra issue: Escalate to SRE/DevOps
>
> **Before 6 AM**: If the fix takes too long, communicate to the reporting team with an ETA.
>
> **Next day**: Post-mortem. Add monitoring to catch this earlier. Update runbook.

---

## SCENARIO 2: Data Quality Issues

**Q: "You discover that 15% of records in yesterday's batch have null values in a critical field. What do you do?"**

> 1. **Don't panic. Don't delete data.** Investigate first.
>
> 2. **Check if it's a source issue**: Did the upstream system send nulls? Compare with previous days â€" was it always 15% or sudden?
>
> 3. **Check if it's a pipeline issue**: Did our transform introduce the nulls? Check the transformation logic.
>
> 4. **Impact assessment**: What downstream systems consumed this data? Are reports already wrong?
>
> 5. **Decision tree**:
>    - If source is wrong â†' Contact upstream, request re-delivery, hold pipeline
>    - If our pipeline broke â†' Fix the transform, re-run (idempotent)
>    - If it's normal (optional field) â†' Update quality thresholds, document
>
> 6. **Prevention**: Add a quality gate that BLOCKS the pipeline if null% exceeds threshold:
>    ```python
>    null_pct = df["critical_field"].isnull().mean()
>    if null_pct > 0.05:  # >5% nulls = fail
>        raise QualityError(f"Critical field has {null_pct:.1%} nulls")
>    ```

---

## SCENARIO 3: Schema Change

**Q: "The source system adds 3 new columns without telling you. Your pipeline breaks. How do you handle this?"**

> **Immediate**: 
> - Spark's `.read.parquet()` is usually resilient to new columns (reads only specified columns)
> - If using `.read.csv()` with fixed schema â†' that's what broke
>
> **Fix**: Use `schema-on-read` with explicit column selection:
> ```python
> # Bad: reads ALL columns (breaks on schema change)
> df = spark.read.csv("source.csv")
> 
> # Good: reads only columns we need (resilient)
> df = spark.read.csv("source.csv").select("id", "amount", "date")
> ```
>
> **Prevention**: 
> - Schema registry for source contracts
> - Slack/email alerts on schema changes detected in Bronze layer
> - Never `SELECT *` in production pipelines

---

## SCENARIO 4: Performance Degradation

**Q: "Your pipeline that used to run in 30 minutes now takes 3 hours. What do you investigate?"**

> **Step 1**: Check if data volume increased. 3x data = 3x time (expected).
>
> **Step 2**: Check Spark UI:
> - **Shuffle spill to disk?** â†' Need more executor memory
> - **One task taking 10x longer?** â†' Data skew on join key
> - **Too many small tasks?** â†' Too many partitions, need `coalesce()`
> - **GC time > 10%?** â†' Reduce in-memory caching, increase off-heap
>
> **Step 3**: Check infrastructure:
> - K8s: Are pods getting evicted? Resource limits hit?
> - S3/MinIO: Throttling? Check request rates
> - Network: Cross-AZ data transfer?
>
> **Step 4**: Check code changes. Did someone modify the pipeline recently?
>
> **Common fixes**: Broadcast join for newly-large dimension table, repartition skewed data, cache intermediate results.

---

## SCENARIO 5: Data Migration

**Q: "We need to migrate from Oracle to Snowflake. How would you plan this?"**

> **Phase 1 â€" Assessment (Week 1-2)**:
> - Inventory all tables, views, stored procedures
> - Map Oracle data types to Snowflake equivalents
> - Identify transformation logic in stored procedures â†' rewrite in Python/Spark
> - Document dependencies (which reports use which tables)
>
> **Phase 2 â€" Build (Week 3-6)**:
> - Create Snowflake schema (stages, tables, views)
> - Build ETL pipeline: Oracle â†' S3 â†' Snowflake (Snowpipe or COPY INTO)
> - Rewrite stored procedures as dbt models or Python transforms
> - Data validation: row counts, checksums, sample comparisons
>
> **Phase 3 â€" Parallel Run (Week 7-8)**:
> - Run both Oracle and Snowflake pipelines simultaneously
> - Compare outputs daily â€" must be identical
> - Fix discrepancies
>
> **Phase 4 â€" Cutover (Week 9)**:
> - Switch downstream reports to Snowflake
> - Keep Oracle read-only for 30 days (rollback option)
> - Decommission Oracle after validation period

---

## BEHAVIORAL QUESTIONS

### Q: "Tell me about a time you disagreed with a team member."

> **S**: During the YARN to K8s migration, a senior engineer wanted to keep HDFS alongside MinIO "just in case."
>
> **T**: I believed maintaining two storage systems would double operational complexity and create data consistency risks.
>
> **A**: Instead of arguing, I prepared a comparison document showing: (1) MinIO is S3-compatible â€" same API, (2) maintaining HDFS costs $X/month in hardware, (3) dual storage means data can get out of sync. I presented this in the team meeting.
>
> **R**: The team agreed to fully migrate to MinIO with a 30-day rollback plan (keep HDFS read-only). After 30 days of zero issues, we decommissioned HDFS.
>
> **I**: Data-driven arguments beat opinions. Always show the trade-offs with numbers.

### Q: "Tell me about a time you missed a deadline."

> **S**: The Nissan Snowflake integration was planned for 3 weeks. At the end of week 2, I realized the schema validation logic was more complex than estimated â€" the source data had 15 different file formats.
>
> **T**: I needed to either cut scope or extend the timeline.
>
> **A**: I communicated early â€" told the project lead on Friday of week 2, not Monday of week 4. I proposed: deliver the 3 most common file formats by the deadline, handle the remaining 12 in a follow-up sprint.
>
> **R**: The core pipeline shipped on time with 3 formats. The remaining formats were delivered in 2 more sprints. Business users had working data ingestion within the original timeline for their most common use case.
>
> **I**: Communicate early, propose solutions (not just problems), and negotiate scope â€" not quality.

### Q: "Tell me about a time you learned something quickly."

> **S**: At TCS, I was assigned to the Nomura project which used AutoSys â€" a tool I'd never used before.
>
> **T**: I needed to be productive within 2 weeks.
>
> **A**: Day 1-3: Read AutoSys documentation and existing JIL files. Day 4-7: Set up a sandbox environment and created test jobs. Day 8-10: Shadowed a senior engineer during production batch monitoring. Day 11-14: Independently handled a batch failure and recovery.
>
> **R**: Within 2 weeks, I was managing AutoSys job chains independently. Within a month, I was optimizing dependency chains and reducing manual intervention by 25%.
>
> **I**: I learn by doing â€" documentation â†' sandbox â†' shadow â†' independent work.

### Q: "Why do you want to leave TCS?"

> "TCS has given me a strong foundation in enterprise data engineering â€" Spark, SQL, cloud, and working with large financial datasets. I'm now looking for an opportunity where I can: (1) work on more modern data stacks (Delta Lake, dbt, Airflow), (2) get closer to the ML/AI side of data engineering, and (3) work at a company where engineering culture and growth are prioritized."

### Q: "Where do you see yourself in 5 years?"

> "As a Senior Data Engineer or ML Platform Engineer â€" someone who builds the infrastructure that powers AI at scale. I want to be the bridge between raw data and production ML systems. In 5 years, I see myself leading a team that owns the data platform: ingestion, transformation, quality, serving, and monitoring."

### Q: "What's your biggest weakness?"

> "I sometimes over-engineer solutions. For example, in my healthcare project, I built 7 middleware layers and comprehensive testing when a simpler setup might have been sufficient for the initial version. I've learned to ask 'what's the minimum viable solution?' before building, and iterate from there."

---

## HR QUESTIONS

### Q: "Tell me about yourself." (2-minute version)

> "I'm Pavan, a Data Engineer at TCS with 2+ years of experience. I currently work on the Nomura Capital Markets project where I build Spark ETL pipelines processing trade and risk data â€" I've optimized execution time by 30% through broadcast joins and partition pruning, and led the migration from YARN to Kubernetes. Before that, I worked on the Nissan project building serverless batch pipelines on AWS. 
>
> Outside work, I've built two production projects: an AI Healthcare System that predicts 5 diseases using XGBoost on 253K records, and a Movie Recommendation Platform with PySpark Delta Lake pipelines and FAISS vector search. These combine my data engineering skills with practical AI/ML experience.
>
> I'm looking for a role where I can work on larger-scale data infrastructure, ideally at the intersection of data engineering and AI."

### Q: "What are your salary expectations?"

> "I'm currently at [X LPA]. Based on my experience and the market range for this role, I'm looking at [X+30% to X+50%]. But I'm flexible â€" the role, growth opportunities, and team matter more than a specific number."

### Q: "Do you have any questions for us?"

> 1. "What does the data stack look like? (Spark? Airflow? dbt? Cloud?)"
> 2. "How large is the data team and how is it structured?"
> 3. "What's the biggest data engineering challenge you're facing right now?"
> 4. "How does the team handle on-call and production incidents?"
> 5. "What does career growth look like for a Data Engineer here?"

