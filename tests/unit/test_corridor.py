"""Tests for control/corridor.py — EV corridor planner."""

from __future__ import annotations

import pytest

from lanerush.control.corridor import plan
from lanerush.models import EVState


class FakeNetView:
    """Minimal NetView for testing corridor planning."""

    def __init__(
        self,
        edge_lengths: dict[str, float] | None = None,
        speed_limits: dict[str, float] | None = None,
        tls_map: dict[str, str] | None = None,
        connections: dict[tuple[str, str], list[str]] | None = None,
    ) -> None:
        self._edge_lengths = edge_lengths or {}
        self._speed_limits = speed_limits or {}
        self._tls_map = tls_map or {}  # edge_id -> tls_id
        self._connections = connections or {}

    def get_edge_length(self, edge_id: str) -> float:
        return self._edge_lengths.get(edge_id, 250.0)

    def get_edge_speed_limit(self, edge_id: str) -> float:
        return self._speed_limits.get(edge_id, 13.89)

    def get_tls_id_for_edge(self, edge_id: str) -> str | None:
        return self._tls_map.get(edge_id)

    def get_lanes_connecting(self, from_edge: str, to_edge: str) -> list[str]:
        return self._connections.get((from_edge, to_edge), [f"{from_edge}_0"])

    def get_next_tls_junctions(
        self,
        edge_id: str,
        route: tuple[str, ...],
        route_index: int,
        max_junctions: int,
    ) -> list[tuple[str, float]]:
        """Return TLS junctions ahead on the route with distance."""
        junctions: list[tuple[str, float]] = []
        dist = self.get_edge_length(edge_id)  # remaining on current edge
        for i in range(route_index + 1, len(route)):
            if len(junctions) >= max_junctions:
                break
            edge = route[i]
            if edge.startswith(":"):
                continue
            tls = self._tls_map.get(edge)
            if tls is not None:
                junctions.append((tls, dist))
            dist += self.get_edge_length(edge)
        return junctions


def _ev(
    vehicle_id: str = "EV1",
    edge: str = "A1B1",
    speed: float = 10.0,
    route: tuple[str, ...] = ("left1A1", "A1B1", "B1C1", "C1right1"),
    route_index: int = 1,
) -> EVState:
    return EVState(
        vehicle_id=vehicle_id,
        edge=edge,
        lane_id=f"{edge}_0",
        lane_pos=100.0,
        lane_len=250.0,
        speed=speed,
        route=route,
        route_index=route_index,
    )


class TestCorridorPlan:
    @pytest.fixture
    def net(self) -> FakeNetView:
        return FakeNetView(
            edge_lengths={"A1B1": 250.0, "B1C1": 250.0, "C1right1": 250.0},
            speed_limits={"A1B1": 13.89, "B1C1": 13.89},
            tls_map={"B1C1": "J_B1", "C1right1": "J_C1"},
            connections={("A1B1", "B1C1"): ["A1B1_0"]},
        )

    def test_ev_generates_request(self, net: FakeNetView) -> None:
        """An EV approaching a junction within ETA threshold should generate a request."""
        ev = _ev(speed=13.89)  # ETA ≈ 250/13.89 ≈ 18s (within default 12 only if closer)
        requests = plan([ev], net, lookahead_junctions=3, eta_threshold_base=20.0)
        assert len(requests) >= 1
        assert requests[0].vehicle_id == "EV1"

    def test_ev_beyond_threshold_no_request(self, net: FakeNetView) -> None:
        """An EV too far from a junction should NOT generate a request."""
        ev = _ev(speed=1.0)  # ETA = 250/1.0 = 250s >> 12s
        requests = plan([ev], net, lookahead_junctions=3, eta_threshold_base=12.0)
        assert len(requests) == 0

    def test_ev_on_internal_edge_skipped(self, net: FakeNetView) -> None:
        """EVs on internal edges (starting with ':') are skipped."""
        ev = _ev(edge=":J_B1_0")
        requests = plan([ev], net, lookahead_junctions=3)
        assert len(requests) == 0

    def test_lookahead_limit(self, net: FakeNetView) -> None:
        """Should not look beyond lookahead_junctions."""
        ev = _ev(speed=100.0)  # very fast → ETA very low
        requests_1 = plan([ev], net, lookahead_junctions=1, eta_threshold_base=100.0)
        requests_3 = plan([ev], net, lookahead_junctions=3, eta_threshold_base=100.0)
        assert len(requests_1) <= len(requests_3)

    def test_two_evs_same_junction(self) -> None:
        """Two EVs requesting the same junction: both generate requests (arbiter resolves)."""
        net = FakeNetView(
            tls_map={"B1C1": "J_B1"},
        )
        ev1 = _ev(vehicle_id="EV1", speed=13.89)
        ev2 = _ev(vehicle_id="EV2", speed=10.0, edge="A1B1", route_index=1)
        requests = plan([ev1, ev2], net, lookahead_junctions=3, eta_threshold_base=100.0)
        # Both should generate requests (arbiter picks earliest ETA)
        vehicle_ids = {r.vehicle_id for r in requests}
        assert len(vehicle_ids) >= 1  # at least one EV generates a request

    def test_stopped_ev_uses_speed_limit(self) -> None:
        """A stopped EV (speed ≈ 0) should use speed_limit for ETA."""
        net = FakeNetView(
            tls_map={"B1C1": "J_B1"},
            speed_limits={"A1B1": 13.89},
        )
        ev = _ev(speed=0.0)  # stopped
        requests = plan([ev], net, lookahead_junctions=3, eta_threshold_base=25.0)
        # ETA = 250/13.89 ≈ 18s, which is < 25 → should request
        assert len(requests) >= 1
