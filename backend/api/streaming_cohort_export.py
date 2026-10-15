"""
FastAPI chunked streaming response generator for million-row patient cohort exports.
"""
import json
from typing import AsyncGenerator, Dict, Any, List

async def stream_cohort_ndjson(cohort_generator: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
    """Yields newline-delimited JSON rows with low server memory footprint."""
    for record in cohort_generator:
        yield json.dumps(record) + "\n"
