"""KPI computation from tripinfo.xml and CSV logs."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Fairness
# ---------------------------------------------------------------------------


def jain_index(values: list[float]) -> float:
    """Jain's fairness index: J = (Σm_i)² / (n·Σm_i²).

    Returns 1.0 for empty or all-zero lists (by convention).
    """
    n = len(values)
    if n == 0 or all(v == 0 for v in values):
        return 1.0
    s = sum(values)
    s2 = sum(v * v for v in values)
    return (s * s) / (n * s2) if s2 > 0 else 1.0


# ---------------------------------------------------------------------------
# Tripinfo parsing
# ---------------------------------------------------------------------------


def parse_tripinfo(tripinfo_xml: Path) -> list[dict]:
    """Parse SUMO tripinfo.xml into a list of vehicle dicts."""
    tree = ET.parse(tripinfo_xml)
    root = tree.getroot()
    trips = []
    for elem in root.findall("tripinfo"):
        trips.append(
            {
                "id": elem.get("id", ""),
                "vtype": elem.get("vtype", ""),
                "depart": float(elem.get("depart", 0)),
                "arrival": float(elem.get("arrival", -1)),
                "duration": float(elem.get("duration", 0)),
                "waitingTime": float(elem.get("waitingTime", 0)),
                "timeLoss": float(elem.get("timeLoss", 0)),
                "routeLength": float(elem.get("routeLength", 0)),
            }
        )
    return trips


def compute_kpis(trips: list[dict], trips_csv_path: Path | None = None) -> dict:
    """Compute all KPIs from a list of parsed tripinfo dicts.

    per-approach mean waits require trips_csv (which records first_edge at depart).
    """
    ordinary = [t for t in trips if t["vtype"] != "emergency"]
    ev_trips = [t for t in trips if t["vtype"] == "emergency"]

    if not ordinary:
        mean_wait = 0.0
        p95_wait = 0.0
        max_wait_val = 0.0
        time_loss = 0.0
        completion = 0.0
        jain = 1.0
        worst_approach = 0.0
    else:
        waits = [t["waitingTime"] for t in ordinary]
        losses = [t["timeLoss"] for t in ordinary]
        arrived = [t for t in ordinary if t["arrival"] >= 0]

        mean_wait = sum(waits) / len(waits)
        waits_sorted = sorted(waits)
        p95_idx = max(0, int(0.95 * len(waits_sorted)) - 1)
        p95_wait = waits_sorted[p95_idx]
        max_wait_val = max(waits)
        time_loss = sum(losses) / len(losses)
        completion = len(arrived) / len(ordinary)

        # Per-approach means (placeholder until trips.csv is available)
        approach_waits: list[float] = waits  # simplified
        jain = jain_index(approach_waits)
        worst_approach = max(approach_waits) if approach_waits else 0.0

    ev_transit: float | None = None
    if ev_trips:
        arrived_evs = [t for t in ev_trips if t["arrival"] >= 0]
        if arrived_evs:
            ev_transit = sum(t["duration"] for t in arrived_evs) / len(arrived_evs)

    return {
        "mean_wait_s": mean_wait,
        "p95_wait_s": p95_wait,
        "max_wait_s": max_wait_val,
        "time_loss_s": time_loss,
        "jain_index": jain,
        "worst_approach_mean_wait_s": worst_approach,
        "completion_rate": completion,
        "ev_transit_s": ev_transit,
        "n_ordinary": len(ordinary),
        "n_ev": len(ev_trips),
    }
