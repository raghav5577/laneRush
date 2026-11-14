"""Simulation runner — orchestrates one complete simulation run."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _run_dir(cfg: Any, mode: str | None = None) -> Path:
    """Return a unique run directory path."""
    from lanerush.config import LaneRushConfig

    c: LaneRushConfig = cfg
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    m = mode or c.mode
    return Path(c.output.runs_dir) / f"{ts}_{m}_seed{c.sim.seed}"


def run_simulation(cfg: Any, port: int = 8813) -> Path:
    """Run a single simulation; return the run output directory."""
    from lanerush.config import LaneRushConfig
    from lanerush.sim.traci_client import TraciClient

    c: LaneRushConfig = cfg
    run_dir = _run_dir(c)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write config snapshot
    import yaml

    with open(run_dir / "config.yaml", "w") as f:
        yaml.dump(c.model_dump(), f, default_flow_style=False)

    client = TraciClient(port=port)
    try:
        client.connect(
            sumo_binary=c.sim.sumo_binary,
            net_file=c.sim.net_file,
            route_file=c.sim.route_file,
            step_length=c.sim.step_length,
            seed=c.sim.seed,
            gui=c.sim.gui,
        )
        _simulate(client, c, run_dir)
    except Exception:
        logger.exception("Simulation failed")
        raise
    finally:
        client.close()

    return run_dir


def _simulate(client: Any, cfg: Any, run_dir: Path) -> None:
    """Inner sim loop."""
    from lanerush.store.memory import MemoryStore
    from lanerush.store.run_logger import CsvRunLogger

    store = MemoryStore()
    _ = store  # placeholder for Phase 3/7 store integration
    log_path = run_dir / "decisions.csv"
    run_logger = CsvRunLogger(log_path)

    try:
        for _ in range(cfg.sim.max_steps):
            client.step()
            snapshot = client.snapshot()
            # TODO (Phase 3): plug in controller, perception, corridor
            _ = snapshot  # noqa: F841
    finally:
        run_logger.close()


def run_sweep(cfg: Any, modes: list[str], seeds: list[int], workers: int) -> None:
    """Parallel sweep over modes × seeds."""
    import concurrent.futures
    import itertools

    from lanerush.config import LaneRushConfig

    c: LaneRushConfig = cfg
    combos = list(itertools.product(modes, seeds))

    def _run_one(args: tuple[str, int], idx: int) -> str:
        mode, seed = args
        # Assign unique TraCI port per worker
        port = 8900 + idx
        updated = c.model_copy(
            update={
                "mode": mode,
                "sim": c.sim.model_copy(update={"seed": seed}),
            }
        )
        run_dir = run_simulation(updated, port=port)
        return str(run_dir)

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_run_one, combo, i): combo for i, combo in enumerate(combos)}
        for fut in concurrent.futures.as_completed(futures):
            combo = futures[fut]
            try:
                result = fut.result()
                logger.info("Done %s seed=%s → %s", combo[0], combo[1], result)
            except Exception:
                logger.exception("Failed %s seed=%s", combo[0], combo[1])


def scan_fixed_splits(seeds: list[int]) -> None:
    """Scan fixed green splits on tuning seeds; write configs/fixed_tuned.yaml."""
    import yaml

    from lanerush.config import LaneRushConfig

    base_cfg = LaneRushConfig.from_yaml(Path("configs/exp_main.yaml"))
    _ = base_cfg  # placeholder for parameter overrides
    best_split: tuple[int, int] = (42, 42)
    best_mean_wait = float("inf")

    for green_a in range(20, 61, 2):
        for seed in seeds:
            # Placeholder: actual scan requires SUMO
            pass

    logger.info("Best fixed split: %s/%s, mean_wait=%.1f", best_split[0], best_split[1], best_mean_wait)
    # Write placeholder config
    cfg_path = Path("configs/fixed_tuned.yaml")
    with open(cfg_path) as f:
        data = yaml.safe_load(f)
    data["mode"] = "fixed_tuned"
    with open(cfg_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    logger.info("Wrote %s", cfg_path)
