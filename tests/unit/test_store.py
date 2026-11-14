"""Tests for store/memory.py and store/run_logger.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

from lanerush.models import LaneObservation, PhaseCommand
from lanerush.store.memory import MemoryStore
from lanerush.store.run_logger import CsvRunLogger


class TestMemoryStore:
    def test_put_get_tls(self) -> None:
        store = MemoryStore()
        store.put_tls("J0", {"phase": 0, "state": "GGrr"})
        result = store.get_tls("J0")
        assert result is not None
        assert result["phase"] == 0

    def test_put_get_lane(self) -> None:
        store = MemoryStore()
        store.put_lane("J0_0", {"count": 5, "halting": 2})
        result = store.get_lane("J0_0")
        assert result is not None
        assert result["count"] == 5

    def test_get_missing_returns_none(self) -> None:
        store = MemoryStore()
        assert store.get_tls("nonexistent") is None
        assert store.get_lane("nonexistent") is None
        assert store.get_ev("nonexistent") is None

    def test_publish_consume(self) -> None:
        store = MemoryStore()
        store.publish("events", {"type": "phase_switch", "tls_id": "J0"})
        store.publish("events", {"type": "ev_detected", "vid": "EV1"})
        events = store.consume_channel("events")
        assert len(events) == 2
        # Second consume should be empty
        assert store.consume_channel("events") == []

    def test_get_all_tls(self) -> None:
        store = MemoryStore()
        store.put_tls("J0", {"phase": 0})
        store.put_tls("J1", {"phase": 2})
        all_tls = store.get_all_tls()
        assert len(all_tls) == 2

    def test_put_ev_data(self) -> None:
        store = MemoryStore()
        store.put_ev("EV1", {"edge": "A1B1", "speed": 10.0}, ttl_s=30)
        result = store.get_ev("EV1")
        assert result is not None
        assert result["edge"] == "A1B1"


class TestCsvRunLogger:
    def test_write_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "decisions.csv"
            logger = CsvRunLogger(log_path)
            cmd = PhaseCommand(tls_id="J0", action="switch", target_phase=2, reason="hysteresis")
            logger.decision(t=10, cmd=cmd, scores={"0": 5.0, "2": 15.0})
            logger.close()

            content = log_path.read_text()
            assert "J0" in content
            assert "hysteresis" in content
            assert "switch" in content

    def test_write_lane_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "decisions.csv"
            logger = CsvRunLogger(log_path)
            obs = {
                "J0_0": LaneObservation(
                    lane_id="J0_0",
                    count=5,
                    halting=2,
                    max_wait=10.0,
                    emergency=False,
                    source="ground_truth",
                )
            }
            logger.lane_sample(t=10, obs=obs)
            logger.close()

            samples_path = Path(tmpdir) / "lane_samples.csv"
            content = samples_path.read_text()
            assert "J0_0" in content
            assert "5" in content

    def test_close_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "decisions.csv"
            logger = CsvRunLogger(log_path)
            logger.close()
            logger.close()  # should not crash

    def test_write_after_close_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "decisions.csv"
            logger = CsvRunLogger(log_path)
            logger.close()
            cmd = PhaseCommand(tls_id="J0", action="hold", target_phase=None, reason="stay")
            # Should not raise
            logger.decision(t=99, cmd=cmd, scores={})
