"""Lane and phase scoring — NO forbidden imports."""

from __future__ import annotations

from lanerush.models import LaneObservation, TlsInfo


def lane_score(
    obs: LaneObservation,
    w_count: float,
    w_halt: float,
    w_age: float,
) -> float:
    """Score a single lane: w_count*count + w_halt*halting + w_age*max_wait."""
    return w_count * obs.count + w_halt * obs.halting + w_age * obs.max_wait


def phase_scores(
    tls: TlsInfo,
    observations: dict[str, LaneObservation],
    w_count: float,
    w_halt: float,
    w_age: float,
) -> dict[int, float]:
    """Return a score for each green phase: sum of lane_score over its lanes."""
    result: dict[int, float] = {}
    for phase in tls.green_phases:
        lanes = tls.lanes_of.get(phase, ())
        result[phase] = sum(
            lane_score(observations[lane], w_count, w_halt, w_age)
            for lane in lanes
            if lane in observations
        )
    return result
