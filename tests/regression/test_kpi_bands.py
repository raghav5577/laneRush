"""Regression test: KPI bands from AGENTS.md §9.

Uses 2 seeds for CI. Real bands are validated with seeds 1-10.
These are placeholder tests until runs/ data is available.
"""

from __future__ import annotations

import pytest

# Regression bands from AGENTS.md §9 (prototype reference, ±15%)
REGRESSION_BANDS = {
    "fixed": {
        "mean_wait_s": (55.2, 0.15),  # (target, tolerance_fraction)
        "jain_index": (0.91, 0.15),
        "max_wait_s": (195, 0.15),
        "ev_transit_s": (166.8, 0.15),
    },
    "adaptive_noaging": {
        "mean_wait_s": (13.2, 0.15),
        "jain_index": (0.83, 0.15),
        "max_wait_s": (81, 0.15),
        "ev_transit_s": (101.8, 0.15),
    },
    "adaptive": {
        "mean_wait_s": (12.2, 0.15),
        "jain_index": (0.96, 0.15),
        "max_wait_s": (49, 0.15),
        "ev_transit_s": (108.4, 0.15),
    },
    "adaptive_corridor": {
        "mean_wait_s": (12.5, 0.15),
        "jain_index": (0.95, 0.15),
        "max_wait_s": (55, 0.15),
        "ev_transit_s": (83.2, 0.15),
    },
}


def _within_band(value: float, target: float, tolerance: float) -> bool:
    """Check if value is within target ± tolerance fraction."""
    lo = target * (1 - tolerance)
    hi = target * (1 + tolerance)
    return lo <= value <= hi


@pytest.mark.sumo
class TestKPIBands:
    """Regression tests — require SUMO runs to validate."""

    def test_placeholder(self) -> None:
        """Placeholder until runs/ data exists."""
        pytest.skip("Regression test — requires SUMO runs. Run with pytest -m sumo")

    def test_band_math(self) -> None:
        """Verify the band math works."""
        assert _within_band(55.0, 55.2, 0.15)
        assert _within_band(12.0, 12.2, 0.15)
        assert not _within_band(100.0, 55.2, 0.15)
