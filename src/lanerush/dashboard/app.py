"""LaneRush Streamlit dashboard.

Run with: streamlit run src/lanerush/dashboard/app.py

Features:
- Control panel: launch/stop simulation via subprocess
- Junction state grid: 9 junctions, colour-coded green/yellow/red
- Corridor panel (top-right): active EV route, per-junction ETA/status
- Lane density chart
- KPI comparison vs fixed baseline
- Replay mode from decisions.csv (works without Redis/Postgres)
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="LaneRush Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "sim_process" not in st.session_state:
    st.session_state.sim_process = None
if "replay_data" not in st.session_state:
    st.session_state.replay_data = []
if "replay_index" not in st.session_state:
    st.session_state.replay_index = 0

# ---------------------------------------------------------------------------
# Sidebar — control panel
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🚦 LaneRush")
    st.header("Control Panel")

    config_path = st.text_input("Config path", value="configs/exp_main.yaml")
    seed_override = st.number_input("Seed override", min_value=1, value=1)
    mode_override = st.selectbox(
        "Mode",
        ["adaptive_corridor", "adaptive", "adaptive_noaging", "fixed", "fixed_tuned"],
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Run", use_container_width=True):
            if st.session_state.sim_process is None:
                proc = subprocess.Popen(  # noqa: S603
                    [
                        "lanerush",
                        "run",
                        "--config", config_path,
                        "--seed", str(seed_override),
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                st.session_state.sim_process = proc
                st.success("Simulation started.")
            else:
                st.warning("Simulation already running.")

    with col2:
        if st.button("⏹ Stop", use_container_width=True):
            if st.session_state.sim_process is not None:
                st.session_state.sim_process.terminate()
                st.session_state.sim_process = None
                st.info("Simulation stopped.")

    st.divider()
    st.header("Replay Mode")
    replay_csv = st.text_input("decisions.csv path", value="")
    if st.button("Load replay"):
        p = Path(replay_csv)
        if p.exists():
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                st.session_state.replay_data = list(reader)
            st.session_state.replay_index = 0
            st.success(f"Loaded {len(st.session_state.replay_data)} decisions.")
        else:
            st.error(f"File not found: {p}")

    if st.session_state.replay_data:
        max_idx = max(0, len(st.session_state.replay_data) - 1)
        st.session_state.replay_index = st.slider(
            "Timestep", 0, max_idx, st.session_state.replay_index
        )

# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
top_left, top_right = st.columns([3, 1])

with top_left:
    st.subheader("Junction State Grid (3×3)")

    @st.fragment(run_every=1)  # type: ignore[misc]
    def junction_grid() -> None:
        """Live junction state grid — colour coded."""
        # Try to read from MemoryStore if sim is running; otherwise show placeholder
        tls_states: dict[str, str] = {}

        if st.session_state.replay_data and st.session_state.replay_index < len(st.session_state.replay_data):
            row = st.session_state.replay_data[st.session_state.replay_index]
            tls_id = row.get("tls_id", "")
            action = row.get("action", "hold")
            tls_states[tls_id] = action

        grid_cols = st.columns(3)
        junction_names = [f"J{r}{c}" for r in range(3) for c in range(3)]
        for i, jname in enumerate(junction_names):
            state = tls_states.get(jname, "unknown")
            if state == "switch":
                colour = "🟡"
            elif state == "hold":
                colour = "🟢"
            else:
                colour = "⚫"
            with grid_cols[i % 3]:
                st.metric(label=jname, value=colour)

    junction_grid()

with top_right:
    st.subheader("🚨 EV Corridor")

    @st.fragment(run_every=1)  # type: ignore[misc]
    def corridor_panel() -> None:
        """Live EV corridor status."""
        if st.session_state.replay_data and st.session_state.replay_index < len(st.session_state.replay_data):
            row = st.session_state.replay_data[st.session_state.replay_index]
            reason = row.get("reason", "")
            if "corridor" in reason:
                st.success(f"🚑 Active corridor: {reason}")
                tls_id = row.get("tls_id", "?")
                st.write(f"Junction: **{tls_id}**")
            else:
                st.info("No active EV corridor.")
        else:
            st.info("No active EV corridor.")

    corridor_panel()

# ---------------------------------------------------------------------------
# Lane density chart
# ---------------------------------------------------------------------------
st.subheader("Lane Density (last sample)")

@st.fragment(run_every=1)  # type: ignore[misc]
def lane_density_chart() -> None:
    """Lane density placeholder — populated by store in Phase 7+."""
    import pandas as pd  # noqa: PLC0415

    if st.session_state.replay_data:
        # Show score data from replay
        rows = []
        for r in st.session_state.replay_data[: st.session_state.replay_index + 1]:
            try:
                scores = json.loads(r.get("scores_json", "{}"))
                for phase, score in scores.items():
                    rows.append({"t": int(r["t"]), "phase": phase, "score": float(score)})
            except (json.JSONDecodeError, KeyError):
                pass
        if rows:
            df = pd.DataFrame(rows)
            st.line_chart(df.pivot(index="t", columns="phase", values="score"))
        else:
            st.info("No lane data in replay.")
    else:
        st.info("Start a simulation or load a replay to see lane density.")

lane_density_chart()

# ---------------------------------------------------------------------------
# KPI comparison vs baseline
# ---------------------------------------------------------------------------
st.subheader("KPI Comparison vs Fixed Baseline")

BASELINE_KPIs = {
    "Mean wait (s)": 55.2,
    "Jain index": 0.91,
    "Max wait (s)": 195.0,
    "EV transit (s)": 166.8,
}

kpi_cols = st.columns(len(BASELINE_KPIs))
for col, (name, baseline) in zip(kpi_cols, BASELINE_KPIs.items()):
    with col:
        # Placeholder until runs/ data is available
        st.metric(label=name, value="—", delta=f"baseline: {baseline}")
