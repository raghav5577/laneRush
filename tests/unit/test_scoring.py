"""Tests for control/scoring.py — lane_score and phase_scores."""

from __future__ import annotations

import pytest

from lanerush.control.scoring import lane_score, phase_scores
from lanerush.models import LaneObservation, TlsInfo


def _obs(count: int = 0, halting: int = 0, max_wait: float = 0.0) -> LaneObservation:
    return LaneObservation(
        lane_id="test_0",
        count=count,
        halting=halting,
        max_wait=max_wait,
        emergency=False,
        source="test",
    )


class TestLaneScore:
    def test_zero_values(self) -> None:
        assert lane_score(_obs(), 1.0, 1.0, 0.5) == 0.0

    def test_count_only(self) -> None:
        assert lane_score(_obs(count=5), 1.0, 0.0, 0.0) == 5.0

    def test_halting_only(self) -> None:
        assert lane_score(_obs(halting=3), 0.0, 1.0, 0.0) == 3.0

    def test_aging_only(self) -> None:
        assert lane_score(_obs(max_wait=10.0), 0.0, 0.0, 0.5) == 5.0

    def test_combined(self) -> None:
        # w_count*count + w_halt*halting + w_age*max_wait
        # 1.0*5 + 1.0*3 + 0.5*10 = 5 + 3 + 5 = 13.0
        assert lane_score(_obs(count=5, halting=3, max_wait=10.0), 1.0, 1.0, 0.5) == 13.0

    def test_no_aging_mode(self) -> None:
        """adaptive_noaging → w_age = 0."""
        obs = _obs(count=5, halting=3, max_wait=100.0)
        assert lane_score(obs, 1.0, 1.0, 0.0) == 8.0


class TestPhaseScores:
    @pytest.fixture
    def tls(self) -> TlsInfo:
        return TlsInfo(
            tls_id="J0",
            green_phases=(0, 2),
            yellow_after={0: 1, 2: 3},
            lanes_of={
                0: ("J0_0", "J0_1"),
                2: ("J0_2", "J0_3"),
            },
        )

    def test_scores_computed(self, tls: TlsInfo) -> None:
        obs = {
            "J0_0": _obs(count=5, halting=2, max_wait=10.0),
            "J0_1": _obs(count=3, halting=1, max_wait=5.0),
            "J0_2": _obs(count=1, halting=0, max_wait=0.0),
            "J0_3": _obs(count=2, halting=1, max_wait=3.0),
        }
        scores = phase_scores(tls, obs, 1.0, 1.0, 0.5)
        # phase 0: (5+2+5) + (3+1+2.5) = 12 + 6.5 = 18.5
        # phase 2: (1+0+0) + (2+1+1.5) = 1 + 4.5 = 5.5
        assert scores[0] == pytest.approx(18.5)
        assert scores[2] == pytest.approx(5.5)

    def test_missing_lane_ignored(self, tls: TlsInfo) -> None:
        """Lanes not in observations are skipped (not crash)."""
        obs = {
            "J0_0": _obs(count=5),
            # J0_1, J0_2, J0_3 are missing
        }
        scores = phase_scores(tls, obs, 1.0, 1.0, 0.0)
        assert scores[0] == 5.0
        assert scores[2] == 0.0
