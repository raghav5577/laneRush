"""LaneRush CLI — entry point for all commands."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="LaneRush adaptive traffic signal control system.")


def _parse_seed_range(seeds_str: str) -> list[int]:
    """Parse '1-10' or '101-105' or '1,2,3' into a list of ints."""
    seeds: list[int] = []
    for part in seeds_str.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            seeds.extend(range(int(lo), int(hi) + 1))
        else:
            seeds.append(int(part))
    return seeds


@app.command()
def run(
    config: Path = typer.Option(Path("configs/exp_main.yaml"), help="Config YAML path."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate config and exit."),
    seed: int | None = typer.Option(None, help="Override seed from config."),
) -> None:
    """Run a single simulation with the given config."""
    from lanerush.config import LaneRushConfig

    cfg = LaneRushConfig.from_yaml(config)
    if seed is not None:
        cfg = cfg.model_copy(update={"sim": cfg.sim.model_copy(update={"seed": seed})})

    if dry_run:
        import json

        typer.echo("Config validated successfully:")
        typer.echo(json.dumps(cfg.model_dump(), indent=2, default=str))
        raise typer.Exit(0)

    # Lazy import to avoid traci at import time
    from lanerush.sim.runner import run_simulation

    run_simulation(cfg)


@app.command()
def sweep(
    config: Path = typer.Argument(..., help="Base config YAML path."),
    modes: str = typer.Option("all", help="Comma-separated modes or 'all'."),
    seeds: str = typer.Option("1-10", help="Seed range e.g. '1-10'."),
    workers: int = typer.Option(4, help="Parallel workers."),
) -> None:
    """Sweep modes × seeds, writing results to runs/."""
    from lanerush.config import _VALID_MODES, LaneRushConfig

    cfg = LaneRushConfig.from_yaml(config)
    seed_list = _parse_seed_range(seeds)

    if modes == "all":
        mode_list = list(_VALID_MODES)
    else:
        mode_list = [m.strip() for m in modes.split(",")]

    typer.echo(f"Sweeping {len(mode_list)} modes × {len(seed_list)} seeds = {len(mode_list)*len(seed_list)} runs, workers={workers}")

    from lanerush.sim.runner import run_sweep

    run_sweep(cfg, mode_list, seed_list, workers)


@app.command(name="scan-fixed")
def scan_fixed(
    seeds: str = typer.Option("101-105", help="Tuning seed range."),
) -> None:
    """Scan fixed-timer green splits on tuning seeds; write configs/fixed_tuned.yaml."""
    seed_list = _parse_seed_range(seeds)
    typer.echo(f"Scanning fixed splits on seeds {seed_list}…")

    from lanerush.sim.runner import scan_fixed_splits

    scan_fixed_splits(seed_list)


@app.command()
def analyze(
    runs_dir: Path = typer.Argument(..., help="Directory containing run output folders."),
    out: Path = typer.Option(Path("results/"), help="Output directory for analysis."),
) -> None:
    """Analyse run outputs and generate KPI tables + figures."""
    out.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Analysing runs in {runs_dir} → {out}")

    from lanerush.evaluation.report import generate_report

    generate_report(runs_dir, out)


if __name__ == "__main__":
    app()
