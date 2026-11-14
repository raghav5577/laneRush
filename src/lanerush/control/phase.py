"""Phase switching logic — NO forbidden imports."""

from __future__ import annotations

from typing import Literal


def decide(
    in_yellow: bool,
    t_in: int,
    cur_score: float,
    other_score: float,
    min_green: int = 8,
    max_green: int = 50,
) -> tuple[Literal["hold", "switch"], str]:
    """Decide whether to hold or switch the current green phase.

    Decision table (AGENTS.md §6):
    1. in_yellow              → hold  (yellow_wait)
    2. t_in >= max_green
       AND other_score > 0    → switch (maxgreen)
    3. t_in < min_green       → hold  (min_green)
    4. other > 1.2*cur + 1    → switch (hysteresis)   [strictly greater]
    5. else                   → hold  (stay)
    """
    if in_yellow:
        return "hold", "yellow_wait"
    if t_in >= max_green and other_score > 0:
        return "switch", "maxgreen"
    if t_in < min_green:
        return "hold", "min_green"
    if other_score > 1.2 * cur_score + 1:
        return "switch", "hysteresis"
    return "hold", "stay"
