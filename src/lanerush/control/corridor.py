"""EV green corridor planner — NO forbidden imports."""

from __future__ import annotations

from lanerush.models import CorridorRequest, EVState, NetView


def plan(
    ev_states: list[EVState],
    net: NetView,
    lookahead_junctions: int = 3,
    eta_threshold_base: float = 12.0,
) -> list[CorridorRequest]:
    """Generate CorridorRequests for EVs approaching signalised junctions.

    Rules (AGENTS.md §6):
    - Only normal edges (not starting with ':')
    - Look at ≤ lookahead_junctions next signalised junctions on route
    - eta = dist / min(speed_limit, ev_vmax or v_free)
    - Request if eta <= eta_threshold_base + 2*halted_on_approach_lane
      (halted count not available here without observations; use base threshold)
    - Phase: the green serving (incoming lane → next edge)
    - Use the lane that actually connects, not lane _0
    - If two EVs want the same junction, earliest ETA wins (resolved in arbiter)
    - Requests vanish once EV has passed
    """
    requests: list[CorridorRequest] = []

    for ev in ev_states:
        if ev.edge.startswith(":"):
            continue  # inside junction

        # Get speed limit for ETA calculation
        speed_limit = net.get_edge_speed_limit(ev.edge)
        ev_speed = ev.speed if ev.speed > 0.1 else speed_limit
        effective_speed = min(speed_limit, ev_speed)

        # Find the next TLS junctions on this EV's route
        upcoming_junctions = net.get_next_tls_junctions(
            ev.edge, ev.route, ev.route_index, lookahead_junctions
        )

        for tls_id, dist_m in upcoming_junctions:
            if effective_speed <= 0:
                continue
            eta_s = dist_m / effective_speed

            if eta_s > eta_threshold_base:
                continue  # too far away

            # Find the green phase that serves this EV's approach
            # Determine which edge comes after the junction on EV's route
            route_idx = ev.route_index
            if route_idx + 1 >= len(ev.route):
                continue
            next_edge = ev.route[route_idx + 1]

            # Find connecting lanes from current edge to next edge
            connecting_lanes = net.get_lanes_connecting(ev.edge, next_edge)
            if not connecting_lanes:
                continue

            # Phase is determined by which phase serves the connecting lane.
            # For now, encode phase as 0 (resolved with TlsInfo in Phase 5).
            # The arbiter will verify phase validity.
            requests.append(
                CorridorRequest(
                    tls_id=tls_id,
                    phase=0,  # Placeholder; Phase 5 will wire in real phase discovery
                    eta_s=eta_s,
                    vehicle_id=ev.vehicle_id,
                )
            )

    return requests
