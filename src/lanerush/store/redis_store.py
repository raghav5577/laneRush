"""Redis StateStore — falls back to MemoryStore on failure."""

from __future__ import annotations

import logging
from typing import Any

from lanerush.store.memory import MemoryStore

logger = logging.getLogger(__name__)

_KEY_TLS = "lr:tls:{}"
_KEY_LANE = "lr:lane:{}"
_KEY_EV = "lr:ev:{}"
_CHANNEL_PREFIX = "lr:events:{}"


class RedisStore:
    """StateStore backed by Redis with MemoryStore fallback.

    Graceful degradation: Redis failure → log one WARNING, fall back to MemoryStore.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        self._fallback = MemoryStore()
        self._redis: Any = None
        self._warned = False
        try:
            import redis  # noqa: PLC0415

            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Connected to Redis at %s", redis_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis unavailable (%s); using MemoryStore fallback.", exc)
            self._redis = None

    def _use_redis(self) -> bool:
        return self._redis is not None

    def put_tls(self, tls_id: str, data: dict[str, Any]) -> None:
        if self._use_redis():
            try:
                import json  # noqa: PLC0415

                self._redis.set(_KEY_TLS.format(tls_id), json.dumps(data))
                return
            except Exception as exc:  # noqa: BLE001
                if not self._warned:
                    logger.warning("Redis write failed (%s); falling back.", exc)
                    self._warned = True
        self._fallback.put_tls(tls_id, data)

    def put_lane(self, lane_id: str, data: dict[str, Any]) -> None:
        if self._use_redis():
            try:
                import json  # noqa: PLC0415

                self._redis.set(_KEY_LANE.format(lane_id), json.dumps(data))
                return
            except Exception as exc:  # noqa: BLE001
                if not self._warned:
                    logger.warning("Redis write failed (%s); falling back.", exc)
                    self._warned = True
        self._fallback.put_lane(lane_id, data)

    def put_ev(self, vehicle_id: str, data: dict[str, Any], ttl_s: int = 30) -> None:
        if self._use_redis():
            try:
                import json  # noqa: PLC0415

                key = _KEY_EV.format(vehicle_id)
                self._redis.setex(key, ttl_s, json.dumps(data))
                return
            except Exception as exc:  # noqa: BLE001
                if not self._warned:
                    logger.warning("Redis write failed (%s); falling back.", exc)
                    self._warned = True
        self._fallback.put_ev(vehicle_id, data, ttl_s)

    def publish(self, channel: str, event: dict[str, Any]) -> None:
        if self._use_redis():
            try:
                import json  # noqa: PLC0415

                self._redis.publish(_CHANNEL_PREFIX.format(channel), json.dumps(event))
                return
            except Exception as exc:  # noqa: BLE001
                if not self._warned:
                    logger.warning("Redis publish failed (%s); falling back.", exc)
                    self._warned = True
        self._fallback.publish(channel, event)
