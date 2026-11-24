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
    gui: bool = typer.Option(False, "--gui", help="Launch SUMO visual GUI."),
) -> None:
    """Run a single simulation with the given config."""
    from lanerush.config import LaneRushConfig

    cfg = LaneRushConfig.from_yaml(config)
    if seed is not None:
        cfg = cfg.model_copy(update={"sim": cfg.sim.model_copy(update={"seed": seed})})
    if gui:
        cfg = cfg.model_copy(update={"sim": cfg.sim.model_copy(update={"gui": True})})

    if dry_run:
        import json

        typer.echo("Config validated successfully:")
        typer.echo(json.dumps(cfg.model_dump(), indent=2, default=str))
        raise typer.Exit(0)

    # Lazy import to avoid traci at import time
    from lanerush.sim.runner import run_simulation

    typer.echo(f"Starting simulation: mode='{cfg.mode}', seed={cfg.sim.seed}, gui={cfg.sim.gui}...")
    run_dir = run_simulation(cfg)
    typer.echo(f"Simulation completed successfully! Outputs saved to: {run_dir}")


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


@app.command()
def ui(
    host: str = typer.Option("127.0.0.1", help="Host interface to bind."),
    port: int = typer.Option(8000, help="Port to serve the dashboard on."),
    reload: bool = typer.Option(True, help="Enable auto-reload on code change."),
) -> None:
    """Launch the LaneRush React Dashboard web server."""
    import uvicorn

    typer.echo(f"Starting LaneRush React Dashboard on http://{host}:{port} ...")
    uvicorn.run("lanerush.server.api:app", host=host, port=port, reload=reload)


@app.command()
def demo(
    config: Path = typer.Option(Path("configs/exp_main.yaml"), help="Config file."),
) -> None:
    """Launch full Evaluator Showcase Demo in SUMO-GUI with EV corridor pre-clearing."""
    from lanerush.config import LaneRushConfig
    from lanerush.sim.runner import run_simulation

    cfg = LaneRushConfig.from_yaml(config)
    cfg.mode = "adaptive_corridor"
    cfg.sim.gui = True

    typer.echo("\n" + "=" * 65)
    typer.echo("🎬 EVALUATOR DEMO: SUMO-GUI + Adaptive EV Corridor Wave")
    typer.echo("=" * 65)
    typer.echo("1. Launching SUMO-GUI window...")
    typer.echo("2. In another terminal, run: .\\lanerush.ps1 ui (open http://127.0.0.1:8000)")
    typer.echo("3. Place SUMO-GUI on the left and React Dashboard on the right!")
    typer.echo("4. Watch EV0 enter at t=40s and cruise through with zero stopping delay.\n")

    run_simulation(cfg)


if __name__ == "__main__":
    app()
