"""Baseline controllers — fixed-timer and stubs for max-pressure / actuated.

NO forbidden imports.
"""

from __future__ import annotations

from lanerush.models import PhaseCommand, TlsInfo


def fixed_timer_command(
    tls_info: TlsInfo,
    current_phase: int,
    t_in: int,
    in_yellow: bool,
    green_duration: int = 42,
    yellow_duration: int = 3,
) -> PhaseCommand:
    """Fixed-timer controller: alternate green phases with fixed durations."""
    if in_yellow:
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="hold",
            target_phase=None,
            reason="fixed:yellow",
        )

    if current_phase in tls_info.green_phases:
        if t_in >= green_duration:
            return PhaseCommand(
                tls_id=tls_info.tls_id,
                action="switch",
                target_phase=tls_info.yellow_after[current_phase],
                reason="fixed:switch",
            )
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="hold",
            target_phase=None,
            reason="fixed:hold",
        )

    # Unexpected phase — hold
    return PhaseCommand(
        tls_id=tls_info.tls_id,
        action="hold",
        target_phase=None,
        reason="fixed:unknown_phase",
    )


def max_pressure_command(
    tls_info: TlsInfo,
    pressures: dict[int, float],
    current_phase: int,
    t_in: int,
    in_yellow: bool,
    min_green: int = 8,
) -> PhaseCommand:
    """Max-pressure baseline (Phase 10).

    pressure[phase] = Σ(incoming queue − outgoing queue) for served movements.
    """
    if in_yellow:
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="hold",
            target_phase=None,
            reason="maxpressure:yellow",
        )

    if t_in < min_green:
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="hold",
            target_phase=None,
            reason="maxpressure:min_green",
        )

    # Find highest-pressure green phase
    if not pressures:
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="hold",
            target_phase=None,
            reason="maxpressure:no_data",
        )

    best_phase = max(pressures, key=lambda p: pressures[p])
    if best_phase != current_phase:
        return PhaseCommand(
            tls_id=tls_info.tls_id,
            action="switch",
            target_phase=best_phase,
            reason="maxpressure:switch",
        )
    return PhaseCommand(
        tls_id=tls_info.tls_id,
        action="hold",
        target_phase=None,
        reason="maxpressure:hold",
    )
