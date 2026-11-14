# LaneRush — AI-Driven Adaptive Traffic Signal Control with EV Green Corridor

A simulation-only system on **SUMO + TraCI (Python)** that adaptively controls traffic signals
and provides emergency vehicle (EV) green corridor pre-clearing.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Install
pip install -e ".[dev]"

# 3. Generate network & routes
bash scenarios/grid3x3/build_net.sh
python scenarios/grid3x3/make_routes.py

# 4. Run
lanerush run --config configs/exp_main.yaml

# 5. Test
pytest -m "not sumo" -v
```

## Architecture

```
src/lanerush/
  cli.py          — Typer CLI entry point
  config.py       — Pydantic v2 configuration
  models.py       — Frozen dataclasses & protocols (contracts)
  sim/            — SUMO/TraCI integration (only module touching TraCI)
  perception/     — Detection providers (ground truth / noisy / YOLO)
  control/        — Pure traffic signal logic (scoring, phase, corridor, arbiter)
  store/          — State storage (memory / Redis / Postgres) with graceful fallback
  evaluation/     — KPI computation, statistics, plots, reports
  dashboard/      — Streamlit real-time dashboard
```

### Key Invariants

- **`control/`** is strictly pure: no I/O, no TraCI, no Redis/DB imports
- Only **`sim/traci_client.py`** imports `traci`/`libsumo`
- Redis/Postgres failures log a warning and fall back to in-memory — **never crash the sim**
- All parameters come from validated Pydantic config — **zero magic constants**

## Modes

| Mode | Description |
|---|---|
| `fixed` | Fixed-timer baseline (42s/3s/42s/3s) |
| `fixed_tuned` | Best split found via `scan-fixed` on tuning seeds |
| `adaptive_noaging` | Adaptive scoring without aging weight |
| `adaptive` | Full adaptive with count + halting + aging |
| `adaptive_corridor` | Adaptive + EV green corridor pre-clearing |

## CLI Commands

```bash
lanerush run --config configs/exp_main.yaml           # Single run
lanerush sweep configs/exp_main.yaml --seeds 1-10     # Multi-seed sweep
lanerush scan-fixed --seeds 101-105                   # Find optimal fixed timing
lanerush analyze runs/ --out results/                  # Generate reports
```

## License

MIT
