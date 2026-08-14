import sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import duckdb, json, os, pandas as pd

print('=' * 75)
print('🏛️ DATABRICKS DELTA LAKE: PATIENT SEARCH & QUERY AGGREGATION AUDIT')
print('=' * 75)

# Simulate or read clickstream events & diagnostic prediction telemetry
sample_events = [
    {"event_id": "evt_001", "patient_name": "Robert M.", "search_query": "Robert M", "user_id": "clinician_1", "event_type": "patient_search", "timestamp": "2026-08-14 18:40:00"},
    {"event_id": "evt_002", "patient_name": "Robert M.", "search_query": "Robert M", "user_id": "clinician_1", "event_type": "diagnostic_query", "model": "heart", "prediction": "Heart Disease Detected", "risk": "High", "timestamp": "2026-08-14 18:43:00"},
    {"event_id": "evt_003", "patient_name": "Robert M.", "search_query": "Robert M", "user_id": "system_admin", "event_type": "diagnostic_query", "model": "heart", "prediction": "Healthy Heart", "risk": "Low", "timestamp": "2026-08-14 20:06:00"},
    {"event_id": "evt_004", "patient_name": "Robert M.", "search_query": "Robert M, 67M", "user_id": "system_admin", "event_type": "patient_search", "timestamp": "2026-08-14 20:07:00"},
    {"event_id": "evt_005", "patient_name": "James T.", "search_query": "James T", "user_id": "clinician_2", "event_type": "patient_search", "timestamp": "2026-08-14 17:15:00"},
    {"event_id": "evt_006", "patient_name": "James T.", "search_query": "James T", "user_id": "clinician_1", "event_type": "diagnostic_query", "model": "heart", "prediction": "Healthy Heart", "risk": "Low", "timestamp": "2026-08-14 17:20:00"},
    {"event_id": "evt_007", "patient_name": "Elena R.", "search_query": "Elena R", "user_id": "clinician_3", "event_type": "patient_search", "timestamp": "2026-08-14 16:00:00"},
]

df = pd.DataFrame(sample_events)

# Connect in-memory DuckDB / Catalyst SQL engine to execute PySpark-equivalent GroupBy
con = duckdb.connect()
con.register("bronze_clickstream_raw", df)

print('\n[1. BRONZE RAW STREAM INGESTION (All Individual Search & Query Events)]')
print(con.execute("SELECT event_id, patient_name, search_query, user_id, event_type, timestamp FROM bronze_clickstream_raw").df().to_string(index=False))

print('\n[2. GOLD LAYER GROUPBY AGGREGATIONS (Counts, Duplicate Searches, & Activity for Specific Person)]')
gold_query = """
SELECT 
    patient_name,
    COUNT(*) as total_events_count,
    COUNT(CASE WHEN event_type = 'patient_search' THEN 1 END) as search_count,
    COUNT(CASE WHEN event_type = 'diagnostic_query' THEN 1 END) as diagnostic_query_count,
    COUNT(DISTINCT user_id) as unique_clinicians_querying,
    MIN(timestamp) as first_searched_at,
    MAX(timestamp) as latest_searched_at
FROM bronze_clickstream_raw
GROUP BY patient_name
ORDER BY total_events_count DESC
"""
df_gold = con.execute(gold_query).df()
print(df_gold.to_string(index=False))

print('\n[3. DRILL-DOWN: SPECIFIC SEARCH QUERY BREAKDOWN FOR "Robert M."]')
robert_query = """
SELECT 
    patient_name,
    search_query,
    COUNT(*) as duplicate_query_frequency,
    COUNT(DISTINCT user_id) as distinct_users,
    MIN(timestamp) as earliest_query,
    MAX(timestamp) as latest_query
FROM bronze_clickstream_raw
WHERE patient_name = 'Robert M.'
GROUP BY patient_name, search_query
"""
df_robert = con.execute(robert_query).df()
print(df_robert.to_string(index=False))
