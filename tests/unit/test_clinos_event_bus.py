"""ClinOS Event Bus unit tests.

Tests the in-memory publish/subscribe pattern of the ClinicalEventBus.
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest


@pytest.fixture
async def _clean_event_bus():
    """Provide a fresh event bus for each test."""
    from backend.event_bus import ClinicalEventBus

    bus = ClinicalEventBus()
    await bus.stop()
    bus._subscribers.clear()
    bus._queue = asyncio.Queue()
    await bus.start()
    yield bus
    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe(_clean_event_bus):
    """Verify that published events are dispatched to the correct subscribers."""
    bus = _clean_event_bus
    received: list[dict] = []

    async def handler(payload: dict) -> None:
        received.append(payload)

    bus.subscribe("VITALS_RECORDED", handler)

    test_payload = {"patient_id": 42, "heart_rate": 95, "spo2": 97.2}
    await bus.publish("VITALS_RECORDED", test_payload)

    # Give the dispatcher a moment to process
    await asyncio.sleep(0.1)

    assert len(received) == 1
    assert received[0]["patient_id"] == 42
    assert received[0]["heart_rate"] == 95


@pytest.mark.asyncio
async def test_event_bus_topic_isolation(_clean_event_bus):
    """Events published on one topic must NOT trigger subscribers of another topic."""
    bus = _clean_event_bus
    wrong_received: list[dict] = []

    async def wrong_handler(payload: dict) -> None:
        wrong_received.append(payload)

    bus.subscribe("ADMISSION_EVENT", wrong_handler)

    await bus.publish("VITALS_RECORDED", {"patient_id": 1})
    await asyncio.sleep(0.1)

    assert len(wrong_received) == 0, "Subscriber for ADMISSION_EVENT should not receive VITALS_RECORDED events"


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers(_clean_event_bus):
    """Multiple subscribers on the same topic should all receive the event."""
    bus = _clean_event_bus
    results_a: list[dict] = []
    results_b: list[dict] = []

    async def handler_a(payload: dict) -> None:
        results_a.append(payload)

    async def handler_b(payload: dict) -> None:
        results_b.append(payload)

    bus.subscribe("DIAGNOSTIC_ALERT", handler_a)
    bus.subscribe("DIAGNOSTIC_ALERT", handler_b)

    await bus.publish("DIAGNOSTIC_ALERT", {"alert": "high_risk"})
    await asyncio.sleep(0.1)

    assert len(results_a) == 1
    assert len(results_b) == 1


def test_event_bus_does_not_log_redis_credentials(caplog):
    from backend.event_bus import ClinicalEventBus

    redis_url = "rediss://service-user:top-secret@example.invalid:6379/0"
    caplog.set_level("INFO", logger="backend.event_bus")
    bus = ClinicalEventBus()

    with patch("redis.asyncio.from_url", return_value=object()):
        bus._init_redis(redis_url)

    assert "Redis Streams backend configured" in caplog.text
    assert redis_url not in caplog.text
    assert "top-secret" not in caplog.text
