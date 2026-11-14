"""Tests for control/arbiter.py — arbitrate() truth table.

Invariants from AGENTS.md §6:
  - Never switch in yellow
  - Never return a phase outside green_phases
"""

from __future__ import annotations

import pytest

from lanerush.control.arbiter import arbitrate
from lanerush.models import CorridorRequest, PhaseCommand, TlsInfo


@pytest.fixture
def tls() -> TlsInfo:
    return TlsInfo(
        tls_id="J0",
        green_phases=(0, 2),
        yellow_after={0: 1, 2: 3},
        lanes_of={0: ("J0_0", "J0_1"), 2: ("J0_2", "J0_3")},
    )


def _adaptive(action: str = "hold", reason: str = "stay") -> PhaseCommand:
    return PhaseCommand(tls_id="J0", action=action, target_phase=None, reason=reason)  # type: ignore[arg-type]


class TestArbitrate:
    def test_yellow_always_hold(self, tls: TlsInfo) -> None:
        """In yellow → hold, regardless of corridor requests."""
        req = CorridorRequest(tls_id="J0", phase=2, eta_s=3.0, vehicle_id="EV1")
        result = arbitrate(_adaptive(), [req], tls, current_phase=0, t_in=10, in_yellow=True)
        assert result.action == "hold"
        assert "yellow" in result.reason

    def test_corridor_switch_different_phase(self, tls: TlsInfo) -> None:
        """Corridor request for different phase + t_in >= 2 → switch (corridor)."""
        req = CorridorRequest(tls_id="J0", phase=2, eta_s=5.0, vehicle_id="EV1")
        result = arbitrate(_adaptive(), [req], tls, current_phase=0, t_in=5, in_yellow=False)
        assert result.action == "switch"
        assert result.target_phase == 2
        assert result.reason == "corridor"

    def test_corridor_hold_same_phase(self, tls: TlsInfo) -> None:
        """Corridor request for same phase → hold (corridor_hold)."""
        req = CorridorRequest(tls_id="J0", phase=0, eta_s=5.0, vehicle_id="EV1")
        result = arbitrate(_adaptive(), [req], tls, current_phase=0, t_in=5, in_yellow=False)
        assert result.action == "hold"
        assert result.reason == "corridor_hold"

    def test_corridor_no_switch_t_in_lt_2(self, tls: TlsInfo) -> None:
        """Corridor request for different phase but t_in < 2 → hold."""
        req = CorridorRequest(tls_id="J0", phase=2, eta_s=5.0, vehicle_id="EV1")
        result = arbitrate(_adaptive(), [req], tls, current_phase=0, t_in=1, in_yellow=False)
        assert result.action == "hold"

    def test_no_request_passthrough(self, tls: TlsInfo) -> None:
        """No corridor request → pass adaptive command through."""
        adaptive = _adaptive(action="switch", reason="hysteresis")
        result = arbitrate(adaptive, [], tls, current_phase=0, t_in=20, in_yellow=False)
        assert result == adaptive

    def test_two_evs_earliest_eta_wins(self, tls: TlsInfo) -> None:
        """Two EVs requesting same junction: earliest ETA wins."""
        req1 = CorridorRequest(tls_id="J0", phase=2, eta_s=8.0, vehicle_id="EV1")
        req2 = CorridorRequest(tls_id="J0", phase=0, eta_s=3.0, vehicle_id="EV2")
        result = arbitrate(_adaptive(), [req1, req2], tls, current_phase=2, t_in=5, in_yellow=False)
        # EV2 has earlier ETA (3.0), requests phase 0, current is 2 → switch to 0
        assert result.action == "switch"
        assert result.target_phase == 0

    def test_invariant_never_switch_in_yellow(self, tls: TlsInfo) -> None:
        """Invariant: never switch in yellow, even with requests."""
        req = CorridorRequest(tls_id="J0", phase=2, eta_s=1.0, vehicle_id="EV1")
        for t_in in range(0, 100):
            result = arbitrate(
                _adaptive(), [req], tls, current_phase=0, t_in=t_in, in_yellow=True
            )
            assert result.action == "hold", f"Switched in yellow at t_in={t_in}"

    def test_invariant_phase_in_green_phases(self, tls: TlsInfo) -> None:
        """Invariant: returned target_phase must be in green_phases or None."""
        for phase in [0, 2]:
            req = CorridorRequest(tls_id="J0", phase=phase, eta_s=2.0, vehicle_id="EV1")
            result = arbitrate(
                _adaptive(), [req], tls, current_phase=(2 if phase == 0 else 0),
                t_in=5, in_yellow=False,
            )
            if result.target_phase is not None:
                assert result.target_phase in tls.green_phases

    def test_request_for_other_junction_ignored(self, tls: TlsInfo) -> None:
        """Requests for a different junction should be ignored."""
        req = CorridorRequest(tls_id="J1", phase=0, eta_s=2.0, vehicle_id="EV1")
        adaptive = _adaptive(reason="stay")
        result = arbitrate(adaptive, [req], tls, current_phase=0, t_in=20, in_yellow=False)
        assert result == adaptive
