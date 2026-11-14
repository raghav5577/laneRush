"""Tests for control/tls_info.py — discover() TLS structure discovery."""

from __future__ import annotations

import pytest

from lanerush.control.tls_info import discover


class TestDiscover:
    def test_standard_4phase(self) -> None:
        """Standard 4-phase program: GGrr/yyrr/rrGG/rryy → 2 greens, 2 yellows."""
        phases = [("GGrr", 42.0), ("yyrr", 3.0), ("rrGG", 42.0), ("rryy", 3.0)]
        info = discover("J0", phases)
        assert info.tls_id == "J0"
        assert len(info.green_phases) == 2
        assert info.green_phases == (0, 2)
        assert info.yellow_after == {0: 1, 2: 3}

    def test_green_followed_by_yellow(self) -> None:
        """Each green must have a following yellow."""
        phases = [("GGrr", 42.0), ("yyrr", 3.0), ("rrGG", 42.0), ("rryy", 3.0)]
        info = discover("J0", phases)
        for gp in info.green_phases:
            assert gp in info.yellow_after, f"Green phase {gp} has no yellow"

    def test_not_exactly_2_greens_raises(self) -> None:
        """v1 requires exactly 2 green phases; 3 greens should raise."""
        phases = [("GGrr", 42.0), ("yyrr", 3.0), ("rrGG", 42.0), ("rryy", 3.0), ("GrGr", 20.0)]
        with pytest.raises(ValueError, match="expected exactly 2"):
            discover("J0", phases)

    def test_one_green_raises(self) -> None:
        """Only 1 green should raise."""
        phases = [("GGrr", 42.0), ("yyrr", 3.0), ("rrrr", 42.0)]
        with pytest.raises(ValueError, match="expected exactly 2"):
            discover("J0", phases)

    def test_no_yellow_after_green_raises(self) -> None:
        """Green with no following yellow should raise."""
        # Two greens in a row, no yellow
        phases = [("GGrr", 42.0), ("rrGG", 42.0)]
        with pytest.raises(ValueError):
            discover("J0", phases)

    def test_lanes_of_maps_green_indices(self) -> None:
        """lanes_of should map state string indices where G/g appears."""
        phases = [("GGrr", 42.0), ("yyrr", 3.0), ("rrGG", 42.0), ("rryy", 3.0)]
        info = discover("J0", phases)
        assert info.lanes_of[0] == ("J0_0", "J0_1")
        assert info.lanes_of[2] == ("J0_2", "J0_3")

    def test_lowercase_g_counted_as_green(self) -> None:
        """Lowercase 'g' should also count as green."""
        phases = [("gGrr", 42.0), ("yyrr", 3.0), ("rrgG", 42.0), ("rryy", 3.0)]
        info = discover("J0", phases)
        assert len(info.green_phases) == 2
