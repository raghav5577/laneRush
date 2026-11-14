"""CSV RunLogger — writes decisions.csv and lane_samples.csv."""

from __future__ import annotations

import csv
from pathlib import Path

from lanerush.models import LaneObservation, PhaseCommand


class CsvRunLogger:
    """RunLogger implementation that writes two CSV files per run.

    - decisions.csv : (t, tls_id, action, target_phase, reason, scores_json)
    - lane_samples.csv : (t, lane_id, count, halting, max_wait, emergency, source)
    """

    def __init__(self, decisions_path: Path) -> None:
        self._decisions_path = decisions_path
        self._samples_path = decisions_path.parent / "lane_samples.csv"
        self._decisions_file = open(decisions_path, "w", newline="", encoding="utf-8")  # noqa: SIM115
        self._samples_file = open(self._samples_path, "w", newline="", encoding="utf-8")  # noqa: SIM115

        self._decisions_writer = csv.writer(self._decisions_file)
        self._samples_writer = csv.writer(self._samples_file)

        self._decisions_writer.writerow(["t", "tls_id", "action", "target_phase", "reason", "scores_json"])
        self._samples_writer.writerow(["t", "lane_id", "count", "halting", "max_wait", "emergency", "source"])

        self._closed = False

    def decision(self, t: int, cmd: PhaseCommand, scores: dict[str, float]) -> None:
        if self._closed:
            return
        import json

        self._decisions_writer.writerow([
            t,
            cmd.tls_id,
            cmd.action,
            cmd.target_phase if cmd.target_phase is not None else "",
            cmd.reason,
            json.dumps(scores),
        ])

    def lane_sample(self, t: int, obs: dict[str, LaneObservation]) -> None:
        if self._closed:
            return
        for lane_id, o in obs.items():
            self._samples_writer.writerow([
                t,
                lane_id,
                o.count,
                o.halting,
                o.max_wait,
                o.emergency,
                o.source,
            ])

    def close(self) -> None:
        if not self._closed:
            self._decisions_file.close()
            self._samples_file.close()
            self._closed = True
