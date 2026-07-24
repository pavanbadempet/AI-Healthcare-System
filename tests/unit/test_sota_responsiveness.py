"""
Unit tests for SOTA Responsiveness Engine (backend/sota_responsiveness.py).
"""

import pytest

from backend.sota_responsiveness import (
    LatencyTracker,
    generate_optimistic_response,
    sota_stream_clinical_response,
)


def test_latency_tracker():
    tracker = LatencyTracker()
    tracker.record("/api/predict", 12.5)
    tracker.record("/api/predict", 7.5)

    avg = tracker.get_average_latency("/api/predict")
    assert avg == 10.0


@pytest.mark.asyncio
async def test_sota_streaming():
    text = "Clinical prediction result for patient 101"
    chunks = []
    async for chunk in sota_stream_clinical_response(text):
        chunks.append(chunk)

    full_reconstructed = "".join(chunks).strip()
    assert full_reconstructed == text


def test_optimistic_response():
    resp = generate_optimistic_response("BOOK_APPOINTMENT", {"patient_id": "P123"})
    assert resp["status"] == "optimistic_success"
    assert resp["action"] == "BOOK_APPOINTMENT"
