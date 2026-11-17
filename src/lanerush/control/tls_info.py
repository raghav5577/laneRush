"""TLS structure discovery — NO forbidden imports."""

from __future__ import annotations

from typing import Any

from lanerush.models import TlsInfo


def discover(
    tls_id: str,
    phases: list[tuple[str, float]],
    controlled_links: list[Any] | None = None,
) -> TlsInfo:
    """Build a TlsInfo from raw SUMO phase list [(state_string, duration), ...].

    Rules (from AGENTS.md §6):
    - green: state has G or g, and NO y or Y
    - yellow: state has y or Y
    - v1 requires exactly 2 green phases; raises ValueError otherwise
    - each green must be cyclically followed by a yellow; raises ValueError otherwise
    - lanes_of[phase] uses the actual incoming lane IDs when controlled_links is provided
    """
    n = len(phases)
    green_indices: list[int] = []
    yellow_indices: list[int] = []

    for i, (state, _) in enumerate(phases):
        sl = state.lower()
        if "y" in sl:
            yellow_indices.append(i)
        elif "g" in sl:
            green_indices.append(i)

    if len(green_indices) != 2:
        raise ValueError(
            f"TLS {tls_id}: expected exactly 2 green phases, got {len(green_indices)}: {green_indices}"
        )

    # Map each green → its nearest following yellow (cyclically)
    yellow_after: dict[int, int] = {}
    for gp in green_indices:
        found = False
        for offset in range(1, n):
            nxt = (gp + offset) % n
            if nxt in yellow_indices:
                yellow_after[gp] = nxt
                found = True
                break
        if not found:
            raise ValueError(
                f"TLS {tls_id}: green phase {gp} has no following yellow phase in program"
            )

    # lanes_of: tuple of incoming lane IDs that get green in this phase
    lanes_of: dict[int, tuple[str, ...]] = {}
    for gp in green_indices:
        state = phases[gp][0]
        if controlled_links:
            phase_lanes: list[str] = []
            for i, c in enumerate(state):
                if c in "Gg" and i < len(controlled_links) and controlled_links[i]:
                    lane_id = str(controlled_links[i][0][0])
                    if lane_id not in phase_lanes:
                        phase_lanes.append(lane_id)
            lanes_of[gp] = tuple(phase_lanes)
        else:
            lanes_of[gp] = tuple(
                f"{tls_id}_{i}" for i, c in enumerate(state) if c in "Gg"
            )

    return TlsInfo(
        tls_id=tls_id,
        green_phases=tuple(green_indices),
        yellow_after=yellow_after,
        lanes_of=lanes_of,
    )
