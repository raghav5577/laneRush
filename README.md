# LaneRush — AI-Driven Adaptive Traffic Signal Control with EV Green Corridor

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![SUMO](https://img.shields.io/badge/SUMO-1.28.0-green.svg)](https://eclipse.dev/sumo/)
[![Tests](https://img.shields.io/badge/tests-67%20passed-brightgreen.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Frontend](https://img.shields.io/badge/frontend-React%2018%20JSX%20%2B%20Vite-61dafb.svg)](http://127.0.0.1:8000)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, simulation-based traffic management platform built on **SUMO + TraCI (Python)** and modern **React 18 JSX**. LaneRush adaptively scores and switches traffic signals based on real-time vehicle counts, halted queues, and waiting-time aging, while dynamically pre-clearing **Multi-Axis Emergency Vehicle (EV) Green Corridors** without causing cross-traffic gridlock.

---

## 📚 Essential Documentation

| Document | Description |
|---|---|
| **[Vision & Simulation Bridge](docs/REAL_WORLD_VISION_AND_SUMO_EXPLANATION.md)** | **How real-world camera ML (YOLOv8) connects to 2D SUMO microscopic simulation** via the Digital Twin Perception Seam. |
| **[Evaluator Presentation Script](docs/EVALUATOR_PRESENTATION_SCRIPT.md)** | Step-by-step cue sheet for demonstrating LaneRush to evaluators and professors with 1-click timestamps. |
| **[Architecture & Technical Reference](docs/ARCHITECTURE_AND_EXPLANATION.md)** | Comprehensive breakdown of TraCI internals, mathematical scoring formulas, and safety invariants. |
| **[Development Log](docs/log.md)** | Detailed changelog, architectural milestones, and solved engineering challenges. |

---

## 🚀 Quick Start & Evaluator Demonstration

### 1. Launch the React AI Dashboard

```powershell
# Windows
.\lanerush.ps1 ui

# Linux / macOS
lanerush ui
```
*Open `http://127.0.0.1:8000` in Google Chrome or Microsoft Edge.*

### 2. Launch the High-Fidelity SUMO-GUI Simulator

You have two convenient ways to launch the microscopic simulator:
- **Option A (1-Click from Web UI):** Click the green **`[ Launch SUMO-GUI ]`** button directly in the navbar at `http://127.0.0.1:8000`.
- **Option B (From Terminal):**
  ```powershell
  python scratch\test_sim_timing.py
  # Or:
  .\lanerush.ps1 demo
  ```

> **The Winning Presentation Setup:** Place **SUMO-GUI** on the left half of your screen and the **React Dashboard** on the right half.

---

## 🌟 Key Features & Demonstrations

### 1. Multi-Axis Emergency Vehicle Green Waves (280s Timeline)
- **First Emergency Vehicle (`EV0` — East-West on Row 1 at $t=40\text{s}$):**
  - **4 Cars Stuck at Red:** 4 passenger cars queue up at Junction A1 at the red light.
  - **Queue Pre-Flush:** The signal commands Green early, flushing all 4 cars out of the lane.
  - **Immediate Cross-Traffic Halt:** North-South traffic safely stops (Yellow $\to$ Red).
  - **Zero-Delay Cruise:** `EV0` cruises through A1, B1, and C1 at 34 km/h with **0.0s delay**.
- **Second Emergency Vehicle (`EV1` — North-South on Col B at $t=120\text{s}$):**
  - Enters from South Ave heading North through Central Boulevard (`B0 -> B1 -> B2`).
  - East-West cross-traffic on all 3 avenues is halted, proving **full multi-axis adaptability**.

### 2. Realistic High-Fidelity SUMO-GUI
- **Authentic 2D Car Bodies:** Vehicles render with real car bodies (`guiShape="passenger/sedan"` and `guiShape="emergency"`), hoods, windshield glass, and trunks.
- **Realistic Color Palette:** Cars spawn in Pearl White, Royal Blue, Metallic Silver, Sunset Amber, and Charcoal Slate, alongside the red ambulance with strobe beacons.
- **Downtown Architectural City Blocks:** Beautiful commercial towers, hospital centers, and urban parks between the intersections.
- **Pre-Focused 260% Zoom:** Centered automatically at `(500, 500)` to fill your screen cleanly on launch.

---

## 🛠 Command Line Interface (CLI)

LaneRush provides an extensive CLI suite powered by Typer:

| Command | Usage | Description |
|---|---|---|
| `ui` | `lanerush ui [--port 8000]` | Launch the React JSX web dashboard and FastAPI backend server. |
| `demo` | `lanerush demo` | Launch the full visual evaluator showcase in SUMO-GUI. |
| `run` | `lanerush run [--gui] [--dry-run]` | Run a simulation under the specified YAML configuration. |
| `scan-fixed` | `lanerush scan-fixed --seeds 101-105` | Scan fixed-timer splits (30s–54s) on tuning seeds to identify the optimal baseline. |
| `sweep` | `lanerush sweep configs/exp_main.yaml --modes all --seeds 1-10 --workers 4` | Run parallel benchmark evaluations across all control modes and test seeds. |
| `analyze` | `lanerush analyze runs/ --out results/` | Compute 95% CIs, paired t-tests, Jain fairness indexes, and generate markdown reports. |

---

## 📈 Benchmark Performance Comparison (Phase 6 Sweep)

Empirical evaluation results averaged across test seeds:

| Metric | Fixed Baseline (42/42) | Fixed Tuned (30/54) | Adaptive (No Aging) | Full Adaptive | Adaptive + Corridor |
|---|---|---|---|---|---|
| **Mean Waiting Time** | 48.1 s [45.2, 51.1] | 40.0 s [37.5, 42.4] | 12.1 s | 10.0 s | **7.4 s (-84.6%)** |
| **EV Transit Duration** | 190.4 s | 128.9 s | 108.4 s | 101.8 s | **97.0 s (-49.1%)** |
| **EV Stopping Delay** | ~45.0 s | ~38.0 s | ~18.0 s | ~12.0 s | **0.0 s (Zero Stop)** |
| **Max Individual Wait** | 195.0 s | 162.0 s | 56.0 s | **30.0 s (-46%)** | **32.0 s** |
| **Jain's Fairness Index** | 0.91 | 0.92 | 0.83 | **0.96** | **0.95** |

---

## 🤖 The Real-World Vision Model (YOLOv8)

- **Training:** Fine-tuned `yolov8n-cls` on 1,066 real-world emergency and passenger vehicle photos (`ml/train_cls.py`).
- **Empirical Test Metrics (`ml/results/metrics.json`):**
  - **EV Detection Recall:** 78.33%
  - **EV Precision:** 82.53%
  - **mAP@50:** 81.25%
  - **False Alarm Rate:** 17.47%
- **Digital Twin Seam:** The `NoisyEmulator` injects this exact empirical error distribution into SUMO's sensor readings with $k$-of-$n$ temporal voting, proving controller stability under real-world camera noise.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Unit test suite (67 unit tests in ~1.0s, no SUMO required)
python -m pytest tests/unit -v -m "not sumo"

# PEP 8 & AST architectural boundary checks
python -m ruff check .
```

---

## 📜 License

This project is licensed under the MIT License.
