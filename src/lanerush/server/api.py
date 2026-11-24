"""FastAPI backend server for LaneRush React Dashboard.

Provides REST and WebSocket endpoints for live simulation monitoring and run replay.
"""

from __future__ import annotations

import csv
import json
import logging
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RUNS_DIR = REPO_ROOT / "runs"

app = FastAPI(
    title="LaneRush Traffic Control API",
    description="Backend API powering the LaneRush React Dashboard",
    version="1.0.0",
)

# Enable CORS for local Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Network Topology Definition (3x3 Grid)
# ---------------------------------------------------------------------------

GRID_TOPOLOGY = {
    "dimensions": {"cols": 3, "rows": 3},
    "junctions": {
        "A0": {"id": "A0", "col": 0, "row": 0, "x": 100, "y": 500, "label": "A0 (SW)"},
        "B0": {"id": "B0", "col": 1, "row": 0, "x": 350, "y": 500, "label": "B0 (S)"},
        "C0": {"id": "C0", "col": 2, "row": 0, "x": 600, "y": 500, "label": "C0 (SE)"},
        "A1": {"id": "A1", "col": 0, "row": 1, "x": 100, "y": 300, "label": "A1 (W)"},
        "B1": {"id": "B1", "col": 1, "row": 1, "x": 350, "y": 300, "label": "B1 (Center)"},
        "C1": {"id": "C1", "col": 2, "row": 1, "x": 600, "y": 300, "label": "C1 (E)"},
        "A2": {"id": "A2", "col": 0, "row": 2, "x": 100, "y": 100, "label": "A2 (NW)"},
        "B2": {"id": "B2", "col": 1, "row": 2, "x": 350, "y": 100, "label": "B2 (N)"},
        "C2": {"id": "C2", "col": 2, "row": 2, "x": 600, "y": 100, "label": "C2 (NE)"},
    },
    "avenues": [
        {"id": "row_0", "name": "South Avenue (Row 0)", "junctions": ["A0", "B0", "C0"]},
        {"id": "row_1", "name": "Main Corridor (Row 1)", "junctions": ["A1", "B1", "C1"]},
        {"id": "row_2", "name": "North Avenue (Row 2)", "junctions": ["A2", "B2", "C2"]},
    ],
    "boulevards": [
        {"id": "col_A", "name": "West Boulevard (Col A)", "junctions": ["A2", "A1", "A0"]},
        {"id": "col_B", "name": "Central Boulevard (Col B)", "junctions": ["B2", "B1", "B0"]},
        {"id": "col_C", "name": "East Boulevard (Col C)", "junctions": ["C2", "C1", "C0"]},
    ],
    "phases": {
        "0": {"direction": "NS", "name": "North-South Green", "conflicting": "EW"},
        "1": {"direction": "NS", "name": "North-South Yellow", "conflicting": "EW"},
        "2": {"direction": "EW", "name": "East-West Green", "conflicting": "NS"},
        "3": {"direction": "EW", "name": "East-West Yellow", "conflicting": "NS"},
    },
}


# ---------------------------------------------------------------------------
# API Schemas
# ---------------------------------------------------------------------------

class StartSimRequest(BaseModel):
    mode: str = "adaptive_corridor"
    max_steps: int = 200
    seed: int = 1
    w_count: float = 1.0
    w_halt: float = 2.0
    w_age: float = 0.8
    eta_threshold: float = 40.0


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/status")
def get_status() -> dict[str, Any]:
    """Return system readiness and available runs count."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs = [d.name for d in RUNS_DIR.iterdir() if d.is_dir()]
    return {
        "status": "online",
        "service": "LaneRush API",
        "runs_count": len(runs),
        "topology": "3x3 Grid Network (9 Traffic Lights)",
    }


@app.get("/api/network")
def get_network() -> dict[str, Any]:
    """Return grid network geometry and junction topology."""
    return GRID_TOPOLOGY


@app.get("/api/runs")
def list_runs() -> list[dict[str, Any]]:
    """Return all available simulation runs sorted newest first."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_list: list[dict[str, Any]] = []

    for d in sorted(RUNS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue

        meta_file = d / "meta.json"
        decisions_file = d / "decisions.csv"
        tripinfo_file = d / "tripinfo.xml"

        mode = "unknown"
        seed = 1
        timestamp = d.name.split("_")[0] if "_" in d.name else ""

        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                mode = meta.get("mode", mode)
                seed = meta.get("seed", seed)
                timestamp = meta.get("timestamp", timestamp)
            except Exception:
                pass

        has_decisions = decisions_file.exists()
        has_tripinfo = tripinfo_file.exists()

        run_list.append({
            "id": d.name,
            "mode": mode,
            "seed": seed,
            "timestamp": timestamp,
            "has_decisions": has_decisions,
            "has_tripinfo": has_tripinfo,
        })

    return run_list


@app.get("/api/runs/{run_id}/data")
def get_run_data(run_id: str) -> dict[str, Any]:
    """Load and return all decisions, trips, and summary metrics for a run."""
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="Run not found")

    decisions_file = run_dir / "decisions.csv"
    trips_file = run_dir / "trips.csv"
    tripinfo_file = run_dir / "tripinfo.xml"
    meta_file = run_dir / "meta.json"

    meta: dict[str, Any] = {}
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 1. Parse decisions.csv
    # Format: t, tls_id, action, target_phase, reason, scores_json
    timesteps: dict[int, dict[str, Any]] = {}
    corridor_events: list[dict[str, Any]] = []

    if decisions_file.exists():
        with open(decisions_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    t = int(row["t"])
                    tid = row["tls_id"]
                    action = row["action"]
                    reason = row["reason"]
                    target_phase = row.get("target_phase")
                    scores = json.loads(row.get("scores_json", "{}"))

                    if t not in timesteps:
                        timesteps[t] = {"t": t, "junctions": {}, "corridor_active": False}

                    timesteps[t]["junctions"][tid] = {
                        "action": action,
                        "target_phase": int(float(target_phase)) if target_phase and target_phase != "" else None,
                        "reason": reason,
                        "scores": scores,
                    }

                    if reason in ("corridor", "corridor_hold"):
                        timesteps[t]["corridor_active"] = True
                        corridor_events.append({
                            "t": t,
                            "tls_id": tid,
                            "action": action,
                            "reason": reason,
                        })
                except Exception:
                    continue

    # 2. Parse departed trips from trips.csv
    departures: list[dict[str, Any]] = []
    if trips_file.exists():
        with open(trips_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    departures.append({
                        "id": row["vehicle_id"],
                        "vtype": row["vtype"],
                        "first_edge": row.get("first_edge", ""),
                        "depart": int(float(row["depart"])),
                    })
                except Exception:
                    continue

    # 3. Parse tripinfo.xml for performance KPIs
    completed_trips: list[dict[str, Any]] = []
    ev_trips: list[dict[str, Any]] = []
    mean_wait = 0.0
    max_wait = 0.0

    if tripinfo_file.exists():
        import xml.etree.ElementTree as ET

        try:
            content = tripinfo_file.read_text(encoding="utf-8", errors="ignore")
            if "<tripinfos" in content and "</tripinfos>" not in content:
                content += "\n</tripinfos>"
            root = ET.fromstring(content)
            waits: list[float] = []

            for elem in root.findall("tripinfo"):
                vid = elem.get("id", "")
                vtype = elem.get("vType", elem.get("vtype", ""))
                duration = float(elem.get("duration", 0.0))
                wait = float(elem.get("waitingTime", 0.0))
                time_loss = float(elem.get("timeLoss", 0.0))

                trip_data = {
                    "id": vid,
                    "vtype": vtype,
                    "duration": duration,
                    "wait": wait,
                    "time_loss": time_loss,
                }
                completed_trips.append(trip_data)

                if vtype == "emergency" or vid.startswith("EV"):
                    ev_trips.append(trip_data)
                else:
                    waits.append(wait)

            if waits:
                mean_wait = sum(waits) / len(waits)
                max_wait = max(waits)
        except Exception:
            pass

    return {
        "run_id": run_id,
        "meta": meta,
        "timesteps": [timesteps[k] for k in sorted(timesteps.keys())],
        "departures": departures,
        "completed_count": len(completed_trips),
        "mean_wait_s": round(mean_wait, 2),
        "max_wait_s": round(max_wait, 2),
        "ev_trips": ev_trips,
        "corridor_events_count": len(corridor_events),
    }


@app.post("/api/sim/start")
def start_simulation(req: StartSimRequest) -> dict[str, Any]:
    """Execute a simulation run in the background."""
    from lanerush.config import LaneRushConfig
    from lanerush.sim.runner import run_simulation

    cfg_path = REPO_ROOT / "configs" / "exp_main.yaml"
    cfg = LaneRushConfig.from_yaml(cfg_path)
    cfg.mode = req.mode
    cfg.sim.seed = req.seed
    cfg.sim.max_steps = req.max_steps
    cfg.sim.gui = False
    cfg.scoring.w_count = req.w_count
    cfg.scoring.w_halt = req.w_halt
    cfg.scoring.w_age = req.w_age
    cfg.corridor.eta_threshold_base = req.eta_threshold

    try:
        run_dir = run_simulation(cfg, port=8820)
        return {
            "status": "success",
            "run_id": run_dir.name,
            "message": f"Simulation completed successfully in {run_dir.name}",
        }
    except Exception as e:
        logger.exception("Simulation execution failed")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# SUMO-GUI Direct Launcher (Evaluator Live Simulation)
# ---------------------------------------------------------------------------

_gui_sim_lock = threading.Lock()
_gui_sim_running = False
_last_gui_run_id: str | None = None


def _run_gui_worker() -> None:
    global _gui_sim_running, _last_gui_run_id
    try:
        from lanerush.config import LaneRushConfig
        from lanerush.sim.runner import run_simulation

        cfg_path = REPO_ROOT / "configs" / "exp_main.yaml"
        cfg = LaneRushConfig.from_yaml(cfg_path)
        cfg.mode = "adaptive_corridor"
        cfg.sim.gui = True
        cfg.sim.max_steps = 280
        run_dir = run_simulation(cfg, port=8835)
        _last_gui_run_id = run_dir.name
        logger.info("SUMO-GUI run completed: %s", run_dir.name)
    except Exception as e:
        logger.exception("SUMO-GUI simulation failed: %s", e)
    finally:
        with _gui_sim_lock:
            _gui_sim_running = False


@app.api_route("/api/sim/launch-gui", methods=["GET", "POST"])
def launch_gui_simulation() -> dict[str, Any]:
    """Launch the exact perfect SUMO-GUI visual simulation on the desktop."""
    global _gui_sim_running
    with _gui_sim_lock:
        if _gui_sim_running:
            return {
                "status": "already_running",
                "message": "SUMO-GUI is already running on your desktop.",
            }
        _gui_sim_running = True

    thread = threading.Thread(target=_run_gui_worker, daemon=True)
    thread.start()

    return {
        "status": "launched",
        "message": "SUMO-GUI launched! Look at your taskbar for the simulation window.",
    }


@app.get("/api/sim/gui-status")
def get_gui_status() -> dict[str, Any]:
    """Check whether a SUMO-GUI simulation is currently active."""
    return {
        "is_running": _gui_sim_running,
        "last_run_id": _last_gui_run_id,
    }


# ---------------------------------------------------------------------------
# Mount React Frontend Static Files (if built)
# ---------------------------------------------------------------------------

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

