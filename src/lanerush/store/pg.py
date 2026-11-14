"""Postgres StateStore — falls back to MemoryStore on failure."""

from __future__ import annotations

import logging
from typing import Any

from lanerush.store.memory import MemoryStore

logger = logging.getLogger(__name__)


class PgStore:
    """StateStore backed by Postgres with MemoryStore fallback.

    Graceful degradation: Postgres failure → log one WARNING, fall back to MemoryStore.
    Uses batched inserts every `batch_every_steps` steps.
    """

    def __init__(
        self,
        pg_dsn: str = "postgresql://lanerush:lanerush@localhost:5432/lanerush",
        batch_every_steps: int = 50,
    ) -> None:
        self._fallback = MemoryStore()
        self._engine: Any = None
        self._warned = False
        self._batch: list[dict[str, Any]] = []
        self._batch_every = batch_every_steps

        try:
            import sqlalchemy as sa  # noqa: PLC0415

            self._engine = sa.create_engine(pg_dsn, pool_pre_ping=True)
            with self._engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            logger.info("Connected to Postgres at %s", pg_dsn)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Postgres unavailable (%s); using MemoryStore fallback.", exc)
            self._engine = None

    def _use_pg(self) -> bool:
        return self._engine is not None

    def put_tls(self, tls_id: str, data: dict[str, Any]) -> None:
        if not self._use_pg():
            self._fallback.put_tls(tls_id, data)
            return
        try:
            import json  # noqa: PLC0415

            import sqlalchemy as sa  # noqa: PLC0415

            with self._engine.begin() as conn:
                conn.execute(
                    sa.text(
                        "INSERT INTO tls_state (tls_id, data) VALUES (:tls_id, :data) "
                        "ON CONFLICT (tls_id) DO UPDATE SET data = EXCLUDED.data"
                    ),
                    {"tls_id": tls_id, "data": json.dumps(data)},
                )
        except Exception as exc:  # noqa: BLE001
            if not self._warned:
                logger.warning("Postgres write failed (%s); falling back.", exc)
                self._warned = True
            self._fallback.put_tls(tls_id, data)

    def put_lane(self, lane_id: str, data: dict[str, Any]) -> None:
        self._fallback.put_lane(lane_id, data)  # Batched insert in Phase 7

    def put_ev(self, vehicle_id: str, data: dict[str, Any], ttl_s: int = 30) -> None:
        self._fallback.put_ev(vehicle_id, data, ttl_s)

    def publish(self, channel: str, event: dict[str, Any]) -> None:
        self._fallback.publish(channel, event)
