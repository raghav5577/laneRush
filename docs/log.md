# LaneRush — Comprehensive Development & Project Log

> **Project Overview:** AI-Driven Adaptive Traffic Signal Control with Emergency Vehicle (EV) Green Corridor Pre-clearing on SUMO + TraCI.
> Built following strict layering invariants, Pydantic v2 configuration, pure algorithmic cores, and multi-backend storage.

---

## 📌 Architectural Principles & Invariants

1. **Strict Layering:**
   - `src/lanerush/control/` is pure logic. It NEVER imports `traci`, `libsumo`, `redis`, `psycopg`, `sqlalchemy`, `ultralytics`, `sim/`, `perception/`, or `store/`. Only sees `models.py` frozen dataclasses. Verified by automated AST import boundary test (`test_control_imports.py`).
2. **Single SUMO Boundary:**
   - Only `src/lanerush/sim/traci_client.py` imports `traci`/`libsumo`. A pure `FakeSim` double allows running simulation tests and logic verification without requiring an active SUMO daemon.
3. **Safety & Traffic Invariants:**
   - Every green-to-green phase change must transition through yellow.
   - Only phases present in the discovered SUMO traffic light program can be commanded.
   - Corridor overrides ignore min/max green constraints strictly on junctions with an active EV pre-clear request.
   - In yellow states, arbitration and phase switching always command `hold`.
4. **Graceful Degradation:**
   - Redis or Postgres connection issues or runtime exceptions fall back seamlessly to `MemoryStore` / local CSV logging without halting the simulation loop.
5. **Zero Magic Constants:**
   - All weights, timing constraints, lookahead parameters, and thresholds originate from validated Pydantic v2 configuration models.

---

## 🗂 Project Structure & Module Map

```
laneRush/
├── pyproject.toml                     # Hatchling build, dependencies, ruff, pytest settings
├── .gitignore                         # Exclusions for runs, venv, generated artifacts
├── .env.example                       # DB & Redis connection templates
├── .pre-commit-config.yaml            # Ruff hook definitions
├── docker-compose.yml                 # Redis 7 & Postgres 16 local containers
├── README.md                          # Quick start and command reference
├── AGENTS.md                          # Master specification and contracts
├── .github/workflows/
│   └── ci.yml                         # Automated CI pipeline
├── configs/
│   ├── exp_main.yaml                  # Primary experiment configuration (adaptive_corridor)
│   └── fixed_tuned.yaml               # Baseline configuration for fixed timings
├── docs/
│   └── log.md                         # Detailed project status and changelog (this file)
├── ml/
│   ├── prepare_data.py                # Data deduplication & 70/15/15 dataset splitter
│   ├── train_cls.py                   # YOLOv8n-cls classification training runner
│   └── evaluate_cls.py                # Metrics evaluation on test split (generates metrics.json)
├── scenarios/grid3x3/
│   ├── build_net.sh                   # Netgenerate script for 3x3 synthetic grid
│   ├── make_routes.py                 # Stochastic route & 4-EV generator (~695 veh/seed)
│   └── grid3x3.rou.xml                # Generated deterministic route file
├── src/lanerush/
│   ├── __init__.py                    # Package marker & version
│   ├── models.py                      # Frozen dataclasses (LaneObservation, EVState, TlsInfo, etc.)
│   ├── config.py                      # Pydantic v2 schemas with comprehensive validation
│   ├── cli.py                         # Typer CLI (run, sweep, scan-fixed, analyze)
│   ├── sim/
│   │   ├── traci_client.py            # TraciClient (sole TraCI consumer) + FakeSim test double
│   │   ├── runner.py                  # Simulation loop, parallel sweep, fixed split scanner
│   │   └── scenario.py                # Scenario generator helpers & SUMO home locator
│   ├── perception/
│   │   ├── base.py                    # DetectionProvider Protocol exports
│   │   ├── ground_truth.py            # Direct ground truth provider from snapshot
│   │   ├── noisy.py                   # Binomial thinning, Poisson phantoms, temporal EV confirmation
│   │   └── yolo_provider.py           # Demo provider for vision-based vehicle counting
│   ├── control/
│   │   ├── tls_info.py                # Dynamic TLS phase & link discovery
│   │   ├── scoring.py                 # Lane and phase scoring (w_count, w_halt, w_age)
│   │   ├── phase.py                   # Phase switching logic (min/max green, hysteresis)
│   │   ├── corridor.py                # EV green corridor routing & ETA planning
│   │   ├── arbiter.py                 # Arbitration between adaptive commands & corridor requests
│   │   └── baselines.py               # Fixed-timer and max-pressure baseline controllers
│   ├── store/
│   │   ├── base.py                    # StateStore & RunLogger Protocols
│   │   ├── memory.py                  # Thread-safe in-memory state store
│   │   ├── redis_store.py             # Redis store with automatic MemoryStore fallback
│   │   ├── pg.py                      # PostgreSQL store with automatic MemoryStore fallback
│   │   ├── run_logger.py              # CSV logger (decisions.csv and lane_samples.csv)
│   │   └── schema.sql                 # SQL schema definition for PostgreSQL
│   ├── evaluation/
│   │   ├── kpis.py                    # Jain fairness index, mean wait, EV transit calculation
│   │   ├── stats.py                   # 95% CI (t-dist), Wilcoxon signed-rank, paired t-tests
│   │   ├── plots.py                   # Boxplots, Jain bar charts, EV transit visualizations
│   │   └── report.py                  # Markdown and tabular report generator
│   └── dashboard/
│       ├── __init__.py                # Dashboard module
│       └── app.py                     # Streamlit dashboard (live junction grid & CSV replay mode)
└── tests/
    ├── unit/
    │   ├── test_arbiter.py            # 9 unit tests for corridor arbitration invariants
    │   ├── test_config.py             # 8 unit tests for Pydantic schema and edge-case errors
    │   ├── test_control_imports.py    # 1 AST-level import boundary test for control/
    │   ├── test_corridor.py           # 6 unit tests for corridor planning and ETA calculations
    │   ├── test_kpis.py               # 8 unit tests for Jain fairness index mathematical correctness
    │   ├── test_phase.py              # 10 unit tests for phase switching decision truth tables
    │   ├── test_scoring.py            # 8 unit tests for lane and phase scoring math
    │   ├── test_store.py              # 10 unit tests for memory store and CSV logging
    │   └── test_tls_info.py           # 7 unit tests for TLS discovery and validation
    ├── integration/
    │   └── test_runner_smoke.py       # FakeSim integration tests & SUMO integration stub
    └── regression/
        └── test_kpi_bands.py          # Regression band verification for ±15% targets
```

---

## 🚀 Execution & Phase Log

### Phase 0 — Skeleton, Contracts & Boundary Tests (`tag: phase-0`)
- **Status:** Complete & Verified
- **Deliverables:**
  - Implemented `models.py` contracts: `LaneObservation`, `EVState`, `TlsInfo`, `CorridorRequest`, `PhaseCommand`, Protocols (`DetectionProvider`, `StateStore`, `RunLogger`, `NetView`), and `is_emergency()` helper.
  - Implemented `config.py` with Pydantic v2 models (`LaneRushConfig`, `SimConfig`, `TlsConfig`, `ScoringConfig`, `CorridorConfig`, `PerceptionConfig`, `StoreConfig`, `OutputConfig`).
  - Added AST-based static verification test `tests/unit/test_control_imports.py` asserting no illicit imports in `control/`.
  - Configured `pyproject.toml` with `hatchling`, Ruff formatting and lint rules, Pytest settings with `pythonpath = ["src"]`.
  - Verified `lanerush run --dry-run` successfully loads and validates YAML configuration.
  - **Test Results:** 67/67 unit tests passing, `ruff check .` passing with 0 warnings.

### Phase 1 — Scenario & Route Synthesis (`tag: phase-1`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `scenarios/grid3x3/build_net.sh`: Shell script using `netgenerate` to generate a 3×3 signalized grid network with 250m link lengths and attached approaches.
  - `scenarios/grid3x3/make_routes.py`: Deterministic route synthesis generating stochastic vehicle flows. Flow probabilities tuned to deliver **~695 ordinary vehicles per seed** (±5%), satisfying acceptance criteria.
  - Injected 4 Emergency Vehicles at fixed timestamps (t=120, 300, 480, 660) along multi-junction paths across horizontal and vertical corridors.

### Phase 2 — Sim Doubles & KPI Suite (`tag: phase-2`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `sim/traci_client.py`: Implemented `FakeSim` providing in-memory step simulation, state snapshots, and mock TLS programs without requiring local TraCI.
  - `evaluation/kpis.py`: Implemented `jain_index` with full edge-case handling (empty/zero arrays returning 1.0), and `compute_kpis` parsing `tripinfo.xml`.
  - Unit tests verified mathematical identity: `jain_index([10, 10, 10]) == 1.0` and `jain_index([30, 0, 0]) == 1/3`.

### Phase 3 & 4 — Adaptive Controller & Scoring Logic (`tag: phase-3`, `tag: phase-4`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `control/scoring.py`: Implemented `lane_score` ($W_{\text{count}}\cdot\text{count} + W_{\text{halt}}\cdot\text{halting} + W_{\text{age}}\cdot\text{max\_wait}$) and `phase_scores` aggregations across active green movements.
  - `control/phase.py`: Implemented decision truth table honoring yellow wait, max green, min green, and the strictly greater hysteresis boundary (`other > 1.2 * cur + 1`).
  - `control/tls_info.py`: Implemented `discover` parsing raw SUMO phase configurations, enforcing 2-green topology and cycle-following yellow logic.

### Phase 5 — EV Green Corridor & Arbiter (`tag: phase-5`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `control/corridor.py`: Implemented corridor `plan` inspecting oncoming non-internal edges, computing ETAs based on speed limits, queue backlog, and lookahead parameters.
  - `control/arbiter.py`: Safety arbiter resolving conflicts between adaptive commands and corridor requests. Guarantees:
    - Never switches during yellow states.
    - Earliest ETA takes precedence on shared junctions.
    - Commands hold when approaching active phase, commands switch only when target phase is valid and $t_{\text{in}} \ge 2\text{s}$.

### Phase 6 & 7 — Persistence, Statistics & Graceful Storage (`tag: phase-6`, `tag: phase-7`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `store/memory.py`: Thread-safe in-memory store with TTL auto-expiration.
  - `store/redis_store.py`: Redis client with automated warning log and seamless fallback to `MemoryStore`.
  - `store/pg.py`: PostgreSQL relational store with schema DDL and graceful in-memory fallback.
  - `store/run_logger.py`: High-throughput CSV logging to `decisions.csv` and `lane_samples.csv`.
  - `evaluation/stats.py`: Statistical testing routines (95% CI via Student's t-distribution, Wilcoxon signed-rank, paired t-tests).

### Phase 8 & 9 — ML Perception Pipeline & Dashboard (`tag: phase-8`, `tag: phase-9`)
- **Status:** Complete & Verified
- **Deliverables:**
  - `ml/prepare_data.py`: Dataset deduplication and 70/15/15 train/val/test splitting with metadata export.
  - `ml/train_cls.py`: YOLOv8n-cls training orchestrator.
  - `ml/evaluate_cls.py`: Model evaluation script computing top-1/top-5 accuracy and confusion matrix, tagged with git commit hash.
  - `perception/noisy.py`: Synthetic noisy detector emulating binomial detection loss, Poisson false alarms, and temporal k-of-n confirmation buffers.
  - `dashboard/app.py`: Real-time Streamlit dashboard supporting live process control, 3×3 junction visual grid, EV corridor alerts, lane density chart, and an offline replay mode reading directly from `decisions.csv`.

---

## 🧪 Current Verification Status

| Gate | Target | Status |
|---|---|---|
| **Unit Test Suite** | 67 tests covering arbiter, config, corridor, imports, kpis, phase, scoring, store, tls_info | ✅ **67 / 67 Passed** (1.12s) |
| **Control Layer Import Boundary** | AST check for zero forbidden imports (`traci`, `redis`, `store`, etc.) | ✅ **Passed** |
| **Linter / Formatter** | `ruff check .` with PEP 8 and modern Python 3.12 rules | ✅ **0 Errors / Clean** |
| **Config Dry Run** | `lanerush run --dry-run` schema validation | ✅ **Validated successfully** |
| **Route Generation** | Expected ordinary vehicles per seed | ✅ **~695 (Target: ≈695 ±5%)** |
| **Replay & Offline Dashboard** | Functions without Redis/Postgres | ✅ **Verified** |

---

## 🎯 Next Steps & Roadmap

1. **Local SUMO Simulation Runs (`lanerush run`):**
   - Execute single-run simulation against local `sumo` or `sumo-gui` binary using `configs/exp_main.yaml`.
   - Record `tripinfo.xml`, verify average wait times against reference bands (Target: ~12.5s for `adaptive_corridor`).
2. **Fixed Baseline Tuning Sweep (`lanerush scan-fixed`):**
   - Execute fixed-timer sweep across tuning seeds (101–105) to find the optimal split and populate `configs/fixed_tuned.yaml`.
3. **Multi-Seed Mode Sweeps (`lanerush sweep`):**
   - Run parallel sweeps across all 5 modes (`fixed`, `fixed_tuned`, `adaptive_noaging`, `adaptive`, `adaptive_corridor`) on evaluation seeds 1–10.
   - Run `lanerush analyze runs/ --out results/` to generate comparative box plots, Jain fairness indexes, and final goal tables.
4. **PostgreSQL & Redis Container Deployment:**
   - Launch containers using `docker compose up -d` for end-to-end telemetry streaming into the live dashboard.
