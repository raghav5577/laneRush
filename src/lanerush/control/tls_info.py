"""TLS structure discovery — NO forbidden imports."""

from __future__ import annotations

from lanerush.models import TlsInfo


def discover(tls_id: str, phases: list[tuple[str, float]]) -> TlsInfo:
    """Build a TlsInfo from raw SUMO phase list [(state_string, duration), ...].

    Rules (from AGENTS.md §6):
    - green: state has G or g, and NO y or Y
    - yellow: state has y or Y
    - v1 requires exactly 2 green phases; raises ValueError otherwise
    - each green must be cyclically followed by a yellow; raises ValueError otherwise
    - lanes_of[phase] uses the actual state string indices, not an assumed lane_0
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

    # lanes_of: tuple of lane indices that go green in this phase
    # Lane IDs in SUMO are built from the TLS link index (position in state string)
    # We use "{tls_id}_{link_index}" as placeholder; the real mapping comes from
    # traci.trafficlight.getControlledLinks at runtime (Phase 3).
    lanes_of: dict[int, tuple[str, ...]] = {}
    for gp in green_indices:
        state = phases[gp][0]
        lanes_of[gp] = tuple(
            f"{tls_id}_{i}" for i, c in enumerate(state) if c in "Gg"
        )

    return TlsInfo(
        tls_id=tls_id,
        green_phases=tuple(green_indices),
        yellow_after=yellow_after,
        lanes_of=lanes_of,
    )
