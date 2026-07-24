"""
Unit tests for SOTA Observability Engine (backend/sota_observability.py).
"""

import time

from backend.sota_observability import SOTAObservabilityEngine


def test_distributed_tracing_and_latency_percentiles():
    engine = SOTAObservabilityEngine()

    start_time = time.time()
    span = engine.start_trace("ANALYZE_PATIENT_RADIOLOGY_CT_SCAN")
    assert len(span.trace_id) > 0
    assert len(span.span_id) == 8

    time.sleep(0.01)  # Simulate 10ms execution
    engine.record_span_completion(span, start_time, status="OK")

    assert len(engine.recorded_spans) == 1
    assert engine.recorded_spans[0].duration_ms >= 5.0

    percentiles = engine.get_latency_percentiles()
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles
    assert percentiles["p50"] >= 5.0
