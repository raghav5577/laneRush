"""LaneRush dataclasses and Protocols — do NOT modify without human approval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable


@dataclass(frozen=True)
class LaneObservation:
    lane_id: str
    count: int
    halting: int
    max_wait: float
    emergency: bool
    source: str


@dataclass(frozen=True)
class EVState:
    vehicle_id: str
    edge: str
    lane_id: str
    lane_pos: float
    lane_len: float
    speed: float
    route: tuple[str, ...]
    route_index: int


@dataclass(frozen=True)
class TlsInfo:
    tls_id: str
    green_phases: tuple[int, ...]
    yellow_after: dict[int, int]
    lanes_of: dict[int, tuple[str, ...]]


@dataclass(frozen=True)
class CorridorRequest:
    tls_id: str
    phase: int
    eta_s: float
    vehicle_id: str


@dataclass(frozen=True)
class PhaseCommand:
    tls_id: str
    action: Literal["hold", "switch"]
    target_phase: int | None
    reason: str


@runtime_checkable
class DetectionProvider(Protocol):
    def observe(self, t: int) -> dict[str, LaneObservation]: ...


@runtime_checkable
class StateStore(Protocol):
    def put_tls(self, tls_id: str, data: dict) -> None: ...  # type: ignore[type-arg]
    def put_lane(self, lane_id: str, data: dict) -> None: ...  # type: ignore[type-arg]
    def put_ev(self, vehicle_id: str, data: dict, ttl_s: int = 30) -> None: ...  # type: ignore[type-arg]
    def publish(self, channel: str, event: dict) -> None: ...  # type: ignore[type-arg]


@runtime_checkable
class RunLogger(Protocol):
    def decision(self, t: int, cmd: PhaseCommand, scores: dict[str, float]) -> None: ...
    def lane_sample(self, t: int, obs: dict[str, LaneObservation]) -> None: ...
    def close(self) -> None: ...


class NetView(Protocol):
    def get_edge_length(self, edge_id: str) -> float: ...
    def get_edge_speed_limit(self, edge_id: str) -> float: ...
    def get_tls_id_for_edge(self, edge_id: str) -> str | None: ...
    def get_lanes_connecting(self, from_edge: str, to_edge: str) -> list[str]: ...
    def get_next_tls_junctions(
        self,
        edge_id: str,
        route: tuple[str, ...],
        route_index: int,
        max_junctions: int,
    ) -> list[tuple[str, float]]: ...


def is_emergency(vtype: str) -> bool:
    """Return True iff the vehicle type string represents an emergency vehicle."""
    return vtype == "emergency"
