"""EV green corridor planner — NO forbidden imports."""

from __future__ import annotations

from lanerush.models import CorridorRequest, EVState, LaneObservation, NetView, TlsInfo


def plan(
    ev_states: list[EVState],
    net: NetView,
    lookahead_junctions: int = 3,
    eta_threshold_base: float = 12.0,
    tls_infos: dict[str, TlsInfo] | None = None,
    observations: dict[str, LaneObservation] | None = None,
) -> list[CorridorRequest]:
    """Generate CorridorRequests for EVs approaching signalised junctions.

    Rules (AGENTS.md §6):
    - Only normal edges (not starting with ':')
    - Look at ≤ lookahead_junctions next signalised junctions on route
    - eta = dist / min(speed_limit, ev_vmax or v_free)
    - Request if eta <= eta_threshold_base + 2*halted_on_approach_lane
    - Phase: the green serving (incoming lane → next edge)
    - Use the lane that actually connects, not lane _0
    - If two EVs want the same junction, earliest ETA wins (resolved in arbiter)
    - Requests vanish once EV has passed
    """
    requests: list[CorridorRequest] = []

    for ev in ev_states:
        if ev.edge.startswith(":"):
            continue  # inside junction

        # Queue term on current approach lane (AGENTS.md §6)
        halted_count = 0
        if observations and ev.lane_id in observations:
            halted_count = observations[ev.lane_id].halting
        eta_threshold = eta_threshold_base + 2.0 * halted_count

        # Get speed limit for ETA calculation
        speed_limit = net.get_edge_speed_limit(ev.edge)
        ev_speed = ev.speed if ev.speed > 0.1 else speed_limit
        effective_speed = min(speed_limit, ev_speed)

        # Find the next TLS junctions on this EV's route
        upcoming_junctions = net.get_next_tls_junctions(
            ev.edge, ev.route, ev.route_index, lookahead_junctions
        )

        for j_idx, (tls_id, dist_m) in enumerate(upcoming_junctions):
            if effective_speed <= 0:
                continue

            # Adjust distance by EV's actual progress along the approach edge
            actual_dist = max(0.0, dist_m - ev.lane_pos)
            eta_s = actual_dist / effective_speed

            if eta_s > eta_threshold:
                continue  # too far away

            # Find the approach edge and target outgoing edge for this junction
            edge_idx = ev.route_index + j_idx
            if edge_idx + 1 >= len(ev.route):
                continue
            curr_approach = ev.route[edge_idx]
            next_edge = ev.route[edge_idx + 1]

            # Find connecting lanes from approach edge to next edge
            connecting_lanes = net.get_lanes_connecting(curr_approach, next_edge)
            if not connecting_lanes:
                continue

            # Determine the green phase that serves the connecting lane
            phase = 0
            if tls_infos and tls_id in tls_infos:
                tinfo = tls_infos[tls_id]
                for p, lanes in tinfo.lanes_of.items():
                    if any(lane in lanes for lane in connecting_lanes):
                        phase = p
                        break

            requests.append(
                CorridorRequest(
                    tls_id=tls_id,
                    phase=phase,
                    eta_s=eta_s,
                    vehicle_id=ev.vehicle_id,
                )
            )

    return requests
