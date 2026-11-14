"""Thread-safe in-memory StateStore implementation."""

from __future__ import annotations

import threading
import time
from typing import Any


class MemoryStore:
    """Full in-memory implementation of the StateStore Protocol.

    Thread-safe with a single lock. TTL entries are expired lazily on read.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tls: dict[str, dict[str, Any]] = {}
        self._lanes: dict[str, dict[str, Any]] = {}
        self._evs: dict[str, tuple[dict[str, Any], float]] = {}  # value, expiry_ts
        self._channels: dict[str, list[dict[str, Any]]] = {}

    # -- StateStore Protocol --

    def put_tls(self, tls_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._tls[tls_id] = dict(data)

    def put_lane(self, lane_id: str, data: dict[str, Any]) -> None:
        with self._lock:
            self._lanes[lane_id] = dict(data)

    def put_ev(self, vehicle_id: str, data: dict[str, Any], ttl_s: int = 30) -> None:
        expiry = time.monotonic() + ttl_s
        with self._lock:
            self._evs[vehicle_id] = (dict(data), expiry)

    def publish(self, channel: str, event: dict[str, Any]) -> None:
        with self._lock:
            self._channels.setdefault(channel, []).append(dict(event))

    # -- Read helpers (not part of Protocol, used by dashboard replay) --

    def get_tls(self, tls_id: str) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._tls[tls_id]) if tls_id in self._tls else None

    def get_lane(self, lane_id: str) -> dict[str, Any] | None:
        with self._lock:
            return dict(self._lanes[lane_id]) if lane_id in self._lanes else None

    def get_ev(self, vehicle_id: str) -> dict[str, Any] | None:
        with self._lock:
            if vehicle_id not in self._evs:
                return None
            data, expiry = self._evs[vehicle_id]
            if time.monotonic() > expiry:
                del self._evs[vehicle_id]
                return None
            return dict(data)

    def get_all_tls(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {k: dict(v) for k, v in self._tls.items()}

    def get_all_active_evs(self) -> dict[str, dict[str, Any]]:
        now = time.monotonic()
        with self._lock:
            expired = [vid for vid, (_, exp) in self._evs.items() if now > exp]
            for vid in expired:
                del self._evs[vid]
            return {vid: dict(data) for vid, (data, _) in self._evs.items()}

    def consume_channel(self, channel: str) -> list[dict[str, Any]]:
        with self._lock:
            events = self._channels.pop(channel, [])
            return events
