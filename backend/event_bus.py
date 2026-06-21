"""Clinical Event Bus — async pub/sub for ClinOS domain events.

Provides topic-based routing for clinical events (vitals, diagnostics,
admissions, care events).  Uses in-memory asyncio queues by default and
upgrades to Redis Streams when ``REDIS_URL`` is configured.

Usage::

    from backend.event_bus import event_bus

    async def on_vitals(payload: dict):
        print(payload)

    event_bus.subscribe("VITALS_RECORDED", on_vitals)
    await event_bus.publish("VITALS_RECORDED", {"patient_id": 42, "hr": 78})
"""
from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical event topics
VITALS_RECORDED = "VITALS_RECORDED"
DIAGNOSTIC_ALERT = "DIAGNOSTIC_ALERT"
ADMISSION_EVENT = "ADMISSION_EVENT"
CARE_EVENT = "CARE_EVENT"

ALL_TOPICS = [VITALS_RECORDED, DIAGNOSTIC_ALERT, ADMISSION_EVENT, CARE_EVENT]

# Type alias for subscriber callbacks
Subscriber = Callable[[dict], Coroutine[Any, Any, None]]


class ClinicalEventBus:
    """Singleton async event bus with optional Redis Streams backend.

    * **In-memory mode** (default): events are dispatched via an
      ``asyncio.Queue`` and a background worker task.
    * **Redis mode**: when ``REDIS_URL`` is set the bus publishes to and
      consumes from Redis Streams so events survive process restarts and
      can be shared across replicas.
    """

    _instance: Optional["ClinicalEventBus"] = None

    def __new__(cls) -> "ClinicalEventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)
        self._queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._redis: Any = None  # lazy redis client
        self._consumer_task: Optional[asyncio.Task] = None

        redis_url = os.getenv("REDIS_URL")
        if redis_url and not os.getenv("TESTING"):
            self._init_redis(redis_url)
        else:
            logger.info("ClinicalEventBus: using in-memory async queue (set REDIS_URL for Redis Streams)")

    # ------------------------------------------------------------------
    # Redis Streams initialisation (best-effort)
    # ------------------------------------------------------------------
    def _init_redis(self, redis_url: str) -> None:
        """Attempt to connect to Redis; fall back to in-memory on failure."""
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]

            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            logger.info("ClinicalEventBus: Redis Streams backend configured")
        except Exception as exc:
            logger.warning("ClinicalEventBus: Redis unavailable (%s). Falling back to in-memory.", exc)
            self._redis = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def subscribe(self, topic: str, callback: Subscriber) -> None:
        """Register *callback* for *topic*.

        Args:
            topic: One of the canonical event topics.
            callback: An async callable receiving the event payload dict.
        """
        self._subscribers[topic].append(callback)
        logger.debug("Subscriber registered for topic '%s'", topic)

    async def publish(self, topic: str, payload: dict) -> None:
        """Publish an event.

        In Redis mode the payload is added to a Redis Stream keyed by
        ``clinos:events:{topic}``.  Otherwise it is enqueued locally.

        Args:
            topic: The event topic string.
            payload: Arbitrary JSON-serialisable dict.
        """
        if self._redis is not None:
            try:
                import json

                stream_key = f"clinos:events:{topic}"
                await self._redis.xadd(stream_key, {"payload": json.dumps(payload)})
                logger.debug("Published to Redis stream '%s'", stream_key)
                # Also dispatch locally so in-process subscribers still fire.
                await self._dispatch(topic, payload)
                return
            except Exception as exc:
                logger.warning("Redis publish failed (%s). Dispatching in-memory.", exc)

        # In-memory fallback
        await self._queue.put((topic, payload))

    async def start(self) -> None:
        """Start the background dispatch worker (and optional Redis consumer)."""
        await self.stop()
        self._queue = asyncio.Queue()

        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("ClinicalEventBus: background worker started")

        if self._redis is not None and (self._consumer_task is None or self._consumer_task.done()):
            self._consumer_task = asyncio.create_task(self._redis_consumer_loop())
            logger.info("ClinicalEventBus: Redis consumer started")

    async def stop(self) -> None:
        """Cancel background tasks gracefully."""
        for task in (self._worker_task, self._consumer_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, RuntimeError):
                    pass
        self._worker_task = None
        self._consumer_task = None
        logger.info("ClinicalEventBus: stopped")

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------
    async def _dispatch(self, topic: str, payload: dict) -> None:
        """Invoke every subscriber registered for *topic*."""
        for callback in self._subscribers.get(topic, []):
            try:
                await callback(payload)
            except Exception:
                logger.exception("Error in subscriber for topic '%s'", topic)

    async def _worker_loop(self) -> None:
        """Background loop that drains the in-memory queue."""
        try:
            while True:
                topic, payload = await self._queue.get()
                await self._dispatch(topic, payload)
                self._queue.task_done()
        except (asyncio.CancelledError, RuntimeError) as exc:
            if isinstance(exc, RuntimeError) and "different event loop" not in str(exc):
                raise
            logger.debug("ClinicalEventBus worker cancelled or event loop changed")

    async def _redis_consumer_loop(self) -> None:
        """Background loop reading new entries from Redis Streams."""
        import json

        streams = {f"clinos:events:{t}": "$" for t in ALL_TOPICS}

        try:
            while True:
                try:
                    results = await self._redis.xread(streams, block=5000, count=50)
                except Exception as exc:
                    logger.warning("Redis xread error: %s. Retrying in 5s.", exc)
                    await asyncio.sleep(5)
                    continue

                for stream_key, messages in results:
                    topic = stream_key.replace("clinos:events:", "")
                    for msg_id, fields in messages:
                        try:
                            payload = json.loads(fields.get("payload", "{}"))
                            await self._dispatch(topic, payload)
                        except Exception:
                            logger.exception("Failed to process Redis message %s", msg_id)
                        # Advance read cursor
                        streams[stream_key] = msg_id
        except asyncio.CancelledError:
            logger.debug("ClinicalEventBus Redis consumer cancelled")


# Module-level singleton
event_bus = ClinicalEventBus()
