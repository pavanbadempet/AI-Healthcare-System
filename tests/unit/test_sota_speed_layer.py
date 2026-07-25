"""
Unit tests for SOTA High-Speed Stream Engine (backend/sota_speed_layer.py).
"""

import time

from backend.sota_speed_layer import SOTASpeedLayerEngine, StreamMetric


def test_streaming_window_aggregation_and_watermarking():
    engine = SOTASpeedLayerEngine(watermark_delay_sec=1.0)
    now = time.time()

    m1 = StreamMetric(device_id="DEV_900", metric_name="heart_rate", value=72.0, timestamp=now - 5)
    m2 = StreamMetric(device_id="DEV_900", metric_name="heart_rate", value=84.0, timestamp=now - 2)

    engine.ingest_stream_metric(m1)
    engine.ingest_stream_metric(m2)

    result = engine.process_window("DEV_900", "heart_rate", window_duration_sec=30)

    assert result.window_count == 2
    assert result.mean_value == 78.0
    assert result.max_value == 84.0
    assert result.min_value == 72.0
    assert result.watermark_delay_ms == 1000.0
