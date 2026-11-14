"""Corridor arbiter — combines adaptive command with corridor requests.

NO forbidden imports.
"""

from __future__ import annotations

from lanerush.models import CorridorRequest, PhaseCommand, TlsInfo


def arbitrate(
    adaptive_cmd: PhaseCommand,
    corridor_requests: list[CorridorRequest],
    tls_info: TlsInfo,
    current_phase: int,
    t_in: int,
    in_yellow: bool,
) -> PhaseCommand:
    """Arbitrate between the adaptive phase command and any corridor requests.

    Invariants:
    - Never switch in yellow
    - Never return a phase outside tls_info.green_phases
    - If two EVs request the same junction, earliest ETA wins
    - Request with different phase and t_in >= 2 → switch (corridor)
    - Request with same phase → hold (corridor_hold)
    - No request → pass adaptive command through
    """
    # Invariant: never switch in yellow
    if in_yellow:
        return PhaseCommand(
            tls_id=adaptive_cmd.tls_id,
            action="hold",
            target_phase=None,
            reason="arbiter:yellow",
        )

    # Find requests for this junction
    tls_requests = [r for r in corridor_requests if r.tls_id == tls_info.tls_id]

    if tls_requests:
        # Earliest ETA wins
        req = min(tls_requests, key=lambda r: r.eta_s)

        # Validate phase is in green_phases
        if req.phase not in tls_info.green_phases:
            # Safety: invalid phase → pass through adaptive command
            return adaptive_cmd

        if req.phase != current_phase and t_in >= 2:
            return PhaseCommand(
                tls_id=adaptive_cmd.tls_id,
                action="switch",
                target_phase=req.phase,
                reason="corridor",
            )
        else:
            return PhaseCommand(
                tls_id=adaptive_cmd.tls_id,
                action="hold",
                target_phase=None,
                reason="corridor_hold",
            )

    return adaptive_cmd
