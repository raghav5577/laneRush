"""Plot generation for KPI analysis."""

from __future__ import annotations

from pathlib import Path


def plot_kpi_comparison(
    results: dict[str, list[float]],
    metric: str,
    out_path: Path,
    ylabel: str = "",
    title: str = "",
) -> None:
    """Box-plot comparing a KPI across modes. Saves to out_path."""
    try:
        import matplotlib.pyplot as plt  # noqa: PLC0415
    except ImportError:
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    modes = list(results.keys())
    data = [results[m] for m in modes]
    ax.boxplot(data, labels=modes)
    ax.set_ylabel(ylabel or metric)
    ax.set_title(title or f"{metric} by mode")
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_jain_vs_modes(
    jain_per_mode: dict[str, float],
    out_path: Path,
) -> None:
    """Bar chart of Jain index per mode."""
    try:
        import matplotlib.pyplot as plt  # noqa: PLC0415
    except ImportError:
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    modes = list(jain_per_mode.keys())
    values = [jain_per_mode[m] for m in modes]
    ax.bar(modes, values)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Jain index")
    ax.set_title("Fairness (Jain) by mode")
    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_ev_transit(
    ev_transit_per_mode: dict[str, list[float]],
    out_path: Path,
) -> None:
    """Box-plot of EV transit times per mode."""
    plot_kpi_comparison(
        ev_transit_per_mode,
        metric="ev_transit_s",
        out_path=out_path,
        ylabel="EV transit time (s)",
        title="EV transit time by mode",
    )
