# 20 — Scenario-Based & Behavioral Questions

> "What would you do if..." — these test your real-world engineering judgment.

---

## SCENARIO 1: Production Pipeline Failure

**Q: "Your Spark ETL pipeline fails at 2 AM. The downstream reporting team needs data by 6 AM. What do you do?"**

> **Minute 0-5**: Check AutoSys/monitoring alerts. Identify WHICH job failed and the error message.
>
> **Minute 5-15**: Check Spark UI or logs.
> - **OutOfMemoryError** → Increase executor memory, reduce partition size
> - **FileNotFoundException** → Source file not delivered, check with upstream
> - **Data quality failure** → Schema change in source data, investigate
> - **Network/infra** → Cluster health, K8s pod status
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
> 2. **Check if it's a source issue**: Did the upstream system send nulls? Compare with previous days — was it always 15% or sudden?
>
> 3. **Check if it's a pipeline issue**: Did our transform introduce the nulls? Check the transformation logic.
>
> 4. **Impact assessment**: What downstream systems consumed this data? Are reports already wrong?
>
> 5. **Decision tree**:
>    - If source is wrong → Contact upstream, request re-delivery, hold pipeline
>    - If our pipeline broke → Fix the transform, re-run (idempotent)
>    - If it's normal (optional field) → Update quality thresholds, document
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
> - If using `.read.csv()` with fixed schema → that's what broke
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
> - **Shuffle spill to disk?** → Need more executor memory
> - **One task taking 10x longer?** → Data skew on join key
> - **Too many small tasks?** → Too many partitions, need `coalesce()`
> - **GC time > 10%?** → Reduce in-memory caching, increase off-heap
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

> **Phase 1 — Assessment (Week 1-2)**:
> - Inventory all tables, views, stored procedures
> - Map Oracle data types to Snowflake equivalents
> - Identify transformation logic in stored procedures → rewrite in Python/Spark
> - Document dependencies (which reports use which tables)
>
> **Phase 2 — Build (Week 3-6)**:
> - Create Snowflake schema (stages, tables, views)
> - Build ETL pipeline: Oracle → S3 → Snowflake (Snowpipe or COPY INTO)
> - Rewrite stored procedures as dbt models or Python transforms
> - Data validation: row counts, checksums, sample comparisons
>
> **Phase 3 — Parallel Run (Week 7-8)**:
> - Run both Oracle and Snowflake pipelines simultaneously
> - Compare outputs daily — must be identical
> - Fix discrepancies
>
> **Phase 4 — Cutover (Week 9)**:
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
> **A**: Instead of arguing, I prepared a comparison document showing: (1) MinIO is S3-compatible — same API, (2) maintaining HDFS costs $X/month in hardware, (3) dual storage means data can get out of sync. I presented this in the team meeting.
>
> **R**: The team agreed to fully migrate to MinIO with a 30-day rollback plan (keep HDFS read-only). After 30 days of zero issues, we decommissioned HDFS.
>
> **I**: Data-driven arguments beat opinions. Always show the trade-offs with numbers.

### Q: "Tell me about a time you missed a deadline."

> **S**: The Nissan Snowflake integration was planned for 3 weeks. At the end of week 2, I realized the schema validation logic was more complex than estimated — the source data had 15 different file formats.
>
> **T**: I needed to either cut scope or extend the timeline.
>
> **A**: I communicated early — told the project lead on Friday of week 2, not Monday of week 4. I proposed: deliver the 3 most common file formats by the deadline, handle the remaining 12 in a follow-up sprint.
>
> **R**: The core pipeline shipped on time with 3 formats. The remaining formats were delivered in 2 more sprints. Business users had working data ingestion within the original timeline for their most common use case.
>
> **I**: Communicate early, propose solutions (not just problems), and negotiate scope — not quality.

### Q: "Tell me about a time you learned something quickly."

> **S**: At TCS, I was assigned to the Nomura project which used AutoSys — a tool I'd never used before.
>
> **T**: I needed to be productive within 2 weeks.
>
> **A**: Day 1-3: Read AutoSys documentation and existing JIL files. Day 4-7: Set up a sandbox environment and created test jobs. Day 8-10: Shadowed a senior engineer during production batch monitoring. Day 11-14: Independently handled a batch failure and recovery.
>
> **R**: Within 2 weeks, I was managing AutoSys job chains independently. Within a month, I was optimizing dependency chains and reducing manual intervention by 25%.
>
> **I**: I learn by doing — documentation → sandbox → shadow → independent work.

### Q: "Why do you want to leave TCS?"

> "TCS has given me a strong foundation in enterprise data engineering — Spark, SQL, cloud, and working with large financial datasets. I'm now looking for an opportunity where I can: (1) work on more modern data stacks (Delta Lake, dbt, Airflow), (2) get closer to the ML/AI side of data engineering, and (3) work at a company where engineering culture and growth are prioritized."

### Q: "Where do you see yourself in 5 years?"

> "As a Senior Data Engineer or ML Platform Engineer — someone who builds the infrastructure that powers AI at scale. I want to be the bridge between raw data and production ML systems. In 5 years, I see myself leading a team that owns the data platform: ingestion, transformation, quality, serving, and monitoring."

### Q: "What's your biggest weakness?"

> "I sometimes over-engineer solutions. For example, in my healthcare project, I built 7 middleware layers and comprehensive testing when a simpler setup might have been sufficient for the initial version. I've learned to ask 'what's the minimum viable solution?' before building, and iterate from there."

---

## HR QUESTIONS

### Q: "Tell me about yourself." (2-minute version)

> "I'm Pavan, a Data Engineer at TCS with 2+ years of experience. I currently work on the Nomura Capital Markets project where I build Spark ETL pipelines processing trade and risk data — I've optimized execution time by 30% through broadcast joins and partition pruning, and led the migration from YARN to Kubernetes. Before that, I worked on the Nissan project building serverless batch pipelines on AWS. 
>
> Outside work, I've built two production projects: an AI Healthcare System that predicts 5 diseases using XGBoost on 253K records, and a Movie Recommendation Platform with PySpark Delta Lake pipelines and FAISS vector search. These combine my data engineering skills with practical AI/ML experience.
>
> I'm looking for a role where I can work on larger-scale data infrastructure, ideally at the intersection of data engineering and AI."

### Q: "What are your salary expectations?"

> "I'm currently at [X LPA]. Based on my experience and the market range for this role, I'm looking at [X+30% to X+50%]. But I'm flexible — the role, growth opportunities, and team matter more than a specific number."

### Q: "Do you have any questions for us?"

> 1. "What does the data stack look like? (Spark? Airflow? dbt? Cloud?)"
> 2. "How large is the data team and how is it structured?"
> 3. "What's the biggest data engineering challenge you're facing right now?"
> 4. "How does the team handle on-call and production incidents?"
> 5. "What does career growth look like for a Data Engineer here?"
