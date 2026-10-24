# Delta Lake File Compaction and Partition Sizing

## Partition Pruning Strategies
- Clinical encounter tables partitioned by `encounter_year` and `admission_quarter`.
- `OPTIMIZE` command with `ZORDER BY (patient_id, encounter_date)` to accelerate temporal slice queries.
- Target file size set to 128MB to avoid small-file overhead in Databricks serverless compute.
