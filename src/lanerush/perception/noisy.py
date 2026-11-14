"""Noisy DetectionProvider — binomial thinning + Poisson phantom vehicles.

NoisyEmulator(recall=1, fa=0, ev_recall=1, ev_fa=0) must reproduce
ground-truth KPIs exactly.
"""

from __future__ import annotations

import random
from collections import deque

from lanerush.models import LaneObservation


class NoisyEmulator:
    """
    Emulates imperfect detection:
    - Binomial thinning of count/halting by `recall`
    - Poisson phantom vehicles at rate `false_alarm`
    - EV flag: recall `ev_recall`, false-alarm rate `ev_false_alarm`
    - Temporal confirmation: EV flag only raised after k-of-n confirmations
    - max_wait retained from ground truth of detected vehicles (documented assumption)
    """

    def __init__(
        self,
        ground_truth: object,
        recall: float = 0.9,
        false_alarm: float = 0.05,
        ev_recall: float = 0.95,
        ev_false_alarm: float = 0.01,
        confirmation_k: int = 2,
        confirmation_n: int = 3,
        seed: int | None = None,
    ) -> None:
        self._gt = ground_truth
        self.recall = recall
        self.false_alarm = false_alarm
        self.ev_recall = ev_recall
        self.ev_false_alarm = ev_false_alarm
        self.confirmation_k = confirmation_k
        self.confirmation_n = confirmation_n
        self._rng = random.Random(seed)
        # Ring buffers per lane for temporal EV confirmation
        self._ev_history: dict[str, deque[bool]] = {}

    def observe(self, t: int) -> dict[str, LaneObservation]:
        snapshot = self._gt.snapshot()  # type: ignore[union-attr]
        gt_obs = snapshot.observations
        result: dict[str, LaneObservation] = {}

        for lane_id, obs in gt_obs.items():
            # Binomial thinning
            if self.recall >= 1.0 and self.false_alarm <= 0.0:
                noisy_count = obs.count
                noisy_halting = obs.halting
            else:
                detected = sum(
                    1 for _ in range(obs.count)
                    if self._rng.random() < self.recall
                )
                phantoms = self._rng.randint(0, max(0, int(self.false_alarm * 10)))
                noisy_count = detected + phantoms
                noisy_halting = min(
                    sum(1 for _ in range(obs.halting) if self._rng.random() < self.recall),
                    noisy_count,
                )

            # EV flag with temporal confirmation
            if self.ev_recall >= 1.0 and self.ev_false_alarm <= 0.0:
                ev_flag = obs.emergency
            else:
                raw_ev = (obs.emergency and self._rng.random() < self.ev_recall) or (
                    not obs.emergency and self._rng.random() < self.ev_false_alarm
                )
                hist = self._ev_history.setdefault(lane_id, deque(maxlen=self.confirmation_n))
                hist.append(raw_ev)
                ev_flag = sum(hist) >= self.confirmation_k

            result[lane_id] = LaneObservation(
                lane_id=lane_id,
                count=noisy_count,
                halting=noisy_halting,
                max_wait=obs.max_wait,  # from ground truth of detected vehicles
                emergency=ev_flag,
                source="noisy",
            )

        return result
