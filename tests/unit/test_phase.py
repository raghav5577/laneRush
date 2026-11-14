"""Tests for control/phase.py — decide() truth table."""

from __future__ import annotations

from lanerush.control.phase import decide


class TestDecide:
    """Decision table from AGENTS.md §6."""

    def test_yellow_always_hold(self) -> None:
        """In yellow → hold (yellow_wait), regardless of other factors."""
        assert decide(True, 10, 100.0, 50.0, 8, 50) == ("hold", "yellow_wait")
        assert decide(True, 0, 0.0, 1000.0, 8, 50) == ("hold", "yellow_wait")
        assert decide(True, 100, 0.0, 100.0, 8, 50) == ("hold", "yellow_wait")

    def test_maxgreen_switch(self) -> None:
        """t_in >= max_green AND other > 0 → switch (maxgreen)."""
        assert decide(False, 50, 100.0, 50.0, 8, 50) == ("switch", "maxgreen")
        assert decide(False, 51, 0.0, 0.1, 8, 50) == ("switch", "maxgreen")

    def test_maxgreen_no_switch_zero_other(self) -> None:
        """t_in >= max_green but other == 0 → NOT maxgreen switch."""
        assert decide(False, 50, 100.0, 0.0, 8, 50) != ("switch", "maxgreen")

    def test_min_green_hold(self) -> None:
        """t_in < min_green → hold (min_green), even if other is huge."""
        assert decide(False, 5, 10.0, 100.0, 8, 50) == ("hold", "min_green")
        assert decide(False, 7, 0.0, 1000.0, 8, 50) == ("hold", "min_green")

    def test_min_green_boundary(self) -> None:
        """t_in == min_green → NOT min_green hold (allows hysteresis)."""
        result = decide(False, 8, 10.0, 100.0, 8, 50)
        assert result[1] != "min_green"

    def test_hysteresis_switch(self) -> None:
        """other > 1.2*cur + 1 → switch (hysteresis)."""
        # cur=10, threshold=1.2*10+1=13.  other=15 > 13 → switch
        assert decide(False, 20, 10.0, 15.0, 8, 50) == ("switch", "hysteresis")
        # cur=0, threshold=1.  other=2 > 1 → switch
        assert decide(False, 20, 0.0, 2.0, 8, 50) == ("switch", "hysteresis")

    def test_hysteresis_boundary_no_switch(self) -> None:
        """other == 1.2*cur + 1 → NOT hysteresis (strictly greater required)."""
        # cur=10, threshold=1.2*10+1=13.  other=13 == 13 → hold(stay)
        assert decide(False, 20, 10.0, 13.0, 8, 50) == ("hold", "stay")

    def test_hysteresis_just_above(self) -> None:
        """other = 1.2*cur + 1 + epsilon → switch."""
        # cur=10, threshold=13. other=13.01 > 13 → switch
        assert decide(False, 20, 10.0, 13.01, 8, 50) == ("switch", "hysteresis")

    def test_stay_hold(self) -> None:
        """All other conditions fail → hold (stay)."""
        assert decide(False, 20, 10.0, 5.0, 8, 50) == ("hold", "stay")
        assert decide(False, 20, 10.0, 10.0, 8, 50) == ("hold", "stay")

    def test_priority_order(self) -> None:
        """Yellow check has highest priority over maxgreen."""
        # Even with t_in >= max_green and hysteresis met, yellow wins
        assert decide(True, 50, 10.0, 100.0, 8, 50) == ("hold", "yellow_wait")
