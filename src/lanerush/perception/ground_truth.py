"""Ground-truth DetectionProvider — reads directly from the sim snapshot."""

from __future__ import annotations

from lanerush.models import LaneObservation


class GroundTruthProvider:
    """Returns the simulator's exact lane observations. No noise."""

    def __init__(self, sim: object) -> None:
        # sim is a TraciClient or FakeSim — accessed via its snapshot() method
        self._sim = sim

    def observe(self, t: int) -> dict[str, LaneObservation]:
        """Return lane observations from the last snapshot."""
        # The runner calls sim.snapshot() once per step and passes it here.
        # This provider just returns the snapshot's observations.
        snapshot = self._sim.snapshot()  # type: ignore[union-attr]
        return snapshot.observations
