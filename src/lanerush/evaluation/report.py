"""Report generator — reads runs/ directory, produces goal table + report.md."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Regression bands (AGENTS.md §9) — used as targets in report
TARGETS = {
    "mean_wait_s": {
        "fixed": 55.2,
        "adaptive_noaging": 13.2,
        "adaptive": 12.2,
        "adaptive_corridor": 12.5,
    },
    "jain_index": {
        "fixed": 0.91,
        "adaptive_noaging": 0.83,
        "adaptive": 0.96,
        "adaptive_corridor": 0.95,
    },
    "max_wait_s": {
        "fixed": 195,
        "adaptive_noaging": 81,
        "adaptive": 49,
        "adaptive_corridor": 55,
    },
    "ev_transit_s": {
        "fixed": 166.8,
        "adaptive_noaging": 101.8,
        "adaptive": 108.4,
        "adaptive_corridor": 83.2,
    },
}


def generate_report(runs_dir: Path, out_dir: Path) -> None:
    """Scan runs_dir, compute per-mode KPI stats, write report.md."""
    from lanerush.evaluation.kpis import compute_kpis, parse_tripinfo
    from lanerush.evaluation.stats import (
        confidence_interval_t,
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect per-mode results
    mode_results: dict[str, list[dict]] = {}
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        tripinfo = run_dir / "tripinfo.xml"
        config_yaml = run_dir / "config.yaml"
        if not tripinfo.exists():
            continue

        try:
            import yaml  # noqa: PLC0415

            with open(config_yaml) as f:
                cfg = yaml.safe_load(f)
            mode = cfg.get("mode", "unknown")
            trips = parse_tripinfo(tripinfo)
            if not trips:
                continue
            kpis = compute_kpis(trips)
            mode_results.setdefault(mode, []).append(kpis)
        except Exception:
            logger.exception("Failed to process %s", run_dir)

    if not mode_results:
        logger.warning("No completed runs found in %s", runs_dir)
        (out_dir / "report.md").write_text("No completed runs found.\n")
        return

    # Build report
    lines = ["# LaneRush KPI Report\n", "## Summary Table\n"]
    lines.append("| Mode | Mean Wait (s) | Jain | Max Wait (s) | EV Transit (s) | n |")
    lines.append("|------|--------------|------|-------------|---------------|---|")

    from lanerush.evaluation.plots import plot_ev_transit, plot_jain_vs_modes, plot_kpi_comparison

    waits_dict: dict[str, list[float]] = {}
    jains_dict: dict[str, float] = {}
    ev_dict: dict[str, list[float]] = {}

    for mode, kpi_list in sorted(mode_results.items()):
        mean_waits = [k["mean_wait_s"] for k in kpi_list]
        jains = [k["jain_index"] for k in kpi_list]
        max_waits = [k["max_wait_s"] for k in kpi_list]
        ev_transits = [k["ev_transit_s"] for k in kpi_list if k["ev_transit_s"] is not None]

        waits_dict[mode] = mean_waits
        if jains:
            jains_dict[mode] = sum(jains) / len(jains)
        if ev_transits:
            ev_dict[mode] = ev_transits

        def fmt(vals: list) -> str:
            if not vals:
                return "—"
            lo, hi = confidence_interval_t(vals)
            m = sum(vals) / len(vals)
            return f"{m:.1f} [{lo:.1f}, {hi:.1f}]"

        lines.append(
            f"| {mode} | {fmt(mean_waits)} | {fmt(jains)} | {fmt(max_waits)} | {fmt(ev_transits)} | {len(kpi_list)} |"
        )

    # Generate comparison plots
    plot_kpi_comparison(waits_dict, "Mean Wait (s)", out_dir / "mean_wait_comparison.png", ylabel="Mean Wait (s)")
    if jains_dict:
        plot_jain_vs_modes(jains_dict, out_dir / "jain_fairness.png")
    if ev_dict:
        plot_ev_transit(ev_dict, out_dir / "ev_transit_times.png")

    report_path = out_dir / "report.md"
    report_path.write_text("\n".join(lines) + "\n")
    logger.info("Report written to %s", report_path)
