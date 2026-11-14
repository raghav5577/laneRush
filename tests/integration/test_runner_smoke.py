"""Integration test: runner smoke test with FakeSim.

Requires: @pytest.mark.sumo for real SUMO tests, otherwise uses FakeSim.
"""

from __future__ import annotations

import pytest

from lanerush.sim.traci_client import FakeSim, SimSnapshot


class TestFakeSim:
    """Verify FakeSim returns valid types without SUMO."""

    def test_step_increments_time(self) -> None:
        sim = FakeSim(tls_ids=["J0"])
        assert sim.current_time == 0
        sim.step()
        assert sim.current_time == 1

    def test_snapshot_returns_simstate(self) -> None:
        sim = FakeSim(
            tls_ids=["J0", "J1"],
            lanes={"J0_0": {"count": 3, "halting": 1, "max_wait": 5.0}},
        )
        snap = sim.snapshot()
        assert isinstance(snap, SimSnapshot)
        assert snap.t == 0
        assert "J0_0" in snap.observations
        assert snap.observations["J0_0"].count == 3

    def test_set_phase(self) -> None:
        sim = FakeSim(tls_ids=["J0"])
        sim.set_phase("J0", 2)
        assert sim.get_tls_phase("J0") == 2

    def test_tls_program(self) -> None:
        sim = FakeSim(tls_ids=["J0"])
        program = sim.get_tls_program("J0")
        assert len(program) == 4
        assert all(isinstance(p, tuple) and len(p) == 2 for p in program)

    def test_close_is_safe(self) -> None:
        sim = FakeSim()
        sim.close()  # should not crash


@pytest.mark.sumo
class TestRunnerSmoke:
    """Smoke test that requires SUMO. Skipped without SUMO marker."""

    def test_placeholder(self) -> None:
        """Placeholder until SUMO is available."""
        pytest.skip("SUMO integration test — run with pytest -m sumo")
