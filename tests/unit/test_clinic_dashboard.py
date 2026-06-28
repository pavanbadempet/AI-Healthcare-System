import sys
import os

# Import the dashboard script components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.clinic_dashboard import TelemetryStream

def test_telemetry_stream_initialization():
    stream = TelemetryStream()
    assert stream.tick == 0
    assert len(stream.beds) == 40
    assert len(stream.vitals_history) == 0
    assert stream.db_connections == 4
    assert stream.cache_hits == 1240
    assert stream.cache_misses == 45
    assert stream.active_consults == 3

def test_telemetry_stream_update():
    stream = TelemetryStream()
    stream.update()
    
    assert stream.tick == 1
    assert len(stream.vitals_history) == 1
    
    hr, sbp, dbp, spo2, temp = stream.vitals_history[0]
    assert 50 <= hr <= 120
    assert 90 <= sbp <= 150
    assert 50 <= dbp <= 100
    assert 90 <= spo2 <= 100
    assert 95.0 <= temp <= 105.0

def test_telemetry_stream_vitals_history_limit():
    stream = TelemetryStream()
    for _ in range(15):
        stream.update()
        
    # Should cap at 10 historical records
    assert len(stream.vitals_history) == 10
