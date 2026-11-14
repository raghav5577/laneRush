"""Tests for evaluation/kpis.py — Jain index and KPI computations."""

from __future__ import annotations

import pytest

from lanerush.evaluation.kpis import jain_index


class TestJainIndex:
    def test_equal_values(self) -> None:
        """All equal → Jain = 1.0."""
        assert jain_index([10, 10, 10]) == pytest.approx(1.0)

    def test_unequal_values(self) -> None:
        """[30, 0, 0] → Jain = 1/3."""
        assert jain_index([30, 0, 0]) == pytest.approx(1 / 3)

    def test_empty_list(self) -> None:
        """Empty list → 1.0 by convention."""
        assert jain_index([]) == pytest.approx(1.0)

    def test_all_zero(self) -> None:
        """All zeros → 1.0 by convention."""
        assert jain_index([0, 0, 0]) == pytest.approx(1.0)

    def test_single_value(self) -> None:
        """Single value → 1.0."""
        assert jain_index([42.0]) == pytest.approx(1.0)

    def test_two_equal(self) -> None:
        """Two equal values → 1.0."""
        assert jain_index([5.0, 5.0]) == pytest.approx(1.0)

    def test_two_very_different(self) -> None:
        """[100, 1] → close to 0.5."""
        j = jain_index([100.0, 1.0])
        assert 0.4 < j < 0.6

    def test_slightly_unequal(self) -> None:
        """Near-equal values → Jain close to 1.0."""
        j = jain_index([10.0, 10.1, 9.9, 10.0, 10.0])
        assert j > 0.999
