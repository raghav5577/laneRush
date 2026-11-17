"""Simulation runner — orchestrates one complete simulation run."""

from __future__ import annotations

import csv
import json
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lanerush.models import PhaseCommand, TlsInfo

logger = logging.getLogger(__name__)


def _get_git_hash() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
        return res.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _get_sumo_version() -> str:
    try:
        import traci  # noqa: PLC0415

        version = traci.getVersion()
        return f"{version[0]}.{version[1]}"
    except Exception:
        return "1.28.0"


def _run_dir(cfg: Any, mode: str | None = None) -> Path:
    """Return a unique run directory path."""
    from lanerush.config import LaneRushConfig

    c: LaneRushConfig = cfg
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    m = mode or c.mode
    return Path(c.output.runs_dir) / f"{ts}_{m}_seed{c.sim.seed}"


def run_simulation(cfg: Any, port: int = 8813) -> Path:
    """Run a single simulation; return the run output directory."""
    import yaml

    from lanerush.config import LaneRushConfig
    from lanerush.sim.traci_client import TraciClient

    c: LaneRushConfig = cfg
    run_dir = _run_dir(c)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write config snapshot
    with open(run_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(c.model_dump(), f, default_flow_style=False)

    tripinfo_path = run_dir / "tripinfo.xml"
    client = TraciClient(port=port)
    try:
        client.connect(
            sumo_binary=c.sim.sumo_binary,
            net_file=c.sim.net_file,
            route_file=c.sim.route_file,
            step_length=c.sim.step_length,
            seed=c.sim.seed,
            gui=c.sim.gui,
            extra_args=["--tripinfo-output", str(tripinfo_path)],
        )
        _simulate(client, c, run_dir)
    except Exception:
        logger.exception("Simulation failed")
        raise
    finally:
        client.close()

    # Write meta.json
    meta = {
        "git_hash": _get_git_hash(),
        "sumo_version": _get_sumo_version(),
        "seed": c.sim.seed,
        "mode": c.mode,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "max_steps": c.sim.max_steps,
    }
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return run_dir


def _simulate(client: Any, cfg: Any, run_dir: Path) -> None:
    """Inner sim loop."""
    from lanerush.control.arbiter import arbitrate
    from lanerush.control.corridor import plan
    from lanerush.control.phase import decide
    from lanerush.control.scoring import phase_scores
    from lanerush.control.tls_info import discover
    from lanerush.perception.noisy import NoisyEmulator
    from lanerush.sim.scenario import SumolibNetView
    from lanerush.store.run_logger import CsvRunLogger

    # 1. Setup logging
    log_path = run_dir / "decisions.csv"
    run_logger = CsvRunLogger(log_path)

    trips_csv_path = run_dir / "trips.csv"
    trips_file = open(trips_csv_path, "w", newline="", encoding="utf-8")
    trips_writer = csv.writer(trips_file)
    trips_writer.writerow(["vehicle_id", "vtype", "first_edge", "depart"])

    # 2. Discover TLS structures
    tls_ids = client.get_tls_ids()
    tls_infos: dict[str, TlsInfo] = {}
    tls_tracker: dict[str, dict[str, Any]] = {}

    if cfg.mode == "fixed_tuned":
        for tid in tls_ids:
            client.set_tls_phase_durations(tid, {0: float(cfg.tls.min_green), 2: float(cfg.tls.max_green)})

    for tid in tls_ids:
        prog = client.get_tls_program(tid)
        links = client.get_tls_controlled_links(tid)
        tinfo = discover(tid, prog, controlled_links=links)
        tls_infos[tid] = tinfo
        cur_phase = client.get_tls_phase(tid)
        in_yellow = cur_phase not in tinfo.green_phases
        tls_tracker[tid] = {
            "cur_phase": cur_phase,
            "t_in": 0,
            "in_yellow": in_yellow,
            "target_green": tinfo.green_phases[0],
            "last_reason": "",
        }

    # 3. Setup NetView for corridor if enabled
    net_view: SumolibNetView | None = None
    if cfg.corridor.enabled or cfg.mode == "adaptive_corridor":
        net_file_path = Path(cfg.sim.net_file)
        if net_file_path.exists():
            net_view = SumolibNetView(net_file_path)

    # 4. Setup Perception Emulator if noisy
    noisy_emulator: NoisyEmulator | None = None
    if cfg.perception.provider == "noisy":
        noisy_emulator = NoisyEmulator(
            recall=cfg.perception.noisy.recall,
            false_alarm=cfg.perception.noisy.false_alarm,
            ev_recall=cfg.perception.noisy.ev_recall,
            ev_false_alarm=cfg.perception.noisy.ev_false_alarm,
            confirmation_k=cfg.perception.noisy.confirmation_k,
            confirmation_n=cfg.perception.noisy.confirmation_n,
            seed=cfg.sim.seed,
        )

    # Weights
    w_count = cfg.scoring.w_count
    w_halt = cfg.scoring.w_halt
    w_age = 0.0 if cfg.mode == "adaptive_noaging" else cfg.scoring.w_age
    is_adaptive = cfg.mode in ("adaptive", "adaptive_noaging", "adaptive_corridor")

    departed_seen: set[str] = set()

    try:
        for _ in range(cfg.sim.max_steps):
            client.step()
            t = client.current_time

            # Record departed vehicles
            for vid in client.get_departed_vehicle_ids():
                if vid not in departed_seen:
                    departed_seen.add(vid)
                    vtype = client.get_vehicle_type(vid)
                    route = client.get_vehicle_route(vid)
                    first_edge = route[0] if route else ""
                    trips_writer.writerow([vid, vtype, first_edge, t])

            # Stop condition: all routes completed and network empty
            if t > 720 and len(client.get_vehicle_ids()) == 0:
                logger.info("Simulation completed early at t=%d (network clear)", t)
                break

            if not is_adaptive:
                # In fixed baseline modes, let SUMO execute its program natively
                continue

            # Read simulation snapshot
            snapshot = client.snapshot()
            observations = snapshot.observations

            if noisy_emulator:
                observations = noisy_emulator.observe(t, observations)

            corridor_requests = []
            if cfg.corridor.enabled and cfg.mode == "adaptive_corridor" and net_view:
                corridor_requests = plan(
                    ev_states=snapshot.ev_states,
                    net=net_view,
                    lookahead_junctions=cfg.corridor.lookahead_junctions,
                    eta_threshold_base=cfg.corridor.eta_threshold_base,
                    tls_infos=tls_infos,
                    observations=observations,
                )

            # Process each TLS
            for tid, tinfo in tls_infos.items():
                st = tls_tracker[tid]
                cur_phase = st["cur_phase"]
                t_in = st["t_in"]
                in_yellow = st["in_yellow"]

                # Handle yellow duration expiration
                if in_yellow:
                    if t_in >= cfg.tls.yellow_wait:
                        target_g = st["target_green"]
                        client.set_phase(tid, target_g)
                        client.set_phase_duration(tid, 5.0)
                        st["cur_phase"] = target_g
                        st["t_in"] = 0
                        st["in_yellow"] = False
                        cur_phase = target_g
                        t_in = 0
                        in_yellow = False
                    else:
                        client.set_phase_duration(tid, 5.0)
                        st["t_in"] += 1
                        continue

                # Compute scores in green phase
                scores = phase_scores(tinfo, observations, w_count, w_halt, w_age)
                cur_score = scores.get(cur_phase, 0.0)
                other_phases = [p for p in tinfo.green_phases if p != cur_phase]
                other_phase = other_phases[0] if other_phases else cur_phase
                other_score = scores.get(other_phase, 0.0)

                action, reason = decide(
                    in_yellow=in_yellow,
                    t_in=t_in,
                    cur_score=cur_score,
                    other_score=other_score,
                    min_green=cfg.tls.min_green,
                    max_green=cfg.tls.max_green,
                )

                cmd = PhaseCommand(
                    tls_id=tid,
                    action=action,
                    target_phase=other_phase if action == "switch" else None,
                    reason=reason,
                )

                if cfg.corridor.enabled and cfg.mode == "adaptive_corridor":
                    cmd = arbitrate(
                        adaptive_cmd=cmd,
                        corridor_requests=corridor_requests,
                        tls_info=tinfo,
                        current_phase=cur_phase,
                        t_in=t_in,
                        in_yellow=in_yellow,
                    )

                # Log decisions on state/reason change or interval
                if cmd.reason != st["last_reason"] or (t % cfg.output.log_decisions_every_n == 0):
                    score_map = {f"phase_{p}": s for p, s in scores.items()}
                    run_logger.decision(t, cmd, score_map)
                    st["last_reason"] = cmd.reason

                # Execute command
                if cmd.action == "switch":
                    yellow_phase = tinfo.yellow_after[cur_phase]
                    client.set_phase(tid, yellow_phase)
                    client.set_phase_duration(tid, cfg.tls.yellow_wait)
                    st["cur_phase"] = yellow_phase
                    st["t_in"] = 0
                    st["in_yellow"] = True
                    st["target_green"] = cmd.target_phase if cmd.target_phase is not None else other_phase
                else:
                    client.set_phase_duration(tid, 5.0)
                    st["t_in"] += 1

    finally:
        trips_file.close()
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
        port = 8900 + idx
        if mode == "fixed_tuned":
            try:
                ft_cfg = LaneRushConfig.from_yaml(Path("configs/fixed_tuned.yaml"))
                tls_cfg = ft_cfg.tls
            except Exception:
                tls_cfg = c.tls.model_copy(update={"min_green": 30, "max_green": 54})
            updated = c.model_copy(
                update={
                    "mode": mode,
                    "tls": tls_cfg,
                    "sim": c.sim.model_copy(update={"seed": seed}),
                }
            )
        else:
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
    from lanerush.evaluation.kpis import compute_kpis, parse_tripinfo

    base_cfg = LaneRushConfig.from_yaml(Path("configs/exp_main.yaml"))
    candidate_splits = [(30, 54), (36, 48), (42, 42), (48, 36), (54, 30)]
    best_split: tuple[int, int] = (42, 42)
    best_mean_wait = float("inf")

    logger.info("Starting fixed split scan across seeds %s...", seeds)

    for ew_green, ns_green in candidate_splits:
        split_waits: list[float] = []
        for i, seed in enumerate(seeds):
            run_cfg = base_cfg.model_copy(
                update={
                    "mode": "fixed_tuned",
                    "tls": base_cfg.tls.model_copy(update={"min_green": ew_green, "max_green": ns_green}),
                    "sim": base_cfg.sim.model_copy(update={"seed": seed}),
                }
            )
            port = 9100 + i
            run_dir = run_simulation(run_cfg, port=port)
            tripinfo_path = run_dir / "tripinfo.xml"
            if tripinfo_path.exists():
                trips = parse_tripinfo(tripinfo_path)
                kpis = compute_kpis(trips)
                split_waits.append(kpis["mean_wait_s"])

        if split_waits:
            avg_wait = sum(split_waits) / len(split_waits)
            logger.info("Split %ds EW / %ds NS → mean wait: %.2fs", ew_green, ns_green, avg_wait)
            if avg_wait < best_mean_wait:
                best_mean_wait = avg_wait
                best_split = (ew_green, ns_green)

    logger.info("Best fixed split: %ds EW / %ds NS, mean_wait=%.2fs", best_split[0], best_split[1], best_mean_wait)

    cfg_path = Path("configs/fixed_tuned.yaml")
    with open(cfg_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["mode"] = "fixed_tuned"
    data["tls"] = {
        "min_green": best_split[0],
        "max_green": best_split[1],
        "yellow_wait": 3,
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)
    logger.info("Wrote tuned configuration to %s", cfg_path)
