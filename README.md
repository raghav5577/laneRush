# LaneRush — AI-Driven Adaptive Traffic Signal Control with EV Green Corridor

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![SUMO](https://img.shields.io/badge/SUMO-1.28.0-green.svg)](https://eclipse.dev/sumo/)
[![Tests](https://img.shields.io/badge/tests-67%20passed-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, simulation-based traffic management platform built on **SUMO + TraCI (Python)**. LaneRush adaptively scores and switches traffic signals based on real-time vehicle counts, halted queues, and waiting-time aging, while dynamically pre-clearing **Emergency Vehicle (EV) Green Corridors** across multi-junction routes without creating gridlock.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and enter directory
git clone https://github.com/username/laneRush.git
cd laneRush

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows PowerShell / CMD
# source .venv/bin/activate  # Linux / macOS

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

> **Note for Windows Users:** Dedicated wrapper scripts (`.\lanerush.ps1` and `lanerush.bat`) are provided in the project root so you can execute `lanerush` commands directly from PowerShell or Command Prompt without PATH or `PYTHONPATH` manual configuration.

---

### 2. Generate Network & Scenarios

Generate the 3×3 signalized grid network and calibrated routes:

```bash
# Generate 3x3 grid network (9 TLS junctions, 4 phases each)
bash scenarios/grid3x3/build_net.sh

# Generate calibrated stochastic flows and emergency vehicle routes
python scenarios/grid3x3/make_routes.py
```

---

### 3. Running the Simulation

#### Interactive GUI Mode (Visual Simulation)
Run the adaptive corridor simulation with visual playback in SUMO-GUI:

```powershell
# Windows
.\lanerush.ps1 run --gui

# Linux / macOS
lanerush run --gui
```

> **Visual Showcase in GUI:**
> - Smooth playback is pre-configured with `--delay 350` (350 ms per step).
> - Vehicles operate at realistic urban velocities (25 km/h for passenger cars, 34 km/h for emergency vehicles).
> - **4-Car Queue & EV Release Demonstration:**
>   - Zoom in on **Junction A1** (middle-left intersection).
>   - Between $t=0\text{s}$ and $t=40\text{s}$, North-South traffic crosses on green.
>   - 4 passenger cars approach on `left1A1` and come to a complete stop at the red light, forming a queue.
>   - At $t=40\text{s}$, the bright red Emergency Vehicle (**EV0**) arrives behind them.
>   - At $t=42\text{s}$, Junction A1 automatically overrides the signal, stops cross-traffic with yellow clearance, turns green, and releases the 4 stuck cars ahead of EV0 so the emergency vehicle cruises through without stopping!

#### Headless Execution (Fast Batch Mode)
```bash
lanerush run --config configs/exp_main.yaml
```

---

## 🛠 Command Line Interface (CLI)

LaneRush provides a suite of CLI tools powered by Typer:

| Command | Usage | Description |
|---|---|---|
| `run` | `lanerush run [--gui] [--dry-run]` | Run a single simulation run under the specified configuration. |
| `scan-fixed` | `lanerush scan-fixed --seeds 101-105` | Sweep fixed-timer phase splits (30s–54s) on tuning seeds to identify the optimal baseline. |
| `sweep` | `lanerush sweep configs/exp_main.yaml --modes all --seeds 1-10 --workers 4` | Run parallel evaluations across all control modes and test seeds. |
| `analyze` | `lanerush analyze runs/ --out results/` | Compute KPIs, paired Wilcoxon/t-tests, 95% CIs, Jain fairness indexes, and generate reports. |
| `dashboard` | `lanerush dashboard` | Launch the interactive Streamlit monitoring and replay dashboard. |

---

## 📊 System Architecture & Invariants

```
src/lanerush/
├── cli.py            # Typer CLI entrypoint
├── config.py         # Pydantic v2 configuration schema
├── models.py         # Frozen dataclasses & protocols (Core contracts)
├── sim/
│   ├── traci_client.py  # ONLY file that imports traci/libsumo
│   ├── runner.py        # Orchestration loop & state snapshotting
│   └── scenario.py      # Network topology & sumolib abstraction
├── control/          # PURE logic — ZERO I/O (no traci, redis, or db imports)
│   ├── scoring.py       # Lane & phase score computation
│   ├── phase.py         # Min/max green & hysteresis switching logic
│   ├── corridor.py      # EV corridor lookahead & ETA planning
│   ├── arbiter.py       # Safety arbiter (yellow lock, corridor override)
│   └── tls_info.py      # TLS signal program discovery
├── perception/       # Detection seam (GroundTruth, NoisyEmulator, YOLO)
├── store/            # In-memory, Redis, and PostgreSQL state persistence
└── evaluation/       # KPI calculation, statistical tests, and report generator
```

### Safety & Structural Invariants (AGENTS.md §2)
1. **Strict Layering:** `control/` never imports `traci`, `redis`, `psycopg`, or `sim/`. It operates purely on frozen dataclasses from `models.py`.
2. **Single SUMO Boundary:** Only `sim/traci_client.py` imports `traci`. All testing utilizes dataclass mocks or `FakeSim`.
3. **Safety Transitions:** Every green-to-green switch passes through yellow clearance (default: 3 seconds). No yellow state may be interrupted.
4. **Graceful Degradation:** Redis or database disconnections log a warning and fall back seamlessly to in-memory state and CSV logging without halting the simulation.
5. **Zero Magic Constants:** All scoring weights, thresholds, and lookahead parameters derive from validated Pydantic v2 schemas.

---

## 🚦 Control Modes

| Mode | Description |
|---|---|
| `fixed` | Standard fixed-timer baseline (42s East-West / 42s North-South). |
| `fixed_tuned` | Optimal fixed-timer baseline (30s EW / 54s NS) discovered via `scan-fixed`. |
| `adaptive_noaging` | Adaptive control using vehicle count and halted queues ($W_{\text{age}} = 0$). |
| `adaptive` | Full adaptive control ($W_{\text{count}} \cdot \text{count} + W_{\text{halt}} \cdot \text{halt} + W_{\text{age}} \cdot \text{wait}$). |
| `adaptive_corridor` | Full adaptive control combined with multi-junction EV Green Corridor pre-clearing. |

---

## 📈 Reference Results & Benchmarks

Empirical performance comparison (averaged across evaluation seeds):

| Metric | Fixed Baseline (42/42) | Fixed Tuned (30/54) | Adaptive | Adaptive + Corridor |
|---|---|---|---|---|
| **Mean Waiting Time (s)** | 55.2 s | 43.6 s | **8.1 s** | **8.5 s** |
| **Emergency Vehicle Transit (s)** | 166.8 s | 158.4 s | 108.4 s | **76.0 s (-54%)** |
| **Emergency Vehicle Delay (s)** | ~45.0 s | ~38.0 s | ~18.0 s | **0.0 s (Zero Stop)** |
| **Jain's Fairness Index** | 0.91 | 0.92 | **0.96** | **0.95** |
| **Longest Waiting Time (s)** | 195.0 s | 162.0 s | **49.0 s** | **52.0 s** |

---

## 🤖 Machine Learning EV Perception (Phase 8)

- **Model:** Fine-tuned YOLOv8n classifier trained on 1,066 emergency vehicle and urban vehicle images.
- **Model Weights:** Saved at `ml/runs/ev_detector/weights/best.pt` (excluded from git via `.gitignore`).
- **Empirical Test Metrics (`ml/results/metrics.json`):**
  - **EV Recall:** 78.33%
  - **EV Precision:** 82.53%
  - **mAP@50:** 81.25%
  - **False Alarm Rate:** 17.47%
- **Simulator Integration:** Empirical metrics are directly coupled into `NoisyEmulator` with $k$-of-$n$ temporal confirmation to validate system resilience under realistic sensor noise.

---

## 🧪 Testing & Verification

Run the full unit test suite (no SUMO binary required):

```bash
# Fast gate (67 unit tests in ~1.3s)
pytest tests/unit -v -m "not sumo"

# Linter and type checks
ruff check .
```

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
